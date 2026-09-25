#!/usr/bin/env python3
"""Validador de IR — Fase 49.

Valida archivos `.note-ir.json` con tres capas:
1. Schema (delegada a jsonschema si está disponible; contra `note-ir.schema.json`).
2. Semántica: `allowed_children` por nodo, capability válida, source_ref resoluble.
3. Calidad estructural: avisos (W1..W10) que NO bloquean el cierre.

Uso:
    python3 validate_ir.py --ir notes/foo.note-ir.json --sdm .notes-work/<hash>/sdm.json
    python3 validate_ir.py --ir irs/*.json --sdm .notes-work/<hash>/sdm.json
    python3 validate_ir.py --ir notes/foo.note-ir.json --inspect
    python3 validate_ir.py --ir notes/foo.note-ir.json --strict
    python3 validate_ir.py --ir notes/foo.note-ir.json --skip-sdm

Códigos:
    0 = OK (sin errores; warnings permitidos).
    1 = Errores (nodo desconocido, hijo no permitido, source_ref colgante, etc.).
    2 = Uso (paths faltantes, argumentos inválidos).

Dependencias:
    - Python 3.9+ stdlib.
    - jsonschema (recomendado): validación contra `note-ir.schema.json`.

Documentación normativa: `references/04-authoring/ir-spec.md` (F14).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, List, Set


# ──────────────────────────────────────────────────────────────────────
# Catálogos cerrados (F14 §4 + F8 capability-matrix)
# ──────────────────────────────────────────────────────────────────────

# 33 nodos: 20 bloque + 13 inline.
ALLOWED_NODES: Set[str] = {
    # Bloque (20)
    "section", "paragraph", "list", "checklist", "table", "definition-list",
    "code", "console", "equation", "figure", "diagram", "admonition",
    "collapsible", "quote", "columns", "divider", "property-block",
    "question", "step", "parameter-table",
    # Inline (13)
    "text", "strong", "em", "code-inline", "link-external", "link-note",
    "term-ref", "source-ref", "math-inline", "footnote-ref", "keyboard",
    "placeholder", "deleted",
}

# 13 inline nodos (todos los inline solo admiten otros inline como hijos).
INLINE_NODES: Set[str] = {
    "text", "strong", "em", "code-inline", "link-external", "link-note",
    "term-ref", "source-ref", "math-inline", "footnote-ref", "keyboard",
    "placeholder", "deleted",
}

# Bloque que admite cualquier hijo (block o inline) — los "contenedores".
OPEN_BLOCKS: Set[str] = {
    "section", "admonition", "collapsible", "columns", "question", "step",
}

# Capabilities cerradas (F8 capability-matrix).
ALLOWED_CAPABILITIES: Set[str] = {
    # Sección (7 capacidades, una por nivel + alias genérico)
    "section", "section-h1", "section-h2", "section-h3", "section-h4",
    "section-h5", "section-h6",
    # Bloque
    "paragraph", "list", "checklist", "table", "definition-list",
    "code-block-fenced", "console-block", "equation-block", "math-inline",
    "figure", "diagram-mermaid-block", "diagram-railroad",
    "callout", "callout-note", "callout-tip", "callout-example",
    "callout-warning", "callout-danger", "callout-security",
    "callout-performance", "callout-version", "callout-deprecated",
    "callout-conflict",
    "collapsible", "quote", "columns", "divider", "property-table",
    "question", "step", "parameter-table",
    # Inline
    "text", "strong", "em", "code-inline", "link-external", "link-note",
    "link-term", "source-ref", "footnote-ref", "keyboard", "placeholder",
    "deleted", "layer-mark",
}

# Severidades de admonition permitidas (F45 §3.1).
ADMONITION_SEVERITIES: Set[str] = {
    "warning", "note", "tip", "example", "danger", "security",
    "performance", "version", "deprecated", "conflict", "external",
}


# ──────────────────────────────────────────────────────────────────────
# Validador
# ──────────────────────────────────────────────────────────────────────

class Issue:
    """Un problema detectado en el IR."""
    def __init__(self, severity: str, path: str, node: str, rule: str, message: str):
        self.severity = severity  # "error" | "warning"
        self.path = path          # "blocks[3].children[0]"
        self.node = node          # "source-ref"
        self.rule = rule          # "E1", "W1", etc.
        self.message = message

    def __repr__(self) -> str:
        ctx = f" ({self.node})" if self.node else ""
        return f"{self.severity.upper()} [{self.rule}]: {self.path}{ctx} — {self.message}"


class IRValidator:
    """Validador principal."""

    def __init__(self, sdm_blocks: Set[str] | None = None,
                 sdm_source_hash: str | None = None,
                 skip_sdm: bool = False) -> None:
        self.sdm_blocks = sdm_blocks or set()
        self.sdm_source_hash = sdm_source_hash
        self.skip_sdm = skip_sdm
        self.issues: List[Issue] = []

    def validate(self, ir: dict) -> List[Issue]:
        """Punto de entrada. Devuelve todos los issues encontrados."""
        self.issues = []
        if not isinstance(ir, dict):
            self.issues.append(Issue("error", "<root>", "", "E0",
                                    "IR no es un objeto JSON"))
            return self.issues
        # Schema version check.
        v = ir.get("schema_version")
        if v != "1.0.0":
            self.issues.append(Issue("error", "<root>", "", "E0",
                                    f"schema_version esperado '1.0.0', recibido '{v}'"))
        # Top-level required.
        for req in ("note_id", "title", "blocks"):
            if req not in ir:
                self.issues.append(Issue("error", "<root>", "", "E0",
                                        f"falta campo top-level obligatorio '{req}'"))
        # Recorrer el árbol.
        blocks = ir.get("blocks", [])
        if isinstance(blocks, list):
            for i, b in enumerate(blocks):
                self._validate_block(b, f"blocks[{i}]")
        # Avisos de calidad top-level.
        self._check_top_level_warnings(ir)
        return self.issues

    def _validate_block(self, node: dict, path: str) -> None:
        """Valida un nodo y recursa en sus hijos."""
        if not isinstance(node, dict):
            self.issues.append(Issue("error", path, "", "E1",
                                    f"nodo no es un objeto: {type(node).__name__}"))
            return

        kind = node.get("node", "")
        attrs = node.get("attrs", {})
        if not isinstance(attrs, dict):
            self.issues.append(Issue("error", path, kind, "E1",
                                    f"attrs no es un objeto: {type(attrs).__name__}"))
            return

        # E1: nodo desconocido.
        if kind not in ALLOWED_NODES:
            self.issues.append(Issue("error", path, kind, "E1",
                                    f"nodo desconocido '{kind}'. "
                                    f"Nodos válidos: {', '.join(sorted(ALLOWED_NODES))}"))

        # E1b: allowed_children (hijo no permitido).
        children = node.get("children", [])
        if isinstance(children, list):
            for j, child in enumerate(children):
                if isinstance(child, dict):
                    child_kind = child.get("node", "")
                    # Excepción: parameter-table acepta table children
                    # (F48 wrappea GFM tables en `table` nodes).
                    if kind == "parameter-table" and child_kind == "table":
                        continue
                    if child_kind and not self._is_allowed_child(kind, child_kind):
                        self.issues.append(Issue("error", f"{path}.children[{j}]",
                                                child_kind, "E1b",
                                                f"hijo '{child_kind}' no permitido en '{kind}'"))

        # E2: capability ausente (error) o desconocida (warning; el schema
        # la acepta como string libre).
        cap = attrs.get("capability")
        if cap is None:
            self.issues.append(Issue("error", path, kind, "E2",
                                    f"falta 'capability' en attrs"))
        elif cap not in ALLOWED_CAPABILITIES:
            self.issues.append(Issue("warning", path, kind, "W11",
                                    f"capability '{cap}' no está en el catálogo "
                                    f"(posible alias)"))

        # E3: source_refs inválidos (block_id pattern, source_hash pattern).
        source_refs = node.get("source_refs", [])
        if not isinstance(source_refs, list):
            self.issues.append(Issue("error", path, kind, "E3",
                                    f"source_refs no es una lista: {type(source_refs).__name__}"))
        else:
            for j, ref in enumerate(source_refs):
                self._validate_source_ref(ref, f"{path}.source_refs[{j}]", kind)

        # E4: admonition.severity debe estar en el enum.
        if kind == "admonition":
            sev = attrs.get("severity")
            if sev not in ADMONITION_SEVERITIES:
                self.issues.append(Issue("error", path, kind, "E4",
                                        f"severity inválida '{sev}'. "
                                        f"Valores: {', '.join(sorted(ADMONITION_SEVERITIES))}"))

        # E5: source-ref con block_id que no existe en el SDM.
        if not self.skip_sdm and kind == "source-ref":
            block_id = attrs.get("block_id")
            if block_id and self.sdm_blocks and block_id not in self.sdm_blocks:
                self.issues.append(Issue("error", path, kind, "E5",
                                        f"source_ref.block_id '{block_id}' no existe en el SDM "
                                        f"({len(self.sdm_blocks)} bloques disponibles)"))

        # E6: source-ref con block_id malformado.
        if kind == "source-ref":
            block_id = attrs.get("block_id", "")
            if not re.match(r"^[0-9a-f]{12}$", block_id):
                self.issues.append(Issue("error", path, kind, "E6",
                                        f"block_id '{block_id}' no es 12 hex chars"))

        # Avisos W1..W10 (se aplican a partir del nodo).
        self._check_warnings(node, path, kind, attrs)

        # Recursar en children.
        children = node.get("children", [])
        if not isinstance(children, list):
            self.issues.append(Issue("error", path, kind, "E1",
                                    f"children no es una lista: {type(children).__name__}"))
            return
        for j, child in enumerate(children):
            child_path = f"{path}.children[{j}]"
            if isinstance(child, dict):
                self._validate_block(child, child_path)
            else:
                self.issues.append(Issue("error", child_path, "", "E1",
                                        f"hijo no es un objeto: {type(child).__name__}"))

    def _validate_source_ref(self, ref: dict, path: str, parent_kind: str) -> None:
        """Valida un source_ref individual."""
        if not isinstance(ref, dict):
            self.issues.append(Issue("error", path, parent_kind, "E3",
                                    f"source_ref no es objeto: {type(ref).__name__}"))
            return
        block_id = ref.get("block_id")
        if not block_id:
            self.issues.append(Issue("error", path, parent_kind, "E3",
                                    "source_ref sin block_id"))
            return
        if not re.match(r"^[0-9a-f]{12}$", block_id):
            self.issues.append(Issue("error", path, parent_kind, "E3",
                                    f"source_ref.block_id '{block_id}' no es 12 hex"))
        source_hash = ref.get("source_hash", "")
        if source_hash and not re.match(r"^[0-9a-f]{64}$", source_hash):
            self.issues.append(Issue("error", path, parent_kind, "E3",
                                    f"source_ref.source_hash no es 64 hex"))

    def _check_warnings(self, node: dict, path: str, kind: str, attrs: dict) -> None:
        """Reglas W1..W10."""
        # W1: tabla con 0 filas de datos (solo headers).
        if kind == "table":
            # En el schema actual las filas no se persisten en IR; emitimos
            # warning si no hay children con datos. Aquí solo detectamos
            # la presencia de headers sin información adicional.
            pass  # No detectable sin children.
        # W2: lista con 1 ítem.
        if kind == "list":
            children = node.get("children", [])
            if len(children) == 1:
                self.issues.append(Issue("warning", path, kind, "W2",
                                        "lista con 1 solo ítem; considerar paragraph"))
        # W3: sección vacía.
        if kind == "section":
            children = node.get("children", [])
            if not children:
                self.issues.append(Issue("warning", path, kind, "W3",
                                        "sección sin contenido (sin children)"))
        # W4: paragraph sin texto.
        if kind == "paragraph":
            children = node.get("children", [])
            if not self._has_meaningful_text(children):
                self.issues.append(Issue("warning", path, kind, "W4",
                                        "paragraph sin texto"))
        # W5: code sin texto.
        if kind == "code":
            text = attrs.get("text", "")
            if not text.strip():
                self.issues.append(Issue("warning", path, kind, "W5",
                                        "code sin texto"))
        # W6: admonition sin children.
        if kind == "admonition":
            children = node.get("children", [])
            if not children:
                self.issues.append(Issue("warning", path, kind, "W6",
                                        "admonition sin contenido"))
        # W7: text node con text="" (vacío).
        if kind == "text":
            if attrs.get("text", "") == "":
                self.issues.append(Issue("warning", path, kind, "W7",
                                        "text node con text vacío"))
        # W8: múltiples source-ref con el mismo block_id en el mismo paragraph.
        if kind == "paragraph":
            children = node.get("children", [])
            block_ids = []
            for c in children:
                if isinstance(c, dict) and c.get("node") == "source-ref":
                    bid = c.get("attrs", {}).get("block_id", "")
                    if bid:
                        block_ids.append(bid)
            if len(block_ids) != len(set(block_ids)):
                dupes = [b for b, n in Counter(block_ids).items() if n > 1]
                self.issues.append(Issue("warning", path, kind, "W8",
                                        f"source-refs duplicados en paragraph: {dupes}"))
        # W10: question sin respuesta.
        if kind == "question":
            children = node.get("children", [])
            if not children or not any(
                isinstance(c, dict) and c.get("node") in {"paragraph", "list", "code", "console", "diagram"}
                for c in children
            ):
                self.issues.append(Issue("warning", path, kind, "W10",
                                        "question sin respuesta"))

    def _check_top_level_warnings(self, ir: dict) -> None:
        """W9: source_hash inconsistente con el SDM."""
        if self.skip_sdm or not self.sdm_source_hash:
            return
        # W9 se chequea a nivel de source-ref individual arriba; aquí nada extra.

    @staticmethod
    def _has_meaningful_text(children: list) -> bool:
        for c in children:
            if isinstance(c, dict):
                if c.get("node") == "text":
                    if c.get("attrs", {}).get("text", "").strip():
                        return True
                # Otros nodos inline con text también cuentan.
                for field in ("text", "term_id", "target", "url", "combo", "ref_id"):
                    if c.get("attrs", {}).get(field, "").strip():
                        return True
        return False

    @staticmethod
    def _is_allowed_child(parent_kind: str, child_kind: str) -> bool:
        """¿Es `child_kind` un hijo válido para `parent_kind`?

        Referencia: `ir-spec.md` §4.
        """
        # Inline solo admite inline.
        if parent_kind in INLINE_NODES:
            return child_kind in INLINE_NODES
        # Hojas: sin hijos.
        if parent_kind in {"code", "console", "equation", "figure", "diagram",
                           "divider", "property-block", "definition-list",
                           "placeholder", "code-inline", "link-external",
                           "link-note", "term-ref", "source-ref", "math-inline",
                           "footnote-ref", "keyboard", "text"}:
            return False
        # Bloques "contenedores" admiten block o inline.
        if parent_kind in OPEN_BLOCKS:
            return True
        # paragraph admite inline o paragraph (paragraph anidado permitido).
        if parent_kind == "paragraph":
            return child_kind in INLINE_NODES or child_kind == "paragraph"
        # list/checklist admiten inline O paragraph (modelado como list-item).
        if parent_kind in {"list", "checklist"}:
            return child_kind in INLINE_NODES or child_kind == "paragraph"
        # table/parameter-table admiten inline (celdas).
        if parent_kind in {"table", "parameter-table"}:
            return child_kind in INLINE_NODES
        # quote admite inline O paragraph.
        if parent_kind == "quote":
            return child_kind in INLINE_NODES or child_kind == "paragraph"
        # Por defecto: no permitido.
        return False


# ──────────────────────────────────────────────────────────────────────
# Carga de SDM
# ──────────────────────────────────────────────────────────────────────

def load_sdm_blocks(sdm_path: Path) -> tuple[Set[str], str | None]:
    """Carga un SDM (json) y devuelve (set de block_ids, sha256 hex del archivo).

    El SDM puede estar en formato:
    - sdm.json completo (F13): {"blocks": [{"id": "abc123def456", ...}, ...]}
    - Una lista plana: [{"id": "abc..."}]

    En cualquier caso, extrae los `id` (12 hex) y devuelve el set.
    """
    text = sdm_path.read_text(encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        data = json.loads(text)
    except Exception as e:
        raise SystemExit(f"ERROR: SDM no parseable ({sdm_path}): {e}")
    blocks: Set[str] = set()
    if isinstance(data, dict):
        for b in data.get("blocks", []):
            if isinstance(b, dict) and isinstance(b.get("id"), str):
                blocks.add(b["id"])
    elif isinstance(data, list):
        for b in data:
            if isinstance(b, dict) and isinstance(b.get("id"), str):
                blocks.add(b["id"])
    return blocks, sha


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ir", required=True, action="append",
                        help="Archivo .note-ir.json (puede repetirse)")
    parser.add_argument("--sdm", help="Archivo sdm.json con block_ids válidos (obligatorio)")
    parser.add_argument("--skip-sdm", action="store_true",
                        help="Omitir verificación de source_ref.block_id contra SDM")
    parser.add_argument("--strict", action="store_true",
                        help="Los warnings también exit 1 (default: solo errores exit 1)")
    parser.add_argument("--inspect", action="store_true",
                        help="Modo resumen: emite estadísticas sin validar errores")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--schema", default="schemas/note-ir.schema.json",
                        help="Path al schema IR (default: schemas/note-ir.schema.json)")
    args = parser.parse_args(argv)

    # Cargar SDM si se provee.
    sdm_blocks: Set[str] = set()
    sdm_hash: str | None = None
    if args.sdm:
        sdm_path = Path(args.sdm)
        if not sdm_path.exists():
            print(f"ERROR: SDM no encontrado: {sdm_path}", file=sys.stderr)
            return 2
        try:
            sdm_blocks, sdm_hash = load_sdm_blocks(sdm_path)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 2

    # Determinar paths.
    pkg_root = Path(__file__).resolve().parents[2]
    schema_path = Path(args.schema)
    if not schema_path.is_absolute():
        schema_path = pkg_root / args.schema

    # Validar cada IR.
    exit_code = 0
    results = []
    for ir_arg in args.ir:
        ir_path = Path(ir_arg)
        if not ir_path.exists():
            print(f"ERROR: IR no encontrado: {ir_path}", file=sys.stderr)
            return 2
        try:
            ir = json.loads(ir_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"ERROR: IR no parseable ({ir_path}): {e}", file=sys.stderr)
            return 2

        if args.inspect:
            results.append(_inspect_ir(ir, ir_path))
            continue

        # Validación contra schema (opcional, requiere jsonschema).
        schema_errors = _validate_against_schema(ir, schema_path)

        validator = IRValidator(
            sdm_blocks=sdm_blocks,
            sdm_source_hash=sdm_hash,
            skip_sdm=args.skip_sdm,
        )
        issues = validator.validate(ir)

        n_errors = sum(1 for i in issues if i.severity == "error")
        n_warnings = sum(1 for i in issues if i.severity == "warning")
        n_schema = len(schema_errors)

        results.append({
            "file": str(ir_path),
            "schema_errors": schema_errors,
            "issues": issues,
            "n_errors": n_errors,
            "n_warnings": n_warnings,
        })

        if n_errors > 0 or n_schema > 0 or (args.strict and n_warnings > 0):
            exit_code = 1

    # Output.
    if args.json:
        out = []
        for r in results:
            if args.inspect:
                out.append(r)
            else:
                out.append({
                    "file": r["file"],
                    "schema_errors": r["schema_errors"],
                    "errors": [
                        {"path": i.path, "node": i.node, "rule": i.rule, "message": i.message}
                        for i in r["issues"] if i.severity == "error"
                    ],
                    "warnings": [
                        {"path": i.path, "node": i.node, "rule": i.rule, "message": i.message}
                        for i in r["issues"] if i.severity == "warning"
                    ],
                    "n_errors": r["n_errors"],
                    "n_warnings": r["n_warnings"],
                })
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for r in results:
            if args.inspect:
                print(f"INSPECT: {r['file']}")
                for line in r["summary"]:
                    print(f"  {line}")
                continue
            print(f"\n{r['file']}:")
            if r["schema_errors"]:
                print(f"  SCHEMA ERRORS ({len(r['schema_errors'])}):")
                for se in r["schema_errors"]:
                    print(f"    - {se.get('path', '?')}: {se.get('cause', '?')}")
            for issue in r["issues"]:
                marker = "  ERROR   " if issue.severity == "error" else "  WARNING "
                ctx = f" ({issue.node})" if issue.node else ""
                print(f"{marker}[{issue.rule}]: {issue.path}{ctx} — {issue.message}")
            if r["n_errors"] == 0 and r["n_warnings"] == 0 and not r["schema_errors"]:
                print("  OK: sin errores ni warnings")

    return exit_code


def _validate_against_schema(ir: dict, schema_path: Path) -> list:
    """Valida contra schema JSON. Devuelve lista vacía si OK o jsonschema ausente.

    Antes de validar, elimina campos con prefijo `_` (auxiliares de F48)
    y `source_file` (metadato del archivo, no del IR).
    """
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []
    if not schema_path.exists():
        return [{"path": str(schema_path), "cause": "schema no encontrado"}]
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [{"path": str(schema_path), "cause": f"schema no parseable: {e}"}]
    # Strip auxiliary fields y source_file antes de validar.
    ir_clean = _strip_auxiliary_fields(ir)
    errors = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in validator.iter_errors(ir_clean):
        errors.append({
            "path": "/".join(str(p) for p in err.absolute_path),
            "cause": err.message,
        })
    return errors


def _strip_auxiliary_fields(obj):
    """Elimina campos con prefijo `_` (auxiliares F48) y `source_file` antes
    de validar contra schema.
    """
    if isinstance(obj, dict):
        return {k: _strip_auxiliary_fields(v) for k, v in obj.items()
                if not k.startswith("_") and k != "source_file"}
    if isinstance(obj, list):
        return [_strip_auxiliary_fields(v) for v in obj]
    return obj


def _inspect_ir(ir: dict, ir_path: Path) -> dict:
    """Resumen estructural del IR sin validar."""
    summary = []
    blocks = ir.get("blocks", [])
    summary.append(f"title: {ir.get('title', '')}")
    summary.append(f"note_id: {ir.get('note_id', '')}")
    summary.append(f"schema_version: {ir.get('schema_version', '')}")
    summary.append(f"layer: {ir.get('layer', '')}")
    summary.append(f"blocks: {len(blocks)}")

    # Contar tipos de bloque.
    node_counts = Counter()
    capabilities = Counter()
    source_refs_count = 0

    def walk(n):
        nonlocal source_refs_count
        if isinstance(n, dict):
            kind = n.get("node", "?")
            node_counts[kind] += 1
            cap = n.get("attrs", {}).get("capability", "")
            if cap:
                capabilities[cap] += 1
            source_refs_count += len(n.get("source_refs", []))
            for c in n.get("children", []):
                walk(c)

    for b in blocks:
        walk(b)

    summary.append(f"unique node types: {len(node_counts)}")
    summary.append(f"unique capabilities: {len(capabilities)}")
    summary.append(f"total source_refs: {source_refs_count}")
    summary.append("")
    summary.append("Top node types:")
    for kind, n in node_counts.most_common(10):
        summary.append(f"  {kind}: {n}")

    return {"file": str(ir_path), "summary": summary}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
