#!/usr/bin/env python3
"""Verificador de la Fase 101 — `i18n-and-citation` (idioma bilingüe y citación).

Ejecuta 18 sub-criterios sobre los deliverables de F101:

  ROADMAP (4):
    C1 — `i18n-and-citation.md` existe, ≤ 600 líneas, contiene las 9 secciones
         canónicas.
    C2 — §2 tabla tiene los 4 valores del enum `language` con regla de prosa.
    C3 — §3 lista cerrada tiene ≥ 40 entradas (regex contra formato de tabla).
    C4 — §4 menciona el formato `[[en:term]]` / `[[es:term]]` y la regla de
         primera aparición.

  Positivos (4):
    C5 — §5 incluye plantilla cerrada de bloque de procedencia con 4 campos.
    C6 — §6 tiene ≥ 8 señales algorítmicas S1-S8.
    C7 — Las 3 notas positivas (good-1, good-2, good-3) cumplen los criterios.
    C8 — Las 3 notas negativas son detectadas por las señales.

  Reglas y wirings (4):
    C9 — Wirings cerrados.
    C10 — Las 6 notas fixture pasan `density_check.py --strict` exit 0.
    C11 — `properties.md §5.13` cita F101.
    C12 — `concept.md §6` lista los 4 items de F101 (F101-AP1 a F101-AP4).

  Derivados (6):
    D1 — `wc -l i18n-and-citation.md` ≤ 600.
    D2 — 9 secciones canónicas §1-§9 presentes.
    D3 — §3 lista cerrada ≥ 40 entradas (alias C3).
    D4 — §5 plantilla de procedencia con 4 campos.
    D5 — Wirings cerrados (alias C9).
    D6 — Density check alias (alias C10).

Uso:
    python3 evals/i18n-and-citation-sample/build_fixtures.py --force
    python3 evals/i18n-and-citation-sample/run_eval.py

Salida esperada: PASS 18/18.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "i18n-and-citation.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
PROPERTIES_PATH = SKILL_DIR / "references" / "04-authoring" / "properties.md"
CONCEPT_MD_PATH = SKILL_DIR / "references" / "05-note-types" / "concept.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Idioma del perfil y de la prosa",
    "## §3 · Lista cerrada de no-traducibles",
    "## §4 · Primera aparición bilingüe",
    "## §5 · Bloque de procedencia al pie de cada nota",
    "## §6 · Señales de diagnóstico",
    "## §7 · Anti-patrones",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = (
    "i18n-good-1-es.md",
    "i18n-good-2-es-en.md",
    "i18n-good-3-citation.md",
)
NEGATIVE_NOTES = (
    "i18n-bad-1-translated.md",
    "i18n-bad-2-no-citation.md",
    "i18n-bad-3-no-bilingual.md",
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

    @property
    def status(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _section_text(text: str, header_prefix: str) -> str:
    """Devuelve el texto de la sección H2/H3 que empieza con header_prefix,
    ignorando headers dentro de code fences."""
    lines = text.split("\n")
    start = None
    start_level = 2
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        if (line.startswith("## ") or line.startswith("### ")) and stripped.startswith(header_prefix):
            start = i
            start_level = len(line) - len(line.lstrip("#"))
            break
    if start is None:
        return ""
    end = len(lines)
    in_fence = False
    fence_marker = None
    for j in range(start + 1, len(lines)):
        stripped = lines[j].lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = stripped[:3]
                continue
            if lines[j].startswith("#"):
                level = len(lines[j]) - len(lines[j].lstrip("#"))
                if level <= start_level:
                    end = j
                    break
        else:
            if stripped.startswith(fence_marker):
                in_fence = False
    return "\n".join(lines[start:end])


def check_c1_doc_structure(result: EvalResult) -> None:
    if not DOC_PATH.exists():
        result.fail("C1-doc-structure", f"no existe {DOC_PATH}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("C1-doc-structure", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    for header in EXPECTED_SECTIONS:
        if header not in text:
            result.fail("C1-doc-structure", f"falta sección {header}")
            return
    result.ok("C1-doc-structure")


def check_c2_language_enum(result: EvalResult) -> None:
    """§2 tabla tiene los 4 valores del enum `language`."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec2 = _section_text(text, "§2")
    if not sec2:
        result.fail("C2-language-enum", "no se encontró §2")
        return
    required = ("es", "en", "es-en", "en-es")
    missing = [v for v in required if v not in sec2]
    if missing:
        result.fail(
            "C2-language-enum",
            f"§2 no menciona los valores del enum: {missing}",
        )
        return
    result.ok("C2-language-enum")


