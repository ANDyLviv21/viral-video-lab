"""Dependency checker for the viral-video-lab plugin (standard library only).

Usage: py -3.12 scripts/check_deps.py --manifest <dependencies.json> [--json]
Exit code 0 when every required dependency is present, 1 otherwise.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def load_manifest(path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("manifest must be a JSON array")
    return data


def _expand(raw: str, home: Path) -> Path:
    if raw == "~":
        return home
    if raw.startswith("~/") or raw.startswith("~\\"):
        return home / raw[2:]
    return Path(raw)


def _installed_plugin_keys(home: Path) -> list[str]:
    path = home / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    plugins = data.get("plugins")
    if isinstance(plugins, dict):
        return list(plugins)
    return list(data)


def check_item(item: dict, home: Path, which=shutil.which) -> dict:
    """Check one manifest entry; status is ok, missing or manual."""
    home = Path(home)
    kind = item.get("kind")
    name = item.get("name", "")
    result = {"id": item.get("id", name), "status": "missing", "detail": ""}
    if kind == "skill":
        path = home / ".claude" / "skills" / name / "SKILL.md"
        if path.is_file():
            result.update(status="ok", detail=str(path))
        else:
            result["detail"] = f"немає файла {path}"
    elif kind == "plugin":
        keys = _installed_plugin_keys(home)
        if any(key.startswith(f"{name}@") for key in keys):
            result.update(status="ok", detail=f"плагін {name} встановлено")
        else:
            result["detail"] = f"плагін {name} не знайдено в installed_plugins.json"
    elif kind == "program":
        found = which(name)
        if not found:
            for raw in item.get("extra_paths", []):
                candidate = _expand(raw, home)
                if candidate.is_file():
                    found = str(candidate)
                    break
        if found:
            result.update(status="ok", detail=str(found))
        else:
            result["detail"] = f"програму {name} не знайдено ні в PATH, ні в extra_paths"
    elif kind == "connector":
        result.update(
            status="manual",
            detail="конектор скрипт перевірити не може: перевіряє скіл viral-lab-setup",
        )
    else:
        result["detail"] = f"невідомий kind: {kind}"
    return result


def summarize(results: list[dict], manifest: list[dict]) -> dict:
    required = {m.get("id", m.get("name")): bool(m.get("required")) for m in manifest}
    summary = {"required_missing": [], "optional_missing": [], "manual": []}
    for res in results:
        if res["status"] == "manual":
            summary["manual"].append(res["id"])
        elif res["status"] == "missing":
            key = "required_missing" if required.get(res["id"]) else "optional_missing"
            summary[key].append(res["id"])
    return summary


def _print_block(title, ids, by_id) -> None:
    print(title)
    if not ids:
        print("  (немає)")
    for dep_id in ids:
        item, res = by_id[dep_id]
        stages = ", ".join(str(s) for s in item.get("used_by", []))
        print(f"  - {dep_id} (етапи: {stages}): {res['detail']}")
        if item.get("install_hint"):
            print(f"    як встановити: {item['install_hint']}")


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Перевірка залежностей viral-video-lab")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--home", default=None, help="домашня папка (для тестів)")
    args = parser.parse_args(argv)

    home = Path(args.home) if args.home else Path.home()
    manifest = load_manifest(args.manifest)
    results = [check_item(item, home) for item in manifest]
    summary = summarize(results, manifest)

    if args.as_json:
        print(json.dumps({"results": results, "summary": summary}, ensure_ascii=True))
    else:
        by_id = {
            res["id"]: (item, res) for item, res in zip(manifest, results)
        }
        print(f"Домашня папка: {home}")
        _print_block("Обов'язкове (відсутнє):", summary["required_missing"], by_id)
        _print_block("Додаткове (відсутнє):", summary["optional_missing"], by_id)
        _print_block("Перевірити вручну:", summary["manual"], by_id)
        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"Знайдено: {ok} з {len(results)}")
    return 1 if summary["required_missing"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
