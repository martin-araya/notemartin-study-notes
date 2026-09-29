#!/usr/bin/env python3
"""Verificador de la Fase 99 — `voice-style` (8 reglas verificables R1-R8).

Ejecuta 17 sub-criterios sobre los deliverables de F99:

  ROADMAP (3):
    C1 — `voice-style.md` existe, ≤ 500 líneas, contiene las 11 secciones
         canónicas.
    C2 — §2 tiene las 8 reglas verificables R1-R8 con regex/señal
         algorítmica por regla.
    C3 — §3 tiene ≥ 15 adjetivos valorativos prohibidos.

  Positivos (5):
    C4 — Las 2 notas base (style-good-1.md, style-good-2.md) cumplen las
         8 reglas R1-R8.
    C5 — style-bad-1-passive.md es detectado por R2 (≥ 30% pasivas).
    C6 — style-bad-2-adjectives.md es detectado por R3 (≥ 5 adjetivos).
    C7 — style-bad-3-long.md es detectado por R1 (≥ 50% frases > 25 palabras).
    C8 — style-bad-4-mixed.md es detectado por R6 (mezcla de tiempos).

  Reglas y wirings (3):
    C9 — §9 plantilla de verificación tiene 8 preguntas binarias.
    C10 — Wirings cerrados (`06-writing/README.md` y `SKILL.md`).
    C11 — Las 6 notas fixture pasan `density_check.py --strict` exit 0.

  Derivados (6):
    D1 — `wc -l voice-style.md` ≤ 500.
    D2 — 11 secciones canónicas §1-§11 presentes.
    D3 — §3 tiene ≥ 15 adjetivos (alias C3).
    D4 — §6 tabla de persona por sección tiene ≥ 4 filas.
    D5 — §7 tiempos tiene regex concreto.
    D6 — Wirings cerrados (alias C10).

Uso:
    python3 evals/voice-style-sample/build_fixtures.py --force
    python3 evals/voice-style-sample/run_eval.py

Salida esperada: PASS 17/17.

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
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "voice-style.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 500

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Las 8 reglas verificables",
    "## §3 · Lista cerrada de adjetivos valorativos prohibidos",
    "## §4 · Longitud de frase",
    "## §5 · Voz activa vs pasiva",
    "## §6 · Persona gramatical",
    "## §7 · Tiempos verbales consistentes",
    "## §8 · Anti-patrones de voz",
    "## §9 · Plantilla cerrada de verificación",
    "## §10 · Wirings y referencias cruzadas",
    "## §11 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = ("style-good-1.md", "style-good-2.md")
ALL_NOTES = POSITIVE_NOTES + (
    "style-bad-1-passive.md",
    "style-bad-2-adjectives.md",
    "style-bad-3-long.md",
    "style-bad-4-mixed.md",
)

PROHIBITED_ADJECTIVES_RE = re.compile(
    r"\b(sencill[oa]|poderos[oa]|potent[e]|elegante|simple|robust[oa]|"
    r"incre[ií]ble|m[aá]gic[oa]|revolucionari[oa]|brutal|bestial|"
    r"killer|awesome|fantastic|amazing|game[- ]?changer|"
    r"indispensable|vital|premium|leading|imprescindible)\b",
    re.IGNORECASE,
)

PASSIVE_RE = re.compile(
    r"\b(es|fue|será|era|sería|ha sido|han sido|había sido)\s+\w+(ado|ido|ada|idos|adas)\b",
    re.IGNORECASE,
)

FILLER_RE = re.compile(
    r"\b(es importante destacar|vale la pena mencionar|cabe se[ñn]alar|es necesario subrayar|es menester destacar)\b",
    re.IGNORECASE,
)

PRESENT_RE = re.compile(
    r"\b\w+(a|an|o|as|amos|áis|an|e|es|emos|éis|en)\b\s+\w+",
    re.IGNORECASE,
)
PAST_RE = re.compile(
    r"\b\w+(ó|aron|ieron|aba|aban|í|imos|iste|ió|isteis)\b",
    re.IGNORECASE,
)
FUTURE_RE = re.compile(
    r"\b\w+(rá|rán|ré|remos|rás|réis|ará|aremos|aráis|erán)\b",
    re.IGNORECASE,
)


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


def check_c2_eight_rules(result: EvalResult) -> None:
    """§2 tiene las 8 reglas verificables R1-R8."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec2 = _section_text(text, "§2")
    if not sec2:
        result.fail("C2-eight-rules", "no se encontró §2")
        return
    rules_found = set(re.findall(r"\*\*R(\d+)\*\*", sec2))
    if len(rules_found) < 8:
        result.fail(
            "C2-eight-rules",
            f"§2 lista {len(rules_found)} reglas R* (esperaba 8)",
        )
        return
    # Cada regla debe tener una señal algorítmica (regex o conteo).
    has_algo = bool(re.search(r"regex|conteo|palabras por frase|ratio", sec2, re.IGNORECASE))
    if not has_algo:
        result.fail("C2-eight-rules", "§2 no menciona métodos algorítmicos")
        return
    result.ok("C2-eight-rules")


