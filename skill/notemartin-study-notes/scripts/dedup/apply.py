#!/usr/bin/env python3
"""apply.py — F108 orquestador de apply sobre F50 transform.py.

Envuelve `scripts/authoring/transform.py merge|split` por subproceso;
actualiza `manifest.json::link_debt[]` con entradas `redirected` por cada
ID viejo redirigido.

Uso (CLI):
    apply.py merge --a A.json --b B.json --output C.json --workdir DIR
                  [--irs-glob 'ir/*.json'] [--note-id ID] [--dry-run] [--yes]
    apply.py split --ir A.json --at-heading "## X" [--at-heading "## Y" ...]
                  --output B.json --workdir DIR [--dry-run] [--yes]
    apply.py specialize --parent P.json --child C.json --workdir DIR
                       [--irs-glob 'ir/*.json'] [--dry-run] [--yes]

Códigos: 0 OK · 1 validación (DEDUP-R1..R5) · 2 uso.
Dependencias: Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

ERR_DEDUP_R1 = "DEDUP_R1_SOURCE_REFS_LOST"
ERR_DEDUP_R2 = "DEDUP_R2_NO_REWRITE_GLOB"
ERR_DEDUP_R5 = "DEDUP_R5_INSUFFICIENT_HEADINGS"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
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


def _collect_source_refs(ir: Dict[str, Any]) -> set:
    """Recorre recursivamente todos los source_refs de un IR."""
    out = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for sr in node.get("source_refs") or []:
                if isinstance(sr, dict):
                    bid = sr.get("block_id", "")
                    sh = sr.get("source_hash", "")
                    if bid:
                        out.add((bid, sh))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(ir)
    return out


def _rewrite_links_in_ir(ir: Dict[str, Any], old_ids: list, new_id: str) -> int:
    """Reescribe attrs.target de link-note en IR. Idempotente."""
    changes = 0

    def walk(node: Any) -> None:
        nonlocal changes
        if not isinstance(node, dict):
            return
        if node.get("node") == "link-note":
            target = node.get("attrs", {}).get("target", "")
            if target in old_ids:
                node["attrs"]["target"] = new_id
                changes += 1
        for c in node.get("children", []) or []:
            walk(c)

    for b in ir.get("blocks", []) or []:
        walk(b)
    return changes


def _rewrite_links_glob(workdir: Path, irs_glob: str, old_ids: list,
                         new_id: str) -> int:
    """Aplica `_rewrite_links_in_ir` a todos los archivos que matchean el glob
    (resuelto relativo a `workdir`). Workaround al bug de F50 v1."""
    import glob as _glob
    pattern = irs_glob
    if not os.path.isabs(pattern):
        pattern = str(workdir / pattern)
    rewrites = 0
    for path_str in _glob.glob(pattern):
        path = Path(path_str)
        try:
            ir = _read_json(path)
        except Exception:
            continue
        changed = _rewrite_links_in_ir(ir, old_ids, new_id)
        if changed > 0:
            _atomic_write_json(path, ir)
            rewrites += 1
    return rewrites


def _find_transformer() -> Path:
    """Localiza scripts/authoring/transform.py en el repo."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "scripts" / "authoring" / "transform.py",
        here.parents[1] / "scripts" / "authoring" / "transform.py",
        here.parents[1] / "authoring" / "transform.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "scripts/authoring/transform.py no encontrado"
    )


def _run_transformer(transformer: Path, cmd_args: List[str],
                       cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(transformer)] + cmd_args,
        capture_output=True, text=True,
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ============================================================
# merge
# ============================================================


def _validate_dedup_r1(a: Dict[str, Any], b: Dict[str, Any],
                        merged: Dict[str, Any]) -> Optional[str]:
    """DEDUP-R1: merged.source_refs ⊇ a.source_refs ∪ b.source_refs."""
    refs_a = _collect_source_refs(a)
    refs_b = _collect_source_refs(b)
    refs_m = _collect_source_refs(merged)
    union = refs_a | refs_b
    missing = union - refs_m
    if missing:
        return f"{ERR_DEDUP_R1}: {len(missing)} source_refs perdidos"
    return None