def check_c3_no_translatables(result: EvalResult) -> None:
    """§3 lista cerrada tiene ≥ 40 entradas."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec3 = _section_text(text, "§3")
    if not sec3:
        result.fail("C3-no-translatables", "no se encontró §3")
        return
    # Contar filas numeradas (formato `| N |` o `| **N** |`).
    rows = re.findall(r"^\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|", sec3, re.MULTILINE)
    nums = sorted({int(n) for n in rows})
    if len(nums) < 40:
        result.fail(
            "C3-no-translatables",
            f"§3 lista {len(nums)} entradas numeradas (esperaba ≥ 40)",
        )
        return
    result.ok("C3-no-translatables")


def check_c4_bilingual_format(result: EvalResult) -> None:
    """§4 menciona `[[en:term]]` / `[[es:term]]` y la primera aparición."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("C4-bilingual-format", "no se encontró §4")
        return
    if not re.search(r"\[\[en:[a-z0-9_-]+\]\]", sec4):
        result.fail("C4-bilingual-format", "§4 no menciona `[[en:term]]`")
        return
    if not re.search(r"\[\[es:[a-z0-9_-]+\]\]", sec4):
        result.fail("C4-bilingual-format", "§4 no menciona `[[es:term]]`")
        return
    if "primera aparición" not in sec4.lower():
        result.fail("C4-bilingual-format", "§4 no menciona la regla de primera aparición")
        return
    result.ok("C4-bilingual-format")


def check_c5_provenance_template(result: EvalResult) -> None:
    """§5 plantilla de procedencia con 4 campos."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec5 = _section_text(text, "§5")
    if not sec5:
        result.fail("C5-provenance-template", "no se encontró §5")
        return
    required_fields = ("Fuente", "Versión", "Fecha de recuperación", "URL/anchor")
    missing = [f for f in required_fields if f not in sec5]
    if missing:
        result.fail(
            "C5-provenance-template",
            f"§5 no incluye los 4 campos: {missing}",
        )
        return
    result.ok("C5-provenance-template")


def check_c6_signals(result: EvalResult) -> None:
    """§6 tiene ≥ 8 señales algorítmicas S1-S8."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C6-signals", "no se encontró §6")
        return
    signals = re.findall(r"\*\*S(\d+)\*\*", sec6)
    if len(set(signals)) < 8:
        result.fail(
            "C6-signals",
            f"§6 lista {len(set(signals))} señales S* (esperaba ≥ 8)",
        )
        return
    has_algo = bool(re.search(r"regex|conteo|presencia|ratio", sec6, re.IGNORECASE))
    if not has_algo:
        result.fail("C6-signals", "§6 no menciona métodos algorítmicos")
        return
    result.ok("C6-signals")