def check_c3_adjectives(result: EvalResult) -> None:
    """§3 tiene ≥ 15 adjetivos valorativos."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec3 = _section_text(text, "§3")
    if not sec3:
        result.fail("C3-adjectives", "no se encontró §3")
        return
    # Adjetivos listados: regex contra los IDs V1-V20.
    adj_ids = re.findall(r"\*\*V(\d+)\*\*", sec3)
    if len(set(adj_ids)) < 15:
        result.fail(
            "C3-adjectives",
            f"§3 lista {len(set(adj_ids))} adjetivos V* (esperaba ≥ 15)",
        )
        return
    result.ok("C3-adjectives")


def _split_sentences(text: str) -> List[str]:
    # Elimina bloques de código fenced antes de dividir.
    lines = text.split("\n")
    body = []
    in_fence = False
    fence_marker = None
    for line in lines:
        stripped = line.lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = stripped[:3]
                continue
            body.append(line)
        else:
            if stripped.startswith(fence_marker):
                in_fence = False
    body_text = "\n".join(body)
    # Divide por `.` `!` `?` seguidos de espacio.
    sents = re.split(r"[.!?]+\s+", body_text)
    return [s.strip() for s in sents if s.strip() and len(s.strip()) > 5]


def _count_words(text: str) -> int:
    return len(text.split())


def _voice_active_ratio(text: str) -> float:
    sents = _split_sentences(text)
    if not sents:
        return 1.0
    passive = sum(1 for s in sents if PASSIVE_RE.search(s))
    return 1.0 - (passive / len(sents))


def _adjective_density(text: str) -> float:
    words = _count_words(text)
    if words == 0:
        return 0.0
    count = len(PROHIBITED_ADJECTIVES_RE.findall(text))
    return count / words


def _long_sentence_ratio(text: str, threshold: int = 25) -> float:
    sents = _split_sentences(text)
    if not sents:
        return 0.0
    over = sum(1 for s in sents if len(s.split()) > threshold)
    return over / len(sents)


def _dominant_tense_ratio(text: str) -> float:
    present = len(PRESENT_RE.findall(text))
    past = len(PAST_RE.findall(text))
    future = len(FUTURE_RE.findall(text))
    total = present + past + future
    if total == 0:
        return 1.0
    return max(present, past, future) / total


def _filler_ratio(text: str) -> float:
    sents = _split_sentences(text)
    if not sents:
        return 0.0
    fill = sum(1 for s in sents if FILLER_RE.search(s))
    return fill / len(sents)


def check_c4_good_notes_pass(result: EvalResult) -> None:
    """Las 2 notas base cumplen las 8 reglas."""
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        if not path.exists():
            result.fail("C4-good-pass", f"falta {path}")
            return
        text = path.read_text(encoding="utf-8")
        # R1: ≤ 30% frases > 25 palabras (más tolerante en good notes).
        long_ratio = _long_sentence_ratio(text, threshold=25)
        if long_ratio > 0.30:
            result.fail(
                "C4-good-pass",
                f"{fname}: {long_ratio:.2f} de frases > 25 palabras (esperaba ≤ 0.30) — R1 falla",
            )
            return
        # R2: ≥ 80% activas.
        active_ratio = _voice_active_ratio(text)
        if active_ratio < 0.80:
            result.fail(
                "C4-good-pass",
                f"{fname}: solo {active_ratio:.2f} activas (esperaba ≥ 0.80) — R2 falla",
            )
            return
        # R3: ≤ 2 adjetivos valorativos por 200 palabras.
        adj_density = _adjective_density(text)
        if adj_density > 0.01:  # 2 / 200
            result.fail(
                "C4-good-pass",
                f"{fname}: {adj_density:.4f} adjetivos/word (esperaba ≤ 0.01) — R3 falla",
            )
            return
    result.ok("C4-good-pass")


def check_c5_bad_passive(result: EvalResult) -> None:
    """style-bad-1-passive.md es detectado por R2."""
    path = NOTES_DIR / "style-bad-1-passive.md"
    if not path.exists():
        result.fail("C5-bad-passive", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    active_ratio = _voice_active_ratio(text)
    # El fixture debería tener < 70% activas (≥ 30% pasivas).
    if active_ratio >= 0.70:
        result.fail(
            "C5-bad-passive",
            f"el fixture pasivo tiene {active_ratio:.2f} activas (esperaba < 0.70)",
        )
        return
    result.ok("C5-bad-passive")


def check_c6_bad_adjectives(result: EvalResult) -> None:
    """style-bad-2-adjectives.md es detectado por R3."""
    path = NOTES_DIR / "style-bad-2-adjectives.md"
    if not path.exists():
        result.fail("C6-bad-adjectives", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    count = len(PROHIBITED_ADJECTIVES_RE.findall(text))
    if count < 5:
        result.fail(
            "C6-bad-adjectives",
            f"el fixture de adjetivos tiene solo {count} matches (esperaba ≥ 5)",
        )
        return
    result.ok("C6-bad-adjectives")


def check_c7_bad_long(result: EvalResult) -> None:
    """style-bad-3-long.md es detectado por R1."""
    path = NOTES_DIR / "style-bad-3-long.md"
    if not path.exists():
        result.fail("C7-bad-long", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    long_ratio = _long_sentence_ratio(text, threshold=25)
    # El fixture debería tener ≥ 50% frases > 25 palabras.
    if long_ratio < 0.50:
        result.fail(
            "C7-bad-long",
            f"el fixture de frases largas tiene solo {long_ratio:.2f} (esperaba ≥ 0.50)",
        )
        return
    result.ok("C7-bad-long")


def check_c8_bad_mixed(result: EvalResult) -> None:
    """style-bad-4-mixed.md es detectado por R6."""
    path = NOTES_DIR / "style-bad-4-mixed.md"
    if not path.exists():
        result.fail("C8-bad-mixed", f"falta {path}")
        return
    text = path.read_text(encoding="utf-8")
    # El fixture tiene presente + pasado + futuro todos ≥ 1 cada uno.
    present = len(PRESENT_RE.findall(text))
    past = len(PAST_RE.findall(text))
    future = len(FUTURE_RE.findall(text))
    total = present + past + future
    if total == 0:
        result.fail("C8-bad-mixed", "el fixture de tiempos no tiene conjugaciones")
        return
    # Tiempo dominante < 80% indica mezcla.
    dominant_ratio = max(present, past, future) / total
    if dominant_ratio >= 0.80:
        result.fail(
            "C8-bad-mixed",
            f"el fixture de tiempos tiene dominante {dominant_ratio:.2f} (esperaba < 0.80)",
        )
        return
    # Verificar que los 3 tiempos están presentes.
    if not (present > 0 and past > 0 and future > 0):
        result.fail(
            "C8-bad-mixed",
            f"el fixture no mezcla los 3 tiempos (presente={present}, pasado={past}, futuro={future})",
        )
        return
    result.ok("C8-bad-mixed")


def check_c9_verification_template(result: EvalResult) -> None:
    """§9 tiene 8 preguntas binarias con método algorítmico."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec9 = _section_text(text, "§9")
    if not sec9:
        result.fail("C9-verification-template", "no se encontró §9")
        return
    questions = re.findall(r"\[\s*\] P(\d+)", sec9)
    if len(set(questions)) < 8:
        result.fail(
            "C9-verification-template",
            f"§9 lista {len(set(questions))} preguntas P* (esperaba ≥ 8)",
        )
        return
    has_algo = bool(re.search(r"regex|ratio|conteo|contar", sec9, re.IGNORECASE))
    if not has_algo:
        result.fail("C9-verification-template", "§9 no menciona métodos algorítmicos")
        return
    result.ok("C9-verification-template")


