"""_linking.py — Módulo compartido de resolución de enlaces (F61).

API centralizada para `collect_link_targets`, `build_link_graph`, `resolve_links`,
y `emit_backlinks_section`. Usado por los 6 renderers (F54-F59) + linking.py CLI.

Importable independientemente:
    python3 -c "from scripts.render._linking import resolve_links; ..."

Stdlib puro (dataclasses, hashlib, re).
"""

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class LinkTarget:
    target: str
    kind: str                # "note" | "term"
    source_note_id: str
    node_path: str
    text: Optional[str] = None

    @property
    def id_stable(self) -> str:
        """Identificador estable para deduplicación."""
        return f"lt-{hashlib.sha256((self.target + self.source_note_id + self.node_path).encode()).hexdigest()[:12]}"


@dataclass
class LinkReport:
    resolved: Dict[str, List[str]] = field(default_factory=dict)
    unresolved: List[LinkTarget] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resolved": dict(self.resolved),
            "unresolved": [
                {
                    "target": lt.target,
                    "kind": lt.kind,
                    "source_note_id": lt.source_note_id,
                    "node_path": lt.node_path,
                    "text": lt.text,
                }
                for lt in self.unresolved
            ],
        }


@dataclass
class LinkGraph:
    edges: Dict[str, Set[str]] = field(default_factory=dict)
    reverse: Dict[str, Set[str]] = field(default_factory=dict)

    def add_edge(self, source: str, target: str) -> None:
        self.edges.setdefault(source, set()).add(target)
        self.reverse.setdefault(target, set()).add(source)

    def has_cycle(self) -> bool:
        """DFS para detectar ciclos. Devuelve True si hay al menos un ciclo."""
        visited: Set[str] = set()
        in_stack: Set[str] = set()

        def _dfs(node: str) -> bool:
            visited.add(node)
            in_stack.add(node)
            for nxt in self.edges.get(node, set()):
                if nxt in in_stack:
                    return True
                if nxt not in visited and _dfs(nxt):
                    return True
            in_stack.discard(node)
            return False

        for n in list(self.edges.keys()):
            if n not in visited:
                if _dfs(n):
                    return True
        return False

    def incoming(self, target: str) -> Set[str]:
        return self.reverse.get(target, set())


# ---------------------------------------------------------------------------
# Recolección y construcción del grafo
# ---------------------------------------------------------------------------


def collect_link_targets(ir_list: List[Dict[str, Any]]) -> List[LinkTarget]:
    """Recorre cada IR y extrae todos los `link-note` y `term-ref`."""
    out: List[LinkTarget] = []

    def _walk(node: Any, source_note_id: str, path: str) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("node", "")
        attrs = node.get("attrs", {}) or {}
        if kind == "link-note":
            tgt = attrs.get("target", "")
            if tgt:
                out.append(LinkTarget(
                    target=tgt, kind="note",
                    source_note_id=source_note_id,
                    node_path=path,
                    text=attrs.get("text"),
                ))
        elif kind == "term-ref":
            tgt = attrs.get("term_id", "")
            if tgt:
                out.append(LinkTarget(
                    target=tgt, kind="term",
                    source_note_id=source_note_id,
                    node_path=path,
                    text=attrs.get("text"),
                ))
        children = node.get("children", []) or []
        for i, child in enumerate(children):
            _walk(child, source_note_id, f"{path}/{i}")

    for ir in ir_list:
        note_id = ir.get("note_id", "")
        children = ir.get("children", []) or []
        for i, child in enumerate(children):
            _walk(child, note_id, f"0/{i}")
    return out


def build_link_graph(ir_list: List[Dict[str, Any]]) -> LinkGraph:
    g = LinkGraph()
    for lt in collect_link_targets(ir_list):
        if lt.kind == "note":
            g.add_edge(lt.source_note_id, lt.target)
    return g


# ---------------------------------------------------------------------------
# Resolución
# ---------------------------------------------------------------------------


