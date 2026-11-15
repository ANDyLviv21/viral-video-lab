"""Structure validator for the viral-video-lab plugin (standard library only).

Usage: py -3.12 scripts/validate_plugin.py [root]
Exit code 0 when the plugin is valid, 1 otherwise.
"""
import json
import re
import sys
from pathlib import Path

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REF_RE = re.compile(r"(?<![\w-])(?:references|scripts|config)/[\w./-]+")
AGENT_REQUIRED = ("name", "description", "model", "color")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse `key: value` lines between the first two `---` lines."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key.strip() and not line[0].isspace():
            fields[key.strip()] = value.strip()
    return fields


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_manifest(root: Path, errors: list[str]) -> None:
    manifest = root / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        errors.append("plugin.json: missing")
        return
    try:
        data = json.loads(_read(manifest))
    except json.JSONDecodeError as exc:
        errors.append(f"plugin.json: invalid JSON ({exc.msg})")
        return
    name = data.get("name") if isinstance(data, dict) else None
    if not isinstance(name, str) or not name:
        errors.append("plugin.json: name missing")
    elif not KEBAB_RE.match(name):
        errors.append(f"plugin.json: name '{name}' must be kebab-case")


def _check_skills(root: Path, errors: list[str]) -> list[Path]:
    files: list[Path] = []
    skills = root / "skills"
    if not skills.is_dir():
        return files
    for skill_dir in sorted(p for p in skills.iterdir() if p.is_dir()):
        label = f"skills/{skill_dir.name}"
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{label}: SKILL.md missing")
            continue
        files.append(skill_md)
        fm = parse_frontmatter(_read(skill_md))
        name = fm.get("name")
        if not name:
            errors.append(f"{label}: name missing")
        elif name != skill_dir.name:
            errors.append(f"{label}: name '{name}' != dir '{skill_dir.name}'")
        if not fm.get("description"):
            errors.append(f"{label}: description missing")
        if "allowed-tools" in fm:
            errors.append(f"{label}: allowed-tools not permitted")
    return files


def _check_agents(root: Path, errors: list[str]) -> list[Path]:
    files: list[Path] = []
    agents = root / "agents"
    if not agents.is_dir():
        return files
    for agent_md in sorted(agents.glob("*.md")):
        files.append(agent_md)
        label = f"agents/{agent_md.name}"
        fm = parse_frontmatter(_read(agent_md))
        for key in AGENT_REQUIRED:
            if not fm.get(key):
                errors.append(f"{label}: {key} missing")
        if "allowed-tools" in fm:
            errors.append(f"{label}: allowed-tools not permitted")
    return files


def _check_references(root: Path, files: list[Path], errors: list[str]) -> None:
    seen: set[tuple[str, str]] = set()
    for path in files:
        label = path.relative_to(root).as_posix()
        for match in REF_RE.findall(_read(path)):
            ref = match.rstrip(".")
            if (label, ref) in seen:
                continue
            seen.add((label, ref))
            if not (root / ref).exists():
                errors.append(f"{ref}: referenced but missing (in {label})")


def _check_dependencies(root: Path, errors: list[str]) -> None:
    manifest = root / "config" / "dependencies.json"
    if not manifest.is_file():
        return
    try:
        entries = json.loads(_read(manifest))
    except json.JSONDecodeError as exc:
        errors.append(f"config/dependencies.json: invalid JSON ({exc.msg})")
        return
    doc = root / "DEPENDENCIES.md"
    doc_text = _read(doc) if doc.is_file() else ""
    if not doc.is_file():
        errors.append("DEPENDENCIES.md: missing")
    for entry in entries if isinstance(entries, list) else []:
        dep_id = entry.get("id") if isinstance(entry, dict) else None
        if dep_id and dep_id not in doc_text:
            errors.append(f"DEPENDENCIES.md: '{dep_id}' not documented")


def validate(root: Path) -> list[str]:
    """Return a list of error strings; an empty list means the plugin is valid."""
    root = Path(root)
    errors: list[str] = []
    _check_manifest(root, errors)
    files = _check_skills(root, errors) + _check_agents(root, errors)
    _check_references(root, files, errors)
    _check_dependencies(root, errors)
    return errors


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    root = Path(argv[0]) if argv else Path.cwd()
    errors = validate(root)
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"{len(errors)} error(s)")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
