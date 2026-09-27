#!/usr/bin/env python3
"""run_eval.py — eval battery del publishing (F62).

10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/publishing-sample/run_eval.py [--verbose]
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
PUB_PY = REPO / "skill/notemartin-study-notes/scripts/publish/publishing.py"
FIXTURES = HERE / "fixtures"

# Importa make_ir desde build_fixtures.
import importlib.util as _il_util
_spec_bf = _il_util.spec_from_file_location(
    "_build_fixtures", HERE / "build_fixtures.py"
)
_mod_bf = _il_util.module_from_spec(_spec_bf)
_spec_bf.loader.exec_module(_mod_bf)
make_ir = _mod_bf.make_ir


def render_to(workdir: pathlib.Path, ir_arg: pathlib.Path,
              dest: str = "markdown",
              preserve_user_content: bool = True) -> None:
    """Pre-renderiza el IR a render/<dest>/<note>.md.

    Si `preserve_user_content=True`, lee el bloque user-content existente y
    lo mantiene al reescribir el archivo (necesario para los tests C7/C8).
    """
    subdir = dest
    target = workdir / "render" / subdir
    target.mkdir(parents=True, exist_ok=True)
    for ir_path in sorted(ir_arg.glob("*.json")):
        note_id = ir_path.stem
        existing = target / f"{note_id}.md"
        user_block = ""
        if preserve_user_content and existing.exists():
            content_old = existing.read_text(encoding="utf-8", errors="replace")
            if "<!-- user-content-start -->" in content_old and "<!-- user-content-end -->" in content_old:
                start = content_old.index("<!-- user-content-start -->") + len("<!-- user-content-start -->")
                end = content_old.index("<!-- user-content-end -->", start)
                block = content_old[start:end].strip()
                if block:
                    user_block = f"\n\n<!-- user-content-start -->\n{block}\n<!-- user-content-end -->\n"
        content = (
            "---\n"
            f'note_id: "{note_id}"\n'
            f"target: {dest}\n"
            "---\n\n"
            f"# {note_id}\n\nGenerated.\n"
            + user_block
        )
        existing.write_text(content, encoding="utf-8")


def run_pub(workdir: pathlib.Path, *args: str) -> int:
    cmd = [sys.executable, str(PUB_PY), *args, "--out-dir", str(workdir)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode


def read_report(workdir: pathlib.Path) -> dict:
    p = workdir / "reports" / "publish-report.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_manifest(workdir: pathlib.Path) -> dict:
    p = workdir / ".publish" / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_idempotent_20_notes(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1): republicar 20 notas actualiza 20, no crea 20."""
    ir_dir = FIXTURES / "ir-20-notes"
    shared = workdir / "c1-shared"
    # Primer publish: 20 creates.
    render_to(shared, ir_dir)
    rc1 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    if rc1 not in (0, 2):
        return False, f"primer publish exit={rc1}"
    rep1 = read_report(shared)
    if rep1.get("summary", {}).get("created") != 20:
        return False, f"esperaba 20 created, obtuvo {rep1.get('summary', {}).get('created')}"

    # Segundo publish (mismo workdir → manifest persiste): 20 skipped.
    render_to(shared, ir_dir)
    rc2 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    if rc2 not in (0, 2):
        return False, f"segundo publish exit={rc2}"
    rep2 = read_report(shared)
    summary2 = rep2.get("summary", {})
    return (summary2.get("created") == 0 and summary2.get("updated") == 0
            and summary2.get("skipped") == 20,
            f"r1: {rep1.get('summary')}; r2: {summary2}")


