"""run_eval.py — autoverificación de Fase 49 (validate_ir.py).

Uso:
    python3 evals/ir-validation-sample/run_eval.py --check-all
    python3 evals/ir-validation-sample/run_eval.py --criterion N

Verifica los 3 criterios ROADMAP de F49 + cobertura sobre los IRs del repo.

Sin dependencias externas (Python 3.9+ stdlib).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "validate" / "validate_ir.py"
SCHEMA = REPO / "skill" / "notemartin-study-notes" / "schemas" / "note-ir.schema.json"
FIXTURES = REPO / "evals" / "ir-validation-sample" / "fixtures"
SDMS = REPO / "evals" / "ir-validation-sample" / "sdms"
IR_SAMPLE = REPO / "evals" / "ir-sample"
PARSER_FIXTURES = REPO / "evals" / "parser-sample" / "fixtures"


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _run(args: list[str]) -> tuple[int, str, str]:
    """Ejecuta validate_ir.py y devuelve (exit, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    return proc.returncode, proc.stdout, proc.stderr


def check_module_exists() -> Result:
    if not SCRIPT.exists():
        return Result("scripts/validate/validate_ir.py existe", False, str(SCRIPT))
    return Result("scripts/validate/validate_ir.py existe", True, "")


def check_rejects_unknown_node() -> Result:
    """Criterio #1 parte 1: rechaza nodo desconocido."""
    ir = FIXTURES / "invalid-unknown-node.json"
    sdm = SDMS / "test-sdm.json"
    if not ir.exists():
        return Result("Rechaza nodo desconocido", False, "fixture no existe")
    exit, stdout, stderr = _run(["--ir", str(ir), "--sdm", str(sdm), "--skip-sdm"])
    if exit == 0:
        return Result("Rechaza nodo desconocido", False, "no rechazó el nodo 'weirdo'")
    combined = stdout + stderr
    if "weirdo" not in combined:
        return Result("Rechaza nodo desconocido", False, f"mensaje no menciona 'weirdo': {combined[:200]}")
    return Result("Rechaza nodo desconocido", exit != 0 and "weirdo" in combined, "")


def check_rejects_bad_child() -> Result:
    """Criterio #1 parte 2: rechaza hijo no permitido.

    Construimos un IR con un 'text' inline dentro de 'code' (que no admite hijos).
    """
    import tempfile
    bad_child_ir = {
        "schema_version": "1.0.0",
        "note_id": "bad-child",
        "title": "Bad child test",
        "layer": "l2",
        "blocks": [
            {
                "node": "code",
                "attrs": {"lang": "sql", "text": "SELECT 1", "capability": "code-block-fenced"},
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "should not be here", "capability": "text"}, "source_refs": []}
                ]
            }
        ]
    }
    tmp = Path(tempfile.mkdtemp()) / "bad-child.json"
    tmp.write_text(json.dumps(bad_child_ir), encoding="utf-8")
    exit, _, _ = _run(["--ir", str(tmp), "--sdm", str(SDMS / "test-sdm.json"), "--skip-sdm"])
    if exit == 0:
        return Result("Rechaza hijo no permitido", False, "no rechazó")
    return Result("Rechaza hijo no permitido", exit != 0, "")


def check_rejects_dangling_source_ref() -> Result:
    """Criterio #1 parte 3: rechaza source_ref.block_id que no existe en el SDM."""
    ir = FIXTURES / "invalid-bad-source-ref.json"
    sdm = SDMS / "test-sdm.json"
    if not ir.exists():
        return Result("Rechaza source_ref colgante", False, "fixture no existe")
    exit, stdout, stderr = _run(["--ir", str(ir), "--sdm", str(sdm)])
    if exit == 0:
        return Result("Rechaza source_ref colgante", False, "no rechazó el block_id inexistente")
    combined = stdout + stderr
    # El block_id 'fffefdfc0000' es el del fixture.
    if "fffefdfc0000" not in combined:
        return Result("Rechaza source_ref colgante", False, f"mensaje no menciona block_id: {combined[:200]}")
    if "no existe en el SDM" not in combined:
        return Result("Rechaza source_ref colgante", False, f"mensaje no menciona 'no existe en el SDM': {combined[:200]}")
    return Result("Rechaza source_ref colgante", True, "")


def check_warnings_not_errors() -> Result:
    """Criterio #2: avisos como warning, no error (default mode)."""
    ir = FIXTURES / "valid-with-1-item-list.json"
    if not ir.exists():
        return Result("Warnings no son errores", False, "fixture no existe")
    exit, stdout, _ = _run(["--ir", str(ir), "--sdm", str(SDMS / "test-sdm.json"), "--skip-sdm"])
    # El IR válido con 1 ítem debe dar warning pero exit 0 (default mode).
    if exit != 0:
        return Result("Warnings no son errores (default mode)", False,
                     f"exit={exit}; se esperaba 0 con solo warnings")
    if "W2" not in stdout:
        return Result("Warnings no son errores (default mode)", False, "warning W2 no reportado")
    # En modo --strict debe dar exit 1.
    exit_strict, _, _ = _run(["--ir", str(ir), "--sdm", str(SDMS / "test-sdm.json"), "--skip-sdm", "--strict"])
    if exit_strict != 1:
        return Result("Warnings no son errores (default mode)", False,
                     f"--strict debería exit 1 pero dio {exit_strict}")
    return Result("Warnings no son errores (default mode)", True, f"exit 0 default, exit 1 --strict")


