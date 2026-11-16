import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import rank  # noqa: E402

CFG = {
    "weights": {"virality": 0.6, "engagement": 0.4},
    "engagement_weights": {"likes": 1, "comments": 2, "saves": 3, "shares": 3},
    "max_duration_sec": 90,
    "period_days": 30,
    "min_views": 10000,
    "top_n": 5,
    "reserve_n": 5,
    "max_per_author": 2,
}
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)


def iso(days_ago: int) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


def cand(id_, **kw):
    base = {
        "id": id_, "platform": "instagram", "url": f"https://x.test/{id_}",
        "author": f"author-{id_}", "caption": "c", "posted_at": iso(5),
        "duration_sec": 30, "views": 50000, "likes": 1000, "comments": 100,
        "shares": 50, "saves": 80, "author_median_views": None,
        "outlier_score": None, "source": "vidiq",
    }
    base.update(kw)
    return base


def write_file(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class RankTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def run_main(self, cands, stdout=None, extra=None):
        src = self.tmp / "candidates.json"
        cfg = self.tmp / "ranking.json"
        write_file(src, {"topic": "t", "generated_at": NOW.isoformat(),
                         "candidates": cands})
        write_file(cfg, CFG)
        out = stdout or io.StringIO()
        with contextlib.redirect_stdout(out):
            code = rank.main([str(src), "--config", str(cfg),
                              "--out-json", str(self.tmp / "ranked.json"),
                              "--out-md", str(self.tmp / "top5.md")]
                             + list(extra or []))
        return code

    def test_missing_metric_is_dropped_not_zeroed(self):
        a = cand("a", views=1000, likes=100, comments=10, shares=5, saves=None)
        b = cand("b", views=1000, likes=100, comments=10, shares=5, saves=0)
        scored = {s["id"]: s for s in rank.score_candidates([a, b], CFG)}
        # a: 135 / (1000 * 6), b: 135 / (1000 * 9)
        self.assertAlmostEqual(scored["a"]["engagement_raw"], 135 / 6000)
        self.assertAlmostEqual(scored["b"]["engagement_raw"], 135 / 9000)
        self.assertGreater(scored["a"]["engagement_raw"],
                           scored["b"]["engagement_raw"])
        self.assertEqual(scored["a"]["missing_metrics"], ["saves"])
        self.assertEqual(scored["b"]["missing_metrics"], [])

    def test_virality_basis_priority(self):
        outlier = cand("o", outlier_score=8, views=50000,
                       author_median_views=10000)
        author = cand("a", views=50000, author_median_views=10000)
        platform = cand("p", views=50000)
        scored = {s["id"]: s for s in
                  rank.score_candidates([outlier, author, platform], CFG)}
        self.assertEqual(scored["o"]["virality_basis"], "outlier")
        self.assertEqual(scored["o"]["virality_raw"], 8)
        self.assertEqual(scored["a"]["virality_basis"], "author")
        self.assertEqual(scored["a"]["virality_raw"], 5.0)
        self.assertEqual(scored["p"]["virality_basis"], "platform")

    def test_percentile_is_per_platform(self):
        cands = [cand("t1", platform="tiktok", views=20000)] + [
            cand(f"i{n}", platform="instagram", views=100000 * (n + 1))
            for n in range(3)]
        scored = {s["id"]: s for s in rank.score_candidates(cands, CFG)}
        self.assertEqual(scored["t1"]["virality_pct"], 1.0)
        self.assertAlmostEqual(scored["i0"]["virality_pct"], 1 / 3)

    def test_score_uses_config_weights(self):
        # a: highest virality, lowest engagement -> pcts 1.0 and 0.5
        a = cand("a", outlier_score=9, views=1000, likes=1, comments=0,
                 shares=0, saves=0)
        b = cand("b", outlier_score=2, views=1000, likes=500, comments=100,
                 shares=50, saves=50)
        scored = {s["id"]: s for s in rank.score_candidates([a, b], CFG)}
        self.assertEqual(scored["a"]["virality_pct"], 1.0)
        self.assertEqual(scored["a"]["engagement_pct"], 0.5)
        self.assertAlmostEqual(scored["a"]["score"], 0.8)

    def test_filters_report_reasons(self):
        cands = [
            cand("dur", duration_sec=120),
            cand("old", posted_at=iso(45)),
            cand("low", views=5000),
            cand("zero", views=0),
            cand("none", views=None),
            cand("ok"),
        ]
        kept, dropped = rank.filter_candidates(cands, CFG, NOW)
        self.assertEqual([c["id"] for c in kept], ["ok"])
        reasons = {d["id"]: d["reason"] for d in dropped}
        self.assertEqual(reasons, {
            "dur": "duration", "old": "period", "low": "min_views",
            "zero": "no_views", "none": "no_views"})

    def test_dedupe_keeps_richer_record(self):
        poor = cand("d1", saves=None, source="vidiq")
        rich = cand("d1", saves=120, source="scrapecreators")
        for order in ([poor, rich], [rich, poor]):
            out = rank.dedupe(copy.deepcopy(order))
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["saves"], 120)

    def test_max_two_per_author(self):
        cands = [cand(f"s{n}", author="star", views=900000 - n * 1000)
                 for n in range(4)]
        cands += [cand(f"o{n}", views=20000 + n) for n in range(4)]
        scored = rank.score_candidates(cands, CFG)
        top = rank.select_top(scored, CFG)["top"]
        self.assertEqual(len(top), 5)
        self.assertEqual(sum(1 for t in top if t["author"] == "star"), 2)

    def test_fewer_than_five_is_not_an_error(self):
        cands = [cand(f"v{n}") for n in range(3)]
        self.assertEqual(self.run_main(cands), 0)
        ranked = json.loads(
            (self.tmp / "ranked.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ranked["top"]), 3)
        md = (self.tmp / "top5.md").read_text(encoding="utf-8")
        self.assertIn("Знайдено лише 3", md)

    def test_reserve_follows_top(self):
        cands = [cand(f"v{n:02d}", views=20000 + n * 1000) for n in range(12)]
        result = rank.select_top(rank.score_candidates(cands, CFG), CFG)
        self.assertEqual(len(result["top"]), 5)
        self.assertEqual(len(result["reserve"]), 5)
        top_ids = {c["id"] for c in result["top"]}
        reserve_ids = {c["id"] for c in result["reserve"]}
        self.assertFalse(top_ids & reserve_ids)

    def test_unicode_caption_does_not_crash_cli(self):
        cands = [cand("u1", caption="Монтаж за 5 хв 🔥")]
        stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1251",
                                  errors="strict")
        self.assertEqual(self.run_main(cands, stdout=stdout), 0)
        md = (self.tmp / "top5.md").read_text(encoding="utf-8")
        self.assertIn("🔥", md)

    def test_markdown_shows_all_numbers(self):
        cands = [cand("m1", views=73421, saves=None),
                 cand("m2", views=64000, outlier_score=4)]
        result = rank.select_top(rank.score_candidates(cands, CFG), CFG)
        md = rank.render_markdown(result, [], CFG)
        for c in result["top"]:
            self.assertIn(str(c["views"]), md)
            self.assertIn("{:.3f}".format(c["score"]), md)
            self.assertIn(c["virality_basis"], md)
            self.assertIn(c["url"], md)
        self.assertIn("saves", md)

    def test_config_missing_key_returns_2(self):
        src = self.tmp / "candidates.json"
        write_file(src, {"topic": "t", "generated_at": NOW.isoformat(),
                         "candidates": [cand("a")]})
        for broken in ({k: v for k, v in CFG.items() if k != "period_days"},
                       {**CFG, "weights": {"virality": 0.6}}):
            cfg = self.tmp / "ranking.json"
            write_file(cfg, broken)
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()),                     contextlib.redirect_stderr(err):
                code = rank.main([str(src), "--config", str(cfg),
                                  "--out-json", str(self.tmp / "r.json"),
                                  "--out-md", str(self.tmp / "t.md")])
            self.assertEqual(code, 2)
            self.assertEqual(len(err.getvalue().strip().splitlines()), 1)

    def test_malformed_records_go_to_dropped(self):
        bad = {
            "notdict": "just a string",
            "badviews": cand("badviews", views="lots"),
            "baddate": cand("baddate", posted_at="yesterday"),
            "nodate": cand("nodate", posted_at=None),
        }
        for name, record in bad.items():
            with self.subTest(name):
                self.assertEqual(self.run_main([record, cand("ok")]), 0)
                ranked = json.loads(
                    (self.tmp / "ranked.json").read_text(encoding="utf-8"))
                self.assertEqual([t["id"] for t in ranked["top"]], ["ok"])
                self.assertEqual(
                    [d["reason"] for d in ranked["dropped"]], ["malformed"])

    def test_unreadable_file_returns_2(self):
        cfg = self.tmp / "ranking.json"
        write_file(cfg, CFG)
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            code = rank.main([str(self.tmp / "missing.json"), "--config",
                              str(cfg), "--out-json", str(self.tmp / "r.json"),
                              "--out-md", str(self.tmp / "t.md")])
        self.assertEqual(code, 2)

    def test_period_days_cli_overrides_config(self):
        """A 90-day run must keep a 60-day-old video the config would drop."""
        cands = [cand("old", posted_at=iso(60)), cand("fresh")]
        self.assertEqual(self.run_main(cands), 0)
        ranked = json.loads((self.tmp / "ranked.json").read_text(encoding="utf-8"))
        self.assertEqual([d["reason"] for d in ranked["dropped"]], ["period"])

        self.assertEqual(self.run_main(cands, extra=["--period-days", "90"]), 0)
        ranked = json.loads((self.tmp / "ranked.json").read_text(encoding="utf-8"))
        self.assertEqual(ranked["dropped"], [])
        self.assertEqual(sorted(t["id"] for t in ranked["top"]), ["fresh", "old"])

    def test_max_duration_sec_cli_overrides_config(self):
        cands = [cand("long", duration_sec=120), cand("short")]
        self.assertEqual(self.run_main(cands), 0)
        ranked = json.loads((self.tmp / "ranked.json").read_text(encoding="utf-8"))
        self.assertEqual([d["reason"] for d in ranked["dropped"]], ["duration"])

        self.assertEqual(
            self.run_main(cands, extra=["--max-duration-sec", "180"]), 0)
        ranked = json.loads((self.tmp / "ranked.json").read_text(encoding="utf-8"))
        self.assertEqual(ranked["dropped"], [])

    def test_dedupe_by_url_when_ids_differ(self):
        """vidIQ and ScrapeCreators give the same reel different id strings."""
        vidiq = cand("3078421556", platform="instagram",
                     url="https://www.instagram.com/reel/C8kQw1xPqRs/",
                     source="vidiq", saves=None)
        scrape = cand("ig_C8kQw1xPqRs", platform="instagram",
                      url="https://instagram.com/reel/C8kQw1xPqRs/?igsh=MXY5",
                      source="scrapecreators", saves=120)
        for order in ([vidiq, scrape], [scrape, vidiq]):
            out = rank.dedupe(copy.deepcopy(order))
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["saves"], 120)

    def test_dedupe_by_url_keeps_different_videos(self):
        a = cand("a", url="https://www.tiktok.com/@u/video/111", platform="tiktok")
        b = cand("b", url="https://www.tiktok.com/@u/video/222", platform="tiktok")
        self.assertEqual(len(rank.dedupe([a, b])), 2)

    def test_non_finite_numbers_are_malformed(self):
        self.assertTrue(rank.is_malformed(cand("inf", views=float("inf"))))
        self.assertTrue(rank.is_malformed(cand("ninf", views=float("-inf"))))
        self.assertTrue(rank.is_malformed(cand("nan", duration_sec=float("nan"))))

    def test_poisoned_infinity_does_not_win_and_output_stays_json(self):
        self.assertEqual(
            self.run_main([cand("poison", views=float("inf")), cand("ok")]), 0)
        text = (self.tmp / "ranked.json").read_text(encoding="utf-8")
        self.assertNotIn("Infinity", text)
        ranked = json.loads(text)
        self.assertEqual([t["id"] for t in ranked["top"]], ["ok"])
        self.assertEqual([d["reason"] for d in ranked["dropped"]], ["malformed"])


if __name__ == "__main__":
    unittest.main()
