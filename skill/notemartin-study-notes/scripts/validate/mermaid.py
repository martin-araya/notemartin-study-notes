#!/usr/bin/env python3
"""mermaid.py — F67 · Validador de diagramas Mermaid.

Parsea bloques `:::diagram` de archivos NoteMark (`.nm`/`.md`) y los
valida contra el catálogo portable de F66 (`references/07-visual/mermaid-portable.md`).

Cubre los 3 criterios de la Fase 67:
- C1: detecta el 100 % de una batería de 20 diagramas rotos a propósito.
- C2: cero falsos positivos sobre los diagramas válidos del repo.
- C3: reporta violaciones de portabilidad (F66 §5) además de errores de
  sintaxis y de legibilidad (F65 §6).

Uso:
    python3 scripts/validate/mermaid.py --source <path>
                                        [--out-dir <dir>]
                                        [--severity {error,warning,info}]
                                        [--fail-on {error,warning,info}]
                                        [--max-nodes N] [--max-label-len N]
                                        [--include-types WP-1,WP-2,...]
                                        [--json]
                                        [--glob <pattern>]

Dependencias: Python 3.9+ stdlib puro.
Códigos de salida:
    0 — PASS (sin violaciones por encima del umbral --fail-on).
    1 — FAIL (al menos 1 violación por encima del umbral).
    2 — Uso incorrecto (paths faltantes, etc.).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util as _importlib_util
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


# Comparte atomic_write_json con F38+.
_IO_PATH = Path(__file__).resolve().parent.parent / "util" / "_io.py"
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json


EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

SCHEMA_VERSION = "1.0.0"

# Tipos portables de F66 §3.
PORTABLE_TYPES: Dict[str, str] = {
    "flowchart": "WP-1",
    "graph": "WP-1",  # alias deprecado pero aceptable
    "sequencediagram": "WP-2",
    "stateDiagram-v2": "WP-3",
    "statediagram-v2": "WP-3",
    "statediagram": "WP-3",  # aceptar también el legacy
    "erdiagram": "WP-4",
    "classdiagram": "WP-5",
    "gantt": "WP-6",
    "gitgraph": "WP-7",
    "pie": "WP-8",
}

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class Node:
    id: str
    shape: str  # '[]', '()', '{}', '[[]]', '[()]', '(())', '[]()', '>(..)', etc.
    label: str  # texto entre comillas
    line: int = 0
    column: int = 0


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""  # texto de la arista
    line: int = 0


@dataclass
class Subgraph:
    id: str
    label: str = ""
    depth: int = 0
    line: int = 0


@dataclass
class Diagram:
    type: str  # flowchart, sequenceDiagram, etc.
    raw_type: str
    line: int = 0
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    subgraphs: List[Subgraph] = field(default_factory=list)
    depth: int = 0
    has_classdef: bool = False
    has_style_literal: bool = False
    has_click: bool = False
    has_linkstyle: bool = False
    has_init: bool = False
    has_html_inline: bool = False
    has_unicode_id: bool = False
    has_unquoted_label: bool = False
    has_participant: bool = False
    has_state_initial: bool = False
    has_state_final: bool = False
    has_dateformat: bool = False
    has_alt_else: bool = False  # sequenceDiagram con alt sin else (warning)
    has_alt_with_else: bool = False
    has_bad_er_cardinality: bool = False  # erDiagram con cardinalidad inválida
    has_unbalanced_brackets: bool = False  # flowchart con corchetes desbalanceados
    directive_src: str = ""
    directive_alt: str = ""
    block_index: int = 0


@dataclass
class Violation:
    rule_id: str
    severity: str
    node_id: str = ""
    line: int = 0
    column: int = 0
    message: str = ""
    fix_hint: str = ""


@dataclass
class DiagramResult:
    block_index: int
    directive_src: str
    directive_alt: str
    diagram_type: str
    violations: List[Violation] = field(default_factory=list)
    parse_ok: bool = True


@dataclass
class Report:
    schema_version: str = SCHEMA_VERSION
    generated_at: str = ""
    files: List[str] = field(default_factory=list)
    blocks_total: int = 0
    blocks_with_violations: int = 0
    parse_ms: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Extracción de bloques
# ---------------------------------------------------------------------------


RE_DIAGRAM_BLOCK = re.compile(
    r':::diagram(?P<attrs>(?:\s+[a-zA-Z\-]+="[^"]*")*)\s*\n'
    r'```mermaid\n(?P<content>.*?)```\s*\n'
    r':::',
    re.DOTALL,
)


def extract_diagrams(text: str) -> List[Tuple[int, str, str, str]]:
    """Devuelve lista de (block_index, attrs_str, content, full_match)."""
    out = []
    for i, m in enumerate(RE_DIAGRAM_BLOCK.finditer(text)):
        attrs = m.group("attrs") or ""
        content = m.group("content")
        out.append((i, attrs, content, m.group(0)))
    return out


def parse_attrs(attrs: str) -> Dict[str, str]:
    """Extrae atributos src=\"...\" alt=\"...\" del bloque :::diagram."""
    result: Dict[str, str] = {}
    for m in re.finditer(r'([a-zA-Z\-]+)="([^"]*)"', attrs):
        result[m.group(1)] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Parser ad-hoc para los 9 tipos portables
