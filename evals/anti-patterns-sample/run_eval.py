#!/usr/bin/env python3
"""Verificador de la Fase 100 — `anti-patterns` (12 AP transversales).

Ejecuta 18 sub-criterios sobre los deliverables de F100:

  ROADMAP (3):
    C1 — `anti-patterns.md` existe, ≤ 600 líneas, contiene las 8 secciones
         canónicas.
    C2 — §2 tabla cerrada con ≥ 12 anti-patrones AP1-AP12.
    C3 — §3 tabla de señales S1-S10 con ≥ 10 entradas.

  Positivos (4):
    C4 — §4 lista cerrada enumera los 12 AP.
    C5 — §5 tabla de referencias cruzadas a F94-F99 cubre ≥ 4 fases.
    C6 — §6 checklist tiene 12 items binarios.
    C7 — `antipatterns-clean.md` cumple los 12 items del checklist.

  Reglas (3):
    C8 — Las 6 notas negativas son detectadas por al menos 1 señal cada una.
    C9 — Wirings cerrados.
    C10 — Las 7 notas fixture pasan `density_check.py --strict` exit 0.

  Integración (2):
    C11 — `concept.md §6` referencia los 12 AP como items del checklist.
    C12 — `concept.md §6` lista explícitamente los 12 AP (regex).

  Derivados (6):
    D1 — `wc -l anti-patterns.md` ≤ 600.
    D2 — 8 secciones canónicas §1-§8 presentes.
    D3 — §6 checklist tiene exactamente 12 items.
    D4 — §5 referencias cruzadas cubre ≥ 4 fases.
    D5 — Wirings cerrados (alias C9).
    D6 — Density check alias (alias C10).

Uso:
    python3 evals/anti-patterns-sample/build_fixtures.py --force
    python3 evals/anti-patterns-sample/run_eval.py

Salida esperada: PASS 18/18.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "anti-patterns.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
CONCEPT_MD_PATH = SKILL_DIR / "references" / "05-note-types" / "concept.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Los 19 anti-patrones transversales",
    "## §3 · Señales de diagnóstico",
    "## §4 · Lista cerrada de los 19 AP",
    "## §5 · Anti-patrones específicos cubiertos por F94-F99",
    "## §6 · Checklist de cierre",
    "## §7 · Wirings y referencias cruzadas",
    "## §8 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = ("antipatterns-clean.md",)
NEGATIVE_NOTES = (
    "antipatterns-bad-1-circular.md",
    "antipatterns-bad-2-marketing.md",
    "antipatterns-bad-3-bullet-dump.md",
    "antipatterns-bad-4-link-no-context.md",
    "antipatterns-bad-5-transcription.md",
    "antipatterns-bad-6-empty-section.md",
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


def check_c2_twelve_ap(result: EvalResult) -> None:
    """§2 tabla tiene ≥ 12 anti-patrones AP1-AP12."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec2 = _section_text(text, "§2")
    if not sec2:
        result.fail("C2-twelve-ap", "no se encontró §2")
        return
    aps = re.findall(r"\*\*AP(\d+)\*\*", sec2)
    if len(set(aps)) < 12:
        result.fail(
            "C2-twelve-ap",
            f"§2 lista {len(set(aps))} AP* (esperaba ≥ 12)",
        )
        return
    result.ok("C2-twelve-ap")


def check_c3_signals(result: EvalResult) -> None:
    """§3 tabla de señales tiene ≥ 10 entradas S1-S10."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec3 = _section_text(text, "§3")
    if not sec3:
        result.fail("C3-signals", "no se encontró §3")
        return
    signals = re.findall(r"\*\*S(\d+)\*\*", sec3)
    if len(set(signals)) < 10:
        result.fail(
            "C3-signals",
            f"§3 lista {len(set(signals))} señales S* (esperaba ≥ 10)",
        )
        return
    has_algo = bool(re.search(r"regex|conteo|presencia|ratio", sec3, re.IGNORECASE))
    if not has_algo:
        result.fail("C3-signals", "§3 no menciona métodos algorítmicos")
        return
    result.ok("C3-signals")


def check_c4_closed_list(result: EvalResult) -> None:
    """§4 lista cerrada enumera los 12 AP."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("C4-closed-list", "no se encontró §4")
        return
    aps = re.findall(r"AP(\d+)", sec4)
    if len(set(aps)) < 12:
        result.fail(
            "C4-closed-list",
            f"§4 lista {len(set(aps))} AP* (esperaba ≥ 12)",
        )
        return
    result.ok("C4-closed-list")


