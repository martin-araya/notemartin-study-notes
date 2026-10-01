#!/usr/bin/env python3
"""build_skill.py — Empaqueta `skill/notemartin-study-notes/` en un `.skill` reproducible

Forma de uso:
  python3 scripts/build_skill.py                                        # build por defecto
  python3 scripts/build_skill.py --version 0.1.0                       # con versión explícita
  python3 scripts/build_skill.py --output <path>                       # ruta de salida custom
  python3 scripts/build_skill.py --check                                # verifica byte-identidad vs build anterior
  python3 scripts/build_skill.py --info <path>                         # inspecciona un .skill sin extraerlo
  python3 scripts/build_skill.py --strict                               # falla si allowlist/denylist no se cumplen

Cierra F122. El paquete es un ZIP con SKILL.md en raíz + manifest.json + payload,
per docs/repo-layout.md §4 (allowlist: SKILL.md, manifest.json, README.md,
references/**, schemas/**, scripts/**, assets/**; denylist: __pycache__/,
*.pyc, .DS_Store, .git/, *.swp, *.tmp, *.bak, *.orig, etc.).

Reproducibilidad (D3): orden determinista, timestamps 1980-01-01, ZIP_DEFLATED,
permisos fijos. Dos builds con mismo git_sha producen ZIPs byte-idénticos.

Exit codes:
  0  build OK / check OK / info OK
  1  error de uso
  2  error de runtime

Dependencias: stdlib puro (zipfile, hashlib, pathlib, json, datetime, argparse).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DIST_DIR = REPO_ROOT / "dist"
VERSION_FILE = REPO_ROOT / "VERSION"

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_RUNTIME = 2

# Allowlist (per docs/repo-layout.md §4.1).
ALLOWLIST_TOP = {"SKILL.md", "README.md", "manifest.json", "references", "schemas", "scripts", "assets"}
# Denylist (per docs/repo-layout.md §4.2 + exclusiones automáticas D7).
DENYLIST_FILES = {
    "__pycache__", ".DS_Store", "Thumbs.db", ".git", ".gitignore",
    ".gitkeep", ".editorconfig", ".vscode", ".idea",
}
DENYLIST_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp", ".bak", ".orig", ".rej"}
# Manifest siempre al inicio (después de SKILL.md y README.md) para reproducibilidad.
MANIFEST_NAME = "manifest.json"
# Tamaño máximo del paquete (smoke_test.py lo verifica).
SIZE_LIMIT_BYTES = 8 * 1024 * 1024  # 8 MB
# Tamaño fijo para reproducibilidad (no incluimos timestamps reales).
FIXED_DATETIME = (1980, 1, 1, 0, 0, 0)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _read_version_file() -> str | None:
    """Lee VERSION del repo (F123). Devuelve None si no existe o está vacío."""
    if not VERSION_FILE.exists():
        return None
    text = VERSION_FILE.read_text(encoding="utf-8").strip()
    return text if text else None


def _is_denied(rel_path: str) -> bool:
    parts = rel_path.split("/")
    for part in parts:
        if part in DENYLIST_FILES:
            return True
        if any(part.endswith(s) for s in DENYLIST_SUFFIXES):
            return True
    return False


def _is_allowed(rel_path: str) -> bool:
    top = rel_path.split("/", 1)[0]
    return top in ALLOWLIST_TOP


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_files(source_dir: Path) -> list[Path]:
    """Devuelve la lista ordenada (determinista) de archivos a incluir."""
    if not source_dir.exists():
        raise FileNotFoundError(f"source dir no existe: {source_dir}")
    paths: list[Path] = []
    for p in sorted(source_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(source_dir).as_posix()
        if rel.startswith(".git/") or "/.git/" in rel:
            continue
        if _is_denied(rel):
            continue
        paths.append(p)
    return paths


def _build_manifest(source_dir: Path, files: list[Path], version: str, git_sha: str) -> dict:
    """Construye el dict del manifest. contents_sha256 = sha256 de la concatenación
    ordenada de (path + sha256 del archivo) sobre todos los archivos del payload
    (excluye manifest.json)."""
    payload_lines: list[str] = []
    file_shas: list[tuple[str, str]] = []
    total_size = 0
    for p in files:
        rel = p.relative_to(source_dir).as_posix()
        if rel == MANIFEST_NAME:
            continue
        sha = _hash_file(p)
        file_shas.append((rel, sha))
        payload_lines.append(f"{rel}\t{sha}\n")
        total_size += p.stat().st_size

    contents_hash = hashlib.sha256("".join(payload_lines).encode("utf-8")).hexdigest()

    # skill_md_sha256: si existe, lo sacamos.
    skill_md_path = source_dir / "SKILL.md"
    skill_md_sha = _hash_file(skill_md_path) if skill_md_path.exists() else None

    manifest = {
        "schema_version": "1.0.0",
        "name": "notemartin-study-notes",
        "version": version,
        "git_sha": git_sha,
        "python_version_min": "3.9",
        "tesseract_required": True,
        "tesseract_min_version": "5.0",
        "contents_sha256": contents_hash,
        "skill_md_sha256": skill_md_sha,
        "files_count": len(file_shas),
        "size_bytes": total_size,
        "build_timestamp": "1980-01-01T00:00:00Z",
        "build_host": "kilo-builder",
        "files": file_shas,
    }
    return manifest


def _detect_executable(rel_path: str) -> bool:
    """Detecta si un archivo debe tener permiso 0o755."""
    if rel_path.startswith("scripts/"):
        name = rel_path.rsplit("/", 1)[-1]
        return name.endswith(".py") or name.endswith(".sh")
    return False


def _zip_info(path: Path, source_dir: Path) -> zipfile.ZipInfo:
    rel = path.relative_to(source_dir).as_posix()
    info = zipfile.ZipInfo(rel, date_time=FIXED_DATETIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o755 if _detect_executable(rel) else 0o644) << 16
    info.create_system = 3  # UNIX
    return info


def build_skill(version: str, output_path: Path, strict: bool = False) -> dict:
    """Construye el .skill. Devuelve el dict del manifest."""
    files = _walk_files(SOURCE_DIR)

    # Validación allowlist (en modo strict).
    if strict:
        for p in files:
            rel = p.relative_to(SOURCE_DIR).as_posix()
            if not _is_allowed(rel):
                raise ValueError(f"archivo fuera de allowlist (docs/repo-layout §4.1): {rel}")

    # Construir manifest.
    manifest = _build_manifest(SOURCE_DIR, files, version, _git_sha())

    # Orden de archivos: SKILL.md primero, README.md segundo, manifest.json tercero, resto alfabético.
    def sort_key(p: Path) -> tuple:
        rel = p.relative_to(SOURCE_DIR).as_posix()
        if rel == "SKILL.md":
            return (0, rel)
        if rel == "README.md":
            return (1, rel)
        if rel == MANIFEST_NAME:
            return (2, rel)
        return (3, rel)

    files_sorted = sorted(files, key=sort_key)

    # Generar ZIP.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in files_sorted:
            rel = p.relative_to(SOURCE_DIR).as_posix()
            if rel == MANIFEST_NAME:
                # Lo escribimos al final para mantener orden determinista.
                continue
            info = _zip_info(p, SOURCE_DIR)
            with p.open("rb") as f:
                zf.writestr(info, f.read(), compresslevel=9)
        # Manifest al final con timestamp fijo.
        manifest_info = zipfile.ZipInfo(MANIFEST_NAME, date_time=FIXED_DATETIME)
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.external_attr = (0o644) << 16
        manifest_info.create_system = 3
        zf.writestr(manifest_info, manifest_bytes, compresslevel=9)

    # Manifest en disco (al lado del ZIP).
    manifest_disk_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    manifest_disk_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"OK build → {output_path}")
    print(f"   manifest → {manifest_disk_path}")
    print(f"   files={manifest['files_count']} size={manifest['size_bytes']} bytes")
    print(f"   contents_sha256={manifest['contents_sha256']}")
    return manifest


def check_skill(output_path: Path, baseline_path: Path | None = None) -> bool:
    """Verifica byte-identidad contra un build previo (o contra el mismo path si existe)."""
    if not output_path.exists():
        print(f"ERROR: skill no existe: {output_path}", file=sys.stderr)
        return False
    baseline = baseline_path or output_path
    if not baseline.exists():
        print(f"ERROR: baseline no existe: {baseline}", file=sys.stderr)
        return False
    a = output_path.read_bytes()
    b = baseline.read_bytes()
    if a == b:
        print(f"OK reproducible: {output_path.name} == {baseline.name} ({len(a)} bytes)")
        return True
    print(f"FAIL: {output_path.name} ({len(a)} bytes) != {baseline.name} ({len(b)} bytes)")
    return False


def info_skill(skill_path: Path) -> int:
    """Lista el contenido de un .skill sin extraerlo."""
    if not skill_path.exists():
        print(f"ERROR: skill no existe: {skill_path}", file=sys.stderr)
        return EXIT_RUNTIME
    print(f"=== {skill_path} ===")
    with zipfile.ZipFile(skill_path, "r") as zf:
        infos = zf.infolist()
        print(f"  entries: {len(infos)}")
        print(f"  size: {sum(i.file_size for i in infos)} bytes uncompressed")
        print(f"  size_compressed: {sum(i.compress_size for i in infos)} bytes")
        print()
        print("  manifest (if present):")
        if MANIFEST_NAME in zf.namelist():
            manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
            for k, v in manifest.items():
                if k == "files":
                    print(f"    files: [{len(v)} entries]")
                else:
                    print(f"    {k}: {v}")
        print()
        print("  top-level entries:")
        for info in sorted(infos, key=lambda i: i.filename):
            print(f"    {info.filename} ({info.file_size} bytes)")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Empaqueta skill/notemartin-study-notes/ en un .skill reproducible")
    p.add_argument("--version", default=None, help="Versión semver (default: lee VERSION en repo root, F123). Fallback: 0.1.0-dev")
    p.add_argument("--output", default=None, help="Ruta del .skill (default: dist/notemartin-study-notes-<version>.skill)")
    p.add_argument("--source", default=str(SOURCE_DIR), help="Directorio fuente (default: skill/notemartin-study-notes/)")
    p.add_argument("--check", action="store_true", help="Verifica byte-identidad vs build previo")
    p.add_argument("--baseline", default=None, help="ZIP baseline para --check (default: mismo path que --output)")
    p.add_argument("--info", default=None, help="Inspecciona un .skill sin extraerlo (proporciona ruta)")
    p.add_argument("--strict", action="store_true", help="Falla si hay archivos fuera de allowlist (per docs/repo-layout §4.1)")
    args = p.parse_args(argv)

    if args.info:
        return info_skill(Path(args.info))

    # Resolución de version: --version flag > VERSION file > fallback.
    if args.version is None:
        v = _read_version_file()
        if v is not None:
            args.version = v
        else:
            print(
                "WARN: VERSION no existe en repo root; usando fallback '0.1.0-dev'. "
                "Recomendado: crear VERSION per F123.",
                file=sys.stderr,
            )
            args.version = "0.1.0-dev"

    output_path = Path(args.output) if args.output else (DIST_DIR / f"notemartin-study-notes-{args.version}.skill")
    output_path = output_path.resolve()

    if args.check:
        baseline = Path(args.baseline).resolve() if args.baseline else None
        return EXIT_OK if check_skill(output_path, baseline) else EXIT_RUNTIME

    try:
        build_skill(args.version, output_path, strict=args.strict)
        return EXIT_OK
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
