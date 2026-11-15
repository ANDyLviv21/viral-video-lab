"""Top-N ranking of viral short-video candidates.

Usage:
    py -3.12 scripts/rank.py <candidates.json> --config <ranking.json>
        --out-json <ranked.json> --out-md <top5.md>

Exit codes: 0 success (even with fewer than top_n videos, and even when some
candidate records are malformed: those go to "dropped" with reason "malformed");
2 when the candidates file is unreadable, not JSON, has no "candidates" list or
a bad "generated_at", or when the config is unreadable or lacks a required key.
Standard library only. Console output is ASCII only.
"""
import argparse
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIELDS = ("id", "platform", "url", "author", "caption", "posted_at",
          "duration_sec", "views", "likes", "comments", "shares", "saves",
          "author_median_views", "outlier_score", "source")
ENGAGEMENT_METRICS = ("likes", "comments", "saves", "shares")


def parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_candidates(path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("candidates"), list):
        raise ValueError("candidates file must be an object with a 'candidates' list")
    return data


NUMERIC_FIELDS = ("duration_sec", "views", "likes", "comments", "shares",
                  "saves", "author_median_views", "outlier_score")


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_config(cfg) -> None:
    """Raise ValueError naming the first missing or invalid config key."""
    if not isinstance(cfg, dict):
        raise ValueError("config must be a JSON object")
    for key in ("max_duration_sec", "period_days", "min_views", "top_n",
                "reserve_n", "max_per_author"):
        if not _is_number(cfg.get(key)):
            raise ValueError("config key missing or not a number: " + key)
    for group, names in (("weights", ("virality", "engagement")),
                         ("engagement_weights", ENGAGEMENT_METRICS)):
        sub = cfg.get(group)
        if not isinstance(sub, dict):
            raise ValueError("config key missing or not an object: " + group)
        for name in names:
            if not _is_number(sub.get(name)):
                raise ValueError("config key missing or not a number: {}.{}"
                                 .format(group, name))


def is_malformed(c) -> bool:
    if not isinstance(c, dict):
        return True
    if not isinstance(c.get("platform"), str) or c.get("id") is None:
        return True
    if any(c.get(f) is not None and not _is_number(c[f]) for f in NUMERIC_FIELDS):
        return True
    posted = c.get("posted_at")
    if not isinstance(posted, str):
        return True
    try:
        parse_iso(posted)
    except ValueError:
        return True
    return False


def split_malformed(cands: list) -> tuple:
    good, bad = [], []
    for c in cands:
        if is_malformed(c):
            bad.append({**c, "reason": "malformed"} if isinstance(c, dict)
                       else {"raw": c, "reason": "malformed"})
        else:
            good.append(c)
    return good, bad


def filled(c: dict) -> int:
    return sum(1 for f in FIELDS if c.get(f) is not None)


def dedupe(cands: list) -> list:
    """One record per (platform, id): the one with more non-null fields; tie -> first."""
    best: dict = {}
    for c in cands:
        key = (c.get("platform"), c.get("id"))
        if key not in best or filled(c) > filled(best[key]):
            best[key] = c
    return list(best.values())


def filter_candidates(cands: list, cfg: dict, now: datetime) -> tuple:
    kept, dropped = [], []
    cutoff = now - timedelta(days=cfg["period_days"])
    for c in cands:
        views = c.get("views")
        duration = c.get("duration_sec")
        posted = c.get("posted_at")
        reason = None
        if not views:
            reason = "no_views"
        elif duration is not None and duration > cfg["max_duration_sec"]:
            reason = "duration"
        elif posted is not None and parse_iso(posted) < cutoff:
            reason = "period"
        elif views < cfg["min_views"]:
            reason = "min_views"
        if reason:
            dropped.append({**c, "reason": reason})
        else:
            kept.append(c)
    return kept, dropped


def engagement_raw(c: dict, weights: dict) -> tuple:
    present = [m for m in ENGAGEMENT_METRICS if c.get(m) is not None]
    missing = [m for m in ENGAGEMENT_METRICS if c.get(m) is None]
    weight_sum = sum(weights[m] for m in present)
    if not present or not weight_sum:
        return 0.0, missing
    total = sum(weights[m] * c[m] for m in present)
    return total / (c["views"] * weight_sum), missing


def virality_raw(c: dict, platform_median: float) -> tuple:
    if c.get("outlier_score") is not None:
        return c["outlier_score"], "outlier"
    median = c.get("author_median_views")
    if median:
        return c["views"] / median, "author"
    return c["views"] / platform_median, "platform"


def percentile(value, values: list) -> float:
    return sum(1 for v in values if v <= value) / len(values)