def _update_manifest_link_debt(workdir: Path, from_ids: List[str], target: str) -> None:
    """Añade entrada(s) `redirected` a manifest.json::link_debt[]. Crea el
    manifest si no existe."""
    manifest_path = workdir / "manifest.json"
    if manifest_path.exists():
        payload = _read_json(manifest_path)
    else:
        payload = {
            "schema_version": "1.0.0",
            "source": {"id": "synthetic", "hash": "0" * 64, "algorithm": "sha256"},
            "stage_progress": {},
            "published_notes": [],
            "link_debt": [],
            "last_modified": _utc_now_iso(),
        }
    debt = payload.setdefault("link_debt", [])
    now = _utc_now_iso()
    for fid in from_ids:
        debt.append({
            "from_note": fid,
            "target": target,
            "kind": "redirected",
            "detected_at": now,
        })
    payload["last_modified"] = now
    _atomic_write_json(manifest_path, payload)


def _verify_dedup_r3(merged: Dict[str, Any], old_ids: List[str]) -> Optional[str]:
    """DEDUP-R3: frontmatter.aliases contiene los IDs viejos."""
    aliases = merged.get("frontmatter", {}).get("aliases", []) or []
    missing = [oid for oid in old_ids if oid not in aliases]
    if missing:
        return f"DEDUP_R3_ALIASES_MISSING: {missing}"
    return None


def cmd_merge(args: argparse.Namespace) -> int:
    if not args.yes:
        sys.stderr.write(
            "FAIL: --yes requerido para confirmar la mutación (cumple INV-12)\n"
        )
        return EXIT_USAGE
    workdir = Path(args.workdir).resolve()
    a_path = Path(args.a).resolve()
    b_path = Path(args.b).resolve()
    out_path = Path(args.output).resolve()
    if not a_path.exists() or not b_path.exists():
        sys.stderr.write("FAIL: --a o --b no existe\n")
        return EXIT_USAGE
    if not args.irs_glob:
        sys.stderr.write(
            f"FAIL: {ERR_DEDUP_R2}: --irs-glob requerido para redirección "
            f"de enlaces entrantes\n"
        )
        return EXIT_VALIDATION
    a = _read_json(a_path)
    b = _read_json(b_path)
    note_id = args.note_id or f"{a.get('note_id', 'merged')}-{b.get('note_id', 'merged')}"
    # Inyectar aliases viejos en frontmatter de A y B para DEDUP-R3.
    for src in (a, b):
        fm = src.setdefault("frontmatter", {})
        aliases = list(fm.get("aliases") or [])
        for old_id in (a.get("note_id", ""), b.get("note_id", "")):
            if old_id and old_id not in aliases:
                aliases.append(old_id)
        fm["aliases"] = sorted(set(aliases))
    # Invocar F50.
    transformer = _find_transformer()
    transform_args = [
        "merge",
        "--irs", str(a_path), str(b_path),
        "--output", str(out_path),
        "--irs-glob", str(workdir / args.irs_glob),
    ]
    if args.dry_run:
        transform_args.append("--dry-run")
    rc, stdout, stderr = _run_transformer(transformer, transform_args, cwd=workdir)
    if rc != 0:
        sys.stderr.write(f"FAIL: transform.py merge rc={rc}\n{stderr}\n")
        return rc if rc in (1, 2) else EXIT_VALIDATION
    if args.dry_run:
        sys.stdout.write(f"OK (dry-run) — {stdout}")
        return EXIT_OK
    # Cargar merged; validar DEDUP-R1 + DEDUP-R3.
    merged = _read_json(out_path)
    merged["note_id"] = note_id
    fm = merged.setdefault("frontmatter", {})
    aliases = list(fm.get("aliases") or [])
    for old_id in (a.get("note_id", ""), b.get("note_id", "")):
        if old_id and old_id not in aliases:
            aliases.append(old_id)
    fm["aliases"] = sorted(set(aliases))
    _atomic_write_json(out_path, merged)
    r1_err = _validate_dedup_r1(a, b, merged)
    if r1_err:
        sys.stderr.write(f"FAIL: {r1_err}\n")
        return EXIT_VALIDATION
    r3_err = _verify_dedup_r3(merged, [a.get("note_id", ""), b.get("note_id", "")])
    if r3_err:
        sys.stderr.write(f"FAIL: {r3_err}\n")
        return EXIT_VALIDATION
    # DEDUP-R2: reescribir enlaces entrantes en el workdir.
    rewrites = _rewrite_links_glob(
        workdir, args.irs_glob,
        [a.get("note_id", ""), b.get("note_id", "")],
        note_id,
    )
    # DEDUP-R4: actualizar manifest.json::link_debt[].
    _update_manifest_link_debt(
        workdir,
        from_ids=[a.get("note_id", ""), b.get("note_id", "")],
        target=note_id,
    )
    sys.stdout.write(
        f"OK — merge {a.get('note_id','')} + {b.get('note_id','')} → {note_id}\n"
        f"  - source_refs union: "
        f"{len(_collect_source_refs(a)) + len(_collect_source_refs(b)) - len(_collect_source_refs(a) & _collect_source_refs(b))} únicos\n"
        f"  - enlaces reescritos en {rewrites} IRs (DEDUP-R2)\n"
        f"  - manifest.link_debt actualizado (2 entradas redirected; DEDUP-R4)\n"
    )
    return EXIT_OK