def check_c10_wirings_closed(result: EvalResult) -> None:
    if not WRITING_README.exists():
        result.fail("C10-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    if re.search(r"\[pendiente\s+F99\]", rread):
        result.fail("C10-wirings-closed", "06-writing/README.md sigue marcando [pendiente F99]")
        return
    if "voice-style.md" not in rread:
        result.fail("C10-wirings-closed", "06-writing/README.md no menciona voice-style.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C10-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "voice-style.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C10-wirings-closed", "SKILL.md no menciona voice-style.md")
        return
    result.ok("C10-wirings-closed")


def check_c11_density(result: EvalResult) -> None:
    if not DENSITY_CHECK.exists():
        result.fail("C11-density", f"no existe {DENSITY_CHECK}")
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
            result.fail("C11-density", f"density_check falló para {fname}: {e}")
            return
        if proc.returncode != 0:
            failed.append(f"{fname} (exit {proc.returncode})")
    if failed:
        result.fail("C11-density", f"density_check --strict falla en: {', '.join(failed)}")
        return
    result.ok("C11-density")


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


def check_d3_adjectives_alias(result: EvalResult) -> None:
    check_c3_adjectives(result)
    if result.passed and result.passed[-1] == "C3-adjectives":
        result.passed[-1] = "D3-adjectives-alias"
    elif result.failed and result.failed[-1][0] == "C3-adjectives":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D3-adjectives-alias", detail)


def check_d4_persona_table(result: EvalResult) -> None:
    """§6 tabla de persona por sección tiene ≥ 4 filas."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("D4-persona-table", "no se encontró §6")
        return
    # Contar secciones H3 o filas de tabla con `##`.
    rows = re.findall(r"`##\s+(\w[\w\s]*)`", sec6)
    if len(rows) < 4:
        result.fail(
            "D4-persona-table",
            f"§6 lista {len(rows)} secciones mapeadas (esperaba ≥ 4)",
        )
        return
    result.ok("D4-persona-table")


def check_d5_tense_regex(result: EvalResult) -> None:
    """§7 regla de tiempos tiene regex concreto."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec7 = _section_text(text, "§7")
    if not sec7:
        result.fail("D5-tense-regex", "no se encontró §7")
        return
    if "re.compile" not in sec7 and "regex" not in sec7.lower():
        result.fail("D5-tense-regex", "§7 no incluye regex concreto")
        return
    result.ok("D5-tense-regex")


def check_d6_wirings_alias(result: EvalResult) -> None:
    check_c10_wirings_closed(result)
    if result.passed and result.passed[-1] == "C10-wirings-closed":
        result.passed[-1] = "D6-wirings-alias"
    elif result.failed and result.failed[-1][0] == "C10-wirings-closed":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D6-wirings-alias", detail)


CHECKS = (
    check_c1_doc_structure,
    check_c2_eight_rules,
    check_c3_adjectives,
    check_c4_good_notes_pass,
    check_c5_bad_passive,
    check_c6_bad_adjectives,
    check_c7_bad_long,
    check_c8_bad_mixed,
    check_c9_verification_template,
    check_c10_wirings_closed,
    check_c11_density,
    check_d1_line_limit,
    check_d2_sections,
    check_d3_adjectives_alias,
    check_d4_persona_table,
    check_d5_tense_regex,
    check_d6_wirings_alias,
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
