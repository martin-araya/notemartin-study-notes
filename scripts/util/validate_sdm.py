#!/usr/bin/env python3
"""Valida SDMs contra `schemas/sdm.schema.json` y la fórmula de ids.

Uso:
    python3 validate_sdm.py --validate <sdm.json> [<sdm.json> ...]
    python3 validate_sdm.py --id <source_hash> <section_path> <block_index>
    python3 validate_sdm.py --help

Modos:
    --validate   Carga cada SDM, valida contra el schema, recomputa cada id
                 con la fórmula del spec §8, verifica presencia de anchor y
                 la regla "ocr ⇒ confidence < 1.0".
                 exit 0 + "OK <path>" por archivo si todo pasa.
                 exit 1 + mensaje de error si alguno falla.
                 exit 2 si el schema o un archivo no existen.

    --id         Imprime el id generado por la fórmula
                 sha1(source_hash + section_path + str(block_index))[:12].
                 Útil para inspección y para verificar determinismo
                 (dos ejecuciones idénticas byte a byte).
                 exit 0 siempre.

Dependencias: PyYAML (no se usa aquí pero es el patrón de Fase 11),
jsonschema. Si faltan, exit 2 con mensaje accionable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "skill" / "notemartin-study-notes" / "schemas" / "sdm.schema.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


def _import_jsonschema():
    try:
        import jsonschema
        return jsonschema
    except ImportError:
        sys.stderr.write(
            "Dependency missing: jsonschema. Install with `pip install jsonschema`.\n"
        )
        sys.exit(EXIT_USAGE)


def compute_block_id(source_hash: str, section_path: str, block_index: int) -> str:
    """sha1(source_hash + section_path + str(block_index))[:12]."""
    h = hashlib.sha1()
    h.update(source_hash.encode("utf-8"))
    h.update(section_path.encode("utf-8"))
    h.update(str(block_index).encode("utf-8"))
    return h.hexdigest()[:12]


def load_schema(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"Schema not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_sdm(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"SDM not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def iter_blocks(sdm: dict):
    """Yield (section_path, block_index, block) for every block in the SDM."""
    for section in sdm.get("sections", []):
        section_path = section["section_path"]
        for idx, block in enumerate(section.get("blocks", [])):
            yield section_path, idx, block


def format_path(section_path: str, idx: int, field: str | None = None) -> str:
    suffix = f".{field}" if field else ""
    return f"section={section_path!r}[{idx}]{suffix}"


def validate_one(path: Path, schema: dict, jsonschema) -> list[str]:
    """Return a list of error messages (empty if all OK)."""
    errors: list[str] = []
    sdm = load_sdm(path)

    # Schema validation
    validator = jsonschema.Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(sdm), key=lambda e: list(e.absolute_path))
    for err in schema_errors:
        errors.append(f"  - schema: {err.message} (path={list(err.absolute_path)})")

    # ID recomputation + content rules
    source_hash = sdm.get("source", {}).get("hash")
    if not source_hash:
        errors.append("  - source.hash ausente (no se puede recomputar ids)")
        return errors

    for section_path, idx, block in iter_blocks(sdm):
        # ID recomputation
        expected_id = compute_block_id(source_hash, section_path, idx)
        declared_id = block.get("id")
        if declared_id != expected_id:
            errors.append(
                f"  - {format_path(section_path, idx, 'id')}: declarado={declared_id!r} != esperado={expected_id!r}"
            )

        # Anchor presence (criteria 3)
        anchor = block.get("anchor")
        if not isinstance(anchor, dict):
            errors.append(f"  - {format_path(section_path, idx)}: anchor ausente o no es objeto")
        else:
            if "page" not in anchor:
                errors.append(f"  - {format_path(section_path, idx, 'anchor.page')}: ausente")
            if "section_path" not in anchor:
                errors.append(f"  - {format_path(section_path, idx, 'anchor.section_path')}: ausente")

        # OCR confidence rule (criteria 4)
        origin = block.get("origin")
        confidence = block.get("confidence")
        if origin == "ocr":
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence < 1.0):
                errors.append(
                    f"  - {format_path(section_path, idx, 'confidence')}: ocr ⇒ debe estar en [0, 1); valor={confidence!r}"
                )
        elif origin == "native":
            if confidence != 1.0:
                errors.append(
                    f"  - {format_path(section_path, idx, 'confidence')}: native ⇒ debe ser 1.0; valor={confidence!r}"
                )

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    jsonschema = _import_jsonschema()
    schema = load_schema(args.schema)
    any_fail = False
    for path in args.validate:
        errs = validate_one(path, schema, jsonschema)
        if errs:
            any_fail = True
            sys.stderr.write(f"FAIL — {path}\n")
            for e in errs:
                sys.stderr.write(e + "\n")
        else:
            sys.stdout.write(f"OK — {path}\n")
    return EXIT_VALIDATION if any_fail else EXIT_OK


def cmd_id(args: argparse.Namespace) -> int:
    block_id = compute_block_id(args.source_hash, args.section_path, args.block_index)
    sys.stdout.write(f"{block_id}\n")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate_sdm.py",
        description="Valida SDMs contra sdm.schema.json y/o computa ids.",
    )
    p.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Ruta al schema (default: {DEFAULT_SCHEMA.relative_to(REPO_ROOT)}).",
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--validate",
        metavar="SDM",
        type=Path,
        nargs="+",
        help="Valida uno o más archivos SDM.",
    )
    mode.add_argument(
        "--id",
        action="store_true",
        help="Imprime el id generado por la fórmula sha1(hash + path + idx)[:12].",
    )
    pid = p.add_argument_group("--id options")
    pid.add_argument(
        "source_hash",
        nargs="?",
        help="(con --id) sha256 hex del source.",
    )
    pid.add_argument(
        "section_path",
        nargs="?",
        help="(con --id) section_path del bloque.",
    )
    pid.add_argument(
        "block_index",
        type=int,
        nargs="?",
        help="(con --id) índice 0-based del bloque dentro de la sección.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.id:
        if args.source_hash is None or args.section_path is None or args.block_index is None:
            sys.stderr.write("--id requiere source_hash section_path block_index\n")
            return EXIT_USAGE
        return cmd_id(args)
    if args.validate:
        return cmd_validate(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
