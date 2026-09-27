#!/usr/bin/env python3
"""run_eval.py — eval battery del migration (F64).

10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/migration-sample/run_eval.py [--verbose]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile


HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
MIGRATE_PY = REPO / "skill/notemartin-study-notes/scripts/render/migrate.py"
FIXTURES = HERE / "fixtures"


def run_migrate(*args: str, cwd: pathlib.Path = None) -> int:
    cmd = [sys.executable, str(MIGRATE_PY), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return proc.returncode


def run_migrate_cwd(*args: str, cwd: pathlib.Path) -> int:
    cmd = [sys.executable, str(MIGRATE_PY), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(cwd))
    return proc.returncode


def read_migration_report(out_dir: pathlib.Path) -> dict:
    p = out_dir / "reports" / "migration-report.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_reverse_ir(out_path: pathlib.Path) -> dict:
    if not out_path.exists():
        return {}
    return json.loads(out_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_re_render_obsidian_to_notion(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1: re-render obsidian → notion sin tocar el PDF."""
    src = FIXTURES
    dst = workdir / "c1"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copy(src / "profile.yaml", dst / "profile.yaml")
    shutil.copytree(src / "reverse-input", dst / "reverse-input")
    # Crear un "PDF" de muestra (que NO debe ser tocado).
    pdf_marker = dst / "render" / "pdf"
    pdf_marker.mkdir(parents=True, exist_ok=True)
    (pdf_marker / "should-not-be-touched.txt").write_text("untouched",
                                                        encoding="utf-8")
    # Re-render obsidian → notion_api.
    rc = run_migrate_cwd(
        "re-render",
        "--ir-source", str(dst / "ir"),
        "--out-dir", str(dst),
        "--from", "obsidian",
        "--to", "notion_md",
        cwd=dst,
    )
    if rc not in (0, 2):
        return False, f"exit={rc}"
    pdf_intact = (pdf_marker / "should-not-be-touched.txt").exists()
    notion_rendered = (dst / "render" / "notion_md").exists()
    return (pdf_intact and notion_rendered,
            f"pdf_intact={pdf_intact}, notion_rendered={notion_rendered}")


def c2_report_gains_losses(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2: reporte lista ganancias y pérdidas por capacidad."""
    src = FIXTURES
    dst = workdir / "c2"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copy(src / "profile.yaml", dst / "profile.yaml")
    rc = run_migrate_cwd(
        "re-render",
        "--ir-source", str(dst / "ir"),
        "--out-dir", str(dst),
        "--from", "obsidian",
        "--to", "html_pdf",
        cwd=dst,
    )
    if rc not in (0, 2):
        return False, f"exit={rc}"
    rep = read_migration_report(dst)
    diff = rep.get("capability_diff", {})
    gains = diff.get("gains", [])
    losses = diff.get("losses", [])
    expected_gains = {"table-merged-cells", "query"}
    found_gains = {g["capability"] for g in gains}
    has_all = expected_gains.issubset(found_gains)
    return (has_all and isinstance(losses, list),
            f"gains={found_gains}, losses={len(losses)} entries")


def c3_reverse_import_structure(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3: reverse-import reconstruye la estructura."""
    src = FIXTURES
    dst = workdir / "c3"
    dst.mkdir(parents=True, exist_ok=True)
    out_ir = dst / "reconstructed.json"
    rc = run_migrate_cwd(
        "reverse-import",
        "--input", str(src / "reverse-input" / "lost-note.md"),
        "--output-ir", str(out_ir),
        cwd=dst,
    )
    if rc != 0:
        return False, f"exit={rc}"
    ir = read_reverse_ir(out_ir)

    def _walk(node, found):
        if not isinstance(node, dict):
            return
        if node.get("node") == "link-note":
            found.append(node)
        for c in node.get("children", []) or []:
            _walk(c, found)

    children = ir.get("children", [])
    types = {c.get("node") for c in children}
    link_notes = []
    for c in children:
        _walk(c, link_notes)
    has_structure = (
        "section" in types
        and "paragraph" in types
        and "list" in types
        and "admonition" in types
        and "code" in types
        and len(link_notes) >= 1
    )
    return (has_structure,
            f"types={types}, link-notes={len(link_notes)}")


def c4_capability_diff_obsidian_to_notion(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4: diff obsidian → notion incluye backlinks como ganancia."""
    dst = workdir / "c4"
    dst.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(MIGRATE_PY),
         "diff-capabilities", "--from", "obsidian", "--to", "notion_api"],
        capture_output=True, text=True, timeout=30, cwd=str(dst),
    )
    output = proc.stdout
    has_backlinks = "backlinks" in output
    return (has_backlinks, f"output contains 'backlinks': {has_backlinks}")


def c5_capability_diff_markdown_to_html(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5: diff markdown → html_pdf lista callouts como pérdida (no aplica; html_pdf SÍ)."""
    dst = workdir / "c5"
    dst.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(MIGRATE_PY),
         "diff-capabilities", "--from", "markdown", "--to", "html_pdf"],
        capture_output=True, text=True, timeout=30, cwd=str(dst),
    )
    output = proc.stdout
    return (all(c in output for c in ("callout", "color", "query", "table-merged-cells"))
            and "Ganancias" in output,
            f"gains include callout/color/query/table-merged-cells")


