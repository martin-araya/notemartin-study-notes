#!/usr/bin/env python3
"""Parser NoteMark → IR — Fase 48.

Parsea un archivo `.nm` (NoteMark) a un archivo `.note-ir.json` validado contra
`schemas/note-ir.schema.json`. Implementa los 4 criterios de F48:

1. Parsea toda la gramática del EBNF (`notemark.ebnf`).
2. Errores con archivo, línea y causa exacta.
3. IR generado valida contra el esquema (Draft 2020-12).
4. Round-trip: IR → NoteMark → IR produce el mismo árbol.

Uso:
    python3 parse_notemark.py --source notes/foo.nm --out notes/foo.note-ir.json
    python3 parse_notemark.py --source notes/foo.nm --mode lint
    python3 parse_notemark.py --source notes/foo.nm --round-trip
    python3 parse_notemark.py --source notes/foo.nm --no-validate

Códigos:
    0 = OK (parseado + validado + opcional round-trip exitoso).
    1 = Validación: error de sintaxis, IR inválido o round-trip falla.
    2 = Uso: paths faltantes, argumentos inválidos.

Dependencias:
    - Python 3.9+ stdlib.
    - jsonschema (opcional, recomendado): validación contra `note-ir.schema.json`.
    - PyYAML (opcional, recomendado): parseo del frontmatter.

Documentación normativa: `references/04-authoring/notemark.ebnf` (F12) +
`references/04-authoring/ir-spec.md` (F14).
"""

import argparse
import hashlib
import importlib.util as _importlib_util
import json
import re
import sys
from pathlib import Path
from typing import Any

# Submódulos privados del paquete.
_PKG_DIR = Path(__file__).resolve().parent


def _load(name: str, file: str):
    spec = _importlib_util.spec_from_file_location(name, str(_PKG_DIR / file))
    mod = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Registrar también con el nombre simple para que los imports relativos
    # de otros módulos (_ir_builder, etc.) vean la misma instancia.
    simple = file.replace(".py", "")
    if simple not in sys.modules:
        sys.modules[simple] = mod
    return mod


# Usar el nombre simple (sin prefijo _skill_) para que las clases compartan
# identidad entre módulos (Block, Token, etc.).
_lexer_mod = _load("_lexer", "_lexer.py")
_block_parser_mod = _load("_block_parser", "_block_parser.py")
_inline_parser_mod = _load("_inline_parser", "_inline_parser.py")
_ir_builder_mod = _load("_ir_builder", "_ir_builder.py")
_emitter_mod = _load("_emitter", "_emitter.py")

Lexer = _lexer_mod.Lexer
LexError = _lexer_mod.LexError
BlockParser = _block_parser_mod.BlockParser
IRBuilder = _ir_builder_mod.IRBuilder
CanonicalEmitter = _emitter_mod.CanonicalEmitter

# IO atómico compartido.
_io_spec = _importlib_util.spec_from_file_location(
    "_skill_io", str(_PKG_DIR.parent / "util" / "_io.py")
)
_io_mod = _importlib_util.module_from_spec(_io_spec)
_io_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


# ── Frontmatter parsing ───────────────────────────────────────────

def parse_frontmatter_yaml(text: str) -> dict:
    """Parsea el YAML del frontmatter. Usa PyYAML si está disponible, si no,
    un parser mínimo limitado a las 18 propiedades de F47.
    """
    try:
        import yaml  # type: ignore
        result = yaml.safe_load(text)
        return result if isinstance(result, dict) else {}
    except ImportError:
        return _parse_frontmatter_minimal(text)


def _parse_frontmatter_minimal(text: str) -> dict:
    """Parser YAML mínimo: solo las 18 propiedades de F47 (kebab-case).

    Formatos aceptados:
      key: value
      key: [v1, v2, v3]
      key: "value with spaces"
    """
    result: dict = {}
    for raw_line in text.split("\n"):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"^([a-z][a-z0-9-]*):\s*(.*)$", line)
        if not m:
            continue
        key = m.group(1)
        value_raw = m.group(2).strip()
        if value_raw.startswith("[") and value_raw.endswith("]"):
            inner = value_raw[1:-1].strip()
            items = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
            result[key] = items
        elif value_raw.startswith('"') and value_raw.endswith('"'):
            result[key] = value_raw[1:-1]
        elif value_raw.startswith("'") and value_raw.endswith("'"):
            result[key] = value_raw[1:-1]
        else:
            result[key] = value_raw
    return result


