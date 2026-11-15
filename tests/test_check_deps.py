import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_deps  # noqa: E402


def no_which(_name):
    return None


def make_item(**overrides):
    item = {
        "id": "x",
        "kind": "skill",
        "name": "watch",
        "required": True,
        "used_by": [3],
        "install_hint": "hint",
        "extra_paths": [],
    }
    item.update(overrides)
    return item


class CheckItemTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)

    def test_skill_found(self):
        skill = self.home / ".claude" / "skills" / "watch"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("x", encoding="utf-8")
        result = check_deps.check_item(make_item(), self.home, no_which)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["id"], "x")

    def test_skill_missing(self):
        result = check_deps.check_item(make_item(), self.home, no_which)
        self.assertEqual(result["status"], "missing")
        expected = self.home / ".claude" / "skills" / "watch" / "SKILL.md"
        self.assertIn(str(expected), result["detail"])

    def test_plugin_found_by_prefix(self):
        plugins = self.home / ".claude" / "plugins"
        plugins.mkdir(parents=True)
        (plugins / "installed_plugins.json").write_text(
            json.dumps({"plugins": {"hyperframes@hyperframes": [{}]}}),
            encoding="utf-8",
        )
        item = make_item(kind="plugin", name="hyperframes")
        self.assertEqual(
            check_deps.check_item(item, self.home, no_which)["status"], "ok"
        )

    def test_plugin_prefix_must_match_whole_name(self):
        plugins = self.home / ".claude" / "plugins"
        plugins.mkdir(parents=True)
        (plugins / "installed_plugins.json").write_text(
            json.dumps({"plugins": {"hyperframes-extra@m": [{}]}}),
            encoding="utf-8",
        )
        item = make_item(kind="plugin", name="hyperframes")
        self.assertEqual(
            check_deps.check_item(item, self.home, no_which)["status"], "missing"
        )

    def test_installed_plugins_json_absent(self):
        item = make_item(kind="plugin", name="hyperframes")
        result = check_deps.check_item(item, self.home, no_which)
        self.assertEqual(result["status"], "missing")

    def test_program_found_via_which(self):
        item = make_item(kind="program", name="ffmpeg")
        result = check_deps.check_item(item, self.home, lambda n: "/bin/" + n)
        self.assertEqual(result["status"], "ok")

    def test_program_found_via_extra_path(self):
        exe = self.home / "whisper-env" / "Scripts" / "whisper.exe"
        exe.parent.mkdir(parents=True)
        exe.write_text("", encoding="utf-8")
        item = make_item(
            kind="program",
            name="whisper",
            extra_paths=["~/whisper-env/Scripts/whisper.exe"],
        )
        result = check_deps.check_item(item, self.home, no_which)
        self.assertEqual(result["status"], "ok")

    def test_program_missing(self):
        item = make_item(kind="program", name="ffmpeg")
        self.assertEqual(
            check_deps.check_item(item, self.home, no_which)["status"], "missing"
        )

    def test_connector_is_manual(self):
        item = make_item(kind="connector", name="ScrapeCreators or vidIQ")
        self.assertEqual(
            check_deps.check_item(item, self.home, no_which)["status"], "manual"
        )


class MainTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def run_main(self, manifest, home, extra=()):
        path = self.tmp / "deps.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_deps.main(
                ["--manifest", str(path), "--home", str(home), *extra]
            )
        return code, out.getvalue()

    def test_exit_code_1_when_required_missing(self):
        code, _ = self.run_main([make_item()], self.tmp)
        self.assertEqual(code, 1)

    def test_exit_code_0_when_only_optional_missing(self):
        code, out = self.run_main([make_item(required=False)], self.tmp)
        self.assertEqual(code, 0)
        self.assertIn("hint", out)

    def test_json_output(self):
        code, out = self.run_main([make_item(required=False)], self.tmp, ["--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["summary"]["optional_missing"], ["x"])

    def test_summarize(self):
        manifest = [make_item(id="a"), make_item(id="b", required=False),
                    make_item(id="c", kind="connector")]
        results = [
            {"id": "a", "status": "missing", "detail": ""},
            {"id": "b", "status": "missing", "detail": ""},
            {"id": "c", "status": "manual", "detail": ""},
        ]
        summary = check_deps.summarize(results, manifest)
        self.assertEqual(summary["required_missing"], ["a"])
        self.assertEqual(summary["optional_missing"], ["b"])
        self.assertEqual(summary["manual"], ["c"])

    def test_cyrillic_home_path_does_not_crash(self):
        home = self.tmp / "Андрій"
        home.mkdir()
        path = self.tmp / "deps.json"
        path.write_text(json.dumps([make_item()]), encoding="utf-8")
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1251", errors="strict")
        old = sys.stdout
        sys.stdout = stream
        try:
            code = check_deps.main(["--manifest", str(path), "--home", str(home)])
            stream.flush()
        finally:
            sys.stdout = old
        self.assertEqual(code, 1)
        self.assertIn("Андрій".encode("cp1251"), raw.getvalue())

    def test_non_cp1251_home_path_does_not_crash(self):
        home = self.tmp / "Андрій-日本"
        home.mkdir()
        path = self.tmp / "deps.json"
        path.write_text(json.dumps([make_item()]), encoding="utf-8")
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1251", errors="strict")
        old = sys.stdout
        sys.stdout = stream
        try:
            code = check_deps.main(["--manifest", str(path), "--home", str(home)])
            stream.flush()
        finally:
            sys.stdout = old
        self.assertEqual(code, 1)
        self.assertIn("Андрій-??".encode("cp1251"), raw.getvalue())

    def test_missing_manifest_returns_2(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_deps.main(["--manifest", str(self.tmp / "nope.json")])
        self.assertEqual(code, 2)
        self.assertEqual(len(out.getvalue().strip().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
