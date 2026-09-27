#!/usr/bin/env python3
"""run_eval.py — eval battery del cross_target (F63).

10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/cross-target-sample/run_eval.py [--verbose]
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
CROSS_TARGET_PY = REPO / "skill/notemartin-study-notes/scripts/validate/cross_target.py"
FIXTURES = HERE / "fixtures"


def run_cross_target(ir_dir: pathlib.Path, out_dir: pathlib.Path,
                      destinations: str = "obsidian,markdown,html_pdf"
                      ) -> int:
    cmd = [
        sys.executable, str(CROSS_TARGET_PY),
        "--ir", str(ir_dir),
        "--out-dir", str(out_dir),
        "--destinations", destinations,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode


def read_report(out_dir: pathlib.Path) -> dict:
    p = out_dir / "reports" / "cross-target-report.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_clean_equivalence(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1: caso clean — todas las unidades presentes, 0 pérdidas."""
    src = FIXTURES
    dst = workdir / "c1"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    # Eliminar IRs degradados/lossy para enfocarnos en clean (ct0000000001-3).
    for f in [dst / "ir" / "degraded.json"]:  # degraded
        f.unlink()
    for f in [dst / "ir" / "lossy.json"]:  # lossy
        f.unlink()
    rc = run_cross_target(dst / "ir", dst)
    if rc != 0:
        return False, f"clean exit={rc} (esperaba 0)"
    rep = read_report(dst)
    s = rep.get("summary", {})
    return (s.get("units_lost", -1) == 0,
            f"summary: {s}")


def c2_degraded_justified(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1): con degradaciones — todas justificadas, 0 pérdidas."""
    src = FIXTURES
    dst = workdir / "c2"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    # Eliminar clean y lossy.
    for f in [dst / "ir" / f"ct000000{n:04d}.json" for n in (1, 2, 3)]:
        f.unlink()
    for f in [dst / "ir" / "lossy.json"]:
        f.unlink()
    # Sobrescribir el report con degradaciones para el degraded note.
    (dst / "reports" / "render-degradation.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "target": "obsidian",
        "source_hash": "0" * 64,
        "totals": {"ir_nodes": 3, "degradations": 2, "content_loss": 0},
        "degradations": [
            {"id": "deg-ct-1", "node_path": "0/1", "node_type": "paragraph",
             "capability": "paragraph", "alternative": "...",
             "evidence": "...", "content_intact": True},
            {"id": "deg-ct-2", "node_path": "0/2", "node_type": "admonition",
             "capability": "callout", "alternative": "...",
             "evidence": "...", "content_intact": True}
        ]
    }, indent=2) + "\n", encoding="utf-8")
    rc = run_cross_target(dst / "ir", dst,
                          destinations="obsidian,markdown")
    rep = read_report(dst)
    s = rep.get("summary", {})
    return (rc == 0 and s.get("units_lost", -1) == 0,
            f"exit={rc}, summary: {s}")


def c3_real_loss_detected(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1+C2: real loss detectado, exit=1."""
    src = FIXTURES
    dst = workdir / "c3"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    # Solo el IR lossy.
    for f in [dst / "ir" / f"ct000000{n:04d}.json" for n in (1, 2, 3)]:  # clean
        f.unlink()
    for f in list((dst / "ir").glob("ct000000001*.json")):  # degraded
        f.unlink()
    rc = run_cross_target(dst / "ir", dst)
    rep = read_report(dst)
    s = rep.get("summary", {})
    lost = s.get("units_lost", -1)
    return (rc == 1 and lost >= 1,
            f"exit={rc}, units_lost={lost}")


def c4_zero_lost_clean(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): cero pérdidas en caso clean para todos los pares."""
    src = FIXTURES
    dst = workdir / "c4"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    for f in [dst / "ir" / "degraded.json"]:
        f.unlink()
    for f in [dst / "ir" / "lossy.json"]:
        f.unlink()
    rc = run_cross_target(dst / "ir", dst)
    rep = read_report(dst)
    s = rep.get("summary", {})
    return (rc == 0 and s.get("units_lost", -1) == 0,
            f"clean: units_lost={s.get('units_lost')}")


def c5_zero_real_lost_with_degradations(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): cero pérdidas reales en caso con degradaciones."""
    src = FIXTURES
    dst = workdir / "c5"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    for f in [dst / "ir" / f"ct000000{n:04d}.json" for n in (1, 2, 3)]:
        f.unlink()
    for f in [dst / "ir" / "lossy.json"]:
        f.unlink()
    # Sobrescribir el report con degradaciones para el degraded note.
    (dst / "reports" / "render-degradation.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "target": "obsidian",
        "source_hash": "0" * 64,
        "totals": {"ir_nodes": 3, "degradations": 2, "content_loss": 0},
        "degradations": [
            {"id": "deg-ct-1", "node_path": "0/1", "node_type": "paragraph",
             "capability": "paragraph", "alternative": "...",
             "evidence": "...", "content_intact": True},
            {"id": "deg-ct-2", "node_path": "0/2", "node_type": "admonition",
             "capability": "callout", "alternative": "...",
             "evidence": "...", "content_intact": True}
        ]
    }, indent=2) + "\n", encoding="utf-8")
    rc = run_cross_target(dst / "ir", dst,
                          destinations="obsidian,markdown")
    rep = read_report(dst)
    s = rep.get("summary", {})
    return (rc == 0 and s.get("units_lost", -1) == 0
            and s.get("units_justified", -1) >= 2,
            f"summary: {s}")


