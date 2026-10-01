#!/usr/bin/env python3
"""check_version.py — Valida VERSION, manifest y schemas (F123)

Forma de uso:
  python3 scripts/check_version.py                       # validaciones básicas
  python3 scripts/check_version.py --propose-bump         # propone tipo de bump
  python3 scripts/check_version.py --all                  # todo + git status clean
  python3 scripts/check_version.py --compat-check --artifact-type ledger --produced-version 2.0.0 --validating-version 0.1.0-dev
                                                       # validación cross-version

Verificaciones (modo default):
  1. VERSION existe y parsea como SemVer 2.0.0.
  2. Cada schema en skill/notemartin-study-notes/schemas/ tiene schema_version const.
  3. Si existe un .skill previo en dist/, su manifest.json::version == VERSION.

Verificaciones extra (--all):
  4. git status --porcelain vacío.
  5. CHANGELOG.md tiene una entrada para VERSION actual.

--propose-bump:
  Compara git diff <last-tag>..HEAD -- schemas/ y propone MAJOR/MINOR/PATCH.
  Sin tag previo: propone "initial release".

--compat-check:
  Aplica la regla de COMPATIBILITY.md §1.

Exit codes:
  0  PASS — todas las validaciones pasan
  1  FAIL — alguna validación falla
  2  USAGE — args inválidos

Dependencias: stdlib puro + jsonschema opcional (no requerido).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "VERSION"
SCHEMAS_DIR = REPO_ROOT / "skill" / "notemartin-study-notes" / "schemas"
DIST_DIR = REPO_ROOT / "dist"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_RUNTIME = 2

SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def _read_version() -> str | None:
    if not VERSION_FILE.exists():
        return None
    text = VERSION_FILE.read_text(encoding="utf-8").strip()
    return text if text else None


def _parse_semver(v: str) -> dict | None:
    m = SEMVER_RE.match(v)
    if not m:
        return None
    return {
        "major": int(m.group("major")),
        "minor": int(m.group("minor")),
        "patch": int(m.group("patch")),
        "prerelease": m.group("prerelease") or "",
        "build": m.group("build") or "",
    }


def _check_version_format() -> tuple[bool, str]:
    v = _read_version()
    if v is None:
        return False, "VERSION file no existe o está vacío"
    parsed = _parse_semver(v)
    if parsed is None:
        return False, f"VERSION no es semver válido: {v!r}"
    return True, f"VERSION = {v} (parsed OK)"


def _check_schemas() -> tuple[bool, str]:
    if not SCHEMAS_DIR.exists():
        return False, f"schemas dir no existe: {SCHEMAS_DIR}"
    schema_files = sorted(SCHEMAS_DIR.glob("*.schema.json"))
    if not schema_files:
        return False, "no hay schemas en schemas/"
    missing_const: list[str] = []
    for f in schema_files:
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            return False, f"JSON inválido en {f.name}: {e}"
        sv = data.get("properties", {}).get("schema_version", {})
        const = sv.get("const")
        if not const:
            missing_const.append(f.name)
    if missing_const:
        return False, f"schemas sin schema_version const: {missing_const}"
    return True, f"{len(schema_files)} schemas OK (todas con schema_version const)"


def _check_manifest_version() -> tuple[bool, str]:
    """Verifica que el último .skill de dist/ tenga manifest.json::version == VERSION."""
    if not DIST_DIR.exists():
        return True, "no dist/ presente (skip manifest check)"
    skills = sorted(DIST_DIR.glob("*.skill"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not skills:
        return True, "no .skill previo en dist/ (skip manifest check)"
    latest = skills[0]
    try:
        import zipfile

        with zipfile.ZipFile(latest, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return False, f"{latest.name}: sin manifest.json"
            manifest = json.loads(zf.read("manifest.json"))
    except (zipfile.BadZipFile, json.JSONDecodeError) as e:
        return False, f"{latest.name}: error leyendo manifest.json: {e}"
    manifest_v = manifest.get("version")
    repo_v = _read_version()
    if manifest_v != repo_v:
        return False, f"{latest.name}: manifest.version={manifest_v!r} != VERSION={repo_v!r}"
    return True, f"{latest.name}: manifest.version = {manifest_v} == VERSION"


def _check_changelog() -> tuple[bool, str]:
    if not CHANGELOG.exists():
        return False, "CHANGELOG.md no existe"
    text = CHANGELOG.read_text(encoding="utf-8")
    version = _read_version()
    if version is None:
        return False, "VERSION ausente"
    # Strip prerelease tag for matching (e.g. 0.1.0-dev matches "[0.1.0-dev]")
    if f"[{version}]" not in text:
        return False, f"CHANGELOG.md no tiene entrada para [{version}]"
    return True, f"CHANGELOG.md tiene entrada [{version}]"


def _check_git_clean() -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True, "git no disponible (skip clean check)"
    if r.returncode != 0:
        return True, f"git status exit={r.returncode} (skip)"
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    if lines:
        return False, f"git status no limpio: {len(lines)} entries"
    return True, "git status clean"


def _check_compat(produced: str, validating: str, artifact_type: str = "ledger") -> tuple[bool, str]:
    """Aplica la regla de COMPATIBILITY.md §1."""
    p = _parse_semver(produced)
    v = _parse_semver(validating)
    if not p or not v:
        return False, f"semver inválido: produced={produced!r} validating={validating!r}"

    p_pre = p["prerelease"]
    v_pre = v["prerelease"]

    if p["major"] != v["major"]:
        if p["major"] > v["major"]:
            return True, f"OK (forward compat): produced {p['major']}.x.y > validating {v['major']}.x.y"
        return False, f"REJECT (major incompatible): produced {p['major']}.x.y < validating {v['major']}.x.y"
    # Same major.
    if p_pre or v_pre:
        # Pre-release: not strictly stable; treat same as same major.
        return True, f"OK (same major, pre-release): {p['major']}.x.y (pre={p_pre or '-'}/{v_pre or '-'})"
    return True, f"OK (same major): produced {p['major']}.{p['minor']}.{p['patch']} accepted by {v['major']}.{v['minor']}.{v['patch']}"


def _propose_bump() -> tuple[bool, str]:
    """Compara git diff <last-tag>..HEAD -- schemas/ y propone MAJOR/MINOR/PATCH."""
    try:
        last_tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=str(REPO_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True, "no previous tag → initial release (cualquier bump type válido)"

    diff = subprocess.run(
        ["git", "diff", f"{last_tag}..HEAD", "--", "schemas/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if diff.returncode != 0:
        return True, f"git diff exit={diff.returncode} (skip bump proposal)"
    if not diff.stdout.strip():
        return True, "no schema changes → PATCH"

    # Detectar tipo: cambio de const X.0.0 → Y.0.0 con X != Y = MAJOR.
    major_change = re.search(r'-\s*"const":\s*"\d+\.0\.0"', diff.stdout)
    add_change = re.search(r'^\+\s*"[a-z_]+":\s*\{', diff.stdout, re.MULTILINE)
    if major_change:
        return True, f"Proposed bump: MAJOR (schema_version const changed in {last_tag}..HEAD)"
    if add_change:
        return True, f"Proposed bump: MINOR (new properties added in {last_tag}..HEAD)"
    return True, f"Proposed bump: PATCH (only minor schema changes in {last_tag}..HEAD)"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Valida VERSION, manifest y schemas (F123)")
    p.add_argument("--all", action="store_true", help="Todas las validaciones + git status clean")
    p.add_argument("--propose-bump", action="store_true", help="Propone MAJOR/MINOR/PATCH según git diff")
    p.add_argument(
        "--compat-check",
        action="store_true",
        help="Modo compat-check (requiere --artifact-type, --produced-version, --validating-version)",
    )
    p.add_argument("--artifact-type", default="ledger", help="Tipo de artefacto para --compat-check")
    p.add_argument("--produced-version", default=None, help="Versión que produjo el artefacto")
    p.add_argument("--validating-version", default=None, help="Versión del validador")
    args = p.parse_args(argv)

    if args.compat_check:
        if not args.produced_version or not args.validating_version:
            print("ERROR: --compat-check requiere --produced-version y --validating-version", file=sys.stderr)
            return EXIT_RUNTIME
        ok, msg = _check_compat(args.produced_version, args.validating_version, args.artifact_type)
        print(("PASS" if ok else "FAIL") + ": " + msg)
        return EXIT_OK if ok else EXIT_FAIL

    if args.propose_bump:
        ok, msg = _propose_bump()
        print(("PASS" if ok else "FAIL") + ": " + msg)
        return EXIT_OK if ok else EXIT_FAIL

    checks = [
        ("[1/3] VERSION format", _check_version_format()),
        ("[2/3] schemas schema_version const", _check_schemas()),
        ("[3/3] manifest.version == VERSION", _check_manifest_version()),
    ]
    if args.all:
        checks.extend(
            [
                ("[4/5] git status clean", _check_git_clean()),
                ("[5/5] CHANGELOG entry for current VERSION", _check_changelog()),
            ]
        )

    all_pass = True
    for name, (ok, msg) in checks:
        marker = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  {marker} {name}: {msg}")

    return EXIT_OK if all_pass else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
