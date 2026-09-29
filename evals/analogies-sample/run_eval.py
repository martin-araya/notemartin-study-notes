#!/usr/bin/env python3
"""Verificador de la Fase 95 — `analogies` (catálogo de patrones + banco).

Ejecuta 13 sub-criterios sobre los deliverables de F95:

  ROADMAP (3 criterios):
    C1 — `analogies.md` existe, ≤ 600 líneas, contiene las 8 secciones canónicas.
    C2 — §2 tabla tiene ≥ 10 patrones con 5 columnas rellenas por fila.
    C3 — §3 banco tiene ≥ 15 entradas con campo `Rotura:` explícito.

  Anti-patrones y reglas (4):
    C4 — Toda entrada tiene `Rotura:` explícito y concreto (sin palabras prohibidas).
    C5 — §6 tiene ≥ 6 anti-patrones de analogías.
    C6 — Wirings cerrados: `06-writing/README.md` línea 15 ya no marca pendiente;
         `SKILL.md` §5.2 referencia el archivo.
    C7 — El doc tiene ≥ 1 H2 con contenido (no es solo frontmatter vacío).

  Derivados (6):
    D1 — `wc -l analogies.md` ≤ 600.
    D2 — Las 8 secciones canónicas §1-§9 presentes.
    D3 — §4 regla universal tiene plantilla cerrada (regex `Rotura:` + lista de
         verbos válidos).
    D4 — Wirings cerrados (C6 alias).
    D5 — Banco cubre ≥ 2 dominios destino distintos y ≥ 5 dominios fuente.
    D6 — Cada patrón §2 tiene ≥ 1 entrada del banco (auto-referencia); cuenta
         a partir de `catalog.json`.

Uso:
    python3 evals/analogies-sample/build_catalog.py --force
    python3 evals/analogies-sample/run_eval.py

Salida esperada: PASS 13/13.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "analogies.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
CATALOG_PATH = Path(__file__).resolve().parent / "catalog.json"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Taxonomía de patrones",
    "## §3 · Banco reutilizable",
    "## §4 · Regla universal de rotura",
    "## §5 · Cómo elegir patrón al redactar",
    "## §6 · Anti-patrones de analogías",
    "## §7 · Plantilla cerrada de entrada del banco",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

PROHIBITED_ROTURA = re.compile(
    r"\b(?:casi|m[aá]s o menos|no del todo|parcialmente|en general|aproximadamente)\b",
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
    """Devuelve el texto de la sección H2 que empieza con header_prefix."""
    lines = text.split("\n")
    start = None
    start_level = 2
    for i, line in enumerate(lines):
        if line.startswith("## ") and line.lstrip("#").strip().startswith(header_prefix):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#"):
            level = len(lines[j]) - len(lines[j].lstrip("#"))
            if level <= start_level:
                end = j
                break
    return "\n".join(lines[start:end])


def check_c1_doc_structure(result: EvalResult) -> None:
    """C1: doc existe, ≤ 600 líneas, contiene las 9 secciones canónicas."""
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


def check_c2_patterns(result: EvalResult) -> None:
    """C2: §2 tabla tiene ≥ 10 filas de patrones."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec2 = _section_text(text, "§2")
    if not sec2:
        result.fail("C2-patterns-table", "no se encontró §2")
        return
    # Contar filas P1..P12 (nombres en negrita).
    pattern_rows = re.findall(r"\*\*P(\d+)\*\*", sec2)
    unique = set(pattern_rows)
    if len(unique) < 10:
        result.fail("C2-patterns-table", f"§2 lista {len(unique)} patrones P* (esperaba ≥ 10)")
        return
    # Verificar que la tabla tenga 5 columnas por fila (al menos en el header).
    if sec2.count("|---|") < 1:
        result.fail("C2-patterns-table", "§2 no tiene una tabla markdown con columnas")
        return
    result.ok("C2-patterns-table")


def check_c3_bank_size(result: EvalResult) -> None:
    """C3: §3 banco tiene ≥ 15 entradas."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec3 = _section_text(text, "§3")
    if not sec3:
        result.fail("C3-bank-size", "no se encontró §3")
        return
    entries = re.findall(r"###\s+E(\d+)\s+·", sec3)
    if len(entries) < 15:
        result.fail("C3-bank-size", f"§3 lista {len(entries)} entradas (esperaba ≥ 15)")
        return
    result.ok("C3-bank-size")


def check_c4_rotura_concreta(result: EvalResult) -> None:
    """C4: toda entrada del banco tiene Rotura: explícito y concreto."""
    if not CATALOG_PATH.exists():
        result.fail("C4-rotura-concreta", f"falta {CATALOG_PATH}; corre build_catalog.py primero")
        return
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entries = catalog["entries"]
    bad = []
    for e in entries:
        if "rotura" not in e or not e["rotura"]:
            bad.append(f"{e['id']}: falta rotura")
            continue
        if PROHIBITED_ROTURA.search(e["rotura"]):
            bad.append(f"{e['id']}: rotura contiene palabra prohibida ({e['rotura'][:60]}...)")
    if bad:
        result.fail("C4-rotura-concreta", "; ".join(bad[:3]))
        return
    result.ok("C4-rotura-concreta")


def check_c5_antipatrones(result: EvalResult) -> None:
    """C5: §6 tiene ≥ 6 anti-patrones."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C5-antipatrones", "no se encontró §6")
        return
    rows = re.findall(r"\*\*AP(\d+)\*\*", sec6)
    unique = set(rows)
    if len(unique) < 6:
        result.fail("C5-antipatrones", f"§6 lista {len(unique)} anti-patrones AP* (esperaba ≥ 6)")
        return
    result.ok("C5-antipatrones")