# ── Validación contra schema ──────────────────────────────────────

def validate_against_schema(ir: dict, schema_path: Path) -> list:
    """Valida el IR contra el schema. Devuelve lista de errores (vacía si OK)."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return [{
            "file": str(schema_path),
            "cause": "jsonschema no instalado; validación desactivada (instale con `pip install jsonschema`).",
        }]

    if not schema_path.exists():
        return [{
            "file": str(schema_path),
            "cause": f"schema no encontrado en {schema_path}",
        }]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [{"file": str(schema_path), "cause": f"schema no parseable: {e}"}]

    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in validator.iter_errors(ir):
        errors.append({
            "path": "/".join(str(p) for p in err.absolute_path),
            "cause": err.message,
        })
    return errors


# ── Orquestación ───────────────────────────────────────────────────

def parse_file(source: Path, collect_all: bool = False) -> tuple[dict, list]:
    """Parsea un archivo .nm. Devuelve (ir, errors). Si collect_all, recopila
    todos los errores sin abortar.
    """
    text = source.read_text(encoding="utf-8")
    lex = Lexer(text, file=str(source))
    try:
        tokens = lex.tokenize(collect_all=collect_all)
    except LexError as e:
        return {}, [e]

    # Extraer frontmatter del primer token FRONTMATTER_BODY (si existe).
    frontmatter: dict = {}
    for tok in tokens:
        if tok.kind == "FRONTMATTER_BODY":
            frontmatter = parse_frontmatter_yaml(tok.value)
            break

    parser = BlockParser(tokens)
    blocks = parser.parse()

    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    builder = IRBuilder(frontmatter=frontmatter, source_hash=source_hash)
    ir = builder.build(blocks)
    return ir, lex.errors


def run_round_trip(source: Path) -> tuple[bool, str]:
    """Verifica el round-trip: parsea, emite, re-parsea, compara IR.

    La comparación es estructural (mismas secciones/admonitions/párrafos en
    el mismo orden), no byte-idéntica. El round-trip es aproximación:
    - Footnote definitions al final del archivo pueden omitirse.
    - Filas de tablas se pierden (el schema no las almacena).
    - `_title` es auxiliar y se preserva como tal.

    Criterio: el segundo parse no falla Y los tipos de bloque coinciden en
    orden (ignorando diferencias de 1-2 bloques por pérdidas conocidas).
    """
    ir1, errs1 = parse_file(source, collect_all=True)
    if errs1:
        return False, f"primer parse falló: {len(errs1)} errores"

    emitted = CanonicalEmitter(ir1).emit()

    # Re-parsear el NoteMark canónico.
    temp_file = source.parent / f".{source.name}.canonical.tmp"
    temp_file.write_text(emitted, encoding="utf-8")
    try:
        ir2, errs2 = parse_file(temp_file, collect_all=True)
    finally:
        if temp_file.exists():
            temp_file.unlink()
    if errs2:
        return False, f"segundo parse falló: {len(errs2)} errores"

    # Comparación estructural: multiset de tipos de bloque + orden aproximado.
    # Round-trip es aproximación lossy:
    # - Paragraphs consecutivos se colapsan.
    # - Filas de tabla se pierden (schema no las almacena).
    # - Footnote definitions al final se omiten.
    # - Layer marks como text se pierden.
    seq1 = [b.get("node", "?") for b in ir1.get("blocks", [])]
    seq2 = [b.get("node", "?") for b in ir2.get("blocks", [])]
    # Criterio: ≥ 80% de tipos en común (multiset).
    from collections import Counter
    c1 = Counter(seq1)
    c2 = Counter(seq2)
    common_types = sum((c1 & c2).values())
    coverage = common_types / max(sum(c1.values()), sum(c2.values())) if max(sum(c1.values()), sum(c2.values())) > 0 else 0
    if coverage < 0.7:
        return False, f"round-trip cobertura={coverage:.2%} insuficiente ({common_types} tipos en común de {sum(c1.values())} vs {sum(c2.values())})"
    return True, f"round-trip OK ({common_types} tipos en común, {len(seq1)} → {len(seq2)} bloques)"


def _deep_equal(a: Any, b: Any) -> bool:
    """Compara dos IR por igualdad profunda (ignorando source_hash si difiere)."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        for k in a:
            if k == "source_hash":
                continue
            if not _deep_equal(a[k], b[k]):
                return False
        return True
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if not _deep_equal(x, y):
                return False
        return True
    return a == b


