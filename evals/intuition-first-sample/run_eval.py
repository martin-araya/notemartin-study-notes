#!/usr/bin/env python3
"""Verificador de la Fase 94 — `intuition-first` (patrón de 5 etapas).

Ejecuta 9 sub-criterios sobre los deliverables de F94:

  C1 — Ejemplo de base de datos documentado (`### §7.1` con términos PostgreSQL/MVCC).
  C2 — Ejemplo de redes documentado (`### §7.2` con términos TCP/handshake).
  C3 — Excepción acotada (sección §4 con tabla de 4 checks + override textual).
  C4 — Señales de diagnóstico algorítmicas (sección §6 con ≥ 8 filas y métodos
        verificables).
  D1 — `intuition-first.md` existe, ≤ 500 líneas.
  D2 — Las 5 etapas en orden canónico en `db-mvcc.md` y `net-tcp-3whs.md`.
  D3 — `## Analogía` declara la rotura en ambos ejemplos (D5).
  D4 — `## Intuición` introduce el término canónico con `[[term:...]]` (D7).
  D5 — Wirings cerrados (`references/06-writing/README.md` y `SKILL.md`).
  D6 — Override textual presente (study/hybrid + reference-pure).

Uso:
    python3 evals/intuition-first-sample/run_eval.py

Salida esperada: PASS 9/9.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "intuition-first.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
DOC_LINE_LIMIT = 500

# Etapas canónicas en orden estricto (F94 §2).
STAGES = ("Problema", "Intuición", "Analogía", "Definición formal", "Confirmación")

# Regex para encontrar el encabezado H2 de cada etapa (anclado a línea).
STAGE_HEADER_RE = re.compile(r"^##\s+(Problema|Intuición|Analogía|Definición formal|Confirmación)\s*$")

# Regex para citas a bloques fuente.
SRC_RE = re.compile(r"\{src:blk_[0-9a-f]{12}\}")

# Regex para término canónico.
TERM_RE = re.compile(r"\[\[term:[a-z0-9_-]+\]\]")

# Regex para frases que declaran la rotura de la analogía (señal D5).
ROTURA_RE = re.compile(
    r"se rompe|no se parece|la diferencia|en cambio|difiere|difiere de|a diferencia de",
    re.IGNORECASE,
)

# Regex para el override "study/hybrid NO activan reference-pure" (D6).
OVERRIDE_RE = re.compile(
    r"study.*hybrid.*(?:no activan|jam\u00e1s|nunca)|reference-pure.*\u00fanico|override.*perfil",
    re.IGNORECASE | re.DOTALL,
)

# Marcadores del dominio del concepto (D6 — analogía usa dominio distinto).
CONCEPT_DOMAIN_KEYWORDS = (
    "base de datos", "tabla", "tupla", "atributo", "consulta",
    "red", "socket", "paquete", "segmento", "kernel",
    "transacción", "índice",
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
        return f"FAIL {len(self.failed)}/{len(self.passed) + len(self.failed)} (passed {len(self.passed)}/{len(self.passed) + len(self.failed)})"


def _section_range(text: str, header: str) -> Tuple[int, int] | None:
    """Devuelve (start, end) de la sección cuyo encabezado (H2 o H3) empieza con `header`."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        if (line.startswith("## ") or line.startswith("### ")) and stripped.startswith(header):
            start = i
            break
    if start is None:
        return None
    # El fin es el siguiente encabezado de nivel <= al del actual.
    start_level = len(line) - len(line.lstrip("#"))
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#"):
            current_level = len(lines[j]) - len(lines[j].lstrip("#"))
            if current_level <= start_level:
                end = j
                break
    return start, end


def _section_text(text: str, header: str) -> str:
    rng = _section_range(text, header)
    if rng is None:
        return ""
    return "\n".join(text.split("\n")[rng[0]:rng[1]])


def _stages_in_order(text: str) -> List[str]:
    """Devuelve la lista de etapas encontradas en orden de aparición."""
    found: List[str] = []
    for line in text.split("\n"):
        m = STAGE_HEADER_RE.match(line)
        if m:
            found.append(m.group(1))
    return found