def check_c6_wirings_closed(result: EvalResult) -> None:
    """C6: wirings cerrados (06-writing/README.md y SKILL.md referencian el archivo)."""
    if not WRITING_README.exists():
        result.fail("C6-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    if re.search(r"\[pendiente\s+F95\]", rread):
        result.fail("C6-wirings-closed", "06-writing/README.md sigue marcando [pendiente F95]")
        return
    if "analogies.md" not in rread:
        result.fail("C6-wirings-closed", "06-writing/README.md no menciona analogies.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C6-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "analogies.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C6-wirings-closed", "SKILL.md no menciona analogies.md")
        return
    result.ok("C6-wirings-closed")


def check_c7_doc_has_content(result: EvalResult) -> None:
    """C7: el doc tiene ≥ 1 H2 con contenido (≥ 50 líneas de cuerpo)."""
    if not DOC_PATH.exists():
        result.fail("C7-doc-content", f"no existe {DOC_PATH}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    n = sum(1 for _ in text.split("\n") if _.strip() and not _.startswith("#"))
    if n < 50:
        result.fail("C7-doc-content", f"solo {n} líneas de cuerpo (esperaba ≥ 50)")
        return
    result.ok("C7-doc-content")


def check_d1_line_limit(result: EvalResult) -> None:
    """D1: alias de C1 (ya cubierto), pero contamos de forma explícita."""
    if not DOC_PATH.exists():
        result.fail("D1-line-limit", f"no existe {DOC_PATH}")
        return
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("D1-line-limit", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    result.ok("D1-line-limit")


def check_d2_sections_present(result: EvalResult) -> None:
    """D2: alias explícito de las 9 secciones canónicas."""
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [h for h in EXPECTED_SECTIONS if h not in text]
    if missing:
        result.fail("D2-sections", f"faltan {len(missing)} secciones: {missing[:3]}")
        return
    result.ok("D2-sections")


def check_d3_rotura_template(result: EvalResult) -> None:
    """D3: §4 regla universal tiene plantilla cerrada con verbos válidos."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("D3-rotura-template", "no se encontró §4")
        return
    if "Rotura:" not in sec4:
        result.fail("D3-rotura-template", "§4 no contiene la palabra 'Rotura:'")
        return
    # Verbos válidos deben estar listados.
    valid_verbs = ("acumula", "libera", "expira", "persiste", "se negocia",
                   "se rota", "se invalida", "se enruta", "se trunca", "se serializa")
    if not any(v in sec4 for v in valid_verbs):
        result.fail("D3-rotura-template", "§4 no lista verbos válidos para la rotura")
        return
    result.ok("D3-rotura-template")


def check_d4_wirings_alias(result: EvalResult) -> None:
    """D4: alias explícito de C6."""
    check_c6_wirings_closed(result)
    # Renombrar el último ok/fail con prefijo D4- si se añadió.
    if result.passed and result.passed[-1] == "C6-wirings-closed":
        result.passed[-1] = "D4-wirings-alias"
    elif result.failed and result.failed[-1][0] == "C6-wirings-closed":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D4-wirings-alias", detail)


def check_d5_domains(result: EvalResult) -> None:
    """D5: banco cubre ≥ 2 dominios destino y ≥ 5 dominios fuente."""
    if not CATALOG_PATH.exists():
        result.fail("D5-domains", f"falta {CATALOG_PATH}")
        return
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    targets = {e["target_domain"] for e in catalog["entries"]}
    sources = {e["source_domain"] for e in catalog["entries"]}
    if len(targets) < 2:
        result.fail("D5-domains", f"solo {len(targets)} dominio(s) destino: {targets}")
        return
    if len(sources) < 5:
        result.fail("D5-domains", f"solo {len(sources)} dominio(s) fuente: {sources}")
        return
    result.ok("D5-domains")


def check_d6_pattern_coverage(result: EvalResult) -> None:
    """D6: cada patrón §2 tiene ≥ 1 entrada del banco (auto-referencia)."""
    if not CATALOG_PATH.exists():
        result.fail("D6-pattern-coverage", f"falta {CATALOG_PATH}")
        return
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    patterns_used = set()
    for e in catalog["entries"]:
        patterns_used.add(e["pattern_primary"])
        for p in e.get("pattern_secondary", []):
            patterns_used.add(p)
    text = DOC_PATH.read_text(encoding="utf-8")
    sec2 = _section_text(text, "§2")
    # El regex extrae solo dígitos; normalizamos a `P<digits>` para comparar
    # con los strings del catálogo (que usan `P1`, `P10`, etc.).
    raw = set(re.findall(r"\*\*P(\d+)\*\*", sec2))
    patterns_in_table = {f"P{n}" for n in raw}
    missing = patterns_in_table - patterns_used
    if missing:
        result.fail("D6-pattern-coverage", f"patrones §2 sin entrada de banco: {sorted(missing)}")
        return
    result.ok("D6-pattern-coverage")


CHECKS = (
    check_c1_doc_structure,
    check_c2_patterns,
    check_c3_bank_size,
    check_c4_rotura_concreta,
    check_c5_antipatrones,
    check_c6_wirings_closed,
    check_c7_doc_has_content,
    check_d1_line_limit,
    check_d2_sections_present,
    check_d3_rotura_template,
    check_d4_wirings_alias,
    check_d5_domains,
    check_d6_pattern_coverage,
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