# ---------------------------------------------------------------------------


RE_DIRECTION = re.compile(r"^(?:flowchart|graph)\s+(TB|BT|LR|RL|TD)\b", re.IGNORECASE)
RE_DIRECTION_BARE = re.compile(r"^(?:flowchart|graph)\s*$", re.IGNORECASE)


def detect_type(first_line: str) -> Tuple[str, str, int, int]:
    """Detecta tipo y devuelve (tipo_normalizado, tipo_raw, line, col).

    Devuelve ('', '', 0, 0) si no reconoce el tipo.
    """
    s = first_line.strip().split()
    if not s:
        return ("", "", 0, 0)
    raw = s[0]
    t = raw.lower()
    if t in PORTABLE_TYPES:
        return (PORTABLE_TYPES[t], raw, 1, 1)
    return ("", raw, 1, 1)


def parse_flowchart(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para flowchart (WP-1 / WP-9).

    Detecta nodos, edges, subgraphs, click, linkStyle, init, style con hex,
    classDef, HTML inline, IDs Unicode y paréntesis desbalanceados.
    """
    lines = content.splitlines()
    edge_op_re = re.compile(r'(-->\|[^|]*\||---|-->|-\.->|==>)')
    sub_re = re.compile(r'^\s*subgraph\s+(?P<id>[A-Za-z_][A-Za-z0-9_]*)(?:\s+\["(?P<label>[^"]*)"\])?')
    # Match `end` even if there are tokens after it on the same line (compact format)
    end_re = re.compile(r'(?:^|\s)end(?:\s|$)')
    classdef_re = re.compile(r'^\s*classDef\s+')
    class_re = re.compile(r'^\s*class\s+')
    style_re = re.compile(r'^\s*style\s+\S+\s+(?:fill|stroke)\s*:\s*#', re.IGNORECASE)
    click_re = re.compile(r'^\s*click\s+')
    linkstyle_re = re.compile(r'^\s*linkStyle\s+')
    init_re = re.compile(r"^\s*%%\{init:", re.IGNORECASE)
    html_re = re.compile(r"<[a-z]+(?:\s+[^>]*)?>", re.IGNORECASE)

    seen_ids: set = set()
    depth = 0
    max_depth = 0
    subgraph_depth = 0  # current nesting depth (independent of seen_ids dedup)

    for ln_idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip the type declaration line
        if ln_idx == 1 and re.match(r"^\s*(?:flowchart|graph)\b", stripped):
            continue

        if not stripped or stripped.startswith("%%"):
            if init_re.match(line):
                diagram.has_init = True
            continue

        # Bracket balance check (S-03)
        s = line
        in_str = False
        opens = closes = parens_o = parens_c = 0
        i = 0
        while i < len(s):
            c = s[i]
            if c == '"':
                in_str = not in_str
            elif not in_str:
                if c == '[': opens += 1
                elif c == ']': closes += 1
                elif c == '(':
                    if i + 1 < len(s) and s[i+1] == ')':
                        parens_o += 1
                        i += 1
                    else:
                        parens_o += 1
                elif c == ')': parens_c += 1
            i += 1
        if (opens != closes or parens_o != parens_c) and re.search(r'\b[A-Za-z_][A-Za-z0-9_]*\s*\[', s):
            diagram.has_unbalanced_brackets = True

        # Count subgraph and end tokens on this line (supports compact format:
        # multiple subgraphs and ends can appear on one line)
        sub_matches = list(sub_re.finditer(line))
        end_matches = list(end_re.finditer(line))
        for m in sub_matches:
            depth += 1
            subgraph_depth += 1
            max_depth = max(max_depth, subgraph_depth)
            diagram.subgraphs.append(Subgraph(
                id=m.group("id"),
                label=m.group("label") or "",
                depth=subgraph_depth,
                line=ln_idx,
            ))
        for _ in end_matches:
            depth = max(0, depth - 1)
            subgraph_depth = max(0, subgraph_depth - 1)
        if sub_matches or end_matches:
            continue

        if classdef_re.match(line):
            diagram.has_classdef = True
            continue
        if class_re.match(line):
            continue
        if style_re.match(line):
            diagram.has_style_literal = True
            continue
        if click_re.match(line):
            diagram.has_click = True
            continue
        if linkstyle_re.match(line):
            diagram.has_linkstyle = True
            continue

        # Edge chain: A --> B --> C
        remaining = line.strip()
        prev_id: Optional[str] = None
        i = 0
        n = len(remaining)
        while i < n:
            while i < n and remaining[i] in " \t":
                i += 1
            if i >= n:
                break
            m_node = re.match(
                r'(?P<id>[A-Za-z_][A-Za-z0-9_]*)\s*'
                r'(?:'
                r'\["[^"]*"\]\(\)|'
                r'\["[^"]*"\]|'
                r'\("[^"]*"\)|'
                r'\{"[^"]*"\}|'
                r'\[\["[^"]*"\]\]|'
                r'\[\("[^"]*"\)\]|'
                r'\(\("[^"]*"\)\))?',
                remaining[i:],
            )
            if not m_node:
                break
            nid = m_node.group("id")
            shape_full = m_node.group(0)[len(nid):].strip()
            label_match = re.search(r'"([^"]*)"', shape_full)
            label = label_match.group(1) if label_match else ""
            if nid not in seen_ids:
                seen_ids.add(nid)
                diagram.nodes.append(Node(
                    id=nid,
                    shape=shape_full,
                    label=label,
                    line=ln_idx,
                ))
            i += len(m_node.group(0))
            while i < n and remaining[i] in " \t":
                i += 1
            m_op = edge_op_re.match(remaining, i)
            if m_op:
                op = m_op.group(0)
                i += len(op)
                if prev_id is not None:
                    elabel = ""
                    if op.startswith("-->|"):
                        elabel = op[4:-1]
                    diagram.edges.append(Edge(
                        src=prev_id,
                        dst=nid,
                        label=elabel,
                        line=ln_idx,
                    ))
                prev_id = nid
            else:
                prev_id = nid

        # Unquoted label (P-01): id[texto sin comillas]
        if re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[([^\]"]+)\]', line):
            diagram.has_unquoted_label = True

        # Unicode ID (P-02): strip quoted strings first, then check ID position
        stripped_no_strings = re.sub(r'"[^"]*"', '', line)
        id_part_match = re.match(
            r'^\s*([^\s\[\{\(\->][^\s]*?)(?=\s*[\[\{\(]|-->|\s*$)',
            stripped_no_strings,
        )
        if id_part_match:
            id_part = id_part_match.group(1)
            if re.search(r'[^\x00-\x7F]', id_part):
                diagram.has_unicode_id = True

        # HTML inline count
        tags = html_re.findall(line)
        if len(tags) > 1:
            diagram.has_html_inline = True

    diagram.depth = max_depth


def parse_sequence(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para sequenceDiagram (WP-2)."""
    lines = content.splitlines()
    participant_re = re.compile(r"^\s*(?:participant|actor)\s+(?P<id>\S+)(?:\s+as\s+(?P<label>.+))?")
    msg_re = re.compile(
        r"^\s*(?P<src>\S+)\s*(?P<op>->>|-->>|->|--x)\s*(?P<dst>\S+)\s*:(?P<msg>.+)"
    )
    alt_re = re.compile(r"^\s*alt\b")
    else_re = re.compile(r"^\s*else\b")
    note_re = re.compile(r"^\s*Note\b")

    for ln_idx, line in enumerate(lines, 1):
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if participant_re.match(line):
            diagram.has_participant = True
            continue
        m = msg_re.match(line)
        if m:
            diagram.edges.append(Edge(
                src=m.group("src"),
                dst=m.group("dst"),
                label=m.group("msg").strip(),
                line=ln_idx,
            ))
            continue
        if alt_re.match(line):
            diagram.has_alt_else = True  # we'll reset below if else follows
            continue
        if else_re.match(line):
            diagram.has_alt_with_else = True
            diagram.has_alt_else = False
            continue
        if note_re.match(line):
            continue
        # Anything else: loop/opt/par/critical/break/rect — accepted
        if re.match(r"^\s*(loop|opt|par|critical|break|rect)\b", line):
            continue


def parse_state(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para stateDiagram-v2 (WP-3)."""
    has_initial = False
    has_final = False
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if re.search(r"\[\*\]\s*-->", line) or re.search(r"-->\s*\[\*\]", line):
            has_initial = True
            has_final = True
        if re.search(r"-->\s*\[\*\]", line):
            has_final = True
        if re.search(r"\[\*\]\s*-->", line):
            has_initial = True
        # Stereotypes
        if "<<" in line and ">>" in line:
            pass
        # State Composite
        if re.match(r"^\s*state\s+\S+\s*\{", line):
            diagram.depth = max(diagram.depth, 1)
    diagram.has_state_initial = has_initial
    diagram.has_state_final = has_final


def parse_er(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para erDiagram (WP-4)."""
    valid_cardinality = re.compile(
        r"(\|+--o\{|\}+--\|\{|\|\|--o\{|\|\|--\|\{|\|\|--\|<|\|\|--o\}|\|\|--\|\||"
        r"\|\|--\|\}|\|\|o\{|\|\}o\{|\}o--\|\{|\}o--o\{|\}o--\|\{|\}o--\|--\|\{|"
        r"\|\|--\|<|\|\|--o\{|\|o--\|\{|\|o--o\{|\|o--\|\|)",
        re.IGNORECASE,
    )
    bad_cardinality = re.compile(r"\?\?|--|~~", re.IGNORECASE)
    relation_re = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s*:", re.IGNORECASE)
    attr_re = re.compile(r"^\s*\S+\s*\{")
    for ln_idx, line in enumerate(content.splitlines(), 1):
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if attr_re.match(line):
            diagram.edges.append(Edge(src="ATTR", dst="ATTR", label=line.strip(), line=ln_idx))
            continue
        m = relation_re.match(line)
        if m:
            cardinality = m.group(2)
            if bad_cardinality.search(cardinality) and not valid_cardinality.search(cardinality):
                diagram.has_bad_er_cardinality = True
            diagram.edges.append(Edge(src=m.group(1), dst=m.group(3), label=cardinality, line=ln_idx))


def parse_class(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para classDiagram (WP-5)."""
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if re.match(r"^\s*class\s+\S+\s*\{", line):
            continue
        if re.search(r"<\|--|--\|>|--|\*--|o--|\.\.>", line):
            m = re.match(r"^\s*(\S+)\s+(<\|--|--\|>|--|\*--|o--|\.\.>)\s+(\S+)", line)
            if m:
                diagram.edges.append(Edge(src=m.group(1), dst=m.group(3), label="", line=0))


def parse_gantt(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para gantt (WP-6)."""
    has_dateformat = False
    n_tasks = 0
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if re.match(r"^\s*dateFormat\b", line, re.IGNORECASE):
            has_dateformat = True
            continue
        if re.match(r"^\s*(title|axisFormat|section)\b", line, re.IGNORECASE):
            continue
        if ":" in line and "," in line:
            n_tasks += 1
    diagram.has_dateformat = has_dateformat
    # gantt usa `nodes` como tareas para contar
    for i in range(n_tasks):
        diagram.nodes.append(Node(id=f"task{i+1}", shape="", label="", line=0))


def parse_gitgraph(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para gitGraph (WP-7)."""
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if re.match(r"^\s*(commit|branch|checkout|merge|tag|cherry-pick)\b", line):
            continue


def parse_pie(content: str, diagram: Diagram) -> None:
    """Parser ad-hoc para pie (WP-8)."""
    n_entries = 0
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("%%"):
            continue
        if re.match(r"^\s*title\b", line, re.IGNORECASE):
            continue
        if ":" in line:
            n_entries += 1
    for i in range(n_entries):
        diagram.nodes.append(Node(id=f"pie{i+1}", shape="", label="", line=0))


# ---------------------------------------------------------------------------
# Reglas de validación
# ---------------------------------------------------------------------------


def rule_s01(d: Diagram) -> List[Violation]:
    """Tipo declarado y reconocido (uno de WP-1..WP-9)."""
    if not d.type:
        return [Violation(
            rule_id="S-01",
            severity="error",
            node_id="",
            line=d.line,
            message=f"Tipo '{d.raw_type}' no está en la lista blanca de F66 §3",
            fix_hint="Usar uno de: flowchart, sequenceDiagram, stateDiagram-v2, erDiagram, classDiagram, gantt, gitGraph, pie",
        )]
    return []


def rule_s02(d: Diagram) -> List[Violation]:
    """flowchart con dirección declarada."""
    if d.type != "WP-1":
        return []
    if d.raw_type and d.raw_type.strip().lower() in ("flowchart", "graph") \
            and not re.match(r"^(?:flowchart|graph)\s+(TB|BT|LR|RL|TD)\b", d.raw_type.strip(), re.IGNORECASE):
        return [Violation(
            rule_id="S-02",
            severity="error",
            message=f"flowchart sin dirección: '{d.raw_type}'",
            fix_hint="Añadir TB, BT, LR, RL o TD después de 'flowchart'",
        )]
    return []


def rule_s03(d: Diagram) -> List[Violation]:
    """Paréntesis/corchetes balanceados en cada nodo."""
    if d.type != "WP-1":
        return []
    if d.has_unbalanced_brackets:
        return [Violation(
            rule_id="S-03",
            severity="error",
            message="Diagrama flowchart con corchetes/paréntesis desbalanceados",
            fix_hint="Asegurar que cada '[' tiene su ']' y cada '(' tiene su ')'",
        )]
    return []


def rule_s04(d: Diagram) -> List[Violation]:
    """sequenceDiagram participant id es ASCII válido."""
    if d.type != "WP-2":
        return []
    # Check edges: any edge where src or dst starts with a digit is invalid.
    out = []
    for edge in d.edges:
        if edge.src == "ATTR":
            continue
        if re.match(r"^\d", edge.src) or re.match(r"^\d", edge.dst):
            out.append(Violation(
                rule_id="S-04",
                severity="error",
                node_id=edge.src,
                line=edge.line,
                message=f"Identificador de participante inválido: '{edge.src}' o '{edge.dst}'",
                fix_hint="Los identificadores deben comenzar con letra o _",
            ))
    return out


def rule_s05(d: Diagram) -> List[Violation]:
    """sequenceDiagram: alt sin else, o mensaje sin ':'."""
    if d.type != "WP-2":
        return []
    # alt sin else (recomendable tener else para cubrir la rama complementaria)
    if d.has_alt_else and not d.has_alt_with_else:
        return [Violation(
            rule_id="S-05",
            severity="warning",
            message="sequenceDiagram con bloque 'alt' sin 'else' complementario",
            fix_hint="Añadir 'else ... end' dentro del bloque alt para cubrir la rama complementaria",
        )]
    # Si hay participantes pero ningún edge con label
    if d.has_participant and not d.edges:
        return [Violation(
            rule_id="S-05",
            severity="error",
            message="sequenceDiagram con participantes pero sin mensajes con ':'",
            fix_hint="Cada mensaje debe tener ': texto' después de la flecha",
        )]
    return []


def rule_s06(d: Diagram) -> List[Violation]:
    """stateDiagram-v2 con [*] para inicial/final."""
    if d.type != "WP-3":
        return []
    if not d.has_state_initial:
        return [Violation(
            rule_id="S-06",
            severity="warning",
            message="stateDiagram-v2 sin estado inicial [*]",
            fix_hint="Añadir [*] --> FirstState al inicio",
        )]
    return []


def rule_s07(d: Diagram) -> List[Violation]:
    """erDiagram con cardinalidad válida."""
    if d.type != "WP-4":
        return []
    if d.has_bad_er_cardinality:
        return [Violation(
            rule_id="S-07",
            severity="error",
            message="erDiagram con cardinalidad inválida (no es crow's foot)",
            fix_hint="Usar ||, o|, }|, }o entre entidades",
        )]
    return []


def rule_s08(d: Diagram) -> List[Violation]:
    """gantt con dateFormat declarado."""
    if d.type != "WP-6":
        return []
    if not d.has_dateformat:
        return [Violation(
            rule_id="S-08",
            severity="warning",
            message="gantt sin dateFormat",
            fix_hint="Añadir 'dateFormat YYYY-MM-DD' antes de las tareas",
        )]
    return []


def rule_p01(d: Diagram) -> List[Violation]:
    """Toda etiqueta de nodo entrecomillada (R-MP-01)."""
    if d.type != "WP-1":
        return []
    if d.has_unquoted_label:
        return [Violation(
            rule_id="P-01",
            severity="error",
            message="Etiqueta de nodo sin comillas (R-MP-01)",
            fix_hint='Usar A["texto"] en lugar de A[texto]',
        )]
    return []


def rule_p02(d: Diagram) -> List[Violation]:
    """Todo ID de nodo es ASCII (R-MP-02)."""
    if not d.has_unicode_id:
        return []
    return [Violation(
        rule_id="P-02",
        severity="error",
        message="ID de nodo con caracteres no ASCII (R-MP-02)",
        fix_hint='Mantener ID en ASCII (ej. Cliente_Nino) y el acento en la etiqueta',
    )]


def rule_p03(d: Diagram) -> List[Violation]:
    """Sin style X fill:#hex literal (R-MP-04 / LN-8)."""
    if not d.has_style_literal:
        return []
    return [Violation(
        rule_id="P-03",
        severity="error",
        message="style X fill:#hex no es portable en Notion import (F66 §5 LN-8)",
        fix_hint="Usar classDef con nombre semántico + tokens F72",
    )]


def rule_p04(d: Diagram) -> List[Violation]:
    """Sin click / linkStyle (R-MP-06 / LN-9)."""
    out = []
    if d.has_click:
        out.append(Violation(
            rule_id="P-04",
            severity="error",
            message="click A \"url\" no portable en Notion import (F66 §5 LN-9)",
            fix_hint="Documentar el enlace en prosa adyacente o nota al pie",
        ))
    if d.has_linkstyle:
        out.append(Violation(
            rule_id="P-04",
            severity="error",
            message="linkStyle N stroke:... no portable (F66 §5 LN-9)",
            fix_hint="Usar classDef con tokens F72",
        ))
    return out


def rule_p05(d: Diagram) -> List[Violation]:
    """Sin init con theme/themeVariables/htmlLabels (R-MP-06 / LN-10, LN-11)."""
    if not d.has_init:
        return []
    return [Violation(
        rule_id="P-05",
        severity="error",
        message="%%{init:...} con theme/themeVariables no portable (F66 §5 LN-10)",
        fix_hint="Quitar %%{init:...} del bloque; usar tema por defecto",
    )]


def rule_p06(d: Diagram) -> List[Violation]:
    """HTML inline complejo (>1 tag) — warning."""
    if not d.has_html_inline:
        return []
    return [Violation(
        rule_id="P-06",
        severity="warning",
        message="HTML inline complejo (múltiples tags) — limitado en Notion import (F66 §5 LN-12)",
        fix_hint="Reducir a un único tag por etiqueta o usar markdown inline (Mermaid 10+)",
    )]


def rule_l01(d: Diagram, max_nodes: int = 15) -> List[Violation]:
    """≤15 nodos (default)."""
    n = len(d.nodes)
    if n > max_nodes:
        return [Violation(
            rule_id="L-01",
            severity="error",
            message=f"Diagrama con {n} nodos supera el umbral de {max_nodes} (F65 §6 R-D-02)",
            fix_hint="Partir en sub-diagramas según F65 §6 o usar tabla",
        )]
    return []


def rule_l02(d: Diagram, max_gantt: int = 25) -> List[Violation]:
    """Excepción: gantt admite hasta 25 hitos."""
    if d.type != "WP-6":
        return []
    n = len(d.nodes)
    if 15 < n <= max_gantt:
        return [Violation(
            rule_id="L-02",
            severity="info",
            message=f"gantt con {n} hitos (admisible hasta {max_gantt} por F65 §6.2)",
            fix_hint="No requiere acción; informativo",
        )]
    return []


def rule_l03(d: Diagram, max_hier: int = 25) -> List[Violation]:
    """Excepción: jerarquía admite hasta 25 nodos."""
    if d.type != "WP-1":
        return []
    if d.depth == 0:
        return []
    n = len(d.nodes)
    if 15 < n <= max_hier and d.depth <= 4:
        return [Violation(
            rule_id="L-03",
            severity="info",
            message=f"Jerarquía con {n} nodos y profundidad {d.depth} (admisible hasta {max_hier} por F65 §6.2)",
            fix_hint="No requiere acción; informativo",
        )]
    return []


def rule_l04(d: Diagram, max_label: int = 40) -> List[Violation]:
    """Longitud de etiqueta ≤40 chars sin <br/>, ≤60 con."""
    if d.type != "WP-1":
        return []
    out = []
    for node in d.nodes:
        if not node.label:
            continue
        has_br = "<br/>" in node.label or "<br>" in node.label
        limit = 60 if has_br else 40
        if len(node.label) > limit:
            out.append(Violation(
                rule_id="L-04",
                severity="warning",
                node_id=node.id,
                line=node.line,
                message=f"Etiqueta de '{node.id}' tiene {len(node.label)} chars (máx {limit})",
                fix_hint="Acortar la etiqueta o partir con <br/>",
            ))
    return out


def rule_l05(d: Diagram) -> List[Violation]:
    """Subgraphs anidados ≤2 niveles."""
    if d.type != "WP-1":
        return []
    if d.depth > 2:
        return [Violation(
            rule_id="L-05",
            severity="error",
            message=f"Subgraphs anidados a profundidad {d.depth} (máx 2 por R-MP-05)",
            fix_hint="Aplanar la jerarquía o partir en varios diagramas",
        )]
    return []


def rule_l06(d: Diagram) -> List[Violation]:
    """Directiva :::diagram sin alt= (accesibilidad)."""
    if not d.directive_src and d.block_index >= 0:
        pass
    if not d.directive_alt:
        return [Violation(
            rule_id="L-06",
            severity="warning",
            node_id=d.directive_src or "(sin-src)",
            line=0,
            message='Directiva :::diagram sin atributo alt= (F65 §8 accesibilidad)',
            fix_hint='Añadir alt="<descripción textual>" en la directiva :::diagram',
        )]
    return []


RULES: List[Callable[..., List[Violation]]] = [
    rule_s01, rule_s02, rule_s03, rule_s04, rule_s05, rule_s06, rule_s07, rule_s08,
    rule_p01, rule_p02, rule_p03, rule_p04, rule_p05, rule_p06,
    rule_l01, rule_l02, rule_l03, rule_l04, rule_l05, rule_l06,
]


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------


def validate_diagram(
    content: str,
    attrs: Dict[str, str],
    block_index: int,
    max_nodes: int = 15,
    max_label: int = 40,
) -> DiagramResult:
    """Parsea y valida un bloque Mermaid."""
    diagram = Diagram(type="", raw_type="", block_index=block_index)
    diagram.directive_src = attrs.get("src", "")
    diagram.directive_alt = attrs.get("alt", "")

    lines = content.splitlines()
    first_nonempty = next((ln for ln in lines if ln.strip()), "")
    type_str, raw_type, line_no, col_no = detect_type(first_nonempty)
    # raw_type should be the full type line (e.g. "flowchart TD"), not just the first token.
    if first_nonempty:
        diagram.raw_type = first_nonempty.strip()
    else:
        diagram.raw_type = raw_type
    diagram.type = type_str
    diagram.line = line_no

    if type_str == "WP-1":
        parse_flowchart(content, diagram)
    elif type_str == "WP-2":
        parse_sequence(content, diagram)
    elif type_str == "WP-3":
        parse_state(content, diagram)
    elif type_str == "WP-4":
        parse_er(content, diagram)
    elif type_str == "WP-5":
        parse_class(content, diagram)
    elif type_str == "WP-6":
        parse_gantt(content, diagram)
    elif type_str == "WP-7":
        parse_gitgraph(content, diagram)
    elif type_str == "WP-8":
        parse_pie(content, diagram)

    violations: List[Violation] = []
    for rule in RULES:
        try:
            if rule in (rule_l01,):
                violations.extend(rule(diagram, max_nodes=max_nodes))
            elif rule is rule_l04:
                violations.extend(rule(diagram, max_label=max_label))
            elif rule is rule_l03:
                violations.extend(rule(diagram))
            else:
                violations.extend(rule(diagram))
        except Exception as exc:  # defensive: rule must not crash
            rid_raw = rule.__name__.replace("rule_", "")
            m = re.match(r"^([spl])(\d+)$", rid_raw.lower())
            if m:
                rid = f"{m.group(1).upper()}-{int(m.group(2)):02d}"
            else:
                rid = rid_raw
            violations.append(Violation(
                rule_id=rid,
                severity="info",
                message=f"Regla {rule.__name__} falló: {exc}",
            ))

    return DiagramResult(
        block_index=block_index,
        directive_src=diagram.directive_src,
        directive_alt=diagram.directive_alt,
        diagram_type=diagram.type or diagram.raw_type,
        violations=violations,
        parse_ok=True,
    )


def validate_file(path: Path, max_nodes: int = 15, max_label: int = 40) -> List[DiagramResult]:
    text = path.read_text(encoding="utf-8")
    blocks = extract_diagrams(text)
    results: List[DiagramResult] = []
    for block_index, attrs_str, content, _full in blocks:
        attrs = parse_attrs(attrs_str)
        results.append(validate_diagram(content, attrs, block_index, max_nodes=max_nodes, max_label=max_label))
    return results


def validate_directory(
    glob_pattern: str, max_nodes: int = 15, max_label: int = 40
) -> List[Tuple[Path, List[DiagramResult]]]:
    out: List[Tuple[Path, List[DiagramResult]]] = []
    for p in sorted(Path(".").glob(glob_pattern)):
        if p.is_file() and p.suffix in (".md", ".nm"):
            out.append((p, validate_file(p, max_nodes=max_nodes, max_label=max_label)))
    return out


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def build_report(
    files: List[Path],
    per_file: Dict[Path, List[DiagramResult]],
    parse_ms: int,
) -> Report:
    rep = Report()
    rep.generated_at = _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")
    rep.files = [str(f) for f in files]
    rep.parse_ms = parse_ms
    for path, results in per_file.items():
        for r in results:
            rep.blocks_total += 1
            if any(v.severity == "error" for v in r.violations):
                rep.blocks_with_violations += 1
            rep.results.append({
                "file": str(path),
                "block_index": r.block_index,
                "directive_src": r.directive_src,
                "directive_alt": r.directive_alt,
                "diagram_type": r.diagram_type,
                "violations": [asdict(v) for v in r.violations],
            })
    return rep


def render_json(rep: Report) -> str:
    return json.dumps(asdict(rep), indent=2, ensure_ascii=False)


def render_markdown(rep: Report) -> str:
    out: List[str] = []
    out.append(f"# Mermaid validator report (schema {rep.schema_version})")
    out.append("")
    out.append(f"- **Generated:** {rep.generated_at}")
    out.append(f"- **Files:** {len(rep.files)}")
    out.append(f"- **Blocks total:** {rep.blocks_total}")
    out.append(f"- **Blocks with violations:** {rep.blocks_with_violations}")
    out.append(f"- **Parse time:** {rep.parse_ms} ms")
    out.append("")
    out.append("## Violations")
    out.append("")
    out.append("| File | Block | Type | Rule | Severity | Node | Line | Message | Fix hint |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in rep.results:
        for v in r["violations"]:
            out.append(
                f'| `{r["file"]}` | {r["block_index"]} | {r["diagram_type"]} | '
                f'{v["rule_id"]} | {v["severity"]} | {v.get("node_id","")} | '
                f'{v.get("line",0)} | {v["message"]} | {v.get("fix_hint","")} |'
            )
    if not any(r["violations"] for r in rep.results):
        out.append("| (no violations) | | | | | | | | |")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mermaid.py",
        description="F67 — Validador de diagramas Mermaid (F65+F66).",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--source", type=Path, help="Archivo .md o .nm a validar.")
    src.add_argument("--glob", type=str, help="Patrón glob para múltiples archivos (ej. 'evals/**/*.nm').")
    p.add_argument("--out-dir", type=Path, help="Directorio de salida para validate-report.{json,md}.")
    p.add_argument("--severity", choices=["error", "warning", "info"], default="info",
                   help="Umbral mínimo de severidad para reportar (default: info).")
    p.add_argument("--fail-on", choices=["error", "warning", "info"], default="error",
                   help="Severidad que causa exit ≠ 0 (default: error).")
    p.add_argument("--max-nodes", type=int, default=15, help="Umbral de nodos por diagrama (default: 15).")
    p.add_argument("--max-label-len", type=int, default=40, help="Longitud máxima de etiqueta sin <br/> (default: 40).")
    p.add_argument("--include-types", type=str, default="", help="CSV de tipos WP-N a incluir (default: todos).")
    p.add_argument("--json", action="store_true", help="Salida solo JSON (sin Markdown).")
    return p.parse_args(argv)


def severity_at_least(sev: str, threshold: str) -> bool:
    return SEVERITY_ORDER[sev] <= SEVERITY_ORDER[threshold]


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if not args.source and not args.glob:
        print("ERROR: se requiere --source o --glob", file=sys.stderr)
        return EXIT_USAGE

    t0 = time.time()
    per_file: Dict[Path, List[DiagramResult]] = {}
    if args.source:
        if not args.source.exists():
            print(f"ERROR: --source no encontrado: {args.source}", file=sys.stderr)
            return EXIT_USAGE
        per_file[args.source] = validate_file(args.source, max_nodes=args.max_nodes, max_label=args.max_label_len)
    else:
        for p, results in validate_directory(args.glob, max_nodes=args.max_nodes, max_label=args.max_label_len):
            per_file[p] = results

    parse_ms = int((time.time() - t0) * 1000)
    rep = build_report(list(per_file.keys()), per_file, parse_ms)

    # Filter by severity threshold
    rep.results = [
        r for r in rep.results
        if any(severity_at_least(v["severity"], args.severity) for v in r["violations"])
    ]
    for r in rep.results:
        r["violations"] = [v for v in r["violations"] if severity_at_least(v["severity"], args.severity)]

    json_out = render_json(rep)
    md_out = render_markdown(rep)

    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(args.out_dir / "validate-report.json", json.loads(json_out))
        (args.out_dir / "validate-report.md").write_text(md_out, encoding="utf-8")
        print(f"Report written to {args.out_dir / 'validate-report.{json,md}'}", file=sys.stderr)
    else:
        if args.json:
            print(json_out)
        else:
            print(md_out)

    # Decide exit code
    any_fail = any(
        any(severity_at_least(v["severity"], args.fail_on) for v in r["violations"])
        for r in rep.results
    )
    return EXIT_FAIL if any_fail else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
