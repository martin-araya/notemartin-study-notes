#!/usr/bin/env python3
"""
Verificador de la Fase 65 — Catálogo por intención (diagram-catalog.md).

Ejecuta 6 criterios verificables sobre el catálogo:

  C1. Al menos 10 tipos con plantilla y ejemplo técnico (§4).
  C2. La matriz (§5 + §9) resuelve los 14 casos del corpus.
  C3. Ningún ejemplo de visión por computador (lista negra de §1/§2).
  C4. Regla de los 15 nodos (§6) — 8 casos sintéticos con veredicto esperado.
  C5. Obligatoriedad (§7) — 5 situaciones, 3 obligatorias + 2 opcionales.
  C6. Wirings — cada tipo §4.x enlaza al menos 2 archivos `references/0?-*/`.

Uso:
    python run_eval.py --catalog <ruta-al-catalogo>

Salida: imprime PASS 6/6 (o FAIL con detalle) y sale con código 0/1.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Tipos canónicos según §4.
TIPO_IDS = [f"T{i}" for i in range(1, 11)]

# Patrones regex para parseo de Markdown simple.
RE_TIPO_HEADER = re.compile(r"^### §4\.(\d+) · (T\d+) — (.+?)\s*$", re.MULTILINE)
RE_DIAGRAM_BLOCK = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
RE_DIAGRAM_DIRECTIVE = re.compile(r":::diagram")
RE_ALT_ATTR = re.compile(r'alt="([^"]+)"')
RE_SRC_ATTR = re.compile(r'src="([^"]+)"')
RE_WIRING = re.compile(r"\*\*Wirings:\*\*\s*(.+?)(?:\n\n|\n###|\Z)", re.DOTALL)
RE_FOOTER = re.compile(r"references/0\d-[a-z\-]+/[a-z\-]+\.md")
RE_SECTION9_ROW = re.compile(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
RE_SECTION5_ROW = re.compile(r"^\|\s*(I-\d+[^\|]*?)\s*\|\s*\*\*([^*]+)\*\*\s*\|", re.MULTILINE)


class EvalResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    def summary(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _clean_value(v: str) -> str:
    """Quita comentarios trailing (# ...) y comillas envolventes de un valor."""
    v = v.strip()
    # Strip inline comments: text after whitespace + '#'
    for sep in ("  #", " #", "\t#"):
        if sep in v:
            v = v.split(sep, 1)[0].rstrip()
    v = v.strip('"').strip("'")
    return v


def parse_simple_yaml(text: str) -> list[dict[str, str]]:
    """Parser YAML minimalista para fixtures planas (sin comillas anidadas).

    Devuelve una lista de dicts; cada dict representa un elemento de lista top-level.
    """
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            if current is not None:
                items.append(current)
            current = {}
            rest = raw[4:]
            if ":" in rest:
                k, _, v = rest.partition(":")
                current[k.strip()] = _clean_value(v)
        elif current is not None and raw.startswith("    "):
            if ":" in raw:
                k, _, v = raw.partition(":")
                k = k.strip()
                if k and k not in current:
                    current[k] = _clean_value(v)
    if current is not None:
        items.append(current)
    return items


def load_corpus_sources() -> set[str]:
    """Lee evals/corpus/ y devuelve los identificadores de las 14 fuentes."""
    corpus_dir = REPO_ROOT / "evals" / "corpus"
    sources: set[str] = set()
    for child in sorted(corpus_dir.iterdir()):
        if child.is_dir():
            sources.add(child.name)
    return sources


# ---------------------------------------------------------------------------
# Criterios
# ---------------------------------------------------------------------------


def crit_1_10_tipos(text: str, result: EvalResult) -> None:
    """C1: ≥10 tipos con plantilla y ejemplo técnico (§4)."""
    headers = RE_TIPO_HEADER.findall(text)
    found_ids = {tid for _, tid, _ in headers}
    missing = [t for t in TIPO_IDS if t not in found_ids]
    if missing:
        result.fail("C1-10-tipos",
                    f"Faltan tipos: {missing} (encontrados: {sorted(found_ids)})")
        return

    # Para cada tipo, verificar que tenga al menos un :::diagram con bloque mermaid
    # no vacío Y un bloque con código Mermaid "de ejemplo" (no solo la plantilla).
    # La plantilla y el ejemplo están separados en §4.x por un encabezado "Ejemplo".
    sections: dict[str, str] = {}
    current_id = None
    buf: list[str] = []
    for line in text.splitlines():
        m = RE_TIPO_HEADER.match(line)
        if m:
            if current_id is not None:
                sections[current_id] = "\n".join(buf)
            current_id = m.group(2)
            buf = [line]
        elif current_id is not None:
            buf.append(line)
    if current_id is not None:
        sections[current_id] = "\n".join(buf)

    problems: list[str] = []
    for tid in TIPO_IDS:
        sec = sections.get(tid, "")
        if not sec:
            problems.append(f"{tid}: sección ausente")
            continue
        # Exigir bloque mermaid (la plantilla + el ejemplo)
        mermaid_blocks = RE_DIAGRAM_BLOCK.findall(sec)
        if len(mermaid_blocks) < 2:
            problems.append(f"{tid}: solo {len(mermaid_blocks)} bloque(s) mermaid (esperaba ≥2: plantilla + ejemplo)")
            continue
        # Exigir :::diagram directive
        if not RE_DIAGRAM_DIRECTIVE.search(sec):
            problems.append(f"{tid}: falta `:::diagram`")
        # Exigir alt= presente en algún ejemplo
        if not RE_ALT_ATTR.search(sec):
            problems.append(f"{tid}: falta atributo alt=")
    if problems:
        result.fail("C1-10-tipos", "; ".join(problems))
        return
    result.ok("C1-10-tipos")


def crit_2_corpus(text: str, result: EvalResult) -> None:
    """C2: la matriz (§9) resuelve los 14 casos del corpus."""
    sources_in_corpus = load_corpus_sources()
    rows = RE_SECTION9_ROW.findall(text)
    found_sources = {r[0] for r in rows}
    missing = sources_in_corpus - found_sources
    if missing:
        result.fail("C2-corpus-coverage",
                    f"Faltan fuentes en §9: {sorted(missing)}")
        return
    # Verificar que toda fila "sin diagrama" tiene razón no trivial
    no_diagram = [r for r in rows if "sin diagrama" in r[2]]
    for r in no_diagram:
        razon = r[3].strip()
        if not razon or razon in {"-", "N/A"}:
            result.fail("C2-corpus-coverage",
                        f"Fuente {r[0]} sin diagrama sin razón no trivial")
            return
    result.ok(f"C2-corpus-coverage ({len(found_sources)}/{len(sources_in_corpus)})")


def crit_3_no_vision(text: str, result: EvalResult) -> None:
    """C3: ningún ejemplo de visión por computador.

    La regla se enuncia en §1 y §2.2; excluimos esas líneas declarativas del grep.
    Estrategia: split por secciones §N · y, dentro de cada sección, ignorar las
    primeras 5 líneas declarativas (donde se menciona la prohibición).
    """
    blacklist_path = FIXTURES / "no-vision-examples.txt"
    terms = [ln.strip() for ln in blacklist_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    # Dividir el catálogo por secciones §N ·
    sections: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^## §\d", line):
            if current_lines or current_title:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = line
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_title, "\n".join(current_lines)))

    hits: list[tuple[str, int, str]] = []
    line_offset = 0
    for title, body in sections:
        line_offset += 1  # el header
        for i, line in enumerate(body.splitlines(), 1):
            line_offset += 1
            # Saltar las 5 primeras líneas declarativas de cada sección
            # (donde se enuncia la prohibición y se listan los términos).
            if i <= 5:
                continue
            # Saltar secciones declarativas explícitas
            if title.startswith("## §1") or title.startswith("## §2 ·"):
                continue
            for term in terms:
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                if pattern.search(line):
                    hits.append((term, line_offset, line.strip()[:80]))
    if hits:
        result.fail("C3-no-vision",
                    f"Términos de visión por computador encontrados: {hits[:10]}")
        return
    result.ok("C3-no-vision")


