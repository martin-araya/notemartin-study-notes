#!/usr/bin/env python3
"""Trazabilidad bidireccional IR ↔ SDM — Fase 52.

Construye un índice en memoria entre nodos IR y bloques SDM; provee:
- `node`: forward (nodo IR → bloque SDM).
- `block`: backward (bloque SDM → nota IR).
- `orphans`: detecta nodos fácticos sin `source_refs` y derivados sin marca.
- `audit`: ejecuta las 3 verificaciones en un workdir.

Uso:
    python3 trace.py node --ir X --node-path "blocks[3]" --sdm Y
    python3 trace.py block --sdm Y --block-id abc123def456 --workdir DIR
    python3 trace.py orphans --ir X
    python3 trace.py orphans --workdir DIR
    python3 trace.py audit --workdir DIR
    python3 trace.py ... --json

Códigos:
    0 = OK (sin huérfanos tipo A; warnings permitidos).
    1 = Huérfanos tipo A (fácticos sin source_refs) o errores.
    2 = Uso (paths faltantes).

Dependencias:
    - Python 3.9+ stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────
# Carga SDM e IR
# ──────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_sdm_blocks(sdm: dict) -> Dict[str, dict]:
    """Devuelve un dict `block_id → bloque` para lookup O(1)."""
    out: Dict[str, dict] = {}
    for sec in sdm.get("sections", []) or []:
        for blk in sec.get("blocks", []) or []:
            bid = blk.get("id")
            if bid:
                out[bid] = {
                    "id": bid,
                    "type": blk.get("type", ""),
                    "section_path": sec.get("section_path", ""),
                    "section_title": sec.get("title", ""),
                    "anchor": blk.get("anchor", ""),
                    "confidence": blk.get("confidence"),
                    "origin": blk.get("origin", ""),
                    "content": blk.get("content", ""),
                }
    return out


def _strip_aux(obj):
    """Elimina campos con prefijo `_` y `source_file` (auxiliares F48)."""
    if isinstance(obj, dict):
        return {k: _strip_aux(v) for k, v in obj.items()
                if not k.startswith("_") and k != "source_file"}
    if isinstance(obj, list):
        return [_strip_aux(v) for v in obj]
    return obj


def _collect_block_ids(node: Any) -> List[str]:
    """Recolecta todos los block_id de source_refs (nodo + descendientes)."""
    ids: List[str] = []
    if isinstance(node, dict):
        for ref in node.get("source_refs", []) or []:
            if isinstance(ref, dict):
                bid = ref.get("block_id", "")
                if bid:
                    ids.append(bid)
        if node.get("node") == "source-ref":
            bid = node.get("attrs", {}).get("block_id", "")
            if bid:
                ids.append(bid)
        for c in node.get("children", []) or []:
            ids.extend(_collect_block_ids(c))
    return ids


def _node_text(node: Any) -> str:
    """Extrae el texto concatenado de un nodo (recursivo, para heurísticas)."""
    if isinstance(node, dict):
        kind = node.get("node", "")
        if kind == "text":
            return node.get("attrs", {}).get("text", "") or ""
        if kind == "source-ref":
            return ""
        if kind == "code-inline":
            return node.get("attrs", {}).get("text", "") or ""
        if kind == "term-ref":
            return node.get("attrs", {}).get("text", "") or ""
        out = ""
        for c in node.get("children", []) or []:
            out += _node_text(c) + " "
        return out.strip()
    return ""


# ──────────────────────────────────────────────────────────────────────
# Índice bidireccional
# ──────────────────────────────────────────────────────────────────────

class Index:
    """Índice en memoria para trazabilidad bidireccional."""

    def __init__(self) -> None:
        # block_id → lista de (note_id, path, node_type, capability)
        self.block_to_nodes: Dict[str, List[dict]] = defaultdict(list)
        # (note_id, path) → node IR
        self.path_to_node: Dict[Tuple[str, str], dict] = {}

    def add_ir(self, ir_path: Path, ir: dict) -> int:
        """Añade un IR al índice. Devuelve número de nodos indexados."""
        note_id = ir.get("note_id") or ir_path.stem.replace(".note-ir", "")
        count = 0

        def walk(node: Any, path: str) -> None:
            nonlocal count
            if not isinstance(node, dict):
                return
            count += 1
            self.path_to_node[(note_id, path)] = node
            for bid in _collect_block_ids(node):
                self.block_to_nodes[bid].append({
                    "note_id": note_id,
                    "note_path": str(ir_path),
                    "path": path,
                    "node_type": node.get("node", ""),
                    "capability": node.get("attrs", {}).get("capability", ""),
                })
            children = node.get("children", []) or []
            if isinstance(children, list):
                for j, c in enumerate(children):
                    if isinstance(c, dict):
                        walk(c, f"{path}.children[{j}]")

        blocks = ir.get("blocks", []) or []
        if isinstance(blocks, list):
            for i, b in enumerate(blocks):
                if isinstance(b, dict):
                    walk(b, f"blocks[{i}]")
        return count

    def build_from_workdir(self, workdir: Path, glob_pattern: str = "notes/*.note-ir.json") -> int:
        """Construye el índice desde un workdir."""
        total = 0
        notes_dir = workdir / "notes"
        if not notes_dir.exists():
            return 0
        for ir_path in sorted(notes_dir.glob("*.note-ir.json")):
            try:
                ir = _load_json(ir_path)
            except Exception:
                continue
            total += self.add_ir(ir_path, ir)
        return total


# ──────────────────────────────────────────────────────────────────────
# Forward: nodo → bloque
# ──────────────────────────────────────────────────────────────────────

def op_node(args: argparse.Namespace) -> int:
    """Forward: dado un nodo IR, muestra el bloque SDM correspondiente."""
    ir_path = Path(args.ir)
    if not ir_path.exists():
        print(f"ERROR: IR no encontrado: {ir_path}", file=sys.stderr)
        return 2
    ir = _load_json(ir_path)

    note_id = ir.get("note_id") or ir_path.stem
    idx = Index()
    idx.add_ir(ir_path, ir)

    node = idx.path_to_node.get((note_id, args.node_path))
    if node is None:
        print(f"ERROR: node-path '{args.node_path}' no encontrado en {note_id}", file=sys.stderr)
        return 1

    block_ids = _collect_block_ids(node)
    if not block_ids:
        print(f"WARNING: nodo {args.node_path} no tiene source_refs", file=sys.stderr)

    # Cargar SDM si se da.
    sdm_blocks: Dict[str, dict] = {}
    if args.sdm:
        sdm_path = Path(args.sdm)
        if not sdm_path.exists():
            print(f"ERROR: SDM no encontrado: {sdm_path}", file=sys.stderr)
            return 2
        sdm = _load_json(sdm_path)
        sdm_blocks = _load_sdm_blocks(sdm)

    if args.json:
        result = {
            "node_path": args.node_path,
            "note_id": note_id,
            "node_type": node.get("node", ""),
            "capability": node.get("attrs", {}).get("capability", ""),
            "block_ids": block_ids,
            "sdm_blocks": [sdm_blocks.get(bid, {"id": bid, "error": "no encontrado en SDM"})
                            for bid in block_ids],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"NODE: {args.node_path}")
        print(f"  type: {node.get('node', '')}")
        print(f"  capability: {node.get('attrs', {}).get('capability', '')}")
        print(f"  text: {_node_text(node)[:120]}{'...' if len(_node_text(node)) > 120 else ''}")
        print(f"  source_refs: {len(block_ids)}")
        for bid in block_ids:
            blk = sdm_blocks.get(bid)
            if blk:
                print(f"  SDM BLOCK ({bid}):")
                print(f"    section: {blk['section_path']}")
                print(f"    type: {blk['type']}")
                content = blk['content']
                if isinstance(content, dict):
                    content = str(content)
                print(f"    content: {str(content)[:120]}{'...' if len(str(content)) > 120 else ''}")
                print(f"    confidence: {blk['confidence']}")
                print(f"    origin: {blk['origin']}")
            else:
                if args.sdm:
                    print(f"  SDM BLOCK ({bid}): NO ENCONTRADO EN SDM")
    return 0


# ──────────────────────────────────────────────────────────────────────
# Backward: bloque → nodo
# ──────────────────────────────────────────────────────────────────────

def op_block(args: argparse.Namespace) -> int:
    """Backward: dado un block_id, muestra en qué notas IR aparece."""
    if not args.sdm:
        print("ERROR: --sdm requerido", file=sys.stderr)
        return 2
    sdm_path = Path(args.sdm)
    if not sdm_path.exists():
        print(f"ERROR: SDM no encontrado: {sdm_path}", file=sys.stderr)
        return 2
    sdm = _load_json(sdm_path)
    sdm_blocks = _load_sdm_blocks(sdm)
    if args.block_id not in sdm_blocks:
        print(f"ERROR: block_id '{args.block_id}' no existe en SDM", file=sys.stderr)
        return 1
    blk = sdm_blocks[args.block_id]

    # Construir índice.
    idx = Index()
    if args.workdir:
        workdir = Path(args.workdir)
        idx.build_from_workdir(workdir)
    elif args.irs:
        for ir_arg in args.irs:
            ir_path = Path(ir_arg)
            if ir_path.exists():
                try:
                    ir = _load_json(ir_path)
                    idx.add_ir(ir_path, ir)
                except Exception:
                    pass

    appearances = idx.block_to_nodes.get(args.block_id, [])

    if args.json:
        result = {
            "block_id": args.block_id,
            "section": blk["section_path"],
            "type": blk["type"],
            "content": blk["content"],
            "appears_in": appearances,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"BLOCK: {args.block_id}")
        print(f"  source: {blk['section_path']}")
        print(f"  type: {blk['type']}")
        content = blk['content']
        if isinstance(content, dict):
            content = str(content)
        print(f"  content: {str(content)[:200]}{'...' if len(str(content)) > 200 else ''}")
        if appearances:
            print(f"  APPEARS IN ({len(appearances)}):")
            for app in appearances:
                print(f"    - {app['note_id']}: {app['path']} ({app['node_type']})")
        else:
            print(f"  ORPHAN: este bloque SDM no está anclado a ninguna nota")
    return 0


# ──────────────────────────────────────────────────────────────────────
# Detección de huérfanos
# ──────────────────────────────────────────────────────────────────────

# Marcadores de derivación (palabras que indican contenido inferencial).
DERIVATION_MARKERS = [
    "podría", "tal vez", "es probable", "presumiblemente",
    "quizás", "posiblemente", "analogía", "análogo",
]


def _is_factual(node: dict) -> bool:
    """¿Este nodo es fáctico (no derivado, no externo)?"""
    # Flags pueden estar en `node` (sibling de attrs) o en `node.attrs`.
    derived = node.get("derived") or node.get("attrs", {}).get("derived")
    external = node.get("external") or node.get("attrs", {}).get("external")
    if derived or external:
        return False
    return True


def _is_paragraph_factual(node: dict) -> bool:
    """¿Un párrafo con contenido fáctico?"""
    if node.get("node") != "paragraph":
        return False
    text = _node_text(node).strip()
    if not text:
        return False
    # Texto trivial (≤ 3 palabras) no se considera fáctico.
    if len(text.split()) <= 3:
        return False
    return _is_factual(node)


def _find_orphans(ir: dict) -> Tuple[List[dict], List[dict]]:
    """Recorre el IR; devuelve (type_a, type_b).

    type_a: nodos fácticos sin source_refs.
    type_b: párrafos derivados sin marca (heurística de marcadores).
    """
    type_a: List[dict] = []
    type_b: List[dict] = []

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if _is_paragraph_factual(node):
            block_ids = _collect_block_ids(node)
            if not block_ids:
                text = _node_text(node).strip()
                type_a.append({
                    "path": path,
                    "node_type": node.get("node", ""),
                    "text_words": len(text.split()),
                    "preview": text[:80],
                })
        # Detección tipo B: párrafo con marcador de derivación sin marca.
        if node.get("node") == "paragraph":
            text = _node_text(node).strip()
            text_lower = text.lower()
            has_marker = any(m in text_lower for m in DERIVATION_MARKERS)
            if has_marker and len(text.split()) >= 20:
                derived = node.get("derived") or node.get("attrs", {}).get("derived")
                external = node.get("external") or node.get("attrs", {}).get("external")
                if not (derived or external):
                    type_b.append({
                        "path": path,
                        "node_type": node.get("node", ""),
                        "text_words": len(text.split()),
                        "markers_found": [m for m in DERIVATION_MARKERS if m in text_lower],
                        "preview": text[:80],
                    })
        for j, c in enumerate(node.get("children", []) or []):
            if isinstance(c, dict):
                walk(c, f"{path}.children[{j}]")

    for i, b in enumerate(ir.get("blocks", []) or []):
        if isinstance(b, dict):
            walk(b, f"blocks[{i}]")
    return type_a, type_b


def op_orphans(args: argparse.Namespace) -> int:
    """Detecta huérfanos tipo A y tipo B."""
    type_a_total: List[Tuple[str, dict]] = []
    type_b_total: List[Tuple[str, dict]] = []

    if args.workdir:
        workdir = Path(args.workdir)
        notes_dir = workdir / "notes"
        if not notes_dir.exists():
            print(f"ERROR: notes/ no existe en {workdir}", file=sys.stderr)
            return 2
        for ir_path in sorted(notes_dir.glob("*.note-ir.json")):
            try:
                ir = _load_json(ir_path)
            except Exception:
                continue
            type_a, type_b = _find_orphans(ir)
            for entry in type_a:
                type_a_total.append((str(ir_path), entry))
            for entry in type_b:
                type_b_total.append((str(ir_path), entry))
    elif args.ir:
        ir_path = Path(args.ir)
        if not ir_path.exists():
            print(f"ERROR: IR no encontrado: {ir_path}", file=sys.stderr)
            return 2
        ir = _load_json(ir_path)
        type_a, type_b = _find_orphans(ir)
        for entry in type_a:
            type_a_total.append((str(ir_path), entry))
        for entry in type_b:
            type_b_total.append((str(ir_path), entry))
    else:
        print("ERROR: --workdir o --ir requerido", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "type_a_factual_no_source_refs": [
                {"file": f, **entry} for f, entry in type_a_total
            ],
            "type_b_derived_no_mark": [
                {"file": f, **entry} for f, entry in type_b_total
            ],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"ORPHANS REPORT")
        print(f"  Type A (fácticos sin source_refs): {len(type_a_total)}")
        for f, entry in type_a_total:
            print(f"    - {f}: {entry['path']} ({entry['text_words']} palabras)")
        print(f"  Type B (derivados sin marca): {len(type_b_total)}")
        for f, entry in type_b_total:
            markers = ",".join(entry.get("markers_found", []))
            print(f"    - {f}: {entry['path']} (markers={markers})")
    return 1 if type_a_total else 0


# ──────────────────────────────────────────────────────────────────────
# Auditoría completa
# ──────────────────────────────────────────────────────────────────────

def op_audit(args: argparse.Namespace) -> int:
    """Auditoría completa de un workdir."""
    if not args.workdir:
        print("ERROR: --workdir requerido para audit", file=sys.stderr)
        return 2
    workdir = Path(args.workdir)
    if not workdir.exists():
        print(f"ERROR: workdir no existe: {workdir}", file=sys.stderr)
        return 2

    sdm_path = None
    if args.sdm:
        sdm_path = Path(args.sdm)
    elif (workdir / "sdm.json").exists():
        sdm_path = workdir / "sdm.json"
    sdm_blocks: Dict[str, dict] = {}
    if sdm_path and sdm_path.exists():
        try:
            sdm = _load_json(sdm_path)
            sdm_blocks = _load_sdm_blocks(sdm)
        except Exception as e:
            print(f"WARN: SDM no parseable: {e}", file=sys.stderr)

    idx = Index()
    idx.build_from_workdir(workdir)
    n_irs = len({f for f, _ in idx.path_to_node.keys()}) if idx.path_to_node else 0
    n_nodes = len(idx.path_to_node)
    n_blocks_indexed = len(idx.block_to_nodes)

    type_a_total: List[Tuple[str, dict]] = []
    type_b_total: List[Tuple[str, dict]] = []
    notes_dir = workdir / "notes"
    if notes_dir.exists():
        for ir_path in sorted(notes_dir.glob("*.note-ir.json")):
            try:
                ir = _load_json(ir_path)
                type_a, type_b = _find_orphans(ir)
                for entry in type_a:
                    type_a_total.append((str(ir_path), entry))
                for entry in type_b:
                    type_b_total.append((str(ir_path), entry))
            except Exception:
                pass

    orphan_sdm_blocks = []
    if sdm_blocks:
        for bid in sdm_blocks:
            if bid not in idx.block_to_nodes:
                orphan_sdm_blocks.append(bid)

    if args.json:
        print(json.dumps({
            "workdir": str(workdir),
            "sdm_path": str(sdm_path) if sdm_path else None,
            "sdm_blocks": len(sdm_blocks),
            "irs_indexed": n_irs,
            "nodes_indexed": n_nodes,
            "blocks_indexed": n_blocks_indexed,
            "type_a_factual_no_source_refs": len(type_a_total),
            "type_b_derived_no_mark": len(type_b_total),
            "sdm_blocks_unused": orphan_sdm_blocks,
            "details_type_a": [{"file": f, **e} for f, e in type_a_total],
            "details_type_b": [{"file": f, **e} for f, e in type_b_total],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"AUDIT: {workdir}")
        print(f"  SDM: {len(sdm_blocks)} bloques ({sdm_path or 'no cargado'})")
        print(f"  IRs indexados: {n_irs}")
        print(f"  Nodos indexados: {n_nodes}")
        print(f"  Blocks indexados: {n_blocks_indexed}")
        print(f"  Type A (fácticos sin source_refs): {len(type_a_total)}")
        print(f"  Type B (derivados sin marca): {len(type_b_total)}")
        if sdm_blocks:
            print(f"  SDM blocks no usados: {len(orphan_sdm_blocks)}")
            for bid in orphan_sdm_blocks[:5]:
                print(f"    - {bid}")

    return 1 if type_a_total else 0


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # node
    p_node = subparsers.add_parser("node", help="Forward: nodo IR → bloque SDM")
    p_node.add_argument("--ir", required=True)
    p_node.add_argument("--node-path", required=True, help='ej. "blocks[3].children[1]"')
    p_node.add_argument("--sdm", help="Archivo sdm.json")
    p_node.add_argument("--json", action="store_true")

    # block
    p_block = subparsers.add_parser("block", help="Backward: bloque SDM → nota IR")
    p_block.add_argument("--sdm", required=True)
    p_block.add_argument("--block-id", required=True, help="12 hex chars")
    p_block.add_argument("--workdir", help="Directorio de notas")
    p_block.add_argument("--irs", nargs="*", help="IRs específicos (alternativa a workdir)")
    p_block.add_argument("--json", action="store_true")

    # orphans
    p_orph = subparsers.add_parser("orphans", help="Detecta nodos sin source_refs")
    p_orph.add_argument("--workdir", help="Auditar todo el workdir")
    p_orph.add_argument("--ir", help="Auditar un único IR")
    p_orph.add_argument("--json", action="store_true")

    # audit
    p_audit = subparsers.add_parser("audit", help="Auditoría completa de un workdir")
    p_audit.add_argument("--workdir", required=True)
    p_audit.add_argument("--sdm", help="Override de la ruta al sdm.json")
    p_audit.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "node":
        return op_node(args)
    if args.command == "block":
        return op_block(args)
    if args.command == "orphans":
        return op_orphans(args)
    if args.command == "audit":
        return op_audit(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
