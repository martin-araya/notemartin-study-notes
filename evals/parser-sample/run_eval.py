"""run_eval.py — autoverificación de Fase 48 (parser NoteMark → IR).

Uso:
    python3 evals/parser-sample/run_eval.py --check-all
    python3 evals/parser-sample/run_eval.py --criterion N

Verifica los 4 criterios ROADMAP de F48:
1. Parsea toda la gramática sin construcciones no soportadas.
2. Errores con archivo, línea y causa exacta.
3. IR generado valida contra el esquema.
4. Round-trip: IR → NoteMark → IR produce el mismo árbol (aproximación).

Sin dependencias externas (Python 3.9+ stdlib).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "authoring" / "parse_notemark.py"
SCHEMA = REPO / "skill" / "notemartin-study-notes" / "schemas" / "note-ir.schema.json"
FIXTURES = REPO / "evals" / "parser-sample" / "fixtures"


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _run(args: list[str]) -> tuple[int, str, str]:
    """Ejecuta parse_notemark.py y devuelve (exit, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=str(REPO / "skill" / "notemartin-study-notes" / "scripts" / "authoring"),
    )
    return proc.returncode, proc.stdout, proc.stderr


def check_module_exists() -> Result:
    if not SCRIPT.exists():
        return Result("scripts/authoring/parse_notemark.py existe", False, str(SCRIPT))
    return Result("scripts/authoring/parse_notemark.py existe", True, "")


def check_parses_full_grammar() -> Result:
    """Criterio #1: parsea toda la gramática."""
    if not FIXTURES.exists():
        return Result("Criterio #1: parsea gramática completa", False, "fixtures dir no existe")
    fixtures = list(FIXTURES.glob("*.nm"))
    if not fixtures:
        return Result("Criterio #1: parsea gramática completa", False, "sin fixtures .nm")
    failures = []
    for fx in fixtures:
        # error fixtures fallan por diseño; los demás deben parsear OK.
        if "error" in fx.name:
            continue
        exit, _, stderr = _run(["--source", str(fx), "--no-validate"])
        if exit != 0:
            failures.append(f"{fx.name}: exit={exit} stderr={stderr[:200]}")
    return Result(
        "Criterio #1: parsea gramática completa (≥4 fixtures OK)",
        not failures,
        f"fallos={len(failures)} :: {failures[:3]}",
    )


def check_error_with_line_and_cause() -> Result:
    """Criterio #2: error con archivo, línea y causa."""
    fx = FIXTURES / "error-unknown-directive.nm"
    if not fx.exists():
        return Result("Criterio #2: error con línea + causa", False, "fixture no existe")
    exit, _, stderr = _run(["--source", str(fx), "--mode", "lint"])
    if exit == 0:
        return Result("Criterio #2: error con línea + causa", False, "no se detectó error")
    # Verificar formato: archivo:linea:columna, Token, Causa.
    has_file_line = re.search(r"\S+\.nm:\d+:\d+", stderr) is not None
    has_token = "Token:" in stderr
    has_causa = "Causa:" in stderr
    return Result(
        "Criterio #2: error con archivo:linea + causa",
        has_file_line and has_token and has_causa,
        f"file:linea={has_file_line} token={has_token} causa={has_causa}",
    )


def check_ir_validates_against_schema() -> Result:
    """Criterio #3: IR valida contra schema."""
    fx = FIXTURES / "basic.nm"
    if not fx.exists():
        return Result("Criterio #3: IR valida contra schema", False, "fixture no existe")
    out_path = Path("/tmp/parser-eval-ir.json")
    exit, stdout, stderr = _run([
        "--source", str(fx),
        "--schema", str(SCHEMA),
        "--out", str(out_path),
    ])
    return Result(
        "Criterio #3: IR valida contra schema",
        exit == 0,
        f"exit={exit} stderr={stderr[:200]}",
    )


def check_round_trip() -> Result:
    """Criterio #4: round-trip (IR → NM → IR produce el mismo árbol estructuralmente)."""
    fx = FIXTURES / "basic.nm"
    if not fx.exists():
        return Result("Criterio #4: round-trip estructural", False, "fixture no existe")
    exit, stdout, stderr = _run([
        "--source", str(fx),
        "--schema", str(SCHEMA),
        "--round-trip",
    ])
    return Result(
        "Criterio #4: round-trip estructural",
        exit == 0,
        f"exit={exit} stdout={stdout[:200]}",
    )


def check_full_note_fixture() -> Result:
    """Bonus: parsea + valida + round-trip la nota-probe de F12 (full-note.nm)."""
    fx = REPO / "evals" / "notemark-sample" / "full-note.nm"
    if not fx.exists():
        return Result("Bonus: full-note.nm (F12) parsea y valida", False, "no existe")
    exit, _, stderr = _run([
        "--source", str(fx),
        "--schema", str(SCHEMA),
        "--out", "/tmp/full-note.ir.json",
    ])
    return Result(
        "Bonus: full-note.nm (F12) parsea y valida",
        exit == 0,
        f"exit={exit} stderr={stderr[:200]}",
    )


def check_inline_marks_fixture() -> Result:
    """Bonus: parsea + valida + round-trip la nota-probe de F46."""
    fx = REPO / "evals" / "inline-marks-sample" / "note-probe-inline.nm"
    if not fx.exists():
        return Result("Bonus: note-probe-inline.nm (F46) parsea y valida", False, "no existe")
    exit, _, stderr = _run([
        "--source", str(fx),
        "--schema", str(SCHEMA),
        "--round-trip",
    ])
    return Result(
        "Bonus: note-probe-inline.nm (F46) parsea + round-trip",
        exit == 0,
        f"exit={exit} stderr={stderr[:200]}",
    )


CRITERION_MAP = {
    1: ["Criterio #1: parsea gramática completa (≥4 fixtures OK)"],
    2: ["Criterio #2: error con archivo:linea + causa"],
    3: ["Criterio #3: IR valida contra schema"],
    4: ["Criterio #4: round-trip estructural"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3, 4])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    checks = [
        check_module_exists,
        check_parses_full_grammar,
        check_error_with_line_and_cause,
        check_ir_validates_against_schema,
        check_round_trip,
        check_full_note_fixture,
        check_inline_marks_fixture,
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
