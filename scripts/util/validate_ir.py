#!/usr/bin/env python3
"""Valida IRs contra `schemas/note-ir.schema.json` y la tabla de `allowed_children`.

Uso:
    python3 validate_ir.py --validate <ir.json> [<ir.json> ...]
    python3 validate_ir.py --inspect <ir.json>
    python3 validate_ir.py --help

Modos:
    --validate   Carga cada IR, valida contra el schema, verifica
                 `allowed_children` por nodo contra la tabla de §4 del
                 spec, y reporta cobertura de los 33 nodos del catálogo.
                 exit 0 + "OK <path>" si todo pasa.
                 exit 1 si falla.
                 exit 2 si schema/archivo falta o dependencia ausente.

    --inspect    Imprime resumen del IR: count por node_type, capabilities
                 usadas, source_refs únicos.
                 exit 0.

Dependencias: jsonschema. PyYAML no se usa aquí (los IRs son JSON).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "skill" / "notemartin-study-notes" / "schemas" / "note-ir.schema.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

# Catálogo de los 33 nodos (debe coincidir con §4 del spec).
NODE_TYPES = frozenset([
    "section", "paragraph", "list", "checklist", "table",
    "definition-list", "code", "console", "equation", "figure",
    "diagram", "admonition", "collapsible", "quote", "columns",
    "divider", "property-block", "question", "step", "parameter-table",
    "text", "strong", "em", "code-inline", "link-external",
    "link-note", "term-ref", "source-ref", "math-inline",
    "footnote-ref", "keyboard", "placeholder", "deleted",
])

# allowed_children: parent → set de tipos hijo válidos.
# Inline (text, strong, em, ...) solo admite inline.
# Bloques admiten bloque o inline según contexto.
ALLOWED_CHILDREN: dict[str, frozenset[str]] = {
    "section":          frozenset(NODE_TYPES),
    "paragraph":        frozenset({"text", "strong", "em", "code-inline", "link-external",
                                   "link-note", "term-ref", "source-ref", "math-inline",
                                   "footnote-ref", "keyboard", "placeholder", "deleted"}),
    "list":             frozenset(NODE_TYPES),
    "checklist":        frozenset(NODE_TYPES),
    "table":            frozenset({"text", "strong", "em", "code-inline", "link-external",
                                   "link-note", "term-ref", "source-ref"}),
    "definition-list":  frozenset(),
    "code":             frozenset(),
    "console":          frozenset(),
    "equation":         frozenset(),
    "figure":           frozenset(),
    "diagram":          frozenset(),
    "admonition":       frozenset(NODE_TYPES),
    "collapsible":      frozenset(NODE_TYPES),
    "quote":            frozenset(NODE_TYPES),
    "columns":          frozenset(NODE_TYPES),
    "divider":          frozenset(),
    "property-block":   frozenset(),
    "question":         frozenset(NODE_TYPES),
    "step":             frozenset(NODE_TYPES),
    "parameter-table":  frozenset({"text", "strong", "em", "code-inline"}),
    "text":             frozenset(),
    "strong":           frozenset({"text", "strong", "em", "code-inline", "link-external",
                                   "link-note", "term-ref", "source-ref", "math-inline",
                                   "footnote-ref", "keyboard", "placeholder", "deleted"}),
    "em":               frozenset({"text", "strong", "em", "code-inline", "link-external",
                                   "link-note", "term-ref", "source-ref", "math-inline",
                                   "footnote-ref", "keyboard", "placeholder", "deleted"}),
    "code-inline":      frozenset(),
    "link-external":    frozenset({"text", "strong", "em", "code-inline"}),
    "link-note":        frozenset({"text", "strong", "em", "code-inline"}),
    "term-ref":         frozenset({"text", "strong", "em", "code-inline"}),
    "source-ref":       frozenset(),
    "math-inline":      frozenset(),
    "footnote-ref":     frozenset({"text", "strong", "em"}),
    "keyboard":         frozenset(),
    "placeholder":      frozenset(),
    "deleted":          frozenset({"text", "strong", "em", "code-inline"}),
}

# Categoría de cada nodo (para validación inline-vs-block).
INLINE_NODES = frozenset({"text", "strong", "em", "code-inline", "link-external",
                          "link-note", "term-ref", "source-ref", "math-inline",
                          "footnote-ref", "keyboard", "placeholder", "deleted"})
BLOCK_NODES = NODE_TYPES - INLINE_NODES


def _import_jsonschema():
    try:
        import jsonschema
        return jsonschema
    except ImportError:
        sys.stderr.write("Dependency missing: jsonschema. Install with `pip install jsonschema`.\n")
        sys.exit(EXIT_USAGE)


def load_schema(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"Schema not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_ir(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"IR not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def iter_nodes(ir: dict):
    """Yield every node in the IR (recursive)."""
    def walk(node_list):
        for n in node_list or []:
            yield n
            yield from walk(n.get("children") or [])
    yield from walk(ir.get("blocks") or [])


def check_children(node: dict, path: str) -> list[str]:
    """Check that each child node type is in allowed_children of the parent."""
    errors: list[str] = []
    node_type = node.get("node")
    if node_type not in ALLOWED_CHILDREN:
        return errors  # schema already rejects unknown node types
    allowed = ALLOWED_CHILDREN[node_type]
    for i, child in enumerate(node.get("children") or []):
        child_type = child.get("node")
        if child_type not in allowed:
            errors.append(
                f"  - {path}.children[{i}]: nodo {child_type!r} no permitido dentro de {node_type!r} (allowed: {sorted(allowed)})"
            )
        # Recurse
        errors.extend(check_children(child, f"{path}.children[{i}]"))
    return errors


def validate_one(path: Path, schema: dict, jsonschema) -> list[str]:
    errors: list[str] = []
    ir = load_ir(path)

    # Schema validation
    validator = jsonschema.Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(ir), key=lambda e: list(e.absolute_path))
    for err in schema_errors:
        errors.append(f"  - schema: {err.message} (path={list(err.absolute_path)})")

    # Children validation (per §4 of spec)
    for i, root in enumerate(ir.get("blocks") or []):
        errors.extend(check_children(root, f"blocks[{i}]"))

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    jsonschema = _import_jsonschema()
    schema = load_schema(args.schema)
    any_fail = False
    seen_node_types: set[str] = set()
    for path in args.validate:
        errs = validate_one(path, schema, jsonschema)
        if errs:
            any_fail = True
            sys.stderr.write(f"FAIL — {path}\n")
            for e in errs:
                sys.stderr.write(e + "\n")
        else:
            sys.stdout.write(f"OK — {path}\n")
        # Collect node types for coverage
        ir = load_ir(path)
        for node in iter_nodes(ir):
            seen_node_types.add(node.get("node"))
    # Coverage of the 33-node catalog (informational, not a fail criterion)
    coverage = sorted(seen_node_types)
    missing = sorted(NODE_TYPES - set(seen_node_types))
    sys.stderr.write(f"\n[node coverage: {len(coverage)}/33 nodes seen]")
    if missing:
        sys.stderr.write(f" missing={missing}\n")
    else:
        sys.stderr.write("\n")
    return EXIT_VALIDATION if any_fail else EXIT_OK


def cmd_inspect(args: argparse.Namespace) -> int:
    ir = load_ir(args.inspect)
    nodes = list(iter_nodes(ir))
    by_type: Counter = Counter(n.get("node") for n in nodes)
    capabilities: Counter = Counter(n.get("attrs", {}).get("capability", "") for n in nodes if n.get("attrs"))
    source_refs = set()
    for n in nodes:
        for ref in n.get("source_refs") or []:
            source_refs.add((ref.get("block_id"), ref.get("source_hash")))

    sys.stdout.write(f"IR: {args.inspect}\n")
    sys.stdout.write(f"  Total nodes: {len(nodes)}\n")
    sys.stdout.write(f"  By type:\n")
    for t, c in sorted(by_type.items()):
        sys.stdout.write(f"    {t}: {c}\n")
    sys.stdout.write(f"  Unique source_refs: {len(source_refs)}\n")
    sys.stdout.write(f"  Capabilities ({len(capabilities)} unique):\n")
    for cap, c in sorted(capabilities.items()):
        sys.stdout.write(f"    {cap}: {c}\n")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate_ir.py",
        description="Valida IRs contra note-ir.schema.json y la tabla de allowed_children.",
    )
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA,
                   help=f"Ruta al schema (default: {DEFAULT_SCHEMA.relative_to(REPO_ROOT)}).")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", metavar="IR", type=Path, nargs="+",
                      help="Valida uno o más archivos IR.")
    mode.add_argument("--inspect", metavar="IR", type=Path,
                      help="Imprime resumen del IR.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.validate:
        return cmd_validate(args)
    if args.inspect:
        return cmd_inspect(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