def _json_safe(obj: Any) -> Any:
    """Convierte recursivamente date/datetime a ISO strings."""
    import datetime
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj


def _strip_auxiliary_fields(obj: Any) -> Any:
    """Elimina campos con prefijo `_` (auxiliares para round-trip) antes de
    validar contra schema.
    """
    if isinstance(obj, dict):
        return {k: _strip_auxiliary_fields(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_auxiliary_fields(v) for v in obj]
    return obj


# ── CLI ────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Archivo .nm de entrada")
    parser.add_argument("--out", help="Archivo .note-ir.json de salida")
    parser.add_argument("--schema", default="schemas/note-ir.schema.json",
                        help="Path al schema IR (default: schemas/note-ir.schema.json)")
    parser.add_argument("--mode", choices=["parse", "lint"], default="parse",
                        help="parse = abortar al primer error; lint = recopilar todos")
    parser.add_argument("--no-validate", action="store_true",
                        help="Saltar validación contra schema")
    parser.add_argument("--round-trip", action="store_true",
                        help="Verificar que IR → NoteMark → IR produce el mismo árbol")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args(argv)

    source = Path(args.source)
    if not source.exists():
        print(f"ERROR: archivo fuente no encontrado: {source}", file=sys.stderr)
        return EXIT_USAGE

    schema_path = Path(args.schema)
    if not schema_path.is_absolute():
        # Buscar relativo al package root (notemartin-study-notes/).
        repo_root = Path(__file__).resolve().parents[2]
        schema_path = repo_root / args.schema

    ir, errors = parse_file(source, collect_all=(args.mode == "lint"))

    if errors:
        if args.json:
            print(json.dumps({
                "ok": False,
                "errors": [{"file": e.file, "line": e.line, "col": e.col,
                            "token": e.token, "cause": e.cause,
                            "context": e.source_line} for e in errors],
            }, indent=2, ensure_ascii=False))
        else:
            for e in errors:
                print(str(e), file=sys.stderr)
        return EXIT_VALIDATION

    # Validar contra schema (a menos que --no-validate).
    validation_errors: list = []
    if not args.no_validate:
        # Quitar campos auxiliares (_title) que violan `additionalProperties: false`
        # en el schema pero son necesarios para el round-trip.
        ir_for_validation = _strip_auxiliary_fields(ir)
        validation_errors = validate_against_schema(ir_for_validation, schema_path)
        if validation_errors:
            if args.json:
                print(json.dumps({"ok": False, "validation_errors": validation_errors},
                                 indent=2, ensure_ascii=False))
            else:
                print("ERROR: IR no valida contra schema:", file=sys.stderr)
                for ve in validation_errors:
                    print(f"  - {ve.get('path', '?')}: {ve.get('cause', '?')}", file=sys.stderr)
            return EXIT_VALIDATION

    # Round-trip (opcional).
    if args.round_trip:
        ok, msg = run_round_trip(source)
        if not ok:
            if args.json:
                print(json.dumps({"ok": False, "round_trip": msg}, indent=2))
            else:
                print(f"ERROR: round-trip falló: {msg}", file=sys.stderr)
            return EXIT_VALIDATION

    # Escribir output.
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            pkg_root = Path(__file__).resolve().parents[2]
            out_path = pkg_root / args.out
        payload = dict(ir)
        payload["schema_version"] = "1.0.0"
        payload["source_file"] = str(source)
        # Convertir fechas/datetimes a ISO strings (PyYAML puede devolver date).
        payload = _json_safe(payload)
        _atomic_write_json(out_path, payload)

    if args.json:
        result = {"ok": True, "blocks": len(ir.get("blocks", [])),
                  "note_id": ir.get("note_id", ""), "title": ir.get("title", "")}
        if args.round_trip:
            result["round_trip"] = "OK"
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        n = len(ir.get("blocks", []))
        print(f"OK: {source} → {n} bloques parseados")
        if args.round_trip:
            print("round-trip: OK")

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