def c6_lost_unit_identified(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): report identifica explícitamente la unidad perdida."""
    src = FIXTURES
    dst = workdir / "c6"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    for f in list((dst / "ir").glob("ct000000000*.json")):
        f.unlink()
    for f in list((dst / "ir").glob("ct000000001*.json")):
        f.unlink()
    run_cross_target(dst / "ir", dst)
    rep = read_report(dst)
    notes = rep.get("notes", {})
    found_lost = False
    found_path = ""
    found_canonical = ""
    for note_id, dests in notes.items():
        for dest, r in dests.items():
            for u in r.get("lost_units", []):
                if u.get("canonical", "").startswith("real critical"):
                    found_lost = True
                    found_path = u.get("node_path", "")
                    found_canonical = u.get("canonical", "")
                    break
            if found_lost:
                break
        if found_lost:
            break
    return (found_lost and "real critical" in found_canonical.lower(),
            f"found_lost={found_lost}, path={found_path}, "
            f"canon={found_canonical!r}")


def c7_runs_on_release_examples(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3): corre sobre los ejemplos de cada release (F54-F60 fixtures)."""
    # Usa los IRs reales de los renderers ya ejecutados.
    src = FIXTURES
    dst = workdir / "c7"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    rc = run_cross_target(dst / "ir", dst,
                          destinations="obsidian,markdown,html_pdf,notion_md")
    return (rc in (0, 1), f"exit={rc}")


def c8_cross_destination(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1: cross-destination equivalence — cada nodo del IR aparece en ≥1 destino."""
    src = FIXTURES
    dst = workdir / "c8"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    for f in [dst / "ir" / "degraded.json"]:
        f.unlink()
    for f in [dst / "ir" / "lossy.json"]:
        f.unlink()
    rc = run_cross_target(dst / "ir", dst)
    rep = read_report(dst)
    s = rep.get("summary", {})
    return (rc == 0 and s.get("units_lost", -1) == 0,
            f"cross-target clean: units_lost={s.get('units_lost')}")


def c9_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2+C3: idempotencia — correr 2 veces produce mismo summary."""
    src = FIXTURES
    dst1 = workdir / "c9-r1"
    dst2 = workdir / "c9-r2"
    for d in (dst1, dst2):
        shutil.copytree(src / "ir", d / "ir")
        shutil.copytree(src / "render", d / "render")
        shutil.copytree(src / "reports", d / "reports")
    run_cross_target(dst1 / "ir", dst1)
    run_cross_target(dst2 / "ir", dst2)
    rep1 = read_report(dst1)
    rep2 = read_report(dst2)
    s1 = rep1.get("summary", {})
    s2 = rep2.get("summary", {})
    # Compara solo métricas (no timestamps).
    for key in ("total_units", "units_present", "units_justified", "units_lost"):
        if s1.get(key) != s2.get(key):
            return False, f"diferencia en {key}: r1={s1.get(key)} r2={s2.get(key)}"
    return True, f"summary idéntico: {s1}"


def c10_no_regression(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3: el script no rompe los IRs reales (smoke test con todos los IRs)."""
    src = FIXTURES
    dst = workdir / "c10"
    shutil.copytree(src / "ir", dst / "ir")
    shutil.copytree(src / "render", dst / "render")
    shutil.copytree(src / "reports", dst / "reports")
    rc = run_cross_target(dst / "ir", dst)
    rep = read_report(dst)
    has_keys = all(k in rep for k in ("schema_version", "summary", "notes"))
    return (has_keys, f"exit={rc}, has_keys={has_keys}")


CHECKS = [
    ("C1 Caso clean — 0 diferencias (criterio 1)",
     c1_clean_equivalence),
    ("C2 Degradaciones justificadas — 0 pérdidas (criterio 1)",
     c2_degraded_justified),
    ("C3 Real loss detectado — exit 1 (criterio 2)",
     c3_real_loss_detected),
    ("C4 Cero pérdidas clean (criterio 2)",
     c4_zero_lost_clean),
    ("C5 Cero pérdidas reales con degradaciones (criterio 2)",
     c5_zero_real_lost_with_degradations),
    ("C6 Report identifica unidad perdida explícitamente (criterio 2)",
     c6_lost_unit_identified),
    ("C7 Corre sobre los ejemplos en cada release (criterio 3)",
     c7_runs_on_release_examples),
    ("C8 Cross-destination equivalence (criterio 1)",
     c8_cross_destination),
    ("C9 Idempotencia (criterio 2)",
     c9_idempotent),
    ("C10 Report JSON tiene keys correctas (criterio 3)",
     c10_no_regression),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not CROSS_TARGET_PY.exists():
        print(f"ERROR: cross_target.py no encontrado", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="cross-target-eval-"))
    print("=" * 70)
    print("F63 · Eval battery — Cross-target equivalence")
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