def c6_reverse_import_wikilinks(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: reverse-import preserva wikilinks como link-note."""
    src = FIXTURES
    dst = workdir / "c6"
    dst.mkdir(parents=True, exist_ok=True)
    out_ir = dst / "recon.json"
    run_migrate_cwd(
        "reverse-import",
        "--input", str(src / "reverse-input" / "lost-note.md"),
        "--output-ir", str(out_ir),
        cwd=dst,
    )
    ir = read_reverse_ir(out_ir)

    def _walk(node, found):
        if not isinstance(node, dict):
            return
        if node.get("node") == "link-note":
            found.append(node)
        for c in node.get("children", []) or []:
            _walk(c, found)

    link_nodes = []
    _walk(ir, link_nodes)
    return (len(link_nodes) >= 1,
            f"link-note nodes: {len(link_nodes)}")


def c7_reverse_import_empty(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: reverse-import maneja archivos vacíos sin fallar."""
    dst = workdir / "c7"
    dst.mkdir(parents=True, exist_ok=True)
    empty = dst / "empty.md"
    empty.write_text("", encoding="utf-8")
    out_ir = dst / "empty-out.json"
    rc = run_migrate_cwd(
        "reverse-import",
        "--input", str(empty),
        "--output-ir", str(out_ir),
        cwd=dst,
    )
    ir = read_reverse_ir(out_ir)
    return (rc == 0 and ir.get("children", []) == [],
            f"rc={rc}, children={len(ir.get('children', []))}")


def c8_per_note_migration_status(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: el reporte incluye per-note migration_status."""
    src = FIXTURES
    dst = workdir / "c8"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copy(src / "profile.yaml", dst / "profile.yaml")
    run_migrate_cwd(
        "re-render",
        "--ir-source", str(dst / "ir"),
        "--out-dir", str(dst),
        "--from", "obsidian",
        "--to", "markdown",
        cwd=dst,
    )
    rep = read_migration_report(dst)
    notes = rep.get("notes", [])
    has_status = all("status" in n for n in notes)
    return (has_status and len(notes) >= 1,
            f"notes={len(notes)}, has_status={has_status}")


def c9_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: idempotencia — correr re-render 2 veces produce el mismo summary."""
    src = FIXTURES
    dst = workdir / "c9"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copy(src / "profile.yaml", dst / "profile.yaml")
    run_migrate_cwd(
        "re-render",
        "--ir-source", str(dst / "ir"),
        "--out-dir", str(dst),
        "--from", "obsidian",
        "--to", "markdown",
        cwd=dst,
    )
    rep1 = read_migration_report(dst)
    run_migrate_cwd(
        "re-render",
        "--ir-source", str(dst / "ir"),
        "--out-dir", str(dst),
        "--from", "obsidian",
        "--to", "markdown",
        cwd=dst,
    )
    rep2 = read_migration_report(dst)
    s1 = rep1.get("summary", {})
    s2 = rep2.get("summary", {})
    for key in ("notes_total", "notes_created", "notes_updated", "notes_errors"):
        if s1.get(key) != s2.get(key):
            return False, f"diff en {key}: {s1.get(key)} vs {s2.get(key)}"
    return True, f"summary idéntico: {s1}"


def c10_no_regression(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: el script tiene 3 sub-comandos y ayuda."""
    dst = workdir / "c10"
    dst.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(MIGRATE_PY), "--help"],
        capture_output=True, text=True, cwd=str(dst),
    )
    output = proc.stdout
    return ("re-render" in output and "reverse-import" in output
            and "diff-capabilities" in output,
            f"sub-comandos presentes: re-render, reverse-import, diff-capabilities")


CHECKS = [
    ("C1 Re-render obsidian → notion sin tocar PDF (criterio 1)",
     c1_re_render_obsidian_to_notion),
    ("C2 Reporte lista ganancias y pérdidas (criterio 2)",
     c2_report_gains_losses),
    ("C3 Reverse-import reconstruye estructura (criterio 3)",
     c3_reverse_import_structure),
    ("C4 Diff obsidian → notion incluye backlinks",
     c4_capability_diff_obsidian_to_notion),
    ("C5 Diff markdown → html_pdf lista gains",
     c5_capability_diff_markdown_to_html),
    ("C6 Reverse-import preserva wikilinks",
     c6_reverse_import_wikilinks),
    ("C7 Reverse-import maneja archivos vacíos",
     c7_reverse_import_empty),
    ("C8 Reporte incluye per-note migration_status",
     c8_per_note_migration_status),
    ("C9 Idempotencia (criterio 2)",
     c9_idempotent),
    ("C10 CLI tiene 3 sub-comandos",
     c10_no_regression),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not MIGRATE_PY.exists():
        print(f"ERROR: migrate.py no encontrado", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="migration-eval-"))
    print("=" * 70)
    print("F64 · Eval battery — Migration")
    print("=" * 70)

    passed = 0
    try:
        for name, fn in CHECKS:
            try:
                ok, detail = fn(workdir)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ok, detail = False, f"exception: {e}"
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}")
            if args.verbose or not ok:
                print(f"         {detail}")
            if ok:
                passed += 1
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("=" * 70)
    print(f"  Resultado: {passed}/{len(CHECKS)} verde")
    print("=" * 70)
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