def check_c1_db_example(result: EvalResult) -> None:
    """C1: Ejemplo de base de datos (PostgreSQL / MVCC) en §7.1."""
    if not DOC_PATH.exists():
        result.fail("C1-db-example", f"no existe {DOC_PATH}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    # Buscar el bloque §7.1 y dentro de él los términos PostgreSQL|MVCC.
    sec71 = _section_text(text, "§7.1")
    if not sec71:
        result.fail("C1-db-example", "no se encontró la sección §7.1")
        return
    if not re.search(r"PostgreSQL|mvcc|MVCC", sec71):
        result.fail("C1-db-example", "§7.1 no menciona PostgreSQL ni MVCC")
        return
    result.ok("C1-db-example")


def check_c2_net_example(result: EvalResult) -> None:
    """C2: Ejemplo de redes (TCP / three-way handshake) en §7.2."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec72 = _section_text(text, "§7.2")
    if not sec72:
        result.fail("C2-net-example", "no se encontró la sección §7.2")
        return
    if not re.search(r"TCP|three.?way|handshake", sec72, re.IGNORECASE):
        result.fail("C2-net-example", "§7.2 no menciona TCP ni three-way handshake")
        return
    result.ok("C2-net-example")


def check_c3_exception_bounded(result: EvalResult) -> None:
    """C3: Excepción acotada con tabla de 4 checks + override."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("C3-exception-bounded", "no se encontró la sección §4")
        return
    # Tabla de checks: 4 filas R1-R4 (header + 4 filas de datos).
    table_lines = [ln for ln in sec4.split("\n") if ln.startswith("|")]
    if len(table_lines) < 5:
        result.fail("C3-exception-bounded", f"§4 tiene {len(table_lines)} líneas de tabla (esperaba ≥ 5: header + sep + 4 checks)")
        return
    # Override textual con study y hybrid.
    if "study" not in sec4.lower() or "hybrid" not in sec4.lower():
        result.fail("C3-exception-bounded", "§4 no menciona study y hybrid en el override")
        return
    # El override debe establecer que study/hybrid NO activan reference-pure.
    if not re.search(r"study.*hybrid.*(?:no activan|jam\u00e1s|nunca)", sec4, re.IGNORECASE | re.DOTALL):
        result.fail("C3-exception-bounded", "§4 no establece el override 'study/hybrid no activan reference-pure'")
        return
    result.ok("C3-exception-bounded")


def check_c4_diagnostic_signals(result: EvalResult) -> None:
    """C4: Señales de diagnóstico con ≥ 8 filas algorítmicas."""
    text = DOC_PATH.read_text(encoding="utf-8")
    sec6 = _section_text(text, "§6")
    if not sec6:
        result.fail("C4-diagnostic-signals", "no se encontró la sección §6")
        return
    # Contar filas D1..D10.
    signals = re.findall(r"\*\*D(\d+)\*\*", sec6)
    if len(set(signals)) < 8:
        result.fail("C4-diagnostic-signals", f"§6 lista {len(set(signals))} señales D* (esperaba ≥ 8)")
        return
    # Cada fila debe tener columna 'Método' y 'PASS si' (no vacías).
    method_count = sec6.count("Método") + sec6.count("Método")
    pass_if_count = sec6.count("PASS si")
    if method_count < 1 or pass_if_count < 1:
        result.fail("C4-diagnostic-signals", f"§6 no tiene columnas 'Método' ({method_count}) o 'PASS si' ({pass_if_count})")
        return
    # Métodos algorítmicos: al menos una fila menciona regex/conteo/presencia/ratio.
    has_algo = bool(re.search(r"regex|conteo|presencia|ratio|wc -w", sec6, re.IGNORECASE))
    if not has_algo:
        result.fail("C4-diagnostic-signals", "§6 no menciona métodos algorítmicos (regex/conteo/presencia/ratio/wc -w)")
        return
    result.ok("C4-diagnostic-signals")


def check_d1_line_limit(result: EvalResult) -> None:
    """D1: intuition-first.md ≤ 500 líneas."""
    if not DOC_PATH.exists():
        result.fail("D1-line-limit", f"no existe {DOC_PATH}")
        return
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("D1-line-limit", f"intuition-first.md tiene {n} líneas (máx {DOC_LINE_LIMIT})")
        return
    result.ok("D1-line-limit")


def check_d2_stages_order(result: EvalResult) -> None:
    """D2: 5 etapas en orden canónico en db-mvcc.md y net-tcp-3whs.md."""
    for fname in ("db-mvcc.md", "net-tcp-3whs.md"):
        path = NOTES_DIR / fname
        if not path.exists():
            result.fail("D2-stages-order", f"falta nota {path}")
            return
        text = path.read_text(encoding="utf-8")
        found = _stages_in_order(text)
        if found != list(STAGES):
            result.fail(
                "D2-stages-order",
                f"{fname}: etapas en orden {found} (esperaba {list(STAGES)})",
            )
            return
    result.ok("D2-stages-order")


def check_d3_rotura(result: EvalResult) -> None:
    """D3: ## Analogía declara explícitamente su rotura (D5) en ambos ejemplos."""
    for fname in ("db-mvcc.md", "net-tcp-3whs.md"):
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        sec = _section_text(text, "Analogía")
        if not sec:
            result.fail("D3-rotura", f"{fname}: no se encontró ## Analogía")
            return
        if not ROTURA_RE.search(sec):
            result.fail(
                "D3-rotura",
                f"{fname}: ## Analogía no contiene frase de rotura (regex: se rompe|no se parece|…)",
            )
            return
    result.ok("D3-rotura")


def check_d4_term_intro(result: EvalResult) -> None:
    """D4: ## Intuición introduce el término canónico con [[term:...]] (D7)."""
    for fname in ("db-mvcc.md", "net-tcp-3whs.md"):
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        sec = _section_text(text, "Intuición")
        if not sec:
            result.fail("D4-term-intro", f"{fname}: no se encontró ## Intuición")
            return
        if not TERM_RE.search(sec):
            result.fail(
                "D4-term-intro",
                f"{fname}: ## Intuición no contiene [[term:...]]",
            )
            return
    result.ok("D4-term-intro")


def check_d5_wirings_closed(result: EvalResult) -> None:
    """D5: Wirings cerrados (06-writing/README.md y SKILL.md referencian el archivo)."""
    if not WRITING_README.exists():
        result.fail("D5-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    # El README de 06-writing ya no debe marcar [pendiente F94].
    if re.search(r"\[pendiente\s+F94\]", rread):
        result.fail("D5-wirings-closed", "06-writing/README.md sigue marcando [pendiente F94]")
        return
    # Debe referenciar el archivo intuition-first.md.
    if "intuition-first.md" not in rread:
        result.fail("D5-wirings-closed", "06-writing/README.md no menciona intuition-first.md")
        return
    # SKILL.md debe referenciar el archivo.
    if not SKILL_MD_PATH.exists():
        result.fail("D5-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    skill_text = SKILL_MD_PATH.read_text(encoding="utf-8")
    if "intuition-first.md" not in skill_text:
        result.fail("D5-wirings-closed", "SKILL.md no menciona intuition-first.md")
        return
    result.ok("D5-wirings-closed")


def check_d6_override_textual(result: EvalResult) -> None:
    """D6: Override textual study/hybrid + reference-pure único presente en el doc."""
    text = DOC_PATH.read_text(encoding="utf-8")
    # Buscar override en §4 o §8 (la tabla §8 fila 6 también lo textualiza).
    full_text = text
    if not OVERRIDE_RE.search(full_text):
        result.fail(
            "D6-override-textual",
            "no se encontró el override textual (regex: study.*hybrid.*no activan|reference-pure.*único|override.*perfil)",
        )
        return
    result.ok("D6-override-textual")


CHECKS = (
    check_c1_db_example,
    check_c2_net_example,
    check_c3_exception_bounded,
    check_c4_diagnostic_signals,
    check_d1_line_limit,
    check_d2_stages_order,
    check_d3_rotura,
    check_d4_term_intro,
    check_d5_wirings_closed,
    check_d6_override_textual,
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
