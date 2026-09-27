#!/usr/bin/env python3
"""publishing.py — F62 · CLI de publicación idempotente.

Workflow:
  - plan    → dry-run; muestra qué se crearía/actualizaría/saltaría/bloquearía.
  - publish → ejecuta; usa manifest para idempotencia.
  - status  → muestra el estado del manifest.
  - mark-edited → marca manualmente una nota como editada a mano.

Implementa los 3 criterios de F62:
  - C1: republicar N notas actualiza N, no crea N (post-primer-publish).
  - C2: páginas editadas a mano se bloquean sin `--confirm-overwrite`.
  - C3: publicación parcial — solo se tocan las notas con `ir_sha256` cambiado.

Dependencias: Python 3.9+ stdlib puro.
Códigos de salida: 0 OK · 1 error fatal · 2 OK con bloqueos.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


_HERE = Path(__file__).resolve().parent


# Comparte atomic_write_json / atomic_write_text con F38+.
def _import_io():
    spec = _importlib_util.spec_from_file_location(
        "_skill_io",
        _HERE.parent / "util" / "_io.py",
    )
    mod = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_io_mod = _import_io()
_atomic_write_json = _io_mod.atomic_write_json
_atomic_write_text = _io_mod.atomic_write_text


# Importa el módulo sibling _manifest.py.
_spec_m = _importlib_util.spec_from_file_location(
    "_manifest", _HERE / "_manifest.py"
)
_mod_m = _importlib_util.module_from_spec(_spec_m)
_spec_m.loader.exec_module(_mod_m)
Manifest = _mod_m.Manifest
PublishEntry = _mod_m.PublishEntry
sha256_hex = _mod_m.sha256_hex


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Mapeo destino → (render_subdir, file_extension).
DEST_FILE_INFO: Dict[str, Tuple[str, str]] = {
    "obsidian": ("obsidian", ".md"),
    "notion_md": ("notion_md", ".md"),
    "appflowy": ("appflowy", ".md"),
    "markdown": ("markdown", ".md"),
    "html_pdf": ("html_pdf", ".html"),
}

EXIT_OK = 0
EXIT_FATAL = 1
EXIT_WARN = 2

USER_CONTENT_START = "<!-- user-content-start -->"
USER_CONTENT_END = "<!-- user-content-end -->"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_irs(ir_arg: Path) -> List[Dict[str, Any]]:
    if ir_arg.is_dir():
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(ir_arg.glob("*.json"))]
    return [json.loads(ir_arg.read_text(encoding="utf-8"))]


def _sha256_of_ir(ir_obj: Any) -> str:
    canonical = json.dumps(ir_obj, sort_keys=True, ensure_ascii=False)
    return sha256_hex(canonical.encode("utf-8"))


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return sha256_hex(path.read_bytes())


def _read_user_content(remote_path: Path) -> Optional[str]:
    """Extrae el bloque `<!-- user-content-start -->...<!-- user-content-end -->`."""
    if not remote_path.exists():
        return None
    content = remote_path.read_text(encoding="utf-8", errors="replace")
    if USER_CONTENT_START not in content or USER_CONTENT_END not in content:
        return None
    start = content.index(USER_CONTENT_START) + len(USER_CONTENT_START)
    end = content.index(USER_CONTENT_END, start)
    block = content[start:end].strip()
    return block if block else None


def _merge_user_content(generated: str, user_block: Optional[str]) -> str:
    """Añade el bloque user-content al final del contenido generado."""
    if not user_block:
        return generated
    return f"{generated.rstrip()}\n\n{USER_CONTENT_START}\n{user_block}\n{USER_CONTENT_END}\n"


def _extract_user_content_for_storage(remote_path: Path) -> str:
    """Lee el bloque user-content y lo devuelve para almacenarlo en el manifest.

    Si el archivo no existe o no tiene el bloque, devuelve "".
    """
    block = _read_user_content(remote_path)
    return block if block else ""


# ---------------------------------------------------------------------------
# Plan / Publish
# ---------------------------------------------------------------------------


def detect_edited_by_hand(
    note_id: str,
    destination: str,
    manifest_entry: PublishEntry,
    out_dir: Path,
) -> bool:
    """Detecta si el archivo remoto fue editado a mano comparando hashes.

    Para destinos file-based, calcula sha256 del archivo actual y compara
    con `manifest_entry.remote_hash`. Si difieren → editado a mano.
    Devuelve True si fue editado a mano, False en caso contrario.
    """
    if destination not in DEST_FILE_INFO:
        return False
    subdir, ext = DEST_FILE_INFO[destination]
    target_path = out_dir / "render" / subdir / f"{note_id}{ext}"
    if not target_path.exists():
        return False
    current_hash = _file_hash(target_path)
    if not manifest_entry.remote_hash:
        return False
    return current_hash != manifest_entry.remote_hash


def compute_actions(
    ir_list: List[Dict[str, Any]],
    manifest: Manifest,
    destinations: List[str],
    out_dir: Path,
    confirm_overwrite: bool,
    force_keep_comments: bool,
) -> Dict[str, Any]:
    """Determina acciones a tomar (sin ejecutar)."""
    actions: Dict[str, List[Dict[str, Any]]] = {
        "created": [], "updated": [], "skipped": [], "blocked": [], "errors": [],
    }

    for ir_obj in ir_list:
        note_id = str(ir_obj.get("note_id", ""))
        ir_sha = _sha256_of_ir(ir_obj)
        for dest in destinations:
            entry = manifest.get(note_id, dest)
            if entry is None:
                actions["created"].append({
                    "note_id": note_id, "destination": dest,
                    "reason": "no entry in manifest",
                })
                continue
            if entry.ir_sha256 == ir_sha:
                actions["skipped"].append({
                    "note_id": note_id, "destination": dest,
                    "reason": "ir_sha256 unchanged",
                    "ir_sha256": ir_sha,
                })
                continue
            # Auto-detección de edited_by_hand por hash.
            if not entry.edited_by_hand:
                if detect_edited_by_hand(note_id, dest, entry, out_dir):
                    entry.edited_by_hand = True
            if entry.edited_by_hand and not confirm_overwrite:
                actions["blocked"].append({
                    "note_id": note_id, "destination": dest,
                    "reason": "edited_by_hand (use --confirm-overwrite to force)",
                    "remote_hash": entry.remote_hash,
                    "last_published_at": entry.last_published_at,
                })
                continue
            actions["updated"].append({
                "note_id": note_id, "destination": dest,
                "old_ir_sha256": entry.ir_sha256,
                "new_ir_sha256": ir_sha,
                "edited_by_hand": entry.edited_by_hand,
                "force_keep_comments": entry.edited_by_hand and force_keep_comments,
            })
    return actions


def execute_publish(
    ir_list: List[Dict[str, Any]],
    actions: Dict[str, Any],
    manifest: Manifest,
    destinations: List[str],
    out_dir: Path,
    confirm_overwrite: bool,
    force_keep_comments: bool,
) -> Tuple[Dict[str, Any], Manifest]:
    """Ejecuta el publish según las acciones calculadas."""
    ir_by_id = {str(ir.get("note_id", "")): ir for ir in ir_list}
    executed: Dict[str, List[Dict[str, Any]]] = {
        "created": [], "updated": [], "skipped": [], "blocked": [], "errors": [],
    }

    for action_list, action_type in [
        (actions["created"], "created"),
        (actions["updated"], "updated"),
    ]:
        for action in action_list:
            note_id = action["note_id"]
            dest = action["destination"]
            ir_obj = ir_by_id.get(note_id)
            if not ir_obj:
                continue
            ir_sha = _sha256_of_ir(ir_obj)

            subdir, ext = DEST_FILE_INFO[dest]
            target_dir = out_dir / "render" / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{note_id}{ext}"

            if not target_path.exists():
                executed["errors"].append({
                    "note_id": note_id, "destination": dest,
                    "reason": f"render artifact not found: {target_path}",
                })
                continue
            generated = target_path.read_text(encoding="utf-8", errors="replace")

            user_block: Optional[str] = None
            if action.get("force_keep_comments"):
                user_block = _read_user_content(target_path)

            # Si el manifest ya tiene user_content previo, también preservarlo.
            existing_entry = manifest.get(note_id, dest)
            stored_user_content = existing_entry.user_content if existing_entry else ""
            if stored_user_content and not user_block:
                user_block = stored_user_content

            final_content = _merge_user_content(generated, user_block)

            try:
                _atomic_write_text(target_path, final_content)
            except OSError as e:
                executed["errors"].append({
                    "note_id": note_id, "destination": dest,
                    "reason": f"write failed: {e}",
                })
                continue

            new_hash = _file_hash(target_path)
            # Almacenar user-content para próximos publishes.
            new_user_content = user_block if user_block else stored_user_content
            entry = PublishEntry(
                note_id=note_id,
                destination=dest,
                remote_id=str(target_path.relative_to(out_dir)),
                remote_hash=new_hash,
                ir_sha256=ir_sha,
                last_published_at=_now_utc_iso(),
                edited_by_hand=False,
                user_content=new_user_content,
            )
            manifest.upsert(entry)
            executed[action_type].append({
                "note_id": note_id, "destination": dest,
                "remote_id": entry.remote_id,
                "remote_hash": new_hash,
            })

    executed["skipped"] = list(actions["skipped"])
    executed["blocked"] = list(actions["blocked"])
    return executed, manifest


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------


def build_report(executed: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    summary = {
        "created": len(executed["created"]),
        "updated": len(executed["updated"]),
        "skipped": len(executed["skipped"]),
        "blocked": len(executed["blocked"]),
        "errors": len(executed["errors"]),
    }
    report = {
        "schema_version": "1.0.0",
        "generated_at": _now_utc_iso(),
        "summary": summary,
        "created": executed["created"],
        "updated": executed["updated"],
        "skipped": executed["skipped"],
        "blocked": executed["blocked"],
        "errors": executed["errors"],
    }
    md_lines = [
        "# Reporte de publicación — F62",
        "",
        f"- **generated_at:** {report['generated_at']}",
        "",
        "## Resumen",
        "",
        "| Acción | Cuenta |",
        "|---|---|",
        f"| Creadas | {summary['created']} |",
        f"| Actualizadas | {summary['updated']} |",
        f"| Saltadas (sin cambios) | {summary['skipped']} |",
        f"| Bloqueadas (editadas a mano) | {summary['blocked']} |",
        f"| Errores | {summary['errors']} |",
        "",
    ]
    if executed["created"]:
        md_lines.append("## Creadas")
        md_lines.append("")
        for c in executed["created"]:
            md_lines.append(f"- `{c['note_id']}` → `{c['destination']}` (remote_id: `{c.get('remote_id', '')}`)")
        md_lines.append("")
    if executed["updated"]:
        md_lines.append("## Actualizadas")
        md_lines.append("")
        for u in executed["updated"]:
            md_lines.append(f"- `{u['note_id']}` → `{u['destination']}` (remote_id: `{u.get('remote_id', '')}`)")
        md_lines.append("")
    if executed["skipped"]:
        md_lines.append("## Saltadas (sin cambios)")
        md_lines.append("")
        for s in executed["skipped"]:
            md_lines.append(f"- `{s['note_id']}` → `{s['destination']}`: {s['reason']}")
        md_lines.append("")
    if executed["blocked"]:
        md_lines.append("## Bloqueadas (editadas a mano)")
        md_lines.append("")
        for b in executed["blocked"]:
            md_lines.append(f"- `{b['note_id']}` → `{b['destination']}`: {b['reason']}")
        md_lines.append("")
    if executed["errors"]:
        md_lines.append("## Errores")
        md_lines.append("")
        for e in executed["errors"]:
            md_lines.append(f"- `{e['note_id']}` → `{e['destination']}`: {e['reason']}")
        md_lines.append("")
    return report, "\n".join(md_lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_destinations(raw: str) -> List[str]:
    return [d.strip() for d in raw.split(",") if d.strip()]


def cmd_plan(args: argparse.Namespace) -> int:
    ir_list = _load_irs(args.ir)
    manifest = Manifest.load(args.out_dir)
    destinations = _parse_destinations(args.destinations)
    actions = compute_actions(
        ir_list, manifest, destinations, args.out_dir,
        args.confirm_overwrite, args.force_manual_keep_comments,
    )
    report, _ = build_report({**{k: [] for k in
                                   ["created", "updated", "skipped",
                                    "blocked", "errors"]},
                              **actions})
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    ir_list = _load_irs(args.ir)
    manifest = Manifest.load(args.out_dir)
    destinations = _parse_destinations(args.destinations)
    actions = compute_actions(
        ir_list, manifest, destinations, args.out_dir,
        args.confirm_overwrite, args.force_manual_keep_comments,
    )
    executed, manifest = execute_publish(
        ir_list, actions, manifest, destinations,
        args.out_dir, args.confirm_overwrite, args.force_manual_keep_comments,
    )
    manifest.save(args.out_dir)
    report, report_md = build_report(executed)
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "publish-report.json", report)
    _atomic_write_text(reports_dir / "publish-report.md", report_md)
    summary = report["summary"]
    print(f"OK — created={summary['created']}, updated={summary['updated']}, "
          f"skipped={summary['skipped']}, blocked={summary['blocked']}, "
          f"errors={summary['errors']}")
    print(f"     reporte: {reports_dir / 'publish-report.json'}")
    if summary["blocked"] > 0 or summary["errors"] > 0:
        return EXIT_WARN
    return EXIT_OK


def cmd_status(args: argparse.Namespace) -> int:
    manifest = Manifest.load(args.out_dir)
    entries = manifest.list_all()
    print(f"schema_version: {manifest.schema_version}")
    print(f"generated_at: {manifest.generated_at}")
    print(f"total_entries: {len(entries)}")
    by_dest: Dict[str, List[PublishEntry]] = {}
    edited_count = 0
    for e in entries:
        by_dest.setdefault(e.destination, []).append(e)
        if e.edited_by_hand:
            edited_count += 1
    for dest, es in by_dest.items():
        print(f"\n[{dest}] {len(es)} nota(s):")
        for e in es:
            mark = " (EDITED BY HAND)" if e.edited_by_hand else ""
            print(f"  - {e.note_id}{mark}; last_published={e.last_published_at}")
    if edited_count > 0:
        print(f"\nTotal editadas a mano: {edited_count}")
        return EXIT_WARN
    return EXIT_OK


def cmd_mark_edited(args: argparse.Namespace) -> int:
    manifest = Manifest.load(args.out_dir)
    entry = manifest.get(args.note_id, args.destination)
    if entry is not None:
        # Extrae y almacena user-content si existe en el archivo.
        if args.destination in DEST_FILE_INFO:
            subdir, ext = DEST_FILE_INFO[args.destination]
            target = args.out_dir / "render" / subdir / f"{args.note_id}{ext}"
            if target.exists():
                entry.user_content = _extract_user_content_for_storage(target)
        entry.edited_by_hand = True
    else:
        # No hay entry todavía — crear uno.
        if args.destination in DEST_FILE_INFO:
            subdir, ext = DEST_FILE_INFO[args.destination]
            target = args.out_dir / "render" / subdir / f"{args.note_id}{ext}"
            user_content = ""
            if target.exists():
                user_content = _extract_user_content_for_storage(target)
            manifest.upsert(PublishEntry(
                note_id=args.note_id,
                destination=args.destination,
                edited_by_hand=True,
                user_content=user_content,
            ))
    manifest.save(args.out_dir)
    print(f"OK — '{args.note_id}' marcado como edited_by_hand "
          f"en destino '{args.destination}'")
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="publishing.py",
        description="CLI de publicación idempotente (F62).",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_plan = subparsers.add_parser("plan", help="Dry-run; muestra qué se publicaría.")
    p_plan.add_argument("--ir", required=True, type=Path)
    p_plan.add_argument("--out-dir", required=True, type=Path)
    p_plan.add_argument("--destinations", type=str, required=True)
    p_plan.add_argument("--confirm-overwrite", action="store_true")
    p_plan.add_argument("--force-manual-keep-comments", action="store_true")
    p_plan.set_defaults(func=cmd_plan)

    p_pub = subparsers.add_parser("publish", help="Ejecuta la publicación.")
    p_pub.add_argument("--ir", required=True, type=Path)
    p_pub.add_argument("--out-dir", required=True, type=Path)
    p_pub.add_argument("--destinations", type=str, required=True)
    p_pub.add_argument("--confirm-overwrite", action="store_true")
    p_pub.add_argument("--force-manual-keep-comments", action="store_true")
    p_pub.add_argument("--notion-token", type=str, default=None)
    p_pub.set_defaults(func=cmd_publish)

    p_status = subparsers.add_parser("status", help="Muestra el estado del manifest.")
    p_status.add_argument("--out-dir", required=True, type=Path)
    p_status.set_defaults(func=cmd_status)

    p_mark = subparsers.add_parser("mark-edited",
                                   help="Marca una nota como editada a mano.")
    p_mark.add_argument("note_id", type=str)
    p_mark.add_argument("--destination", required=True, type=str)
    p_mark.add_argument("--out-dir", required=True, type=Path)
    p_mark.set_defaults(func=cmd_mark_edited)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