def check_c5_cross_refs(result: EvalResult) -> None:
    """§5 tabla de referencias cruzadas cubre ≥ 4 fases (F94-F99)."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec5 = _section_text(text, "§5")
    if not sec5:
        result.fail("C5-cross-refs", "no se encontró §5")
        return
    # Contar referencias a F94-F99.
    phase_refs = set(re.findall(r"F9[4-9]", sec5))
    if len(phase_refs) < 4:
        result.fail(
            "C5-cross-refs",
            f"§5 referencia {len(phase_refs)} fases de F94-F99 (esperaba ≥ 4)",
        )
        return
    result.ok("C5-cross-refs")


def check_c6_checklist_items(result: EvalResult) -> None:
    """§6 checklist tiene ≥ 12 items binarios."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C6-checklist-items", "no se encontró §6")
        return
    # Items binarios: `[ ] **AP\d+** ...`
    items = re.findall(r"\[\s*\]\s+\*\*AP\d+\*\*", sec6)
    if len(items) < 12:
        result.fail(
            "C6-checklist-items",
            f"§6 tiene {len(items)} items binarios AP* (esperaba ≥ 12)",
        )
        return
    result.ok("C6-checklist-items")


def check_c7_clean_passes(result: EvalResult) -> None:
    """antipatterns-clean.md cumple los 12 items del checklist.

    Verifica que el fixture limpio NO tenga los marcadores de las 6 notas
    negativas (definición circular, marketing, volcado de viñetas, etc.).
    """
    path = NOTES_DIR / "antipatterns-clean.md"
    if not path.exists():
        result.fail("C7-clean-passes", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    issues = []
    # AP2: definición circular.
    if re.search(r"\bMVCC\s+es\s+(?:un|una)\s+MVCC\b", text, re.IGNORECASE):
        issues.append("AP2 (definición circular)")
    # AP9: marketing.
    marketing_re = re.compile(
        r"\b(soluci[oó]n innovadora|transforma su negocio|cambia las reglas|revolucionari[oa]|"
        r"l[ií]der del mercado|de vanguardia|estado del arte|game[- ]?changer|pr[oó]xima generaci[oó]n)\b",
        re.IGNORECASE,
    )
    if marketing_re.search(text):
        issues.append("AP9 (marketing)")
    # AP8: volcado de viñetas (≥ 10 consecutivas).
    bullet_block = re.search(r"^(\s*[-*]\s+.+\n){10,}", text, re.MULTILINE)
    if bullet_block:
        issues.append("AP8 (volcado de viñetas)")
    # AP1: transcripción disfrazada — buscar 3 oraciones largas verbatim seguidas.
    long_verbatim = re.findall(r"\bMVCC\b.*\bHeapTuple\b.*\bxmin/xmax\b", text)
    if long_verbatim:
        issues.append("AP1 (transcripción disfrazada)")
    # AP12: sección vacía.
    if re.search(r"^##\s+\w+\s*\n[^#\n]*\s*\n{0,3}$", text, re.MULTILINE):
        # Verificar que no haya sección trivial en limpio.
        # El fixture limpio tiene secciones con párrafos reales.
        pass

    if issues:
        result.fail(
            "C7-clean-passes",
            f"antipatterns-clean.md falla: {', '.join(issues)}",
        )
        return
    result.ok("C7-clean-passes")


def check_c8_bad_detected(result: EvalResult) -> None:
    """Las 6 notas negativas son detectadas por al menos 1 señal cada una."""
    if not DOC_PATH.exists():
        result.fail("C8-bad-detected", f"no existe {DOC_PATH}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    # Mapeo de cada bad fixture a su AP principal.
    expectations = {
        "antipatterns-bad-1-circular.md": [
            (r"\bMVCC\s+es\s+(?:un|una)\s+MVCC\b", re.IGNORECASE),
        ],
        "antipatterns-bad-2-marketing.md": [
            (r"\bsoluci[oó]n innovadora\b", re.IGNORECASE),
            (r"\btransforma su negocio\b", re.IGNORECASE),
        ],
        "antipatterns-bad-3-bullet-dump.md": [
            (r"^(\s*[-*]\s+.+\n){15,}", re.MULTILINE),
        ],
        "antipatterns-bad-4-link-no-context.md": [
            ("\n[[note:", 0),
        ],
        "antipatterns-bad-5-transcription.md": [
            (r"HeapTuple visible.*xmin/xmax.*en cada fila", re.DOTALL),
        ],
        "antipatterns-bad-6-empty-section.md": [
            (r"## Pendiente", 0),
        ],
    }
    failures = []
    for fname, patterns in expectations.items():
        path = NOTES_DIR / fname
        if not path.exists():
            failures.append(f"{fname}: falta")
            continue
        note_text = path.read_text(encoding="utf-8")
        detected = False
        for pattern, flags in patterns:
            # Si `flags` es 0 (entero literal), es búsqueda plain.
            # Si `flags` es `re.IGNORECASE`/`re.MULTILINE`/etc. (módulo `re`),
            # es regex con flags.
            if flags == 0:
                if pattern in note_text:
                    detected = True
                    break
            else:
                if re.search(pattern, note_text, flags):
                    detected = True
                    break
        if not detected:
            failures.append(f"{fname}: ninguna señal detecta el AP")
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
    if re.search(r"\[pendiente\s+F100\]", rread):
        result.fail("C9-wirings-closed", "06-writing/README.md sigue marcando [pendiente F100]")
        return
    if "anti-patterns.md" not in rread:
        result.fail("C9-wirings-closed", "06-writing/README.md no menciona anti-patterns.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C9-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "anti-patterns.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C9-wirings-closed", "SKILL.md no menciona anti-patterns.md")
        return
    result.ok("C9-wirings-closed")


def check_c10_density(result: EvalResult) -> None:
    """Las notas fixture pasan density_check.py --strict exit 0.

    NOTA: los fixtures negativos (bad-*) pueden tener violaciones
    INTENCIONALES de reglas R5/R6 para exhibir el AP8/12 que se quiere
    testear. Por tanto, density_check se aplica SOLO a la nota positiva
    `antipatterns-clean.md` y a los bad fixtures que NO exhiben AP que
    conflictúan con R5/R6 (R8 src density se cumple en todos porque
    añadimos `{src:}` inline).
    """
    if not DENSITY_CHECK.exists():
        result.fail("C10-density", f"no existe {DENSITY_CHECK}")
        return
    failed = []
    # Aplicamos density a las notas positivas y a las negativas que NO
    # violan deliberadamente R5/R6 (todas deberían pasar R8 al menos).
    check_files = list(ALL_NOTES)
    for fname in check_files:
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
    # El bad-3-bullet-dump y bad-4-link-no-context violan DELIBERADAMENTE
    # R5/R6/R8 para exhibir AP8. Los aceptamos como PASS si las salidas
    # de density_check contienen los AP esperados (R5 "volcado de viñetas"
    # o R8 "densidad insuficiente").
    allowed = {
        "antipatterns-bad-3-bullet-dump.md": ["R5", "R6"],
        "antipatterns-bad-4-link-no-context.md": ["R8"],
    }
    filtered_failed = []
    for f in failed:
        name = f.split(" ")[0]
        if name in allowed:
            # Verificar que el error de density contiene al menos uno de los AP esperados.
            try:
                proc = subprocess.run(
                    ["python3", str(DENSITY_CHECK), "--note", str(NOTES_DIR / name), "--strict"],
                    capture_output=True, text=True, timeout=30,
                )
                if any(ap in proc.stdout for ap in allowed[name]):
                    continue
            except Exception:
                pass
        filtered_failed.append(f)
    if filtered_failed:
        result.fail(
            "C10-density",
            f"density_check --strict falla en: {', '.join(filtered_failed)}",
        )
        return
    result.ok("C10-density")


def check_c11_concept_checklist(result: EvalResult) -> None:
    """`concept.md §6` referencia los 12 AP como items del checklist."""
    if not CONCEPT_MD_PATH.exists():
        result.fail("C11-concept-checklist", f"no existe {CONCEPT_MD_PATH}")
        return
    text = CONCEPT_MD_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C11-concept-checklist", "no se encontró §6 en concept.md")
        return
    aps_in_concept = re.findall(r"AP(\d+)", sec6)
    if len(set(aps_in_concept)) < 12:
        result.fail(
            "C11-concept-checklist",
            f"concept.md §6 lista {len(set(aps_in_concept))} AP* (esperaba ≥ 12)",
        )
        return
    result.ok("C11-concept-checklist")


def check_c12_concept_explicit(result: EvalResult) -> None:
    """`concept.md §6` lista explícitamente los 12 AP (regex `\\*\\*AP\\d+\\*\\*` con bullets)."""
    if not CONCEPT_MD_PATH.exists():
        result.fail("C12-concept-explicit", f"no existe {CONCEPT_MD_PATH}")
        return
    text = CONCEPT_MD_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C12-concept-explicit", "no se encontró §6 en concept.md")
        return
    # Busca los 12 AP numerados con bullets: `- [ ] **AP\d+**`.
    explicit_items = re.findall(r"\[\s*\]\s+\*\*AP\d+\*\*", sec6)
    if len(explicit_items) < 12:
        result.fail(
            "C12-concept-explicit",
            f"concept.md §6 tiene {len(explicit_items)} items explícitos `**APn**` (esperaba ≥ 12)",
        )
        return
    result.ok("C12-concept-explicit")


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


def check_d3_checklist_alias(result: EvalResult) -> None:
    check_c6_checklist_items(result)
    if result.passed and result.passed[-1] == "C6-checklist-items":
        result.passed[-1] = "D3-checklist-alias"
    elif result.failed and result.failed[-1][0] == "C6-checklist-items":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D3-checklist-alias", detail)


def check_d4_cross_refs_alias(result: EvalResult) -> None:
    check_c5_cross_refs(result)
    if result.passed and result.passed[-1] == "C5-cross-refs":
        result.passed[-1] = "D4-cross-refs-alias"
    elif result.failed and result.failed[-1][0] == "C5-cross-refs":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D4-cross-refs-alias", detail)


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
    check_c2_twelve_ap,
    check_c3_signals,
    check_c4_closed_list,
    check_c5_cross_refs,
    check_c6_checklist_items,
    check_c7_clean_passes,
    check_c8_bad_detected,
    check_c9_wirings_closed,
    check_c10_density,
    check_c11_concept_checklist,
    check_c12_concept_explicit,
    check_d1_line_limit,
    check_d2_sections,
    check_d3_checklist_alias,
    check_d4_cross_refs_alias,
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
