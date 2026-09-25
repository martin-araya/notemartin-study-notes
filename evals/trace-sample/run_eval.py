"""run_eval.py — autoverificación de Fase 52 (trace.py).

Uso:
    python3 evals/trace-sample/run_eval.py --check-all
    python3 evals/trace-sample/run_eval.py --criterion N

Verifica los 3 criterios ROADMAP de F52 + cobertura sobre los fixtures.

Sin dependencias externas (Python 3.9+ stdlib).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "util" / "trace.py"
FIXTURES = REPO / "evals" / "trace-sample" / "fixtures"
SDMS = REPO / "evals" / "trace-sample" / "sdms"


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _run(args: list, cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True,
        cwd=str(cwd or REPO),
    )
    return proc.returncode, proc.stdout, proc.stderr


def check_module_exists() -> Result:
    if not SCRIPT.exists():
        return Result("scripts/util/trace.py existe", False, str(SCRIPT))
    return Result("scripts/util/trace.py existe", True, "")


def check_forward_in_one_step() -> Result:
    """Criterio #1: forward nodo → bloque en un paso (O(1) lookup)."""
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "clean.note-ir.json"
    sdm_src = SDMS / "test-sdm.json"
    ir_dst = workdir / "clean.note-ir.json"
    shutil.copy(src, ir_dst)

    exit, stdout, stderr = _run([
        "node",
        "--ir", str(ir_dst),
        "--node-path", "blocks[0]",
        "--sdm", str(sdm_src),
    ])
    if exit != 0:
        return Result("Criterio #1: forward en un paso", False,
                     f"exit={exit} stderr={stderr[:200]}")
    # Debe mostrar el bloque SDM con block_id aaa000000001.
    if "aaa000000001" not in stdout:
        return Result("Criterio #1: forward en un paso", False,
                     f"block_id no encontrado: {stdout[:300]}")
    return Result("Criterio #1: forward en un paso (índice O(1))", True, "")


def check_backward_for_any_block() -> Result:
    """Criterio #2: backward bloque → nodo funciona para cualquier bloque del SDM."""
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "clean.note-ir.json"
    ir_dst = workdir / "clean.note-ir.json"
    shutil.copy(src, ir_dst)
    sdm_src = SDMS / "test-sdm.json"
    notes_dir = workdir / "notes"
    notes_dir.mkdir()
    shutil.move(str(ir_dst), str(notes_dir / "clean.note-ir.json"))

    # Block usado en clean.note-ir.json.
    exit, stdout, _ = _run([
        "block",
        "--sdm", str(sdm_src),
        "--block-id", "aaa000000001",
        "--workdir", str(workdir),
    ])
    if exit != 0:
        return Result("Criterio #2: backward para bloque usado", False, f"exit={exit}")
    if "clean" not in stdout or "blocks[0]" not in stdout:
        return Result("Criterio #2: backward para bloque usado", False,
                     f"no muestra clean/blocks[0]: {stdout[:300]}")

    # Block NO usado (ccc000000003).
    exit2, stdout2, _ = _run([
        "block",
        "--sdm", str(sdm_src),
        "--block-id", "ccc000000003",
        "--workdir", str(workdir),
    ])
    if exit2 != 0:
        return Result("Criterio #2: backward para bloque no usado", False, f"exit={exit2}")
    if "ORPHAN" not in stdout2 and "no está anclado" not in stdout2:
        return Result("Criterio #2: backward para bloque no usado", False,
                     f"no marca como ORPHAN: {stdout2[:300]}")
    return Result("Criterio #2: backward funciona para cualquier bloque", True, "")


def check_orphans_type_a() -> Result:
    """Criterio #3 parte A: huérfanos tipo A (fácticos sin source_refs)."""
    src = FIXTURES / "orphan-typeA.note-ir.json"
    workdir = Path(tempfile.mkdtemp())
    ir_dst = workdir / "orphan-typeA.note-ir.json"
    shutil.copy(src, ir_dst)
    exit, stdout, _ = _run([
        "orphans",
        "--ir", str(ir_dst),
    ])
    if exit == 0:
        return Result("Criterio #3: huérfanos tipo A", False,
                     "no detectó el huérfano (exit=0 esperado !=0)")
    if "Type A" not in stdout:
        return Result("Criterio #3: huérfanos tipo A", False,
                     f"no reporta Type A: {stdout[:300]}")
    if "orphan-typeA.note-ir.json" not in stdout and "blocks[0]" not in stdout:
        return Result("Criterio #3: huérfanos tipo A", False,
                     f"no identifica archivo o path: {stdout[:300]}")
    return Result("Criterio #3: huérfanos tipo A detectados", True, "")