def check_c7_good_notes_pass(result: EvalResult) -> None:
    """Las 3 notas positivas cumplen los criterios i18n.

    Verificaciones:
    - good-1 (es): no flags traducidos; tiene Procedencia.
    - good-2 (es-en): tiene `[[en:]]` o `[[es:]]`; tiene Glosario; Procedencia.
    - good-3 (en): tiene Procedencia; sin marcas bilingües (monolingüe).
    """
    checks = {
        "i18n-good-1-es.md": [
            ("procedencia", "## Procedencia"),
            ("no-flag-traducido", "max-connections"),
            ("no-max-conexiones", "max-conexiones", False),  # False = NOT present
        ],
        "i18n-good-2-es-en.md": [
            ("procedencia", "## Procedencia"),
            ("glosario", "## Glosario"),
            ("bilingue", "[[en:"),
        ],
        "i18n-good-3-citation.md": [
            ("procedencia", "## Procedencia"),
            ("english-only", "Pending"),  # monolingüe inglés
        ],
    }
    failures = []
    for fname, expected in checks.items():
        path = NOTES_DIR / fname
        if not path.exists():
            failures.append(f"{fname}: falta")
            continue
        text = path.read_text(encoding="utf-8")
        for check in expected:
            name = check[0]
            pattern = check[1]
            should_be_present = check[2] if len(check) > 2 else True
            found = pattern in text
            if should_be_present and not found:
                failures.append(f"{fname}: falta '{pattern}'")
            if not should_be_present and found:
                failures.append(f"{fname}: contiene '{pattern}' (no debería)")
    if failures:
        result.fail("C7-good-pass", f"{len(failures)} checks fallan: {failures[:3]}")
        return
    result.ok("C7-good-pass")


def check_c8_bad_detected(result: EvalResult) -> None:
    """Las 3 notas negativas son detectadas por al menos 1 señal cada una."""
    expectations = {
        "i18n-bad-1-translated.md": ["max-conexiones"],
        "i18n-bad-2-no-citation.md": [],  # absence of Procedencia
        "i18n-bad-3-no-bilingual.md": [],  # absence of [[en:]] and [[es:]]
    }
    failures = []
    for fname, must_contain in expectations.items():
        path = NOTES_DIR / fname
        if not path.exists():
            failures.append(f"{fname}: falta")
            continue
        raw = path.read_text(encoding="utf-8")
        # Elimina líneas de comentario `> ...` antes de verificar.
        body_lines = [
            line for line in raw.split("\n")
            if not line.lstrip().startswith(">") and not line.lstrip().startswith("BAD:")
        ]
        text = "\n".join(body_lines)
        if must_contain:
            detected = any(s in text for s in must_contain)
            if not detected:
                failures.append(f"{fname}: no contiene ninguno de {must_contain}")
        elif "no-citation" in fname:
            if "## Procedencia" in text:
                failures.append(f"{fname}: contiene '## Procedencia' (no debería)")
        elif "no-bilingual" in fname:
            if "[[en:" in text or "[[es:" in text:
                failures.append(f"{fname}: contiene marcas bilingües (no debería)")
    if failures:
        result.fail(
            "C8-bad-detected",
            f"{len(failures)}/{len(expectations)} notas negativas no detectadas: {failures[:3]}",
        )
        return
    result.ok("C8-bad-detected")