def score_candidates(cands: list, cfg: dict) -> list:
    by_platform: dict = {}
    for c in cands:
        by_platform.setdefault(c["platform"], []).append(c)
    medians = {p: statistics.median(x["views"] for x in group)
               for p, group in by_platform.items()}

    scored = []
    for c in cands:
        v_raw, basis = virality_raw(c, medians[c["platform"]])
        e_raw, missing = engagement_raw(c, cfg["engagement_weights"])
        scored.append({**c, "virality_raw": v_raw, "virality_basis": basis,
                       "engagement_raw": e_raw, "missing_metrics": missing})

    for platform in by_platform:
        peers = [s for s in scored if s["platform"] == platform]
        v_all = [s["virality_raw"] for s in peers]
        e_all = [s["engagement_raw"] for s in peers]
        for s in peers:
            s["virality_pct"] = percentile(s["virality_raw"], v_all)
            s["engagement_pct"] = percentile(s["engagement_raw"], e_all)

    w = cfg["weights"]
    for s in scored:
        s["score"] = (w["virality"] * s["virality_pct"]
                      + w["engagement"] * s["engagement_pct"])
    return scored


def select_top(scored: list, cfg: dict) -> dict:
    """Walk the sorted list; skip an author's video once max_per_author are
    already selected (top and reserve share one counter)."""
    ordered = sorted(scored, key=lambda s: (-s["score"], -(s["views"] or 0),
                                            str(s["id"])))
    top, reserve, per_author = [], [], {}
    for s in ordered:
        if len(top) >= cfg["top_n"] and len(reserve) >= cfg["reserve_n"]:
            break
        author = s.get("author")
        if author is not None and per_author.get(author, 0) >= cfg["max_per_author"]:
            continue
        target = top if len(top) < cfg["top_n"] else reserve
        target.append(s)
        if author is not None:
            per_author[author] = per_author.get(author, 0) + 1
    return {"top": top, "reserve": reserve}


def _video_block(rank_no: int, s: dict) -> list:
    missing = ", ".join(s["missing_metrics"]) if s["missing_metrics"] else "немає"
    caption = " ".join((s.get("caption") or "").split())
    return [
        "### {}. {} / {}".format(rank_no, s["platform"], s.get("author") or "?"),
        "- Посилання: {}".format(s["url"]),
        "- Перегляди: {}".format(s["views"]),
        "- Бал: {:.3f} (вірусність {:.3f}, залученість {:.3f})".format(
            s["score"], s["virality_pct"], s["engagement_pct"]),
        "- Основа вірусності: {} (сире значення {:.3f})".format(
            s["virality_basis"], s["virality_raw"]),
        "- Немає метрик: {}".format(missing),
        "- Опис: {}".format(caption),
        "",
    ]


def render_markdown(result: dict, dropped: list, cfg: dict) -> str:
    top, reserve = result["top"], result["reserve"]
    lines = ["# Топ відео: {}".format(result.get("topic") or ""), ""]
    if len(top) < cfg["top_n"]:
        lines += ["Знайдено лише {} з {} запланованих відео.".format(
            len(top), cfg["top_n"]), ""]
    for i, s in enumerate(top, 1):
        lines += _video_block(i, s)
    if reserve:
        lines += ["## Резерв", ""]
        for i, s in enumerate(reserve, len(top) + 1):
            lines += _video_block(i, s)
    if dropped:
        lines += ["## Відкинуто", ""]
        for d in dropped:
            lines.append("- {} ({}): {}".format(d.get("id"), d.get("platform"),
                                                d["reason"]))
        lines.append("")
    return "\n".join(lines)


def _ascii(text) -> str:
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def _write(path: str, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Rank viral video candidates.")
    ap.add_argument("candidates")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args(argv)

    try:
        data = load_candidates(args.candidates)
        with open(args.config, encoding="utf-8") as fh:
            cfg = json.load(fh)
        validate_config(cfg)
        now = parse_iso(data["generated_at"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("error: cannot read input: {}".format(_ascii(exc)), file=sys.stderr)
        return 2

    good, malformed = split_malformed(data["candidates"])
    kept, dropped = filter_candidates(dedupe(good), cfg, now)
    dropped = malformed + dropped
    result = select_top(score_candidates(kept, cfg), cfg)
    result.update({"topic": data.get("topic"),
                   "generated_at": data["generated_at"]})
    output = {"topic": result["topic"], "generated_at": result["generated_at"],
              "top": result["top"], "reserve": result["reserve"],
              "dropped": dropped}
    _write(args.out_json, json.dumps(output, ensure_ascii=False, indent=2))
    _write(args.out_md, render_markdown(result, dropped, cfg))
    print("top: {}, reserve: {}, dropped: {}".format(
        len(result["top"]), len(result["reserve"]), len(dropped)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