def check_zero_false_positives() -> Result:
    """Criterio #3: cero falsos positivos sobre los ejemplos del repo.

    Construye un SDM dummy que cubre todos los block_ids presentes en los IRs
    generados por el parser y los IRs sintéticos, y verifica que no haya
    errores.
    """
    # Recopilar todos los block_ids de los IRs del repo.
    irs_to_check = []

    # 1) IRs sintéticos de F14.
    for fx in IR_SAMPLE.glob("*.json"):
        if fx.name.startswith("generate") or fx.suffix != ".json":
            continue
        irs_to_check.append(fx)

    # 2) Generar IRs del parser F48 sobre los probes.
    parser_script = REPO / "skill" / "notemartin-study-notes" / "scripts" / "authoring" / "parse_notemark.py"
    probe_files = [
        REPO / "evals" / "notemark-sample" / "full-note.nm",
        REPO / "evals" / "inline-marks-sample" / "note-probe-inline.nm",
    ]
    out_dir = Path(tempfile.mkdtemp()) if False else REPO / "evals" / "ir-validation-sample" / "real-corpus"
    out_dir.mkdir(parents=True, exist_ok=True)
    for probe in probe_files:
        if not probe.exists():
            continue
        ir_out = out_dir / f"{probe.stem}.note-ir.json"
        proc = subprocess.run(
            [sys.executable, str(parser_script), "--source", str(probe),
             "--schema", str(SCHEMA), "--out", str(ir_out)],
            capture_output=True, text=True,
            cwd=str(REPO / "skill" / "notemartin-study-notes" / "scripts" / "authoring"),
        )
        if proc.returncode == 0 and ir_out.exists():
            irs_to_check.append(ir_out)

    if not irs_to_check:
        return Result("Cero falsos positivos", False, "no se encontraron IRs para validar")

    # Construir SDM dummy con todos los block_ids.
    all_blocks = set()
    for ir_path in irs_to_check:
        try:
            ir = json.loads(ir_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Extraer block_ids de source_refs y source-ref inline.
        def walk(n):
            if isinstance(n, dict):
                for ref in n.get("source_refs", []):
                    if isinstance(ref, dict) and isinstance(ref.get("block_id"), str):
                        all_blocks.add(ref["block_id"])
                if n.get("node") == "source-ref":
                    bid = n.get("attrs", {}).get("block_id")
                    if bid:
                        all_blocks.add(bid)
                for c in n.get("children", []):
                    walk(c)
        for b in ir.get("blocks", []):
            walk(b)

    if not all_blocks:
        return Result("Cero falsos positivos", False, "no se encontraron block_ids en los IRs")

    # Crear SDM dummy.
    sdm_dummy = out_dir / "sdm-dummy.json"
    sdm_data = {
        "schema_version": "1.0.0",
        "source_hash": "0" * 64,
        "blocks": [{"id": bid, "kind": "p", "text": f"dummy for {bid}"} for bid in sorted(all_blocks)],
    }
    sdm_dummy.write_text(json.dumps(sdm_data), encoding="utf-8")

    # Validar cada IR con --skip-sdm (ya no necesitamos el SDM para esta verificación).
    failures = []
    n_pass = 0
    for ir_path in irs_to_check:
        exit, stdout, stderr = _run([
            "--ir", str(ir_path),
            "--sdm", str(sdm_dummy),
            "--skip-sdm",
        ])
        if exit != 0:
            failures.append(f"{ir_path.name}: exit={exit} stderr={stderr[:150]}")
        else:
            n_pass += 1
    return Result(
        f"Cero falsos positivos ({n_pass}/{len(irs_to_check)} IRs sin errores)",
        not failures,
        f"fallos={len(failures)} :: {failures[:3]}",
    )


def check_inspect_mode() -> Result:
    """Modo --inspect emite resumen estructural sin errores."""
    ir = FIXTURES / "valid-basic.json"
    if not ir.exists():
        return Result("--inspect mode", False, "fixture no existe")
    exit, stdout, _ = _run(["--ir", str(ir), "--sdm", str(SDMS / "test-sdm.json"), "--inspect"])
    if exit != 0:
        return Result("--inspect mode", False, f"exit={exit}")
    if "title:" not in stdout:
        return Result("--inspect mode", False, "no muestra 'title:'")
    if "blocks:" not in stdout:
        return Result("--inspect mode", False, "no muestra 'blocks:'")
    return Result("--inspect mode", True, "OK")


def check_malformed_source_ref_id() -> Result:
    """Bonus: detecta block_id malformado (no 12 hex)."""
    ir = FIXTURES / "invalid-source-ref-malformed.json"
    if not ir.exists():
        return Result("Detecta block_id malformado", False, "fixture no existe")
    exit, _, stderr = _run(["--ir", str(ir), "--sdm", str(SDMS / "test-sdm.json"), "--skip-sdm"])
    if exit == 0:
        return Result("Detecta block_id malformado", False, "no rechazó")
    return Result("Detecta block_id malformado", exit != 0, "")


CRITERION_MAP = {
    1: ["Rechaza nodo desconocido", "Rechaza hijo no permitido", "Rechaza source_ref colgante"],
    2: ["Warnings no son errores (default mode)"],
    3: ["Cero falsos positivos"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    checks = [
        check_module_exists,
        check_rejects_unknown_node,
        check_rejects_bad_child,
        check_rejects_dangling_source_ref,
        check_warnings_not_errors,
        check_zero_false_positives,
        check_inspect_mode,
        check_malformed_source_ref_id,
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
    # tempfile es necesario para check_rejects_bad_child.
    import tempfile  # noqa
    sys.exit(main(sys.argv[1:]))