def check_orphans_type_b() -> Result:
    """Criterio #3 parte B: huérfanos tipo B (derivados sin marca)."""
    src = FIXTURES / "orphan-typeB.note-ir.json"
    workdir = Path(tempfile.mkdtemp())
    ir_dst = workdir / "orphan-typeB.note-ir.json"
    shutil.copy(src, ir_dst)
    exit, stdout, _ = _run([
        "orphans",
        "--ir", str(ir_dst),
    ])
    if "Type B" not in stdout:
        return Result("Criterio #3: huérfanos tipo B", False,
                     f"no reporta Type B: {stdout[:300]}")
    if "analogía" not in stdout.lower() and "podría" not in stdout.lower():
        return Result("Criterio #3: huérfanos tipo B", False,
                     f"no menciona marcadores: {stdout[:300]}")
    return Result("Criterio #3: huérfanos tipo B detectados", True, "")


def check_clean_no_orphans() -> Result:
    """Fixture clean no debe tener huérfanos."""
    src = FIXTURES / "clean.note-ir.json"
    workdir = Path(tempfile.mkdtemp())
    ir_dst = workdir / "clean.note-ir.json"
    shutil.copy(src, ir_dst)
    exit, stdout, _ = _run([
        "orphans",
        "--ir", str(ir_dst),
    ])
    # Clean no debe tener huérfanos tipo A; exit 0.
    if exit != 0:
        return Result("clean: sin huérfanos", False,
                     f"detectó huérfanos en clean: {stdout[:300]}")
    return Result("clean: sin huérfanos", True, "")


def check_audit_workdir() -> Result:
    """audit ejecuta node + block + orphans en un workdir completo."""
    workdir = Path(tempfile.mkdtemp())
    for fx in FIXTURES.glob("*.note-ir.json"):
        shutil.copy(fx, workdir / fx.name)
    notes_dir = workdir / "notes"
    notes_dir.mkdir()
    for fx in FIXTURES.glob("*.note-ir.json"):
        shutil.move(str(workdir / fx.name), str(notes_dir / fx.name))

    exit, stdout, _ = _run([
        "audit",
        "--workdir", str(workdir),
        "--sdm", str(SDMS / "test-sdm.json"),
    ])
    # Debe reportar ≥1 huérfano tipo A y tipo B.
    if "Type A" not in stdout:
        return Result("audit reporta Type A", False, f"no reporta Type A: {stdout[:300]}")
    if "Type B" not in stdout:
        return Result("audit reporta Type B", False, f"no reporta Type B: {stdout[:300]}")
    if "Blocks indexados" not in stdout:
        return Result("audit cuenta blocks indexados", False,
                     f"no reporta 'Blocks indexados': {stdout[:300]}")
    # Verificar que el número de blocks indexados > 0.
    import re
    m = re.search(r"Blocks indexados:\s*(\d+)", stdout)
    if m and int(m.group(1)) < 1:
        return Result("audit cuenta blocks indexados", False, f"blocks_indexed={m.group(1)}")
    return Result("audit ejecuta las 3 verificaciones", True, "")


CRITERION_MAP = {
    1: ["Criterio #1: forward en un paso (índice O(1))"],
    2: ["Criterio #2: backward funciona para cualquier bloque"],
    3: ["Criterio #3: huérfanos tipo A detectados",
        "Criterio #3: huérfanos tipo B detectados"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    checks = [
        check_module_exists,
        check_forward_in_one_step,
        check_backward_for_any_block,
        check_orphans_type_a,
        check_orphans_type_b,
        check_clean_no_orphans,
        check_audit_workdir,
    ]
    results = [c() for c in checks]

    if args.criterion:
        wanted = CRITERION_MAP[args.criterion]
        results = [r for r in results if r.name in wanted]

    if args.json:
        print(json.dumps([r._asdict() for r in results], indent=2, ensure_ascii=False))
    else:
        width = max(len(r.name) for r in results) + 2
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.name.ljust(width)} {r.detail}")
        n_pass = sum(1 for r in results if r.passed)
        n_total = len(results)
        print(f"\n  Resultado: {n_pass}/{n_total} verde")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