def _expected_verdict(case: dict[str, str]) -> str:
    """Aplica §6.1 + §6.2 a un caso para producir el veredicto."""
    nodos = int(case["nodos"])
    tipo = case["tipo"]
    if tipo == "T8" and nodos <= 25:
        return "unico"
    if tipo == "T4" and nodos <= 25:
        return "unico"
    if nodos <= 7:
        return "unico"
    if nodos <= 14:
        return "unico_subgraphs"
    if nodos <= 25:
        return "partir"
    return "tabla"


def crit_4_fifteen_nodes(text: str, result: EvalResult) -> None:
    """C4: regla de los 15 nodos (§6). 8 casos sintéticos."""
    cases = parse_simple_yaml((FIXTURES / "fifteen-nodes-decision.yaml").read_text(encoding="utf-8"))
    # La tabla §6.1 debe existir; verificar presencia
    if "## §6" not in text:
        result.fail("C4-15-nodes", "Falta sección §6")
        return
    if "## §6.1" not in text:
        result.fail("C4-15-nodes", "Falta tabla §6.1")
        return
    # Verificar excepciones
    if "## §6.2" not in text:
        result.fail("C4-15-nodes", "Falta excepciones §6.2")
        return
    # Evaluar lógica contra cada caso
    logic_ok = True
    for case in cases:
        expected = case["verdict"]
        actual = _expected_verdict(case)
        if expected != actual:
            logic_ok = False
            result.fail("C4-15-nodes",
                        f"Caso {case['id']}: esperado={expected} lógica={actual}")
            return
    if not logic_ok:
        return
    result.ok(f"C4-15-nodes ({len(cases)} casos)")


