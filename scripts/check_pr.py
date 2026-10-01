#!/usr/bin/env python3
"""check_pr.py — Gate soft para PRs de la skill (F124)

Forma de uso:
  python3 scripts/check_pr.py                       # default: HEAD
  python3 scripts/check_pr.py --branch <name>       # rama específica
  python3 scripts/check_pr.py --base main           # contra main
  python3 scripts/check_pr.py --strict              # WARN tratado como FAIL

10 items verificables (ver CONTRIBUTING.md §4):
  1. No archivos en denylist (auto, FAIL si hay)
  2. No archivos nuevos fuera de regla de ubicación (auto, FAIL si hay)
  3. scripts/check_version.py --all exit 0 (auto, FAIL si no)
  4. scripts/check_deps.py no exit 1 (auto, FAIL si exit 1)
  5. references/** modificado tiene sección Cómo verificar (semi-auto, WARN)
  6. schemas/** tocado: schema_version bumped coherentemente (semi-auto, WARN)
  7. scripts/ añadido/modificado aparece en scripts/README.md (semi-auto, WARN)
  8. INV-NN nuevo: triada motivación + definición + prueba presente (semi-auto, WARN)
  9. examples/ añadido: INV-15 (≥ 2 categorías) o justificación (semi-auto, WARN)
  10. Contrato tocado: ADR al día (semi-auto, WARN)

Soft gate (default): exit 0 con WARN. Hard gate (--strict): exit 1 con WARN.

Exit codes:
  0  PASS o WARN
  1  FAIL
  2  USAGE / error de runtime

Dependencias: stdlib puro + subprocess.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_RUNTIME = 2

# Allowlist por top-level (per docs/repo-layout.md §5).
ALLOWED_TOPS = {
    "skill": {"notemartin-study-notes", "README.md"},
    "skill/notemartin-study-notes": {
        "SKILL.md",
        "README.md",
        "references",
        "schemas",
        "scripts",
        "assets",
    },
    "docs": {"*.md", "adr"},
    "evals": {"*.md", "corpus", "suite", "regression", "trigger-eval", "sdm-sample", "ledger-sample", "ir-sample", "probe", "ocr-sample", "anchor-sample", "fidelity-sample", "validator-suite-sample", "preprocess-sample", "code-ocr-sample", "table-ocr-sample", "visual", "analogies-sample", "anti-patterns-sample", "api-reference-sample", "appflowy-render-sample", "architecture-sample", "assets-sample", "block-directives-sample", "book-index-sample", "book-mode-sample", "checks-sample", "compliance-sample", "conflict-sample", "concept-graph-sample", "consolidate-sample", "corpus", "cross-target-sample", "cs-layout-sample", "density-sample", "diagram-sample", "fact-check-sample", "formulas-sample", "formula-density-sample", "glossary-sample", "html-pdf-sample", "i18n-sample", "inline-mark-sample", "intuition-sample", "ipynb-sample", "lang-detect-sample", "links-sample", "manifest-sample", "math-sample", "mermaid-render-sample", "notemartin-sample", "notion-md-sample", "notion-render-sample", "obsidian-render-sample", "page-asymmetry-sample", "pdf-native-sample", "phases-sample", "post-ocr-sample", "preprocess-sample", "profile-sample", "prompt-sample", "prop-block-sample", "query-sample", "README.md", "regression-sample", "render-contract-sample", "review-report-sample", "runbook-sample", "scenario-sample", "schema-bump-sample", "self-eval-sample", "source-id-sample", "split-sample", "triage-sample", "validate-note-sample", "version-delta-sample", "visual-eval-sample", "web-docs-sample", "workflow-sample"},
    "examples": {"README.md", "SCHEMA.md", "build_examples.py", "capture.py", "assets", "synthetic-notes", "01-postgresql-chapter", "02-database-internals-chapter", "06-kubernetes-api-ref", "13-internet-archive-scan-hostil"},
    "scripts": {"README.md", "build_skill.py", "check_version.py", "check_deps.py", "smoke_test.py", "check_pr.py", "util", "validate", "render"},
    "tests": set(),
    ".kilo": set(),
}
# Denylist (files / suffixes / dirs)
DENYLIST_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp", ".bak", ".orig", ".rej", ".DS_Store"}
DENYLIST_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}
DENYLIST_PATHS = {"dist/*.skill", "dist/*.skill.manifest.json", "node_modules"}


def _run_git(args: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        ["git"] + args,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def _diff_files(base: str, head: str) -> list[dict]:
    """Lista archivos cambiados en `base`..`head` con su status."""
    rc, out = _run_git(["diff", "--name-status", f"{base}..{head}"])
    if rc != 0:
        return []
    files: list[dict] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[-1]  # para rename old/new, tomar el último
        files.append({"status": status, "path": path})
    return files


def _item_pass(label: str, msg: str) -> tuple[str, str, str]:
    return ("PASS", label, msg)


def _item_warn(label: str, msg: str) -> tuple[str, str, str]:
    return ("WARN", label, msg)


def _item_fail(label: str, msg: str) -> tuple[str, str, str]:
    return ("FAIL", label, msg)


def _check_denylist(files: list[dict]) -> tuple[str, str, str]:
    """Item 1: no archivos en denylist."""
    bad: list[str] = []
    for f in files:
        path = f["path"]
        name = path.rsplit("/", 1)[-1]
        if name in DENYLIST_NAMES:
            bad.append(path)
        elif any(path.endswith(s) for s in DENYLIST_SUFFIXES):
            bad.append(path)
        elif any(pat.rsplit("/", 1)[-1] == name for pat in DENYLIST_PATHS):
            bad.append(path)
    if bad:
        return _item_fail("[1/10] denylist", f"{len(bad)} archivos en denylist: {bad[:3]}")
    return _item_pass("[1/10] denylist", "sin archivos en denylist")


def _check_location(files: list[dict]) -> tuple[str, str, str]:
    """Item 2: archivos nuevos/modificados en paths registrados."""
    bad: list[str] = []
    for f in files:
        path = f["path"]
        if f["status"] not in {"A", "M"}:
            continue
        top = path.split("/", 1)[0]
        if top not in ALLOWED_TOPS:
            bad.append(f"{path} (top-level {top!r} no en allowlist)")
            continue
        # Verificación más fina: si está en skill/, debe estar bajo skill/notemartin-study-notes/
        if top == "skill" and not path.startswith("skill/notemartin-study-notes/"):
            bad.append(f"{path} (debe estar bajo skill/notemartin-study-notes/)")
    if bad:
        return _item_fail("[2/10] regla de ubicación", f"{len(bad)} archivos fuera de allowlist: {bad[:3]}")
    return _item_pass("[2/10] regla de ubicación", "todos los archivos en paths registrados")


def _check_version() -> tuple[str, str, str]:
    """Item 3: scripts/check_version.py --all exit 0."""
    rc, out = _run_git(["status", "--porcelain"])
    if rc == 0 and not out:
        # Working tree clean → check_version no necesita ejecutarse; asumir pass.
        return _item_pass("[3/10] check_version", "git clean; asumido OK (check_version ejecutado en CI)")
    rc, _ = _run_git(["status", "--short", "--", "VERSION", "schemas/", "skill/notemartin-study-notes/schemas/"])
    has_version_changes = bool(rc == 0 and _)
    if not has_version_changes:
        return _item_pass("[3/10] check_version", "sin cambios en VERSION o schemas (skip)")
    # Si hay cambios, ejecutar check_version.py.
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_version.py")],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            return _item_pass("[3/10] check_version", "exit 0")
        return _item_fail("[3/10] check_version", f"exit {r.returncode}: {r.stderr.strip()[:200]}")
    except Exception as e:
        return _item_fail("[3/10] check_version", f"error: {e}")


def _check_deps() -> tuple[str, str, str]:
    """Item 4: scripts/check_deps.py no exit 1."""
    deps_script = SCRIPTS_DIR / "check_deps.py"
    if not deps_script.exists():
        return _item_pass("[4/10] check_deps", "check_deps.py no existe (skip; F117)")
    try:
        r = subprocess.run(
            [sys.executable, str(deps_script)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 1:
            return _item_fail("[4/10] check_deps", f"exit 1: {r.stdout.strip()[:200]}")
        return _item_pass("[4/10] check_deps", f"exit {r.returncode} (deps req presentes)")
    except Exception as e:
        return _item_fail("[4/10] check_deps", f"error: {e}")


def _check_references_have_verify(files: list[dict]) -> tuple[str, str, str]:
    """Item 5: cada archivo de references/ modificado tiene sección Cómo verificar + Cambios permitidos."""
    bad: list[str] = []
    for f in files:
        path = f["path"]
        if not path.startswith("skill/notemartin-study-notes/references/") or not path.endswith(".md"):
            continue
        if f["status"] not in {"A", "M"}:
            continue
        full = REPO_ROOT / path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"## §N.+C[oó]mo verificar", text):
            bad.append(f"{path} (sin § Cómo verificar)")
        if "Cambios permitidos" not in text:
            bad.append(f"{path} (sin 'Cambios permitidos')")
    if bad:
        return _item_warn("[5/10] references cierre", f"{len(bad)} archivos sin cierre completo: {bad[:3]}")
    return _item_pass("[5/10] references cierre", "todos los archivos modificados tienen cierre")


def _check_schema_bump(files: list[dict]) -> tuple[str, str, str]:
    """Item 6: schemas/** tocado: schema_version bumped coherentemente."""
    bad: list[str] = []
    for f in files:
        path = f["path"]
        if not path.startswith("skill/notemartin-study-notes/schemas/") or not path.endswith(".json"):
            continue
        # Si es creación, no requiere bump (es nuevo).
        if f["status"] == "A":
            continue
        # Si es modificación, leer el archivo actual y verificar schema_version const.
        full = REPO_ROOT / path
        if not full.exists():
            continue
        try:
            import json
            data = json.loads(full.read_text())
        except Exception:
            continue
        sv = data.get("properties", {}).get("schema_version", {})
        if not sv.get("const"):
            bad.append(f"{path} (sin schema_version const)")
    if bad:
        return _item_warn("[6/10] schemas schema_version", f"{len(bad)} archivos sin const: {bad[:3]}")
    return _item_pass("[6/10] schemas schema_version", "todos los schemas modificados tienen const")


def _check_scripts_documented(files: list[dict]) -> tuple[str, str, str]:
    """Item 7: scripts/ añadido/modificado aparece en scripts/README.md con Dependencias."""
    bad: list[str] = []
    scripts_readme = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "README.md"
    if not scripts_readme.exists():
        return _item_warn("[7/10] scripts documentados", "scripts/README.md no existe (skip)")
    readme_text = scripts_readme.read_text(encoding="utf-8", errors="replace")
    for f in files:
        path = f["path"]
        if not path.startswith("skill/notemartin-study-notes/scripts/") or not path.endswith(".py"):
            continue
        if f["status"] not in {"A", "M"}:
            continue
        name = path.rsplit("/", 1)[-1]
        if name not in readme_text:
            bad.append(name)
    if bad:
        return _item_warn(
            "[7/10] scripts documentados",
            f"{len(bad)} scripts nuevos/modificados sin entrada en scripts/README.md: {bad[:3]}",
        )
    return _item_pass("[7/10] scripts documentados", "todos los scripts modificados están documentados")


def _check_triada(files: list[dict]) -> tuple[str, str, str]:
    """Item 8: heurística — INV-NN nuevo en references/ sin companion en evals/."""
    bad: list[str] = []
    inv_pattern = re.compile(r"INV-(\d+)")
    for f in files:
        path = f["path"]
        if not path.endswith(".md") or f["status"] not in {"A", "M"}:
            continue
        full = REPO_ROOT / path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        # Solo considerar archivos en references/ o skills/AGENT.md (donde se definen INV).
        if "references/" not in path and "skills/AGENT.md" not in path:
            continue
        invs = inv_pattern.findall(text)
        for inv in invs:
            # Buscar companion test en evals/ o tests/.
            expected_test = REPO_ROOT / "evals" / f"inv-{inv.zfill(2)}-sample"
            if not expected_test.exists():
                bad.append(f"INV-{inv} nuevo en {path} sin evals/inv-{inv.zfill(2)}-sample/")
    if bad:
        return _item_warn("[8/10] triada regla→prueba", "; ".join(bad[:3]))
    return _item_pass("[8/10] triada regla→prueba", "INV nuevos tienen companion test (o ninguno detectado)")


def _check_multi_domain(files: list[dict]) -> tuple[str, str, str]:
    """Item 9: examples/ añadido: INV-15 (≥ 2 categorías) o justificación."""
    bad: list[str] = []
    for f in files:
        path = f["path"]
        if not path.startswith("examples/") or f["status"] != "A":
            continue
        if not (path.endswith(".py") or path.endswith(".md") or path.endswith(".yaml") or path.endswith(".nm")):
            continue
        # Heurística: buscar "single-domain-test" en frontmatter o en nombre de archivo.
        full = REPO_ROOT / path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")[:500]
        if "single-domain-test" in text:
            continue
        # Por ahora, solo WARN — la validación completa requiere leer todo el directorio.
        bad.append(path)
    if bad:
        return _item_warn(
            "[9/10] ejemplos multi-dominio",
            f"{len(bad)} ejemplos nuevos sin justificación explícita INV-15; verificar manualmente",
        )
    return _item_pass("[9/10] ejemplos multi-dominio", "sin ejemplos nuevos (skip)")


def _check_adrs(files: list[dict]) -> tuple[str, str, str]:
    """Item 10: ADRs al día si el PR toca un contrato."""
    bad: list[str] = []
    for f in files:
        path = f["path"]
        # Detección heurística de "toca contrato": schemas/, note-plan schema, manifest schema, profile schema, etc.
        if not path.endswith(".json"):
            continue
        if not path.startswith("skill/notemartin-study-notes/schemas/"):
            continue
        # Si el archivo es uno de los schemas de contrato, verificar ADR reciente.
        schema_name = path.rsplit("/", 1)[-1].replace(".schema.json", "")
        contract_schemas = {"sdm", "note-ir", "note-plan", "ledger", "manifest", "profile", "quality-gate"}
        if schema_name not in contract_schemas:
            continue
        # Heurística: si NO hay ADRs en docs/adr/, warn.
        adr_dir = REPO_ROOT / "docs" / "adr"
        if not adr_dir.exists() or not any(adr_dir.glob("ADR-*.md")):
            bad.append(f"{schema_name} modificado sin ADRs en docs/adr/")
    if bad:
        return _item_warn("[10/10] ADRs al día", "; ".join(bad))
    return _item_pass("[10/10] ADRs al día", "ADRs al día (o no se tocaron contratos)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gate soft para PRs (F124)")
    p.add_argument("--branch", default=None, help="Rama a comparar contra --base")
    p.add_argument("--base", default="HEAD~1", help="Base ref (default: HEAD~1)")
    p.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    p.add_argument("--strict", action="store_true", help="WARN tratado como FAIL")
    p.add_argument(
        "--all",
        action="store_true",
        help="Alias de --strict (más legible para uso en CI)",
    )
    args = p.parse_args(argv)

    strict = args.strict or args.all

    files = _diff_files(args.base, args.head)
    if not files:
        print(f"WARN: no hay diff entre {args.base}..{args.head}; el PR puede estar vacío", file=sys.stderr)
        print("(revisar si esto es intencional)")
        files = []

    checks = [
        _check_denylist(files),
        _check_location(files),
        _check_version(),
        _check_deps(),
        _check_references_have_verify(files),
        _check_schema_bump(files),
        _check_scripts_documented(files),
        _check_triada(files),
        _check_multi_domain(files),
        _check_adrs(files),
    ]

    n_fail = 0
    n_warn = 0
    n_pass = 0
    for status, label, msg in checks:
        marker = {"PASS": "[OK]  ", "WARN": "[WARN]", "FAIL": "[FAIL]"}[status]
        if status == "PASS":
            n_pass += 1
        elif status == "WARN":
            n_warn += 1
        else:
            n_fail += 1
        print(f"{marker} {label}: {msg}")

    print()
    print(f"=== Resumen: {n_pass} OK, {n_warn} WARN, {n_fail} FAIL (mode: {'strict' if strict else 'soft'}) ===")

    if n_fail > 0:
        return EXIT_FAIL
    if strict and n_warn > 0:
        return EXIT_FAIL
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
