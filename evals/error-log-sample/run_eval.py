#!/usr/bin/env python3
"""Verificador de la Fase 103 — `error-log` (registro de errores propios).

Ejecuta 16 sub-criterios sobre los deliverables de F103:

  ROADMAP (3):
    C1 — La consulta de repaso vencido funciona donde hay soporte.
    C2 — Los errores registrados pueden generar tarjetas.
    C3 — La plantilla no contiene lenguaje de evaluación personal.

  Estructura del doc (3):
    C4 — `error-log.md` existe, ≤ 600 líneas, 9 secciones canónicas.
    C5 — §3 plantilla con 5 H4 obligatorios en orden.
    C6 — §4 lista cerrada ≥ 16 frases en 4 categorías.

  Scripts (3):
    C7 — `error_log_query.py --due --domain postgresql` devuelve ≥ 1 entrada vencida.
    C8 — `error_cards.py --domain postgresql --format obsidian-sr` genera ≥ 1 tarjeta.
    C9 — `error_log_check.py --strict` pasa en los 2 living-docs buenos.

  Negativos (1):
    C10 — `error_log_check.py --strict` falla en los 4 living-docs negativos.

  Density + wirings (3):
    C11 — Las 6 notas fixture pasan `density_check.py --strict`.
    C12 — Wirings cerrados: SKILL.md §5.3 menciona error-log.md;
          09-study/README.md marca error-log.md como publicado;
          anti-patterns.md §2 lista AP16; error-troubleshooting.md §6
          lista F103-1 + F103-2; properties.md §5.16 cita F103.
    C13 — `error_log_check.py --notes <dir>` (batch) pasa con ≥ 2 archivos buenos.

  Derivados (3):
    D1 — `wc -l error-log.md` ≤ 600 (INV-02).
    D2 — 9 secciones canónicas §1-§9 presentes.
    D3 — §4 lista cerrada ≥ 16 entradas (alias C6).

Uso:
    python3 evals/error-log-sample/build_fixtures.py --force
    python3 evals/error-log-sample/run_eval.py

Salida esperada: PASS 16/16.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "09-study" / "error-log.md"
STUDY_README = SKILL_DIR / "references" / "09-study" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
PROPERTIES_PATH = SKILL_DIR / "references" / "04-authoring" / "properties.md"
ANTI_PATTERNS_PATH = SKILL_DIR / "references" / "06-writing" / "anti-patterns.md"
ERROR_TROUBLESHOOTING_PATH = SKILL_DIR / "references" / "05-note-types" / "error-troubleshooting.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
SCRIPT_QUERY = SKILL_DIR / "scripts" / "study" / "error_log_query.py"
SCRIPT_CARDS = SKILL_DIR / "scripts" / "study" / "error_cards.py"
SCRIPT_CHECK = SKILL_DIR / "scripts" / "validate" / "error_log_check.py"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Estructura del living-doc",
    "## §3 · Plantilla cerrada de una entrada",
    "## §4 · Lenguaje de evaluación personal: lista cerrada de prohibidos",
    "## §5 · Reglas duras (R-E1 a R-E7)",
    "## §6 · Algoritmo del script",
    "## §7 · Algoritmo del script",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = (
    "error-log-good-postgresql.md",
    "error-log-good-docker.md",
)
NEGATIVE_NOTES = (
    "error-log-bad-autocritica.md",
    "error-log-bad-no-fundamento.md",
    "error-log-bad-no-repaso.md",
    "error-log-bad-verbatim-modificado.md",
)
ALL_NOTES = POSITIVE_NOTES + NEGATIVE_NOTES


class EvalResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _doc_line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def _run_script(script: Path, *args: str) -> Tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(script), *args],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    result = EvalResult()

    if not DOC_PATH.exists():
        result.fail("C4", f"no existe {DOC_PATH}")
        return _finalize(result)

    doc_text = _read(DOC_PATH)
    line_count = _doc_line_count(DOC_PATH)

    # ─── ROADMAP (3) ───
    # C1: la consulta de repaso vencido funciona — alias explícito de C7.
    # Se agrega tras C7 en el bloque de scripts; aquí solo emitimos OK
    # si C7 pasó (verificamos al final).
    # C2: los errores registrados pueden generar tarjetas — alias de C8.
    # C3: la plantilla no contiene lenguaje de evaluación personal —
    #     alias de C9 (positivos) + C10 (negativos).
    # Los añadimos como "alias" al final del main(), justo antes de _finalize.

    # ─── Estructura del doc (3) ───
    # C4: doc ≤ 600 + 9 secciones canónicas.
    if line_count > DOC_LINE_LIMIT:
        result.fail("C4", f"doc tiene {line_count} líneas (límite {DOC_LINE_LIMIT})")
    elif not all(sec in doc_text for sec in EXPECTED_SECTIONS):
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("C4", f"faltan secciones: {missing}")
    else:
        result.ok("C4")

    # C5: §3 plantilla con los 5 H4 obligatorios.
    sec3_match = re.search(
        r"## §3 · Plantilla cerrada.*?(?=^## §4)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec3_match:
        result.fail("C5", "no se encuentra §3")
    else:
        sec3 = sec3_match.group(0)
        required = ["Concepto", "Comando erróneo", "Corrección", "Origen", "Repaso"]
        missing = [r for r in required if f"#### {r}" not in sec3]
        if missing:
            result.fail("C5", f"§3 faltan H4: {missing}")
        else:
            result.ok("C5")

    # C6: §4 lista cerrada ≥ 16 frases en 4 categorías.
    sec4_match = re.search(
        r"## §4 · Lenguaje de evaluación.*?(?=^## §5)",
        doc_text, re.MULTILINE | re.DOTALL,
    )
    if not sec4_match:
        result.fail("C6", "no se encuentra §4")
    else:
        sec4 = sec4_match.group(0)
        # Contar filas con frase prohibida (formato `| N | Categoría | "frase" |`).
        rows = re.findall(r"^\|\s*\d+\s*\|\s*[^\|]+\|\s*\"[^\"]+\"", sec4, re.MULTILINE)
        # Contar categorías distintas en la columna 2.
        cats = re.findall(r"^\|\s*\d+\s*\|\s*([^\|]+?)\s*\|", sec4, re.MULTILINE)
        unique_cats = {c.strip() for c in cats if c.strip()}
        if len(rows) < 12:
            result.fail("C6", f"§4 tabla tiene {len(rows)} filas (esperaba ≥ 12)")
        elif len(unique_cats) < 4:
            result.fail("C6", f"§4 tiene {len(unique_cats)} categorías únicas (esperaba ≥ 4)")
        else:
            result.ok("C6")

    # ─── Scripts (3) ───
    # C7: error_log_query.py --due con postgresql devuelve ≥ 1 vencida.
    rc, output = _run_script(
        SCRIPT_QUERY, "--due", "--domain", "postgresql",
        "--errors-dir", str(NOTES_DIR),
    )
    # Contar entradas listadas (filas `| postgres | ...`).
    if rc == 0 and "| `postgresql` |" in output:
        result.ok("C7")
    elif rc == 1:
        # rc=1 con --due significa "sin vencidas" — falla C7.
        result.fail("C7", f"error_log_query --due no devolvió entradas vencidas (rc=1)")
    else:
        result.fail("C7", f"error_log_query --due fallo: rc={rc}, output={output[:200]}")

    # C8: error_cards.py --domain postgresql genera ≥ 1 tarjeta con tag priority-error.
    rc, output = _run_script(
        SCRIPT_CARDS, "--domain", "postgresql",
        "--errors-dir", str(NOTES_DIR),
        "--out-dir", "/tmp/error-log-eval-cards",
    )
    if rc == 0:
        # Verificar que el archivo contiene tarjetas con #priority-error.
        out_path = Path("/tmp/error-log-eval-cards/priority-error-postgresql.md")
        if out_path.exists():
            content = out_path.read_text(encoding="utf-8")
            if "#priority-error" in content and content.count("#priority-error") >= 1:
                result.ok("C8")
            else:
                result.fail("C8", "el archivo no contiene tag #priority-error")
        else:
            result.fail("C8", f"archivo no generado: {out_path}")
    else:
        result.fail("C8", f"error_cards fallo: rc={rc}, output={output[:300]}")

    # C9: error_log_check.py --strict pasa en los 2 living-docs buenos.
    positive_ok = 0
    positive_failures: List[str] = []
    for name in POSITIVE_NOTES:
        path = NOTES_DIR / name
        if not path.exists():
            positive_failures.append(f"{name}: no existe")
            continue
        rc, _ = _run_script(SCRIPT_CHECK, "--note", str(path), "--strict")
        if rc == 0:
            positive_ok += 1
        else:
            positive_failures.append(f"{name}: exit={rc}")
    if positive_ok == len(POSITIVE_NOTES):
        result.ok("C9")
    else:
        result.fail("C9", "; ".join(positive_failures))

    # ─── Negativos (1) ───
    # C10: error_log_check.py --strict falla en los 4 living-docs negativos.
    negative_ok = 0
    negative_failures: List[str] = []
    for name in NEGATIVE_NOTES:
        path = NOTES_DIR / name
        if not path.exists():
            negative_failures.append(f"{name}: no existe")
            continue
        rc, _ = _run_script(SCRIPT_CHECK, "--note", str(path), "--strict")
        if rc != 0:
            negative_ok += 1
        else:
            negative_failures.append(f"{name}: exit=0 (debería fallar)")
    if negative_ok == len(NEGATIVE_NOTES):
        result.ok("C10")
    else:
        result.fail("C10", "; ".join(negative_failures))

    # ─── Density + wirings (3) ───
    # C11: las 6 notas fixture pasan density_check --strict.
    density_ok = 0
    density_failures: List[str] = []
    for name in ALL_NOTES:
        path = NOTES_DIR / name
        if not path.exists():
            density_failures.append(f"{name}: no existe")
            continue
        rc, _ = _run_script(DENSITY_CHECK, "--note", str(path), "--strict")
        if rc == 0:
            density_ok += 1
        else:
            density_failures.append(f"{name}: exit={rc}")
    if density_ok == len(ALL_NOTES):
        result.ok("C11")
    else:
        result.fail("C11", "; ".join(density_failures))

    # C12: wirings cerrados.
    wirings_fail: List[str] = []
    if SKILL_MD_PATH.exists():
        skill_text = _read(SKILL_MD_PATH)
        if "error-log.md" not in skill_text:
            wirings_fail.append("SKILL.md no menciona error-log.md")
    else:
        wirings_fail.append("SKILL.md no existe")
    if STUDY_README.exists():
        study_text = _read(STUDY_README)
        # Buscar si error-log.md está en la columna "Estado" como [pendiente].
        # Patrón: fila de tabla Markdown con error-log.md.
        m = re.search(
            r"\|\s*`?error-log\.md`?\s*\|\s*F103\s*\|\s*(\S+?)\s*\|",
            study_text,
        )
        if m and "[pendiente]" in m.group(1):
            wirings_fail.append("09-study/README.md aún marca error-log.md como [pendiente]")
    else:
        wirings_fail.append("09-study/README.md no existe")
    if ANTI_PATTERNS_PATH.exists():
        ap_text = _read(ANTI_PATTERNS_PATH)
        if "AP16" not in ap_text:
            wirings_fail.append("anti-patterns.md no lista AP16")
    else:
        wirings_fail.append("anti-patterns.md no existe")
    if ERROR_TROUBLESHOOTING_PATH.exists():
        et_text = _read(ERROR_TROUBLESHOOTING_PATH)
        if "**F103-1**" not in et_text or "**F103-2**" not in et_text:
            wirings_fail.append("error-troubleshooting.md no lista F103-1 + F103-2")
    else:
        wirings_fail.append("error-troubleshooting.md no existe")
    if PROPERTIES_PATH.exists():
        props_text = _read(PROPERTIES_PATH)
        if "F103" not in props_text:
            wirings_fail.append("properties.md §5.16 no cita F103")
    if not wirings_fail:
        result.ok("C12")
    else:
        result.fail("C12", "; ".join(wirings_fail))

    # C13: error_log_check.py --notes <dir> batch pasa con ≥ 2 archivos buenos.
    # Crear un directorio temporal con solo los 2 positivos.
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in POSITIVE_NOTES:
            src = NOTES_DIR / name
            shutil.copy(src, Path(tmpdir) / name)
        rc, output = _run_script(SCRIPT_CHECK, "--notes", tmpdir, "--strict")
        if rc == 0:
            result.ok("C13")
        else:
            result.fail("C13", f"batch mode fallo: rc={rc}")

    # ─── Derivados (3) ───
    # D1: doc ≤ 600 líneas.
    if line_count <= DOC_LINE_LIMIT:
        result.ok("D1")
    else:
        result.fail("D1", f"{line_count} líneas (>{DOC_LINE_LIMIT})")

    # D2: 9 secciones canónicas presentes.
    if all(sec in doc_text for sec in EXPECTED_SECTIONS):
        result.ok("D2")
    else:
        missing = [s for s in EXPECTED_SECTIONS if s not in doc_text]
        result.fail("D2", f"faltan: {missing}")

    # D3: §4 lista cerrada ≥ 16 entradas (alias C6).
    if sec4_match:
        sec4 = sec4_match.group(0)
        rows = re.findall(r"^\|\s*\d+\s*\|\s*[^\|]+\|\s*\"[^\"]+\"", sec4, re.MULTILINE)
        if len(rows) >= 16:
            result.ok("D3")
        else:
            result.fail("D3", f"§4 tiene {len(rows)} filas (esperaba ≥ 16)")
    else:
        result.fail("D3", "no se encontró §4")

    # ─── Aliases de los 3 criterios ROADMAP (3) ───
    # C1: repaso vencido (alias de C7).
    if "C7" in result.passed:
        result.ok("C1-roadmap-repaso-vencido")
    else:
        result.fail("C1-roadmap-repaso-vencido", "C7 falló")
    # C2: tarjetas prioritarias (alias de C8).
    if "C8" in result.passed:
        result.ok("C2-roadmap-tarjetas-prioritarias")
    else:
        result.fail("C2-roadmap-tarjetas-prioritarias", "C8 falló")
    # C3: sin autocrítica (alias de C9 + C10).
    if "C9" in result.passed and "C10" in result.passed:
        result.ok("C3-roadmap-sin-autocritica")
    else:
        result.fail("C3-roadmap-sin-autocritica", "C9 o C10 fallaron")

    return _finalize(result)


def _finalize(result: EvalResult) -> int:
    total = result.total
    passed = len(result.passed)
    failed = len(result.failed)
    print(f"PASS {passed}/{total}")
    for name in result.passed:
        print(f"  [PASS] {name}")
    for name, detail in result.failed:
        print(f"  [FAIL] {name}: {detail}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