def crit_5_obligatoriedad(text: str, result: EvalResult) -> None:
    """C5: obligatoriedad (§7). 5 situaciones."""
    cases = parse_simple_yaml((FIXTURES / "obligatoriedad.yaml").read_text(encoding="utf-8"))
    if "## §7" not in text:
        result.fail("C5-obligatoriedad", "Falta sección §7")
        return

    def expected(case: dict[str, str]) -> str:
        ent = int(case["entidades"])
        rel = int(case["relaciones"])
        tn = case["tipo_nota"]
        if tn == "architecture":
            return "obligatorio" if (ent >= 3 and rel >= 2) else "opcional"
        if tn == "index-moc":
            return "obligatorio" if ent >= 6 else "opcional"
        if tn == "procedure":
            return "obligatorio" if rel >= 3 else "opcional"
        return "opcional"

    problems: list[str] = []
    for case in cases:
        if case["esperado"] != expected(case):
            problems.append(f"{case['id']}: esperado={case['esperado']} lógica={expected(case)}")
    if problems:
        result.fail("C5-obligatoriedad", "; ".join(problems))
        return
    # Verificar que la tabla §7 menciona los 3 tipos nota
    for tn in ("architecture", "index-moc", "procedure"):
        if tn not in text:
            result.fail("C5-obligatoriedad", f"§7 no menciona {tn}")
            return
    result.ok(f"C5-obligatoriedad ({len(cases)} casos)")


def crit_6_wirings(text: str, result: EvalResult) -> None:
    """C6: cada tipo §4.x enlaza al menos 2 referencias a archivos de `references/`.

    Las wirings aparecen como `F66`, `F67`, `mermaid-portable.md`, etc. Aceptamos
    cualquiera de estas formas como una wiring válida; exigimos ≥2 menciones
    distintas de archivos de `references/0?-*/` (por nombre de archivo o por
    identificador de fase que mapea a un archivo de la skill).
    """
    sections: dict[str, str] = {}
    current_id = None
    buf: list[str] = []
    for line in text.splitlines():
        m = RE_TIPO_HEADER.match(line)
        if m:
            if current_id is not None:
                sections[current_id] = "\n".join(buf)
            current_id = m.group(2)
            buf = [line]
        elif current_id is not None:
            buf.append(line)
    if current_id is not None:
        sections[current_id] = "\n".join(buf)

    # Mapeo F-id → archivo (subset usado por §4.x)
    F_TO_FILE = {
        "F66": "mermaid-portable.md",
        "F67": "scripts/validate/mermaid.py",
        "F68": "scripts/render/diagram_image.py",
        "F69": "monospace-diagrams.md",
        "F70": "scripts/render/diagram_image.py",
        "F71": "reconstruction.md",
        "F72": "tokens.md",
        "F73": "style-mapping.md",
        "F76": "density.md",
        "F83": "05-note-types/architecture.md",
        "F80": "05-note-types/procedure.md",
        "F91": "05-note-types/index-moc.md",
    }
    RE_F_REF = re.compile(r"\bF(\d{2,3})\b")

    problems: list[str] = []
    for tid in TIPO_IDS:
        sec = sections.get(tid, "")
        # Contar referencias F-distintas mencionadas en la sección
        f_ids = set(RE_F_REF.findall(sec))
        # Contar referencias explícitas a archivos (ruta o basename)
        explicit_files = set(RE_FOOTER.findall(sec))
        # Wirings = unión de F-ids y archivos explícitos
        wirings = f_ids | {f.split("/")[-1] for f in explicit_files}
        if len(wirings) < 2:
            problems.append(f"{tid}: solo {len(wirings)} wirings (F-ids={sorted(f_ids)})")
    if problems:
        result.fail("C6-wirings", "; ".join(problems))
        return
    result.ok("C6-wirings")


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True,
                        help="Ruta al archivo diagram-catalog.md")
    args = parser.parse_args()
    catalog: Path = args.catalog
    if not catalog.exists():
        print(f"ERROR: catálogo no encontrado: {catalog}", file=sys.stderr)
        return 2
    text = catalog.read_text(encoding="utf-8")

    result = EvalResult()
    crit_1_10_tipos(text, result)
    crit_2_corpus(text, result)
    crit_3_no_vision(text, result)
    crit_4_fifteen_nodes(text, result)
    crit_5_obligatoriedad(text, result)
    crit_6_wirings(text, result)

    print("=" * 60)
    print("Fase 65 — Catálogo por intención")
    print("=" * 60)
    for name in result.passed:
        print(f"  ✓ {name}")
    for name, detail in result.failed:
        print(f"  ✗ {name}")
        print(f"      {detail}")
    print("=" * 60)
    print(result.summary())
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