def c2_edited_blocks(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): editada a mano bloqueada sin --confirm-overwrite."""
    import json as _json
    ir_dir = FIXTURES / "ir-1-note-edited-by-hand"
    shared = workdir / "c2-shared"
    note_id = "pe0000000001"

    # Reset IR to original state.
    ir_path = ir_dir / f"{note_id}.json"
    ir_orig = make_ir(note_id, "EditedByHand")
    ir_path.write_text(_json.dumps(ir_orig, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    render_to(shared, ir_dir)
    rc1 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    if rc1 not in (0, 2):
        return False, f"primer publish exit={rc1}"

    target = shared / "render" / "markdown" / f"{note_id}.md"

    # Modifica el IR (cambia ir_sha) Y edita el archivo a mano.
    ir = _json.loads(ir_path.read_text(encoding="utf-8"))
    ir["title"] = "EditedByHand V2"
    ir_path.write_text(_json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    # Re-renderizar con el IR nuevo; el archivo tendrá el contenido nuevo del renderer.
    render_to(shared, ir_dir)
    # Editar a mano (añadir una línea de comentario).
    target.write_text(target.read_text(encoding="utf-8") + "\n<!-- manual edit -->\n",
                     encoding="utf-8")

    rc2 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    rep2 = read_report(shared)
    blocked = rep2.get("summary", {}).get("blocked", 0)
    if rc2 not in (0, 2) or blocked != 1:
        return False, f"esperaba 1 blocked, exit={rc2}; report={rep2.get('summary')}"

    # Con --confirm-overwrite: actualiza.
    render_to(shared, ir_dir)
    target.write_text(target.read_text(encoding="utf-8") + "\n<!-- manual edit -->\n",
                     encoding="utf-8")
    rc3 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown",
                  "--confirm-overwrite")
    rep3 = read_report(shared)
    updated = rep3.get("summary", {}).get("updated", 0)
    return (updated == 1 and rc3 == 0,
            f"con --confirm-overwrite: exit={rc3}, updated={updated}")


def c3_partial_publish(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3): publicación parcial solo toca lo cambiado."""
    import json as _json
    ir_dir = FIXTURES / "ir-20-notes"
    shared = workdir / "c3-shared"

    # Reset IR to original state (in case previous runs left modifications).
    target_ir = ir_dir / "pb0000000005.json"
    ir_orig = make_ir("pb0000000005", "Note 05")
    target_ir.write_text(_json.dumps(ir_orig, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    render_to(shared, ir_dir)
    rc1 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    if rc1 not in (0, 2):
        return False, f"primer publish exit={rc1}"
    rep1 = read_report(shared)

    # Modifica 1 IR.
    ir = _json.loads(target_ir.read_text(encoding="utf-8"))
    ir["title"] = "Modified Note 05"
    target_ir.write_text(_json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    render_to(shared, ir_dir)
    rc2 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    if rc2 not in (0, 2):
        return False, f"segundo publish exit={rc2}"
    rep2 = read_report(shared)
    s = rep2.get("summary", {})
    return (s.get("created") == 0 and s.get("updated") == 1 and s.get("skipped") == 19,
            f"r1: created={rep1.get('summary', {}).get('created')}; "
            f"r2: {s}")


def c4_status_command(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4: status command muestra manifest legible."""
    ir_dir = FIXTURES / "ir-1-note-changed"
    wd = workdir / "c4"
    render_to(wd, ir_dir)
    rc = run_pub(wd, "publish",
                 "--ir", str(ir_dir), "--destinations", "markdown")
    if rc not in (0, 2):
        return False, f"publish falló: exit={rc}"
    rc2 = run_pub(wd, "status")
    return (rc2 == 0, f"status exit={rc2}")


def c5_mark_edited(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5: mark-edited marca como edited_by_hand; siguiente publish bloquea."""
    import json as _json
    ir_dir = FIXTURES / "ir-1-note-changed"
    shared = workdir / "c5-shared"
    note_id = "pc0000000001"

    # Reset IR.
    ir_path = ir_dir / f"{note_id}.json"
    ir_orig = make_ir(note_id, "Changed")
    ir_path.write_text(_json.dumps(ir_orig, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    render_to(shared, ir_dir)
    run_pub(shared, "publish",
            "--ir", str(ir_dir), "--destinations", "markdown")
    rc = run_pub(shared, "mark-edited", note_id,
                 "--destination", "markdown")
    if rc != 0:
        return False, f"mark-edited exit={rc}"
    manifest = read_manifest(shared)
    entry = manifest.get("destinations", {}).get("markdown", {}).get(note_id, {})
    if not entry.get("edited_by_hand"):
        return False, f"edited_by_hand not set: {entry}"

    # Modificar el IR para que el siguiente publish vaya por la rama updated
    # (no skipped) y detecte edited_by_hand.
    ir = _json.loads(ir_path.read_text(encoding="utf-8"))
    ir["title"] = "Changed V2"
    ir_path.write_text(_json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    render_to(shared, ir_dir)
    rc2 = run_pub(shared, "publish",
                  "--ir", str(ir_dir), "--destinations", "markdown")
    rep2 = read_report(shared)
    return (rep2.get("summary", {}).get("blocked", 0) == 1,
            f"blocked={rep2.get('summary', {}).get('blocked', 0)}")


def c6_idempotent_three_runs(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: idempotencia — 3 corridas seguidas."""
    ir_dir = FIXTURES / "ir-1-note-changed"
    shared = workdir / "c6-shared"
    summaries = []
    for i in range(3):
        render_to(shared, ir_dir)
        run_pub(shared, "publish",
                "--ir", str(ir_dir), "--destinations", "markdown")
        summaries.append(read_report(shared).get("summary", {}))
    return (summaries[0].get("created") == 1
            and summaries[1].get("skipped") == 1
            and summaries[2].get("skipped") == 1,
            f"3 runs: {summaries}")


def c7_user_content_preserved(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: preserva bloque user-content entre publishes."""
    import json as _json
    ir_dir = FIXTURES / "ir-1-note-changed"
    note_id = "pc0000000001"
    shared = workdir / "c7-shared"

    # Reset IR.
    ir_path = ir_dir / f"{note_id}.json"
    ir_orig = make_ir(note_id, "Changed")
    ir_path.write_text(_json.dumps(ir_orig, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    render_to(shared, ir_dir)
    run_pub(shared, "publish",
            "--ir", str(ir_dir), "--destinations", "markdown")
    target = shared / "render" / "markdown" / f"{note_id}.md"
    content = target.read_text(encoding="utf-8")
    content += "\n\n<!-- user-content-start -->\nMy manual note.\n<!-- user-content-end -->\n"
    target.write_text(content, encoding="utf-8")
    run_pub(shared, "mark-edited", note_id, "--destination", "markdown")

    # Modificar IR para que el siguiente publish entre a la rama updated.
    ir = _json.loads(ir_path.read_text(encoding="utf-8"))
    ir["title"] = "Changed V2"
    ir_path.write_text(_json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    # Renderizar sin el bloque user-content (será preservado por el publisher).
    target2 = shared / "render" / "markdown" / f"{note_id}.md"
    content_no_block = content.split("<!-- user-content-start -->")[0].rstrip()
    target2.write_text(content_no_block + "\n", encoding="utf-8")

    rc = run_pub(shared, "publish",
                 "--ir", str(ir_dir), "--destinations", "markdown",
                 "--confirm-overwrite", "--force-manual-keep-comments")
    final = target2.read_text(encoding="utf-8")
    has_block = "<!-- user-content-start -->" in final and "My manual note." in final
    return (rc == 0 and has_block,
            f"rc={rc}, has_block={has_block}")


def c8_force_overwrite_keep(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: --force-manual-keep-comments preserva incluso si editada."""
    import json as _json
    ir_dir = FIXTURES / "ir-1-note-edited-by-hand"
    note_id = "pe0000000001"
    shared = workdir / "c8-shared"

    # Reset IR.
    ir_path = ir_dir / f"{note_id}.json"
    ir_orig = make_ir(note_id, "EditedByHand")
    ir_path.write_text(_json.dumps(ir_orig, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    render_to(shared, ir_dir)
    run_pub(shared, "publish",
            "--ir", str(ir_dir), "--destinations", "markdown")

    # Edit + add block.
    target = shared / "render" / "markdown" / f"{note_id}.md"
    target.write_text(target.read_text(encoding="utf-8")
                     + "\n<!-- user-content-start -->\nKeep me.\n<!-- user-content-end -->\n",
                     encoding="utf-8")
    # mark-edited captura el user-content al manifest.
    run_pub(shared, "mark-edited", note_id, "--destination", "markdown")

    # Modificar IR para que el siguiente publish entre a la rama updated.
    ir = _json.loads(ir_path.read_text(encoding="utf-8"))
    ir["title"] = "EditedByHand V2"
    ir_path.write_text(_json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    # render_to preserva el user-content (gracias a preserve_user_content=True).
    render_to(shared, ir_dir)

    rc = run_pub(shared, "publish",
                 "--ir", str(ir_dir), "--destinations", "markdown",
                 "--confirm-overwrite", "--force-manual-keep-comments")
    final = target.read_text(encoding="utf-8")
    return (rc == 0 and "Keep me." in final,
            f"rc={rc}, has 'Keep me.' = {'Keep me.' in final}")


def c9_report_json_valid(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: report JSON tiene keys correctas."""
    ir_dir = FIXTURES / "ir-1-note-changed"
    wd = workdir / "c9"
    render_to(wd, ir_dir)
    run_pub(wd, "publish",
            "--ir", str(ir_dir), "--destinations", "markdown")
    rep = read_report(wd)
    required = {"schema_version", "generated_at", "summary", "created",
                "updated", "skipped", "blocked", "errors"}
    summary_required = {"created", "updated", "skipped", "blocked", "errors"}
    missing = required - set(rep.keys())
    missing_summary = summary_required - set(rep.get("summary", {}).keys())
    return (len(missing) == 0 and len(missing_summary) == 0,
            f"missing={missing}, missing_summary={missing_summary}")


def c10_manifest_persists(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: el manifest persiste entre runs (atomic_write_json)."""
    ir_dir = FIXTURES / "ir-1-note-changed"
    wd = workdir / "c10"
    render_to(wd, ir_dir)
    run_pub(wd, "publish",
            "--ir", str(ir_dir), "--destinations", "markdown")
    m = read_manifest(wd)
    has_entry = "pc0000000001" in m.get("destinations", {}).get("markdown", {})
    return (has_entry, f"manifest entries: {list(m.get('destinations', {}).keys())}")


USER_CONTENT_START = "<!-- user-content-start -->"


CHECKS = [
    ("C1 Republicar 20 notas actualiza 20, no crea 20 (criterio 1)",
     c1_idempotent_20_notes),
    ("C2 Editada a mano bloqueada sin --confirm-overwrite (criterio 2)",
     c2_edited_blocks),
    ("C3 Publicación parcial solo toca lo cambiado (criterio 3)",
     c3_partial_publish),
    ("C4 Status command",
     c4_status_command),
    ("C5 mark-edited bloquea siguiente publish",
     c5_mark_edited),
    ("C6 Idempotencia en 3 corridas",
     c6_idempotent_three_runs),
    ("C7 user-content preservado con --force-manual-keep-comments",
     c7_user_content_preserved),
    ("C8 force-overwrite-keep preserva incluso si editada",
     c8_force_overwrite_keep),
    ("C9 Report JSON tiene keys correctas",
     c9_report_json_valid),
    ("C10 Manifest persiste entre runs",
     c10_manifest_persists),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not PUB_PY.exists():
        print(f"ERROR: publishing.py no encontrado", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="publishing-eval-"))
    print("=" * 70)
    print("F62 · Eval battery — Publicación idempotente")
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
