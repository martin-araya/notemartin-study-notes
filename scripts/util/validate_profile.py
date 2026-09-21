#!/usr/bin/env python3
"""Valida o resuelve un perfil contra `schemas/profile.schema.json`.

Uso:
    python3 validate_profile.py --validate <archivo.yaml>
    python3 validate_profile.py --resolve --empty
    python3 validate_profile.py --resolve --input <archivo.yaml>
    python3 validate_profile.py --help

Modos:
    --validate  Carga el YAML y lo valida contra el esquema.
                exit 0 + "OK" si válido.
                exit 1 + mensaje con ruta del campo si inválido.
                exit 2 si el archivo o el esquema no existen.

    --resolve   Carga defaults del esquema y los aplica a la instancia.
                --empty parte de {}; --input parte del YAML dado.
                Valida recursivamente que el resultado cumple el esquema.
                Serializa a YAML en stdout (o --output).
                exit 0 si todo OK; exit 1 si la resolución produce inválido.

Dependencias: PyYAML, jsonschema. Si faltan, exit 2 con mensaje accionable:
    pip install pyyaml jsonschema
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "skill" / "notemartin-study-notes" / "schemas" / "profile.schema.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


def _import_yaml():
    try:
        import yaml
        return yaml
    except ImportError:
        sys.stderr.write(
            "Dependency missing: PyYAML. Install with `pip install pyyaml`.\n"
        )
        sys.exit(EXIT_USAGE)


def _import_jsonschema():
    try:
        import jsonschema
        return jsonschema
    except ImportError:
        sys.stderr.write(
            "Dependency missing: jsonschema. Install with `pip install jsonschema`.\n"
        )
        sys.exit(EXIT_USAGE)


def load_schema(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"Schema not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> dict:
    yaml = _import_yaml()
    if not path.exists():
        sys.stderr.write(f"YAML not found: {path}\n")
        sys.exit(EXIT_USAGE)
    with path.open(encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    return loaded if loaded is not None else {}


def deref_schema(schema: dict, root: dict) -> dict:
    """Resolve local $ref pointers (#/$defs/...). Handles only `#/$defs/<name>`."""
    if not isinstance(schema, dict):
        return schema
    if "$ref" in schema:
        ref = schema["$ref"]
        # Only support local refs of the form "#/$defs/<name>"
        if ref.startswith("#/$defs/"):
            name = ref.split("/")[-1]
            return deref_schema(root["$defs"][name], root)
        # Unknown ref form: return as-is and let validation catch it
        return schema
    return schema


def resolve_defaults(instance: Any, schema: dict, root: dict | None = None) -> Any:
    """Recursively apply `default` from schema to instance."""
    if not isinstance(schema, dict):
        return instance
    if root is None:
        root = schema
    # Dereference $ref first so we work on the concrete schema
    schema = deref_schema(schema, root)
    if not isinstance(schema, dict):
        return instance
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(instance, dict):
            instance = {}
        properties = schema.get("properties", {})
        result = {}
        # First, copy instance keys that are allowed properties
        for key, value in instance.items():
            if key in properties:
                result[key] = resolve_defaults(value, properties[key], root)
        # Then, fill in defaults for missing keys
        for key, prop_schema in properties.items():
            if key not in result:
                prop_schema = deref_schema(prop_schema, root)
                if "default" in prop_schema:
                    # Recurse on the default in case it's an object/array with nested defaults
                    result[key] = resolve_defaults(prop_schema["default"], prop_schema, root)
                elif "const" in prop_schema:
                    # Const fields (e.g. schema_version) act as implicit defaults
                    result[key] = prop_schema["const"]
                elif prop_schema.get("type") == "object":
                    # Recurse to apply nested defaults (empty starting instance)
                    result[key] = resolve_defaults({}, prop_schema, root)
        return result
    elif schema_type == "array":
        if not isinstance(instance, list):
            instance = []
        items_schema = deref_schema(schema.get("items", {}), root)
        return [resolve_defaults(item, items_schema, root) for item in instance]
    else:
        return instance


def format_path(error) -> str:
    """Format jsonschema ValidationError path as a dotted string."""
    path = list(error.absolute_path) if error.absolute_path else []
    if not path:
        return "<root>"
    return ".".join(str(p) for p in path)


def cmd_validate(args: argparse.Namespace) -> int:
    jsonschema = _import_jsonschema()
    schema = load_schema(args.schema)
    validator_cls = jsonschema.Draft202012Validator
    instance = load_yaml(args.validate)

    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if not errors:
        sys.stdout.write(f"OK — {args.validate} validates against {args.schema.name}\n")
        return EXIT_OK

    sys.stderr.write(f"FAIL — {args.validate} does not validate against {args.schema.name}\n")
    for err in errors:
        sys.stderr.write(f"  - {format_path(err)}: {err.message}\n")
    return EXIT_VALIDATION


def cmd_resolve(args: argparse.Namespace) -> int:
    yaml = _import_yaml()
    jsonschema = _import_jsonschema()
    schema = load_schema(args.schema)

    if args.empty and args.input:
        sys.stderr.write("--empty and --input are mutually exclusive\n")
        return EXIT_USAGE
    if args.empty:
        instance = {}
    elif args.input:
        instance = load_yaml(args.input)
    else:
        sys.stderr.write("--resolve requires --empty or --input\n")
        return EXIT_USAGE

    resolved = resolve_defaults(instance, schema)

    # Re-validate the resolved profile to ensure defaults compose into a valid doc.
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(resolved), key=lambda e: list(e.absolute_path))
    if errors:
        sys.stderr.write("FAIL — resolved profile does not validate (default bug?):\n")
        for err in errors:
            sys.stderr.write(f"  - {format_path(err)}: {err.message}\n")
        return EXIT_VALIDATION

    serialized = yaml.safe_dump(resolved, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: temp + rename
        tmp = args.output.with_suffix(args.output.suffix + ".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.rename(args.output)
        sys.stdout.write(f"OK — resolved profile written to {args.output}\n")
    else:
        sys.stdout.write(serialized)
        if not serialized.endswith("\n"):
            sys.stdout.write("\n")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate_profile.py",
        description="Valida o resuelve un perfil contra profile.schema.json.",
    )
    p.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Ruta al schema JSON (default: {DEFAULT_SCHEMA.relative_to(REPO_ROOT)}).",
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--validate",
        metavar="YAML",
        type=Path,
        help="Valida el archivo YAML contra el schema.",
    )
    mode.add_argument(
        "--resolve",
        action="store_true",
        help="Resuelve defaults y emite el YAML final.",
    )
    p.add_argument(
        "--empty",
        action="store_true",
        help="(con --resolve) parte de una instancia vacía.",
    )
    p.add_argument(
        "--input",
        metavar="YAML",
        type=Path,
        help="(con --resolve) instancia inicial cargada de este YAML.",
    )
    p.add_argument(
        "--output",
        metavar="YAML",
        type=Path,
        help="(con --resolve) escribe a este archivo en lugar de stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.validate:
        return cmd_validate(args)
    if args.resolve:
        return cmd_resolve(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
