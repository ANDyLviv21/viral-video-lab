import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_plugin import validate  # noqa: E402


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_plugin(root: Path, name: str = "x-y") -> None:
    write(root, ".claude-plugin/plugin.json", json.dumps({"name": name}))


class ValidatePluginTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_valid_minimal_plugin_has_no_errors(self):
        make_plugin(self.root)
        self.assertEqual(validate(self.root), [])

    def test_missing_plugin_json(self):
        self.assertIn("plugin.json: missing", validate(self.root))

    def test_name_must_be_kebab_case(self):
        make_plugin(self.root, "Viral Lab")
        self.assertTrue(any("kebab-case" in e for e in validate(self.root)))

    def test_skill_dir_without_skill_md(self):
        make_plugin(self.root)
        (self.root / "skills" / "foo").mkdir(parents=True)
        self.assertTrue(
            any("skills/foo: SKILL.md missing" in e for e in validate(self.root))
        )

    def test_skill_name_must_match_dir(self):
        make_plugin(self.root)
        write(self.root, "skills/foo/SKILL.md",
              "---\nname: bar\ndescription: d\n---\nbody\n")
        self.assertTrue(
            any("name 'bar' != dir 'foo'" in e for e in validate(self.root))
        )

    def test_skill_requires_description(self):
        make_plugin(self.root)
        write(self.root, "skills/foo/SKILL.md", "---\nname: foo\n---\nbody\n")
        self.assertTrue(
            any("skills/foo: description missing" in e for e in validate(self.root))
        )

    def test_allowed_tools_is_forbidden(self):
        make_plugin(self.root)
        write(self.root, "skills/foo/SKILL.md",
              "---\nname: foo\ndescription: d\nallowed-tools: Bash\n---\nbody\n")
        self.assertTrue(
            any("skills/foo: allowed-tools not permitted" in e
                for e in validate(self.root))
        )

    def test_agent_requires_name_description_model_color(self):
        make_plugin(self.root)
        write(self.root, "agents/a.md",
              "---\nname: a\ndescription: d\ncolor: blue\n---\nbody\n")
        self.assertTrue(
            any("agents/a.md: model missing" in e for e in validate(self.root))
        )

    def test_agent_requires_tools(self):
        make_plugin(self.root)
        write(self.root, "agents/a.md",
              "---\nname: a\ndescription: d\nmodel: inherit\ncolor: blue\n---\nbody\n")
        self.assertTrue(
            any("agents/a.md: tools missing" in e for e in validate(self.root))
        )

    def test_referenced_plugin_file_must_exist(self):
        make_plugin(self.root)
        write(self.root, "skills/foo/SKILL.md",
              "---\nname: foo\ndescription: d\n---\nSee ../../references/nope.md\n")
        self.assertTrue(
            any("references/nope.md: referenced but missing" in e
                for e in validate(self.root))
        )

    def test_every_dependency_id_is_documented(self):
        make_plugin(self.root)
        write(self.root, "config/dependencies.json",
              json.dumps([{"id": "watch"}]))
        write(self.root, "DEPENDENCIES.md", "# Dependencies\n")
        self.assertTrue(
            any("DEPENDENCIES.md: 'watch' not documented" in e
                for e in validate(self.root))
        )


if __name__ == "__main__":
    unittest.main()
