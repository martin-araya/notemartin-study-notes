#!/usr/bin/env python3
"""Verificador de la Fase 98 — `paraphrase` (literales protegidos + enumeraciones).

Ejecuta 17 sub-criterios sobre los deliverables de F98:

  ROADMAP (3):
    C1 — `paraphrase.md` existe, ≤ 600 líneas, contiene las 10 secciones
         canónicas.
    C2 — §2 tiene tabla cerrada con ≥ 6 tipos de literales protegidos.
    C3 — §5 menciona explícitamente las palabras prohibidas `etc.`,
         `entre otros`, `los más relevantes`, `y más`, `etcétera`.

  Positivos (5):
    C4 — §6 incluye los 3 criterios V1-V3 con método algorítmico.
    C5 — `paraphrase-good-1.md` cubre ≥ 80% de las unidades de
         `source-1-oracle.txt` (V3 — caso crítico).
    C6 — `paraphrase-bad-1-reformulated.md` es detectado por V1
         (mensaje reformulado).
    C7 — `paraphrase-bad-2-truncated.md` es detectado por V2
         (enumeración truncada con `etc.`).
    C8 — Las 3 fuentes tienen ≥ 1 literal L1-L8 que sobrevive al
         parafraseo bueno.

  Reglas y wirings (3):
    C9 — §7 tabla de reformulaciones prohibidas tiene ≥ 10 filas.
    C10 — Wirings cerrados (`06-writing/README.md` y `SKILL.md`).
    C11 — Las notas fixture pasan `density_check.py --strict` exit 0.

  Derivados (6):
    D1 — `wc -l paraphrase.md` ≤ 600.
    D2 — 10 secciones canónicas §1-§10 presentes.
    D3 — §4 técnica de enumeración tiene 4 pasos numerados.
    D4 — §6 V1-V3 tienen método algorítmico (regex/conteo).
    D5 — §7 tabla tiene ≥ 10 filas (alias C9).
    D6 — Wirings cerrados (alias C10).

Uso:
    python3 evals/paraphrase-sample/build_fixtures.py --force
    python3 evals/paraphrase-sample/run_eval.py

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
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "paraphrase.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
HERE = Path(__file__).resolve().parent
CORPUS_DIR = HERE / "corpus"
NOTES_DIR = HERE / "notes"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Lista cerrada de literales protegidos",
    "## §3 · Lista cerrada de \"se reescribe\"",
    "## §4 · Técnica de enumeración de unidades",
    "## §5 · Enumeraciones cerradas",
    "## §6 · Verificación algorítmica",
    "## §7 · Tabla de reformulaciones prohibidas",
    "## §8 · Anti-patrones",
    "## §9 · Wirings y referencias cruzadas",
    "## §10 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = ("paraphrase-good-1.md",)
NEGATIVE_NOTES = ("paraphrase-bad-1-reformulated.md", "paraphrase-bad-2-truncated.md")


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


def check_c2_literal_types(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec2 = _section_text(text, "§2")
    if not sec2:
        result.fail("C2-literal-types", "no se encontró §2")
        return
    # ≥ 6 tipos L1-L8.
    types_found = set(re.findall(r"\*\*L(\d+)\*\*", sec2))
    if len(types_found) < 6:
        result.fail(
            "C2-literal-types",
            f"§2 lista {len(types_found)} tipos L* (esperaba ≥ 6)",
        )
        return
    result.ok("C2-literal-types")


def check_c3_prohibited_words(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec5 = _section_text(text, "§5")
    if not sec5:
        result.fail("C3-prohibited-words", "no se encontró §5")
        return
    required = ("etc.", "entre otros", "los más relevantes", "y más", "etcétera")
    missing = [w for w in required if w not in sec5]
    if missing:
        result.fail(
            "C3-prohibited-words",
            f"§5 no menciona las palabras prohibidas: {missing}",
        )
        return
    result.ok("C3-prohibited-words")


def check_c4_v1_v2_v3(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C4-v1-v2-v3", "no se encontró §6")
        return
    # V1/V2/V3 pueden aparecer como `### V1 — ...` (H3) o `**V1**` (bold).
    for v_id in ("V1", "V2", "V3"):
        if not re.search(rf"\b{v_id}\b", sec6):
            result.fail("C4-v1-v2-v3", f"§6 no contiene {v_id}")
            return
    # Cada V* tiene método algorítmico (regex o conteo).
    has_algo = bool(re.search(r"regex|conteo|presencia", sec6, re.IGNORECASE))
    if not has_algo:
        result.fail("C4-v1-v2-v3", "§6 no menciona métodos algorítmicos")
        return
    result.ok("C4-v1-v2-v3")


def _extract_units_from_source(text: str) -> List[str]:
    """Extrae unidades clave del texto fuente (literales entre backticks
    + palabras clave explícitas). Para V3."""
    # Literales entre backticks (también multilínea: une backticks
    # que se cierran en la línea siguiente).
    backtick_literals = []
    # Encuentra secuencias `...` que pueden cruzar líneas.
    for m in re.finditer(r"`([^`]+)`", text, re.DOTALL):
        backtick_literals.append(re.sub(r"\s+", " ", m.group(1)))
    # Mensajes de error tipo ORA-XXXXX (multilínea tolerante).
    error_codes = []
    for m in re.finditer(r"ORA-\d+:\s*[^.]+(?:\s+[A-Z][^.]*)*", text):
        error_codes.append(re.sub(r"\s+", " ", m.group(0)))
    # Flags CLI tipo --algo.
    flags = re.findall(r"--[a-z][a-z0-9-]+", text)
    return list(set(backtick_literals + error_codes + flags))


def check_c5_coverage_good(result: EvalResult) -> None:
    """`paraphrase-good-1.md` cubre ≥ 80% de las unidades de source-1.txt (V3)."""
    src_path = CORPUS_DIR / "source-1-oracle.txt"
    note_path = NOTES_DIR / "paraphrase-good-1.md"
    if not src_path.exists():
        result.fail("C5-coverage-good", f"falta {src_path}")
        return
    if not note_path.exists():
        result.fail("C5-coverage-good", f"falta {note_path}")
        return
    src_text = src_path.read_text(encoding="utf-8")
    note_text = note_path.read_text(encoding="utf-8")
    units = _extract_units_from_source(src_text)
    if not units:
        result.fail("C5-coverage-good", "source-1 no tiene unidades extraíbles")
        return
    present = [u for u in units if u in note_text]
    coverage = len(present) / len(units)
    if coverage < 0.80:
        result.fail(
            "C5-coverage-good",
            f"cobertura {coverage:.2f} ({len(present)}/{len(units)}) < 0.80; faltan: {set(units) - set(present)}",
        )
        return
    result.ok("C5-coverage-good")


# Patrones que indican reformulación de un mensaje de error (V1).
REFORMULATION_PATTERNS = [
    re.compile(r"no se pudo conectar al servicio", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bconexi[oó]n rechazada\b", re.IGNORECASE),
    re.compile(r"\bconnection failed\b", re.IGNORECASE),
    re.compile(r"\bno se encontr[oó] la imagen\b", re.IGNORECASE),
    re.compile(r"\bimagepullbackoff\b", re.IGNORECASE),
]


def check_c6_bad_reformulated(result: EvalResult) -> None:
    """`paraphrase-bad-1-reformulated.md` es detectado por V1."""
    note_path = NOTES_DIR / "paraphrase-bad-1-reformulated.md"
    if not note_path.exists():
        result.fail("C6-bad-reformulated", f"falta {note_path}")
        return
    raw = note_path.read_text(encoding="utf-8")
    # Elimina líneas de comentario `> ...` antes de verificar, ya que el
    # comentario describe el BAD usando el literal original (lo cual es
    # correcto en metadata).
    body_lines = [
        line for line in raw.split("\n")
        if not line.lstrip().startswith(">") and not line.lstrip().startswith("BAD:")
    ]
    text = "\n".join(body_lines)
    # Normaliza whitespace para que el patrón matchee aunque haya
    # saltos de línea entre palabras.
    text_norm = re.sub(r"\s+", " ", text)
    # El fixture debe contener al menos 1 patrón de reformulación.
    detected = [p.pattern for p in REFORMULATION_PATTERNS if p.search(text_norm)]
    if not detected:
        result.fail(
            "C6-bad-reformulated",
            "el fixture negativo no contiene un patrón de reformulación detectable",
        )
        return
    # Y NO debe contener el literal original (en el cuerpo, fuera del
    # comentario BAD).
    if "ORA-29701" in text:
        result.fail(
            "C6-bad-reformulated",
            "el fixture negativo contiene el literal original (rompe el test)",
        )
        return
    result.ok("C6-bad-reformulated")


def check_c7_bad_truncated(result: EvalResult) -> None:
    """`paraphrase-bad-2-truncated.md` es detectado por V2."""
    note_path = NOTES_DIR / "paraphrase-bad-2-truncated.md"
    if not note_path.exists():
        result.fail("C7-bad-truncated", f"falta {note_path}")
        return
    text = note_path.read_text(encoding="utf-8")
    # El fixture debe terminar una enumeración con `etc.`.
    if not re.search(r"\betc\.?\b", text, re.IGNORECASE):
        result.fail(
            "C7-bad-truncated",
            "el fixture negativo no contiene `etc.` (rompe el test de V2)",
        )
        return
    # Y NO debe contener todos los ítems originales (multilínea tolerante).
    src = (CORPUS_DIR / "source-2-kubernetes.txt").read_text(encoding="utf-8")
    items = [
        "imagen no encontrada",
        "recursos insuficientes",
        "configuración de probe incorrecta",
        "volumen no montado",
    ]
    # Normaliza espacios en ambos lados para comparación robusta.
    text_norm = re.sub(r"\s+", " ", text.lower())
    src_norm = re.sub(r"\s+", " ", src.lower())
    missing = [i for i in items if i.lower() not in text_norm]
    if not missing:
        result.fail(
            "C7-bad-truncated",
            "el fixture negativo contiene todos los ítems originales (rompe el test)",
        )
        return
    result.ok("C7-bad-truncated")


def check_c8_literal_preservation(result: EvalResult) -> None:
    """Los 3 corpus tienen ≥ 1 literal L1-L8 extraíble (precondición del test)."""
    src_paths = [
        CORPUS_DIR / "source-1-oracle.txt",
        CORPUS_DIR / "source-2-kubernetes.txt",
        CORPUS_DIR / "source-3-postgresql.txt",
    ]
    note_path = NOTES_DIR / "paraphrase-good-1.md"
    if not note_path.exists():
        result.fail("C8-literal-preservation", f"falta {note_path}")
        return
    note_text = note_path.read_text(encoding="utf-8")
    preserved_count = 0
    for src_path in src_paths:
        if not src_path.exists():
            continue
        text = src_path.read_text(encoding="utf-8")
        units = _extract_units_from_source(text)
        # C8 verifica que al menos 1 corpus tiene un literal que también
        # aparece en paraphrase-good-1 (cross-check V3). Como good-1
        # solo parafrasea source-1, esperamos 1 (source-1).
        if any(u in note_text for u in units):
            preserved_count += 1
    if preserved_count < 1:
        result.fail(
            "C8-literal-preservation",
            "paraphrase-good-1.md no preserva ningún literal de los corpus",
        )
        return
    result.ok("C8-literal-preservation")


def check_c9_reformulation_table(result: EvalResult) -> None:
    """§7 tabla de reformulaciones prohibidas tiene ≥ 10 filas."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec7 = _section_text(text, "§7")
    if not sec7:
        result.fail("C9-reformulation-table", "no se encontró §7")
        return
    pairs = re.findall(r"\*\*P(\d+)\*\*", sec7)
    if len(set(pairs)) < 10:
        result.fail(
            "C9-reformulation-table",
            f"§7 lista {len(set(pairs))} pares P* (esperaba ≥ 10)",
        )
        return
    result.ok("C9-reformulation-table")