# ============================================================
# split
# ============================================================


def cmd_split(args: argparse.Namespace) -> int:
    if not args.yes:
        sys.stderr.write("FAIL: --yes requerido\n")
        return EXIT_USAGE
    workdir = Path(args.workdir).resolve()
    if len(args.at_heading) < 2:
        sys.stderr.write(
            f"FAIL: {ERR_DEDUP_R5}: --at-heading requiere ≥ 2 valores "
            f"(recibidos {len(args.at_heading)})\n"
        )
        return EXIT_VALIDATION
    transformer = _find_transformer()
    transform_args = [
        "split",
        "--ir", str(Path(args.ir).resolve()),
        "--output", str(Path(args.output).resolve()),
        "--workdir", str(workdir),
    ]
    for h in args.at_heading:
        transform_args.extend(["--at-heading", h])
    if args.dry_run:
        transform_args.append("--dry-run")
    rc, stdout, stderr = _run_transformer(transformer, transform_args, cwd=workdir)
    if rc != 0:
        sys.stderr.write(f"FAIL: transform.py split rc={rc}\n{stderr}\n")
        return rc if rc in (1, 2) else EXIT_VALIDATION
    sys.stdout.write(f"OK — split → {args.output}\n{stdout}")
    return EXIT_OK


# ============================================================
# specialize
# ============================================================


def cmd_specialize(args: argparse.Namespace) -> int:
    if not args.yes:
        sys.stderr.write("FAIL: --yes requerido\n")
        return EXIT_USAGE
    sys.stderr.write(
        "WARN: specialize es un wrapper parcial; en esta versión emite "
        "instrucciones al agente para crear nota sister con back-link\n"
    )
    return EXIT_OK


# ============================================================
# CLI main
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F108 — Orquestador de apply sobre F50 transform.py.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_merge = sub.add_parser("merge", help="Fusionar 2 IRs en uno (F50)")
    p_merge.add_argument("--a", required=True)
    p_merge.add_argument("--b", required=True)
    p_merge.add_argument("--output", required=True)
    p_merge.add_argument("--workdir", required=True)
    p_merge.add_argument("--irs-glob", default=None,
                        help="Glob IRs a reescribir (DEDUP-R2)")
    p_merge.add_argument("--note-id", default=None,
                        help="ID de la nota resultante (default: a-b)")
    p_merge.add_argument("--dry-run", action="store_true")
    p_merge.add_argument("--yes", action="store_true",
                        help="Confirma la mutación (cumple INV-12)")
    p_merge.set_defaults(func=cmd_merge)

    p_split = sub.add_parser("split", help="Dividir 1 IR (F50)")
    p_split.add_argument("--ir", required=True)
    p_split.add_argument("--output", required=True)
    p_split.add_argument("--workdir", required=True)
    p_split.add_argument("--at-heading", action="append", required=True,
                        help="Heading de corte (≥ 2)")
    p_split.add_argument("--dry-run", action="store_true")
    p_split.add_argument("--yes", action="store_true")
    p_split.set_defaults(func=cmd_split)

    p_spec = sub.add_parser("specialize", help="Crear nota sister (back-link)")
    p_spec.add_argument("--parent", required=True)
    p_spec.add_argument("--child", required=True)
    p_spec.add_argument("--workdir", required=True)
    p_spec.add_argument("--irs-glob", default=None)
    p_spec.add_argument("--dry-run", action="store_true")
    p_spec.add_argument("--yes", action="store_true")
    p_spec.set_defaults(func=cmd_specialize)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())