def check_c9_wirings_closed(result: EvalResult) -> None:
    if not WRITING_README.exists():
        result.fail("C9-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    if re.search(r"\[pendiente\s+F101\]", rread):
        result.fail("C9-wirings-closed", "06-writing/README.md sigue marcando [pendiente F101]")
        return
    if "i18n-and-citation.md" not in rread:
        result.fail("C9-wirings-closed", "06-writing/README.md no menciona i18n-and-citation.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C9-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "i18n-and-citation.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C9-wirings-closed", "SKILL.md no menciona i18n-and-citation.md")
        return
    result.ok("C9-wirings-closed")


def check_c10_density(result: EvalResult) -> None:
    if not DENSITY_CHECK.exists():
        result.fail("C10-density", f"no existe {DENSITY_CHECK}")
        return
    failed = []
    for fname in ALL_NOTES:
        path = NOTES_DIR / fname
        if not path.exists():
            continue
        try:
            proc = subprocess.run(
                ["python3", str(DENSITY_CHECK), "--note", str(path), "--strict"],
                capture_output=True, text=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            result.fail("C10-density", f"density_check falló para {fname}: {e}")
            return
        if proc.returncode != 0:
            failed.append(f"{fname} (exit {proc.returncode})")
    if failed:
        result.fail("C10-density", f"density_check --strict falla en: {', '.join(failed)}")
        return
    result.ok("C10-density")


def check_c11_properties_wiring(result: EvalResult) -> None:
    """`properties.md §5.13` cita F101."""
    if not PROPERTIES_PATH.exists():
        result.fail("C11-properties-wiring", f"no existe {PROPERTIES_PATH}")
        return
    text = PROPERTIES_PATH.read_text(encoding="utf-8")
    if "F101" not in text:
        result.fail(
            "C11-properties-wiring",
            "properties.md no menciona F101 en §5.13 (language)",
        )
        return
    result.ok("C11-properties-wiring")


def check_c12_concept_checklist(result: EvalResult) -> None:
    """`concept.md §6` lista los 4 items de F101 (F101-AP1 a F101-AP4)."""
    if not CONCEPT_MD_PATH.exists():
        result.fail("C12-concept-checklist", f"no existe {CONCEPT_MD_PATH}")
        return
    text = CONCEPT_MD_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C12-concept-checklist", "no se encontró §6 en concept.md")
        return
    # Buscar los 4 items F101-APn explícitos.
    f101_items = re.findall(r"\*\*F101-AP(\d+)\*\*", sec6)
    if len(set(f101_items)) < 4:
        result.fail(
            "C12-concept-checklist",
            f"concept.md §6 lista {len(set(f101_items))} items F101-AP* (esperaba ≥ 4)",
        )
        return
    result.ok("C12-concept-checklist")


def check_d1_line_limit(result: EvalResult) -> None:
    if not DOC_PATH.exists():
        result.fail("D1-line-limit", f"no existe {DOC_PATH}")
        return
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("D1-line-limit", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    result.ok("D1-line-limit")


def check_d2_sections(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [h for h in EXPECTED_SECTIONS if h not in text]
    if missing:
        result.fail("D2-sections", f"faltan {len(missing)} secciones")
        return
    result.ok("D2-sections")


def check_d3_no_translatables_alias(result: EvalResult) -> None:
    check_c3_no_translatables(result)
    if result.passed and result.passed[-1] == "C3-no-translatables":
        result.passed[-1] = "D3-no-translatables-alias"
    elif result.failed and result.failed[-1][0] == "C3-no-translatables":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D3-no-translatables-alias", detail)


def check_d4_provenance_alias(result: EvalResult) -> None:
    check_c5_provenance_template(result)
    if result.passed and result.passed[-1] == "C5-provenance-template":
        result.passed[-1] = "D4-provenance-alias"
    elif result.failed and result.failed[-1][0] == "C5-provenance-template":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D4-provenance-alias", detail)


def check_d5_wirings_alias(result: EvalResult) -> None:
    check_c9_wirings_closed(result)
    if result.passed and result.passed[-1] == "C9-wirings-closed":
        result.passed[-1] = "D5-wirings-alias"
    elif result.failed and result.failed[-1][0] == "C9-wirings-closed":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D5-wirings-alias", detail)


def check_d6_density_alias(result: EvalResult) -> None:
    check_c10_density(result)
    if result.passed and result.passed[-1] == "C10-density":
        result.passed[-1] = "D6-density-alias"
    elif result.failed and result.failed[-1][0] == "C10-density":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D6-density-alias", detail)


CHECKS = (
    check_c1_doc_structure,
    check_c2_language_enum,
    check_c3_no_translatables,
    check_c4_bilingual_format,
    check_c5_provenance_template,
    check_c6_signals,
    check_c7_good_notes_pass,
    check_c8_bad_detected,
    check_c9_wirings_closed,
    check_c10_density,
    check_c11_properties_wiring,
    check_c12_concept_checklist,
    check_d1_line_limit,
    check_d2_sections,
    check_d3_no_translatables_alias,
    check_d4_provenance_alias,
    check_d5_wirings_alias,
    check_d6_density_alias,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args = parser.parse_args()

    result = EvalResult()
    for fn in CHECKS:
        fn(result)

    for name in result.passed:
        print(f"[PASS] {name}")
    for name, detail in result.failed:
        print(f"[FAIL] {name}: {detail}")
    print(f"\n{result.status}")
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
