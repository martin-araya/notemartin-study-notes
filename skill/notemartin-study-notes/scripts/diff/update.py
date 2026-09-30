#!/usr/bin/env python3
"""update.py — F111 orquestador de actualización incremental.

Compara un SDM antiguo con uno nuevo, identifica bloques afectados, marca
obsoletos sin borrar, genera notas `version-delta` (F88) con el resumen
de cambios, y republica selectivamente en destinos remotos.

Uso (CLI):
    update.py diff --old-sdm OLD.json --new-sdm NEW.json [--json-out PATH]
    update.py dry-run --old-sdm OLD.json --new-sdm NEW.json --workdir DIR
    update.py run-all --old-sdm OLD.json --new-sdm NEW.json --workdir DIR
                  [--yes] [--force]
    update.py status --workdir DIR [--json]

Códigos: 0 OK · 1 validación (INC-R* violado) · 2 uso.
Dependencias: Python 3.9+ stdlib puro. Sin jsonschema.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
DELTA_NOTE_TYPE = "version-delta"
IR_GLOB = "ir/*.json"
DEFAULT_BAK_SUFFIX = ".bak"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

ERR_NO_SDM = "INC_NO_SDM"
ERR_SOURCE_MISMATCH = "INC_SOURCE_MISMATCH"
ERR_INVALID_PAIR = "INC_INVALID_PAIR"
ERR_PARTIAL_RUN_FAILED = "INC_PARTIAL_RUN_FAILED"
ERR_BLOCK_ID_INVALID = "INC_BLOCK_ID_INVALID"

VERSION_RE = re.compile(r"^(\d+\.\d+(?:\.\d+)?)$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + DEFAULT_BAK_SUFFIX)
        shutil.copy2(path, bak)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        Path(tmp).replace(path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _glob(workdir: Path, pattern: str) -> List[Path]:
    import glob as _glob
    p = pattern if os.path.isabs(pattern) else str(workdir / pattern)
    return [Path(x) for x in _glob.glob(p)]


# ============================================================
# Diff
# ============================================================


class SDMDiffer:
    def __init__(self, old_sdm: Dict[str, Any], new_sdm: Dict[str, Any]):
        self.old = old_sdm
        self.new = new_sdm
        self._validate()

    def _validate(self) -> None:
        if "blocks" not in self.old or "blocks" not in self.new:
            raise ValueError(ERR_NO_SDM)
        old_src = self.old.get("source", {})
        new_src = self.new.get("source", {})
        if old_src.get("id") != new_src.get("id"):
            raise ValueError(
                f"{ERR_SOURCE_MISMATCH}: {old_src.get('id')} != {new_src.get('id')}"
            )

    def diff(self) -> Dict[str, Any]:
        old_blocks = {b.get("block_id"): b for b in self.old.get("blocks", [])}
        new_blocks = {b.get("block_id"): b for b in self.new.get("blocks", [])}
        added, removed, modified, unchanged = [], [], [], []
        for bid, nb in new_blocks.items():
            if not bid:
                continue
            if bid not in old_blocks:
                added.append(nb)
            elif self._block_differs(old_blocks[bid], nb):
                modified.append(nb)
            else:
                unchanged.append(bid)
        for bid, ob in old_blocks.items():
            if not bid:
                continue
            if bid not in new_blocks:
                removed.append(ob)
        affected_sections = sorted({b.get("anchor", {}).get("section_path", "/")
                                      for b in added + removed + modified})
        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": unchanged,
            "affected_sections": affected_sections,
            "old_hash": self.old.get("source", {}).get("hash", ""),
            "new_hash": self.new.get("source", {}).get("hash", ""),
            "source_id": self.old.get("source", {}).get("id", ""),
            "new_version": self.new.get("source", {}).get("version", "1.0"),
        }

    @staticmethod
    def _block_differs(old_b: Dict[str, Any], new_b: Dict[str, Any]) -> bool:
        """Compara text + attrs (excluyendo timestamp)."""
        def _normalize(b: dict) -> Any:
            cp = {k: v for k, v in b.items() if k not in ("started_at", "modified_at")}
            return json.dumps(cp, sort_keys=True, ensure_ascii=False)
        return _normalize(old_b) != _normalize(new_b)


# ============================================================
# Identify affected IRs
# ============================================================


def _find_affected_irs(workdir: Path, diff_result: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Retorna (affected_ir_ids, obsoleted_ir_ids).

    - affected_ir_ids: IRs que tienen ≥ 1 source_ref en una sección afectada.
    - obsoleted_ir_ids: subset cuyo TODOS los source_refs están en bloques `removed`.
    """
    removed_section_paths = {b.get("anchor", {}).get("section_path", "")
                              for b in diff_result["removed"]}
    modified_added_sections = {b.get("anchor", {}).get("section_path", "")
                                 for b in diff_result["modified"] + diff_result["added"]}
    affected_sections = removed_section_paths | modified_added_sections

    affected: List[str] = []
    obsoleted: List[str] = []
    for ir_path in _glob(workdir, IR_GLOB):
        try:
            ir = _read_json(ir_path)
        except Exception:
            continue
        nid = ir.get("note_id", "")
        if not nid:
            continue
        ref_sections = set()
        removed_refs_count = 0
        total_refs = 0

        def walk(node: Any) -> None:
            nonlocal removed_refs_count, total_refs
            if isinstance(node, dict):
                for sr in node.get("source_refs") or []:
                    if isinstance(sr, dict):
                        total_refs += 1
                        sp = sr.get("section_path", "")
                        ref_sections.add(sp)
                        if sp in removed_section_paths:
                            removed_refs_count += 1
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(ir)
        if ref_sections & affected_sections:
            affected.append(nid)
            if total_refs > 0 and removed_refs_count == total_refs:
                obsoleted.append(nid)
    return affected, obsoleted


