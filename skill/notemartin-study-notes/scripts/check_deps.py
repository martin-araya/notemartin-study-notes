#!/usr/bin/env python3
"""
check_deps.py — Verificador de dependencias (F117).

Recorre scripts/README.md y scripts/pkg/deps.yaml; cruza con módulos
disponibles en sys.path y binarios en PATH; emite reporte con 4 niveles
(req/rec/opt/bin).

Exit codes:
  0 — todo OK
  2 — sólo rec/opt faltan
  1 — ≥ 1 req falta
  3 — uso/schema

Uso:
  python3 scripts/check_deps.py [--strict] [--json] [--filter NAME]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

# Regex para filas | Dependencias | ... en scripts/README.md.
DEPS_ROW_RE = re.compile(r"^\|\s*Dependencias\s*\|\s*([^|]+?)\s*\|",
                          re.IGNORECASE | re.MULTILINE)
H3_RE = re.compile(r"^###\s+`?([^`\s]+)`?\s+[—\-]+\s+(F\d+)", re.MULTILINE)


# ────────────────────────────────────────────────────────────────────
# Data classes
# ────────────────────────────────────────────────────────────────────
@dataclass
class DepToken:
    level: str   # req / rec / opt / bin
    name: str
    used_by: list[str] = field(default_factory=list)


@dataclass
class Finding:
    level: str        # req / rec / opt / info / warn
    category: str     # py / bin / mismatch / unused
    name: str
    message: str
    used_by: list[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────────────────
# Loader
# ────────────────────────────────────────────────────────────────────
def load_yaml(path: Path) -> dict:
    """Carga YAML usando PyYAML si está disponible; fallback mini-parser."""
    try:
        import yaml  # type: ignore
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        return _minimal_yaml(path)


def _minimal_yaml(path: Path) -> dict:
    """Fallback ultra-mínimo: solo claves top-level planas y listas inline."""
    out: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("-"):
            continue
        if ":" not in s:
            continue
        k, _, v = s.partition(":")
        k = k.strip()
        v = v.strip()
        if v == "":
            out[k] = {}
        elif v.startswith("[") and v.endswith("]"):
            items = [x.strip().strip('"').strip("'")
                     for x in v[1:-1].split(",") if x.strip()]
            out[k] = items
        else:
            out[k] = v.strip('"').strip("'")
    return out


def load_manifest(path: Path) -> dict:
    return load_yaml(path)


# ────────────────────────────────────────────────────────────────────
# Parse del README — dependencias declaradas
# ────────────────────────────────────────────────────────────────────
def parse_readme_deps(readme_path: Path) -> dict[str, list[DepToken]]:
    """Devuelve {script_name: [DepToken, ...]} parseando cada H3."""
    text = readme_path.read_text(encoding="utf-8")
    out: dict[str, list[DepToken]] = {}
    matches = list(re.finditer(
        r"^###\s+`?([^`\s]+)`?\s+[—\-]+\s+(F\d+)",
        text, flags=re.MULTILINE,
    ))
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end]
        m2 = DEPS_ROW_RE.search(body)
        if not m2:
            continue
        tokens = parse_dep_tokens(m2.group(1), used_by=name)
        out[name] = tokens
    return out


def parse_dep_tokens(raw: str, used_by: str = "") -> list[DepToken]:
    """Parsea tokens en forma canónica (req:pkg; rec:pkg; bin:bin) o libre.

    Forma canónica: cada token lleva prefijo de nivel.
    Forma libre: cada token es solo el nombre; se le asigna `req` por
    default. Descripciones entre paréntesis, refs a stdlib y referencias
    a scripts locales se filtran.
    """
    out: list[DepToken] = []
    used_by_clean = used_by.removesuffix(".py")
    STOPWORDS = {
        "subprocess", "sys", "os", "pathlib", "json", "yaml",
        "argparse", "re", "datetime", "shutil", "dataclasses",
        "typing", "collections", "itertools", "functools",
        "urllib", "http", "io", "csv", "uuid", "hashlib",
        "tempfile", "traceback", "warnings", "copy", "asyncio",
        "contextlib", "secrets", "base64", "time", "string",
        "textwrap", "unicodedata", "zipfile", "difflib",
    }
    DESCRIPTIVE_PREFIXES = (
        "parser ", "invoca ", "usa ", "fallback", "no invoca",
        "opcional para ", "cuando ", "subproceso", "wrapper",
        "soft-dep", "no muerde",
    )
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        # Strip ALL backticks y espacios asociados.
        part = part.replace("`", "").strip()
        # Strip descripciones entre paréntesis al final (múltiples niveles).
        while True:
            new = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
            if new == part:
                break
            part = new
        # Strip comas descriptivas al final.
        part = re.sub(r",\s*$", "", part).strip()
        if not part:
            continue
        if "scripts/" in part or "util/" in part or "F38" in part:
            continue
        # Eliminar frases descriptivas (empiezan por prefijo conocido).
        lowered = part.lower().strip()
        if any(lowered.startswith(p) for p in DESCRIPTIVE_PREFIXES):
            continue
        # Strip "implícitos cuando" (después del paquete).
        if "implícito" in lowered or "disponible" in lowered:
            continue
        # Strip "(opcional)" residual dentro del nombre.
        if "(opcional" in lowered or "opcional)" in lowered:
            continue
        if ":" in part:
            level, name = part.split(":", 1)
            level = level.strip().lower()
            name = name.strip()
            # Strip " opcionales" residual.
            name = re.sub(r"\s+opcionales?\s*$", "", name).strip()
            name = re.sub(r"\s*[<>=]+\s*\d+(\.\d+)*\s*$", "", name).strip()
        else:
            level = "req"
            name = part
            name = re.sub(r"\s+opcionales?\s*$", "", name).strip()
            name = re.sub(r"\s*[<>=]+\s*\d+(\.\d+)*\s*$", "", name).strip()
        if level not in ("req", "rec", "opt", "bin"):
            continue
        if name.lower().startswith("python"):
            continue
        # Stopwords de stdlib.
        if name.lower() in STOPWORDS:
            continue
        # Limpiar nombres con `+` (dos paquetes en uno).
        if "+" in name and level in ("req", "rec", "opt"):
            for sub in name.split("+"):
                sub = sub.strip()
                if not sub or sub.lower() in STOPWORDS:
                    continue
                if " " in sub:
                    continue
                tok = DepToken(level=level, name=sub,
                                used_by=[used_by_clean] if used_by_clean else [])
                out.append(tok)
            continue
        if " " in name:
            # Frase descriptiva, descartar.
            continue
        if not name:
            continue
        tok = DepToken(level=level, name=name, used_by=[used_by_clean] if used_by_clean else [])
        out.append(tok)
    return out


# ────────────────────────────────────────────────────────────────────
# AST-lite para imports
# ────────────────────────────────────────────────────────────────────
def extract_imports(path: Path) -> set[str]:
    """Recorre el AST y devuelve los nombres top-level importados."""
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if not top.startswith("__"):
                    imports.add(top)
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod and not mod.startswith("__"):
                imports.add(mod)
    # Filtrar imports del proyecto (módulos locales en scripts/util/, etc.).
    imports -= {"scripts"}
    return imports


# ────────────────────────────────────────────────────────────────────
# Verificadores
# ────────────────────────────────────────────────────────────────────
def check_py_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def check_binary(name: str) -> str | None:
    return shutil.which(name)


def run_checks(manifest: dict, declared: dict[str, list[DepToken]],
               scripts_root: Path, bin_search_path: str | None = None,
               filter_name: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    alias = manifest.get("alias", {}) or {}

    # Globales.
    globals_map = manifest.get("globals", {}) or {}
    for name, level in globals_map.items():
        if filter_name and filter_name != name:
            continue
        if name.startswith("python"):
            ok = sys.version_info >= (3, 9)
            findings.append(Finding(
                level="info" if ok else level,
                category="py",
                name=name,
                message=f"python {sys.version_info.major}.{sys.version_info.minor}"
                        if ok else f"{name} required, not available",
            ))
        elif name == "git":
            path = check_binary("git")
            ok = path is not None
            findings.append(Finding(
                level="info" if ok else level,
                category="bin",
                name="git",
                message=path or "git not in PATH",
            ))
        elif name in ("curl", "unzip"):
            path = check_binary(name)
            ok = path is not None
            sev = "info" if ok else level
            findings.append(Finding(
                level=sev,
                category="bin",
                name=name,
                message=path or f"{name} not in PATH",
            ))

    # Extras declarados en el manifest.
    by_tier = manifest.get("extras", {}).get("by_tier", {}) or {}
    # Reverse alias: package_name → module_name candidates.
    pkg_to_modules: dict[str, list[str]] = {}
    for k, v in alias.items():
        pkg_to_modules.setdefault(v, []).append(k)
    for tier in ("req", "rec", "opt"):
        for pkg in by_tier.get(tier, []) or []:
            if filter_name and filter_name != pkg:
                continue
            # Buscar primero por el nombre del paquete, luego por aliases.
            candidates = [pkg] + pkg_to_modules.get(pkg, [])
            ok = any(check_py_module(c) for c in candidates)
            if not ok:
                findings.append(Finding(
                    level=tier,
                    category="py",
                    name=pkg,
                    message=f"{pkg} missing ({tier})",
                ))

    # Binarios externos del manifest.
    binaries = manifest.get("binaries", {}) or {}
    for tier in ("req", "rec", "opt"):
        for bin_name in binaries.get(tier, []) or []:
            if filter_name and filter_name != bin_name:
                continue
            path = check_binary(bin_name)
            if not path and bin_search_path:
                # Buscar manualmente en bin_search_path.
                candidate = Path(bin_search_path) / bin_name
                if candidate.is_file() and candidate.stat().st_mode & 0o111:
                    path = str(candidate)
            if not path:
                findings.append(Finding(
                    level=tier,
                    category="bin",
                    name=bin_name,
                    message=f"{bin_name} missing (bin:{tier})",
                ))

    # Dependencias declaradas por script (token por token).
    for script_name, tokens in declared.items():
        if filter_name and filter_name != script_name:
            continue
        for tok in tokens:
            if tok.level == "bin":
                path = check_binary(tok.name)
                if not path and bin_search_path:
                    candidate = Path(bin_search_path) / tok.name
                    if candidate.is_file() and candidate.stat().st_mode & 0o111:
                        path = str(candidate)
                if not path:
                    findings.append(Finding(
                        level=tok.level,
                        category="bin",
                        name=tok.name,
                        message=f"{tok.name} missing (bin:{tok.level}) — usado por {script_name}",
                        used_by=[script_name],
                    ))
            else:
                pkg = tok.name
                candidates = [pkg, alias.get(pkg, pkg)]
                # Si pkg_alias resuelve a otro nombre, probar también el inverso.
                for k, v in alias.items():
                    if v == pkg:
                        candidates.append(k)
                ok = any(check_py_module(c) for c in candidates)
                if not ok:
                    findings.append(Finding(
                        level=tok.level,
                        category="py",
                        name=pkg,
                        message=f"{pkg} missing ({tok.level}) — usado por {script_name}",
                        used_by=[script_name],
                    ))

    # Mismatch declarado-vs-importado (AST-lite).
    for script_name in declared.keys():
        script_path = scripts_root / f"{script_name}.py"
        if not script_path.is_file():
            # Buscar en subcarpetas (e.g., validate/density_check.py).
            for sub in ("ingest", "validate", "audit", "authoring",
                        "render", "util", "dedup", "diff",
                        "pipeline", "publish", "study"):
                candidate = scripts_root / sub / f"{script_name}.py"
                if candidate.is_file():
                    script_path = candidate
                    break
        if not script_path.is_file():
            continue
        imported = extract_imports(script_path)
        declared_pkgs: set[str] = set()
        for tok in declared.get(script_name, []):
            if tok.level != "bin":
                declared_pkgs.add(tok.name)
                # Alias → declarado.
                for k, v in alias.items():
                    if v == tok.name:
                        declared_pkgs.add(k)
        declared_pkgs -= {"python3.9+"}
        for mod in imported:
            if mod in {"scripts", "scripts_pkg"}:
                continue
            if mod not in declared_pkgs and mod not in globals_map \
                    and not any(tok.name == mod for tok in declared.get(script_name, [])):
                # Filtrar stdlib probable.
                if mod in ("pathlib", "json", "argparse", "re", "sys", "os",
                           "datetime", "subprocess", "shutil", "dataclasses",
                           "typing", "collections", "itertools", "functools",
                           "random", "math", "uuid", "string", "io", "csv",
                           "textwrap", "unicodedata", "hashlib", "contextlib",
                           "copy", "time", "warnings", "traceback"):
                    continue
                findings.append(Finding(
                    level="info",
                    category="mismatch",
                    name=mod,
                    message=f"{script_name}.py importa `{mod}` pero su README no lo declara",
                    used_by=[script_name],
                ))

    return findings


# ────────────────────────────────────────────────────────────────────
# Report
# ────────────────────────────────────────────────────────────────────
def render_text(findings: list[Finding]) -> str:
    lines = ["check_deps.py — Verificador de dependencias", "=" * 44]
    py_lines: list[str] = []
    bin_lines: list[str] = []
    other_lines: list[str] = []
    for f in findings:
        mark = {"req": "✗", "rec": "⚠", "opt": "ℹ", "info": "✓", "warn": "⚠"}.get(f.level, "?")
        line = f"  {mark} {f.name:20s} {f.message}"
        if f.category == "py":
            py_lines.append(line)
        elif f.category == "bin":
            bin_lines.append(line)
        else:
            other_lines.append(line)
    if py_lines:
        lines += ["", "PAQUETES PYTHON:"]
        lines += py_lines
    if bin_lines:
        lines += ["", "BINARIOS EXTERNOS:"]
        lines += bin_lines
    if other_lines:
        lines += ["", "OTROS:"]
        lines += other_lines
    n_req = sum(1 for f in findings if f.level == "req")
    n_rec = sum(1 for f in findings if f.level == "rec")
    n_opt = sum(1 for f in findings if f.level == "opt")
    n_info = sum(1 for f in findings if f.level == "info")
    lines += ["", f"Summary: {n_req} missing (required), {n_rec} missing (recommended), "
             f"{n_opt} missing (optional), {n_info} info"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--filter", help="filtrar por nombre de dep o script")
    parser.add_argument("--bin-search-path", help="path adicional para buscar binarios")
    parser.add_argument("--catalog", default="scripts/README.md")
    parser.add_argument("--manifest", default="scripts/pkg/deps.yaml")
    parser.add_argument("--scripts-root", default="scripts",
                        help="raíz donde buscar los scripts para AST-lite")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    manifest_path = Path(args.manifest)
    scripts_root = Path(args.scripts_root)
    if not catalog_path.is_file():
        print(f"ERROR: catalog no existe: {catalog_path}", file=sys.stderr)
        return 3
    if not manifest_path.is_file():
        print(f"ERROR: manifest no existe: {manifest_path}", file=sys.stderr)
        return 3

    manifest = load_manifest(manifest_path)
    declared = parse_readme_deps(catalog_path)
    findings = run_checks(manifest, declared, scripts_root,
                          bin_search_path=args.bin_search_path,
                          filter_name=args.filter)

    if args.json:
        out = {
            "schema_version": SCHEMA_VERSION,
            "summary": {
                "errors": sum(1 for f in findings if f.level == "req"),
                "warnings": sum(1 for f in findings if f.level == "rec"),
                "info": sum(1 for f in findings if f.level == "info"),
                "optional": sum(1 for f in findings if f.level == "opt"),
            },
            "findings": [
                {"level": f.level, "category": f.category, "name": f.name,
                 "message": f.message, "used_by": f.used_by}
                for f in findings
            ],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(render_text(findings))

    if any(f.level == "req" for f in findings):
        return 1
    if any(f.level == "rec" for f in findings):
        return 2 if not args.strict else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())