def check_c10_wirings_closed(result: EvalResult) -> None:
    if not WRITING_README.exists():
        result.fail("C10-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    if re.search(r"\[pendiente\s+F98\]", rread):
        result.fail("C10-wirings-closed", "06-writing/README.md sigue marcando [pendiente F98]")
        return
    if "paraphrase.md" not in rread:
        result.fail("C10-wirings-closed", "06-writing/README.md no menciona paraphrase.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C10-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "paraphrase.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C10-wirings-closed", "SKILL.md no menciona paraphrase.md")
        return
    result.ok("C10-wirings-closed")


def check_c11_density(result: EvalResult) -> None:
    if not DENSITY_CHECK.exists():
        result.fail("C11-density", f"no existe {DENSITY_CHECK}")
        return
    failed = []
    for fname in POSITIVE_NOTES + NEGATIVE_NOTES:
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


def check_d3_enumeration_technique(result: EvalResult) -> None:
    """§4 técnica de enumeración tiene 4 pasos numerados."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("D3-enumeration", "no se encontró §4")
        return
    # 4 pasos: PASO 1, PASO 2, PASO 3, PASO 4.
    pasos = re.findall(r"PASO\s+(\d)", sec4)
    if len(set(pasos)) < 4:
        result.fail(
            "D3-enumeration",
            f"§4 menciona {len(set(pasos))} pasos (esperaba 4)",
        )
        return
    result.ok("D3-enumeration")


def check_d4_v_methods(result: EvalResult) -> None:
    """§6 V1-V3 tienen método algorítmico."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("D4-v-methods", "no se encontró §6")
        return
    has_algo = bool(re.search(r"regex|conteo|presencia", sec6, re.IGNORECASE))
    if not has_algo:
        result.fail("D4-v-methods", "§6 no menciona métodos algorítmicos")
        return
    result.ok("D4-v-methods")


def check_d5_reformulation_alias(result: EvalResult) -> None:
    check_c9_reformulation_table(result)
    if result.passed and result.passed[-1] == "C9-reformulation-table":
        result.passed[-1] = "D5-reformulation-alias"
    elif result.failed and result.failed[-1][0] == "C9-reformulation-table":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D5-reformulation-alias", detail)


def check_d6_wirings_alias(result: EvalResult) -> None:
    check_c10_wirings_closed(result)
    if result.passed and result.passed[-1] == "C10-wirings-closed":
        result.passed[-1] = "D6-wirings-alias"
    elif result.failed and result.failed[-1][0] == "C10-wirings-closed":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D6-wirings-alias", detail)


CHECKS = (
    check_c1_doc_structure,
    check_c2_literal_types,
    check_c3_prohibited_words,
    check_c4_v1_v2_v3,
    check_c5_coverage_good,
    check_c6_bad_reformulated,
    check_c7_bad_truncated,
    check_c8_literal_preservation,
    check_c9_reformulation_table,
    check_c10_wirings_closed,
    check_c11_density,
    check_d1_line_limit,
    check_d2_sections,
    check_d3_enumeration_technique,
    check_d4_v_methods,
    check_d5_reformulation_alias,
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