def resolve_links(
    ir_list: List[Dict[str, Any]],
    note_ids: Set[str],
    term_ids: Set[str],
    degradations: Optional[List[Dict[str, Any]]] = None,
    placeholders: bool = False,
) -> Tuple[LinkReport, List[LinkTarget]]:
    """Resuelve todos los links del workdir.

    Args:
        ir_list: lista de IRs (notas).
        note_ids: set de note_ids existentes en el workdir.
        term_ids: set de term_ids existentes en el glosario.
        degradations: lista mutable donde añadir entradas de degradación por
            unresolved; si None, no se emiten.
        placeholders: si True, retorna los placeholders en lugar de la
            sintaxis final (no-op aquí; los renderers usan placeholders en pass 1).

    Returns:
        (LinkReport, List[LinkTarget]) — el reporte y todos los targets.
    """
    report = LinkReport()
    targets = collect_link_targets(ir_list)

    for lt in targets:
        if lt.kind == "note" and lt.target in note_ids:
            report.resolved.setdefault(lt.target, []).append(lt.source_note_id)
        elif lt.kind == "term" and lt.target in term_ids:
            report.resolved.setdefault(lt.target, []).append(lt.source_note_id)
        else:
            report.unresolved.append(lt)
            if degradations is not None:
                _add_unresolved_degradation(lt, degradations)

    return report, targets


def _add_unresolved_degradation(
    lt: LinkTarget, degradations: List[Dict[str, Any]]
) -> None:
    """Emite una entrada de degradación por link no resuelto."""
    kind_str = "term-ref" if lt.kind == "term" else "link-note"
    degradations.append({
        "id": f"deg-link-{hashlib.sha256((lt.target + lt.source_note_id + lt.node_path).encode()).hexdigest()[:12]}",
        "node_path": lt.node_path,
        "node_type": kind_str,
        "capability": "link-note",
        "alternative": (
            f"link preservado en texto: {lt.target} "
            f"(target no resuelto en workdir; ver reports/link_debt.json)"
        ),
        "evidence": (
            f"target='{lt.target}' no en note_ids del workdir"
        ),
        "content_intact": True,
        "link_debt": True,
    })


# ---------------------------------------------------------------------------
# Emisión de backlinks
# ---------------------------------------------------------------------------


def build_backlinks_section_md(
    note_id: str, graph: LinkGraph,
    base_url: str = "",
    title: str = "Referenciado por",
) -> Optional[str]:
    """Markdown: `## Referenciado por` con lista de wikilinks."""
    incoming = sorted(graph.incoming(note_id) - {note_id})
    if not incoming:
        return None
    lines = [f"## {title}", ""]
    for src in incoming:
        if base_url:
            lines.append(f"- [{src}]({base_url.rstrip('/')}/{src}.md)")
        else:
            lines.append(f"- [{src}]({src}.md)")
    lines.append("")
    return "\n".join(lines)


def build_backlinks_aside_html(
    note_id: str, graph: LinkGraph,
    base_url: str = "",
    title: str = "Referenciado por",
) -> Optional[str]:
    """HTML: `<aside class="backlinks">` con `<ul>` de `<a>`."""
    incoming = sorted(graph.incoming(note_id) - {note_id})
    if not incoming:
        return None
    items = "\n".join(
        f'    <li><a href="{_html_escape_attr(src)}.html" '
        f'data-note-id="{_html_escape_attr(src)}">{_html_escape_text(src)}</a></li>'
        for src in incoming
    )
    return (
        f'<aside class="backlinks">\n'
        f'  <h2>{_html_escape_text(title)}</h2>\n'
        f'  <ul>\n{items}\n  </ul>\n'
        f'</aside>'
    )


def _html_escape_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def _html_escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Link debt aggregator
# ---------------------------------------------------------------------------


def aggregate_link_debt(
    destination: str, report: LinkReport, page_map: Dict[str, str],
) -> Dict[str, Any]:
    """Construye la entrada per-destino de `link_debt.json`.

    Args:
        destination: nombre del destino (e.g. "obsidian", "markdown").
        report: LinkReport con resolved y unresolved.
        page_map: {target_id: page_id_or_path} para resolved; permite
            validar qué se resolvió realmente vs qué quedó en deuda.
    """
    actually_resolved: List[Dict[str, str]] = []
    for target, sources in report.resolved.items():
        page_id = page_map.get(target, "")
        if page_id:
            for src in sources:
                actually_resolved.append({
                    "target": target,
                    "source_note_id": src,
                    "page_id": page_id,
                })

    return {
        "resolved_count": len(actually_resolved),
        "unresolved_count": len(report.unresolved),
        "resolved": actually_resolved,
        "unresolved": [
            {
                "target": lt.target,
                "kind": lt.kind,
                "source_note_id": lt.source_note_id,
                "node_path": lt.node_path,
                "text": lt.text,
            }
            for lt in report.unresolved
        ],
    }
