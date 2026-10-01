#!/usr/bin/env python3
"""smoke_test.py — Caso de humo del .skill (F122)

Forma de uso:
  python3 scripts/smoke_test.py --skill dist/notemartin-study-notes-0.1.0-dev.skill
  python3 scripts/smoke_test.py --skill <path> --workdir /tmp/smoke

5 verificaciones obligatorias (todas deben pasar):
  1. Desempaquetar el ZIP en --workdir (default /tmp/smoke-<random>).
  2. SKILL.md parsea el frontmatter (name + description presentes, YAML válido).
  3. Las rutas `references/.../*.md` mencionadas en SKILL.md existen en el workdir.
  4. `<workdir>/scripts/check_deps.py` corre sin exit fatal.
  5. Tamaño total ≤ 8 MB (SIZE_LIMIT_BYTES).

Exit codes:
  0  PASS — todas las verificaciones pasan
  1  FAIL — alguna verificación falla
  2  USAGE / error de runtime

Dependencias: stdlib puro (zipfile, yaml opcional, pathlib, re).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_RUNTIME = 2

SIZE_LIMIT_BYTES = 8 * 1024 * 1024  # 8 MB
SKILL_LINE_LIMIT = 500  # INV-02 (warning, no fail)


def _load_yaml(text: str) -> dict | None:
    """Carga YAML simple. Si PyYAML no está, parser mínimo para el frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    body = text[3:end].strip()
    try:
        import yaml  # type: ignore

        return yaml.safe_load(body)
    except ImportError:
        out: dict = {}
        for line in body.splitlines():
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
        return out


def _unpack(skill_path: Path, workdir: Path) -> tuple[int, str]:
    """Desempaqueta el ZIP en workdir. Devuelve (exit, mensaje)."""
    try:
        with zipfile.ZipFile(skill_path, "r") as zf:
            zf.extractall(workdir)
        return 0, f"unpacked {len(zipfile.ZipFile(skill_path).namelist())} entries"
    except (zipfile.BadZipFile, FileNotFoundError, PermissionError) as e:
        return 1, f"unpack failed: {e}"


def _check_skill_md(workdir: Path) -> tuple[int, str]:
    """Verifica que SKILL.md existe y su frontmatter parsea con name+description."""
    skill_md = workdir / "SKILL.md"
    if not skill_md.exists():
        return 1, f"SKILL.md no existe en {workdir}"
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return 1, "SKILL.md no tiene frontmatter (no empieza con '---')"
    end = text.find("\n---", 3)
    if end == -1:
        return 1, "SKILL.md frontmatter no cierra con '---'"
    fm = _load_yaml(text)
    if fm is None:
        return 1, "SKILL.md frontmatter no parsea como YAML"
    if "name" not in fm or "description" not in fm:
        return 1, f"SKILL.md frontmatter falta name/description: keys={list(fm.keys())}"
    line_count = text.count("\n") + 1
    if line_count > SKILL_LINE_LIMIT:
        # Warning, no fail.
        print(f"  WARN: SKILL.md tiene {line_count} líneas (INV-02: límite {SKILL_LINE_LIMIT})")
    return 0, f"frontmatter OK (name={fm.get('name')!r} desc_len={len(fm.get('description', ''))})"


def _check_references(workdir: Path) -> tuple[int, str]:
    """Verifica que las rutas references/* mencionadas en SKILL.md existen."""
    skill_md = workdir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    # Patrón: references/NN-name/file.md (sin caracteres raros)
    pattern = re.compile(r"`?(references/[a-z0-9-]+/[a-z0-9_.-]+\.md)`?", re.MULTILINE)
    refs = sorted(set(pattern.findall(text)))
    if not refs:
        return 0, "no references/ paths found in SKILL.md (skipping)"
    missing: list[str] = []
    for ref in refs:
        if not (workdir / ref).exists():
            missing.append(ref)
    if missing:
        return 1, f"missing {len(missing)} references: {missing[:5]}"
    return 0, f"{len(refs)} references resolubles"


def _check_deps_script(workdir: Path) -> tuple[int, str]:
    """Verifica que scripts/check_deps.py existe y ejecuta sin error fatal."""
    check_deps = workdir / "scripts" / "check_deps.py"
    if not check_deps.exists():
        # F117 puede haber marcado scripts/check_deps.py como pendiente; en ese
        # caso, verificar que al menos existe un script cualquiera.
        scripts_dir = workdir / "scripts"
        if not scripts_dir.exists() or not any(scripts_dir.glob("*.py")):
            return 1, f"scripts/ vacío o ausente (no hay check_deps.py ni alternativa)"
        return 0, "scripts/ presente (sin check_deps.py, F117 pendiente)"
    try:
        r = subprocess.run(
            ["python3", str(check_deps)],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        # F117 emite exit 0/1/2/3 según severidad; cualquier exit != 0 no es fatal
        # para el smoke test (puede haber deps opt/rec faltantes sin afectar carga).
        if r.returncode > 3:
            return 1, f"check_deps.py exit={r.returncode} stderr={r.stderr[:200]}"
        return 0, f"check_deps.py exit={r.returncode}"
    except subprocess.TimeoutExpired:
        return 1, "check_deps.py timeout (>30s)"
    except FileNotFoundError:
        return 1, "python3 no encontrado"


def _check_size(skill_path: Path) -> tuple[int, str]:
    """Verifica que el .skill no excede SIZE_LIMIT_BYTES."""
    size = skill_path.stat().st_size
    if size > SIZE_LIMIT_BYTES:
        return 1, f"size={size} > limit={SIZE_LIMIT_BYTES}"
    return 0, f"size={size} bytes ({size / 1024 / 1024:.2f} MB)"


def smoke_test(skill_path: Path, workdir: Path | None = None) -> int:
    print(f"=== smoke test: {skill_path} ===")
    cleanup_workdir = False
    if workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="smoke-"))
        cleanup_workdir = True

    try:
        checks = [
            ("[1/5] unpack", _unpack(skill_path, workdir)),
            ("[2/5] SKILL.md frontmatter", _check_skill_md(workdir)),
            ("[3/5] references resolubles", _check_references(workdir)),
            ("[4/5] check_deps.py", _check_deps_script(workdir)),
            ("[5/5] size limit", _check_size(skill_path)),
        ]
        all_pass = True
        for name, (rc, msg) in checks:
            marker = "PASS" if rc == 0 else "FAIL"
            if rc != 0:
                all_pass = False
            print(f"  {marker} {name}: {msg}")
        return EXIT_OK if all_pass else EXIT_FAIL
    finally:
        if cleanup_workdir and workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Caso de humo del .skill")
    p.add_argument("--skill", required=True, help="Ruta al .skill")
    p.add_argument("--workdir", default=None, help="Directorio temporal (default: auto)")
    args = p.parse_args(argv)

    skill_path = Path(args.skill)
    if not skill_path.exists():
        print(f"ERROR: skill no existe: {skill_path}", file=sys.stderr)
        return EXIT_RUNTIME

    workdir = Path(args.workdir) if args.workdir else None
    return smoke_test(skill_path, workdir)


if __name__ == "__main__":
    raise SystemExit(main())
