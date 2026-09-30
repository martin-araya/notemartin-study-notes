#!/usr/bin/env python3
"""
validate_profile.py — Validador del perfil de usuario (F11).

Modos:
  --note <profile.yaml>     valida un archivo de perfil.
  --notes-dir <dir>         itera archivos *.yaml/*yml del directorio.
  --workdir <dir>           detecta profile.yaml en el workdir.

Reglas:
  V-PROF-01 target desconocido
  V-PROF-02 default faltante para target activo
  V-PROF-03 override mal formado (tipo inválido)
  V-PROF-04 product-version ausente en profile de docs técnicas
  V-PROF-05 idioma no soportado
  V-PROF-06 ocr_engine desconocido

Exit: 0 sin issues / 2 warnings / 1 errors / 3 uso.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

# Targets activos soportados (subset cerrado de los 7 destinos del pipeline).
KNOWN_TARGETS = {
    "obsidian",
    "notion_api",
    "notion_md",
    "appflowy",
    "markdown",
    "html_pdf",
    "flashcards",
}

KNOWN_LANGUAGES = {
    "es", "en", "es-en", "en-es", "fr", "de", "pt", "ja", "zh",
}

KNOWN_OCR_ENGINES = {
    "tesseract",
    "easyocr",
    "paddleocr",
    "auto",
}

DEFAULTS_REQUIRED_KEYS = {
    "targets",
    "language",
    "ocr_engine",
    "ocr_languages",
    "notes",
}


def load_yaml(path: Path) -> dict:
    """Carga YAML con fallback mínimo (sólo las claves que validamos)."""
    try:
        import yaml  # type: ignore
    except ImportError:
        # Fallback: parser ad-hoc muy limitado.
        return _minimal_yaml(path)
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _minimal_yaml(path: Path) -> dict:
    """Fallback si PyYAML no está instalado: parser superficial de claves."""
    out: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("#"):
            k, _, v = line.partition(":")
            v = v.strip().strip('"').strip("'")
            if v:
                out[k.strip()] = v
    return out


def check_profile(path: Path, data: dict, issues: list) -> None:
    rel = str(path)

    # V-PROF-01 target desconocido.
    targets = data.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if t not in KNOWN_TARGETS:
                issues.append({
                    "rule_id": "V-PROF-01",
                    "severity": "error",
                    "message": f"target desconocido: {t!r} (soportados: {sorted(KNOWN_TARGETS)})",
                    "file": rel,
                    "node": "targets",
                    "fix_hint": f"usa uno de {sorted(KNOWN_TARGETS)}",
                })

    # V-PROF-02 default faltante.
    if isinstance(data, dict):
        for key in DEFAULTS_REQUIRED_KEYS:
            if key not in data:
                issues.append({
                    "rule_id": "V-PROF-02",
                    "severity": "warning",
                    "message": f"default ausente: {key!r}",
                    "file": rel,
                    "node": key,
                    "fix_hint": f"añade {key}: con su default en profile.template.yaml",
                })

    # V-PROF-03 override mal formado.
    overrides = data.get("overrides")
    if overrides is not None and not isinstance(overrides, dict):
        issues.append({
            "rule_id": "V-PROF-03",
            "severity": "error",
            "message": f"overrides debe ser dict, es {type(overrides).__name__}",
            "file": rel,
            "node": "overrides",
            "fix_hint": "estructura: overrides: {dominio: {clave: valor}}",
        })

    # V-PROF-04 product-version ausente en profile de docs técnicas.
    if data.get("language") in ("es", "en", "es-en", "en-es") and "product_version" in data:
        pv = data["product_version"]
        if pv in (None, "", "null"):
            issues.append({
                "rule_id": "V-PROF-04",
                "severity": "warning",
                "message": "product_version vacío en perfil de documentación técnica",
                "file": rel,
                "node": "product_version",
                "fix_hint": "declara la versión del producto (semver)",
            })

    # V-PROF-05 idioma no soportado.
    lang = data.get("language")
    if lang is not None and lang not in KNOWN_LANGUAGES:
        issues.append({
            "rule_id": "V-PROF-05",
            "severity": "error",
            "message": f"idioma no soportado: {lang!r}",
            "file": rel,
            "node": "language",
            "fix_hint": f"usa uno de {sorted(KNOWN_LANGUAGES)}",
        })

    # V-PROF-06 ocr_engine desconocido.
    engine = data.get("ocr_engine")
    if engine is not None and engine not in KNOWN_OCR_ENGINES:
        issues.append({
            "rule_id": "V-PROF-06",
            "severity": "error",
            "message": f"ocr_engine desconocido: {engine!r}",
            "file": rel,
            "node": "ocr_engine",
            "fix_hint": f"usa uno de {sorted(KNOWN_OCR_ENGINES)}",
        })


def build_report(target: str, issues: list, started: datetime, duration_ms: int) -> dict:
    summary = {"errors": 0, "warnings": 0, "info": 0}
    for it in issues:
        summary[it["severity"] + "s" if it["severity"] != "info" else "info"] = \
            summary.get(it["severity"] + "s" if it["severity"] != "info" else "info", 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "validate_profile",
        "target": target,
        "started_at": started.isoformat(),
        "duration_ms": duration_ms,
        "summary": {
            "errors": sum(1 for i in issues if i["severity"] == "error"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--note", help="profile.yaml a validar")
    grp.add_argument("--notes-dir", help="directorio con perfiles")
    grp.add_argument("--workdir", help=".notes-work/<hash>/")
    parser.add_argument("--json", action="store_true", help="emit JSON al final")
    parser.add_argument("--out", help="ruta del JSON de salida")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    issues: list = []
    targets_to_check: list[Path] = []

    if args.note:
        p = Path(args.note)
        if not p.is_file():
            print(f"ERROR: no existe {p}", file=sys.stderr)
            return 3
        targets_to_check = [p]
    elif args.notes_dir:
        d = Path(args.notes_dir)
        if not d.is_dir():
            print(f"ERROR: no existe {d}", file=sys.stderr)
            return 3
        targets_to_check = sorted(
            list(d.rglob("*.yaml")) + list(d.rglob("*.yml"))
        )
    else:
        d = Path(args.workdir)
        p = d / "profile.yaml"
        if p.is_file():
            targets_to_check = [p]
        else:
            print(f"ERROR: no hay profile.yaml en {d}", file=sys.stderr)
            return 3

    for p in targets_to_check:
        try:
            data = load_yaml(p)
        except Exception as e:
            issues.append({
                "rule_id": "V-PROF-99",
                "severity": "error",
                "message": f"YAML inválido: {e}",
                "file": str(p),
                "node": "<root>",
                "fix_hint": "verifica indentación y comillas",
            })
            continue
        check_profile(p, data, issues)

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = build_report(
        args.note or args.notes_dir or args.workdir,
        issues, started, duration_ms,
    )

    if args.json or args.out:
        out = json.dumps(report, indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out)
    else:
        for it in issues:
            print(f"[{it['severity'].upper():7}] {it['rule_id']} {it['file']}:{it['node']} — {it['message']}")
        print(f"\n{len(issues)} issues", file=sys.stderr)

    has_error = any(i["severity"] == "error" for i in issues)
    has_warn = any(i["severity"] == "warning" for i in issues)
    if has_error:
        return 1
    if has_warn:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())