def _group_changes_by_section(diff_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa blocks de cambio por section_path."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for kind in ("added", "removed", "modified"):
        for b in diff_result[kind]:
            sp = b.get("anchor", {}).get("section_path", "/")
            entry = {
                "change_type": kind,
                "block_id": b.get("block_id", ""),
                "section_path": sp,
                "description": b.get("text", "")[:120] or b.get("title", "")[:120] or kind,
            }
            groups.setdefault(sp, []).append(entry)
    return groups


def _infer_superseding_note_id(
    section_path: str,
    diff_result: Dict[str, Any],
    workdir: Path,
) -> Optional[str]:
    """Encuentra el IR 'sister' (la IR que reemplaza a la obsoleta).

    Estrategia en cascada:
    1. Added block en el mismo section_path → IR cuyo title coincide.
    2. Cualquier added block → IR cuyo title coincide.
    3. Si hay exactamente 1 added block total, devuelve el IR cuyo
       primer source_ref coincide con ese block_id.
    Si ninguna estrategia produce match, devuelve None (superseded_by = null).
    """
    added_section_blocks = [b for b in diff_result["added"]
                              if b.get("anchor", {}).get("section_path") == section_path]
    added_title_candidates = [
        (added_section_blocks[0].get("title", "")
         or added_section_blocks[0].get("text", "")[:50])
        for _ in [1] if added_section_blocks
    ]

    def _find_by_title(title: str) -> Optional[str]:
        if not title:
            return None
        for ir_path in _glob(workdir, IR_GLOB):
            try:
                ir = _read_json(ir_path)
            except Exception:
                continue
            if title in str(ir):
                return ir.get("note_id")
        return None

    # Strategy 1+2: match by title.
    for title in added_title_candidates:
        match = _find_by_title(title)
        if match:
            return match

    # Strategy 3: if there's exactly 1 added block, find IR with matching
    # source_ref block_id.
    added_blocks = diff_result["added"]
    if len(added_blocks) == 1:
        target_block_id = added_blocks[0].get("block_id", "")
        for ir_path in _glob(workdir, IR_GLOB):
            try:
                ir = _read_json(ir_path)
            except Exception:
                continue
            for sr in _collect_source_refs_iter(ir):
                if sr.get("block_id") == target_block_id:
                    return ir.get("note_id")
    return None


def _collect_source_refs_iter(ir: dict):
    def walk(node):
        if isinstance(node, dict):
            for sr in node.get("source_refs") or []:
                if isinstance(sr, dict):
                    yield sr
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
    yield from walk(ir)


# ============================================================
# Apply (mark obsolete + version-delta + selective republish)
# ============================================================


def _mark_obsolete(ir_path: Path, superseded_by: Optional[str]) -> bool:
    """Marca un IR como obsoleto: status=archived + superseded_by. NO borra."""
    try:
        ir = _read_json(ir_path)
    except Exception:
        return False
    fm = ir.setdefault("frontmatter", {})
    fm["status"] = "archived"
    if superseded_by is not None:
        fm["superseded_by"] = superseded_by
    else:
        fm["superseded_by"] = None
    _atomic_write_json(ir_path, ir)
    return True


def _emit_version_delta(
    workdir: Path,
    diff_result: Dict[str, Any],
    affected_ir_ids: List[str],
    obsoleted_ir_ids: List[str],
    delta_id: str,
) -> Path:
    version = diff_result["new_version"]
    if not VERSION_RE.match(str(version)):
        version = "1.0"
    groups = _group_changes_by_section(diff_result)
    changes: List[Dict[str, Any]] = []
    for sp, entries in groups.items():
        changes.append({
            "version": version,
            "change_type": entries[0]["change_type"] if len(entries) == 1 else "mixed",
            "description": f"Sección {sp}: {len(entries)} cambio(s)",
            "section_path": sp,
            "block_ids": [e["block_id"] for e in entries if e["block_id"]],
        })
    delta = {
        "schema_version": SCHEMA_VERSION,
        "delta_id": delta_id,
        "source_id": diff_result["source_id"],
        "old_source_hash": diff_result["old_hash"],
        "new_source_hash": diff_result["new_hash"],
        "version": version,
        "created_at": _utc_now_iso(),
        "affected_chapters": [],
        "affected_ir_ids": affected_ir_ids,
        "obsoleted_ir_ids": obsoleted_ir_ids,
        "changes": changes,
        "frontmatter": {
            "title": f"Version Delta — {diff_result['source_id']} → {version}",
            "note-type": DELTA_NOTE_TYPE,
            "status": "draft",
            "tags": ["type/version-delta", "domain/update"],
        },
    }
    out_path = workdir / "ir" / f"{delta_id}.note-ir.json"
    _atomic_write_json(out_path, delta)
    return out_path


def _next_delta_id(workdir: Path) -> str:
    """Genera el siguiente delta_id disponible (vd0001, vd0002, ...)."""
    existing = set()
    for p in _glob(workdir, IR_GLOB):
        m = re.match(r"^(vd\d+)\.note-ir\.json$", p.name)
        if m:
            existing.add(int(m.group(1)[2:]))
    n = 1
    while n in existing:
        n += 1
    return f"vd{n:04d}"


# ============================================================
# CLI
# ============================================================


def cmd_diff(args: argparse.Namespace) -> int:
    old_path = Path(args.old_sdm).resolve()
    new_path = Path(args.new_sdm).resolve()
    if not old_path.exists() or not new_path.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_SDM}\n")
        return EXIT_USAGE
    try:
        differ = SDMDiffer(_read_json(old_path), _read_json(new_path))
        diff_result = differ.diff()
    except ValueError as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    summary = {
        "added": len(diff_result["added"]),
        "removed": len(diff_result["removed"]),
        "modified": len(diff_result["modified"]),
        "unchanged": len(diff_result["unchanged"]),
        "affected_sections": diff_result["affected_sections"],
        "source_id": diff_result["source_id"],
        "old_hash": diff_result["old_hash"],
        "new_hash": diff_result["new_hash"],
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "summary": summary,
        "changes": {
            "added": [{"block_id": b.get("block_id"), "section_path": b.get("anchor", {}).get("section_path", "")} for b in diff_result["added"]],
            "removed": [{"block_id": b.get("block_id"), "section_path": b.get("anchor", {}).get("section_path", "")} for b in diff_result["removed"]],
            "modified": [{"block_id": b.get("block_id"), "section_path": b.get("anchor", {}).get("section_path", "")} for b in diff_result["modified"]],
        },
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.json_out:
        out = Path(args.json_out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        sys.stdout.write(
            f"OK — diff: added={summary['added']}, removed={summary['removed']}, "
            f"modified={summary['modified']} (wrote {out})\n"
        )
    else:
        sys.stdout.write(text + "\n")
    return EXIT_OK


def _execute_run_all(args: argparse.Namespace, dry_run: bool = False) -> Tuple[int, Optional[Path]]:
    """Lógica común de dry-run y run-all. Retorna (exit_code, delta_path)."""
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: workdir no existe: {workdir}\n")
        return EXIT_USAGE, None
    try:
        old = _read_json(Path(args.old_sdm).resolve())
        new = _read_json(Path(args.new_sdm).resolve())
        differ = SDMDiffer(old, new)
        diff_result = differ.diff()
    except ValueError as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION, None
    affected, obsoleted = _find_affected_irs(workdir, diff_result)
    if dry_run:
        # Emitir dry-run report y terminar.
        report = {
            "schema_version": SCHEMA_VERSION,
            "dry_run": True,
            "affected_ir_ids": affected,
            "obsoleted_ir_ids": obsoleted,
            "summary": {
                "added": len(diff_result["added"]),
                "removed": len(diff_result["removed"]),
                "modified": len(diff_result["modified"]),
            },
        }
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        return EXIT_OK, None
    # Paso 4: marcar obsoletos.
    obsoleted_marked: List[str] = []
    obsoleted_failed: List[str] = []
    for nid in obsoleted:
        # Encontrar el archivo.
        ir_file = None
        for p in _glob(workdir, IR_GLOB):
            try:
                if _read_json(p).get("note_id") == nid:
                    ir_file = p
                    break
            except Exception:
                continue
        if ir_file is None:
            obsoleted_failed.append(nid)
            continue
        # Inferir superseded_by.
        # Buscar la sección principal del IR (primer source_ref).
        section_path = None
        try:
            ir = _read_json(ir_file)
            def walk(n):
                nonlocal section_path
                if section_path:
                    return
                if isinstance(n, dict):
                    for sr in n.get("source_refs") or []:
                        if isinstance(sr, dict) and sr.get("section_path"):
                            section_path = sr["section_path"]
                            return
                    for v in n.values():
                        walk(v)
                elif isinstance(n, list):
                    for v in n:
                        walk(v)
            walk(ir)
        except Exception:
            pass
        superseded_by = _infer_superseding_note_id(
            section_path or "/", diff_result, workdir
        )
        if _mark_obsolete(ir_file, superseded_by):
            obsoleted_marked.append(nid)
        else:
            obsoleted_failed.append(nid)
    # Paso 5: generar version-delta.
    delta_id = _next_delta_id(workdir)
    delta_path = _emit_version_delta(
        workdir, diff_result, affected, obsoleted_marked, delta_id
    )
    # Paso 6 (INC-R4): republish selectiva — emitimos el log; el agente
    # puede invocar el motor de publishing manualmente.
    affected_set = set(affected)
    affected_republish: List[Dict[str, Any]] = []
    manifest_path = workdir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = _read_json(manifest_path)
            for entry in manifest.get("published_notes", []):
                if entry.get("note_id") in affected_set:
                    affected_republish.append({
                        "note_id": entry["note_id"],
                        "destination": entry.get("destination"),
                        "remote_id": entry.get("remote_id"),
                    })
        except Exception:
            pass
    summary = {
        "affected_ir_count": len(affected),
        "obsoleted_marked_count": len(obsoleted_marked),
        "obsoleted_failed_count": len(obsoleted_failed),
        "delta_id": delta_id,
        "delta_path": str(delta_path.relative_to(workdir)),
        "republish_count": len(affected_republish),
        "republish_targets": affected_republish,
    }
    if obsoleted_failed:
        sys.stderr.write(f"FAIL: {ERR_PARTIAL_RUN_FAILED}: {obsoleted_failed}\n")
        sys.stdout.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
        return EXIT_VALIDATION, delta_path
    sys.stdout.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return EXIT_OK, delta_path


def cmd_dry_run(args: argparse.Namespace) -> int:
    rc, _ = _execute_run_all(args, dry_run=True)
    return rc


def cmd_run_all(args: argparse.Namespace) -> int:
    if not args.yes:
        sys.stderr.write(
            "FAIL: --yes requerido para confirmar mutaciones (cumple INV-12)\n"
        )
        return EXIT_USAGE
    rc, _ = _execute_run_all(args)
    return rc


def cmd_status(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: workdir no existe\n")
        return EXIT_USAGE
    deltas: List[Dict[str, Any]] = []
    for p in sorted(_glob(workdir, IR_GLOB)):
        m = re.match(r"^(vd\d+)\.note-ir\.json$", p.name)
        if m:
            try:
                deltas.append(_read_json(p))
            except Exception:
                continue
    if args.json:
        sys.stdout.write(json.dumps(deltas, indent=2, ensure_ascii=False) + "\n")
    else:
        print(f"version-delta count: {len(deltas)}")
        for d in deltas[-5:]:
            print(f"  - {d.get('delta_id')}: source={d.get('source_id')} "
                  f"v={d.get('version')} obsoleted={len(d.get('obsoleted_ir_ids', []))}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F111 — Orquestador de actualización incremental.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_diff = sub.add_parser("diff", help="Comparar 2 SDMs sin tocar workdir")
    p_diff.add_argument("--old-sdm", required=True)
    p_diff.add_argument("--new-sdm", required=True)
    p_diff.add_argument("--json-out", default=None)
    p_diff.set_defaults(func=cmd_diff)

    p_dry = sub.add_parser("dry-run", help="Mostrar qué se haría sin escribir")
    p_dry.add_argument("--old-sdm", required=True)
    p_dry.add_argument("--new-sdm", required=True)
    p_dry.add_argument("--workdir", required=True)
    p_dry.set_defaults(func=cmd_dry_run)

    p_run = sub.add_parser("run-all", help="Aplicar diff + obsolete + delta + selective republish")
    p_run.add_argument("--old-sdm", required=True)
    p_run.add_argument("--new-sdm", required=True)
    p_run.add_argument("--workdir", required=True)
    p_run.add_argument("--force", action="store_true",
                        help="Forzar re-proceso de IRs modificados (preserva previous_processed_at)")
    p_run.add_argument("--yes", action="store_true",
                        help="Confirmación de mutación (cumple INV-12)")
    p_run.set_defaults(func=cmd_run_all)

    p_stat = sub.add_parser("status", help="Mostrar version-deltas existentes")
    p_stat.add_argument("--workdir", required=True)
    p_stat.add_argument("--json", action="store_true")
    p_stat.set_defaults(func=cmd_status)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())