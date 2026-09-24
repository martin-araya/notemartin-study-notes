#!/usr/bin/env python3
"""sdm_cache.py — F36 SDM cache library.

Caché por hash con invalidación selectiva por `engine_version`. La clave
del entry combina `source_hash`, `step` (e.g. `ocr`, `tables`, `code_ocr`),
`engine_version` (e.g. `tesseract@5.0.0`), `script_version` (e.g. SHA1 del
script) y un hash del `params` canonizado (JSON con claves ordenadas).

El primer lookup con la misma clave devuelve el valor cacheado sin invocar
`compute_fn`. Cambiar `engine_version` (o cualquier componente) genera una
clave distinta y fuerza recompute; los entries de versiones anteriores se
invalidan selectivamente vía el subcomando `invalidate`.

Uso como biblioteca:

    from sdm_cache import cache_get_or_compute

    value = cache_get_or_compute(
        source_hash=sha256_of_pdf,
        step="ocr",
        engine_version="tesseract@5.0.0",
        script_version=__version__,
        params={"page": 1},
        compute_fn=lambda: slow_ocr(...),  # solo se invoca en cache miss
        cache_dir=Path("/tmp/.sdm_cache"),
    )

Uso como CLI:

    python3 scripts/util/sdm_cache.py put --step ocr --source-hash <h> --engine-version <ev> --value-file <f>
    python3 scripts/util/sdm_cache.py get --step ocr --source-hash <h> --engine-version <ev> --params '<json>'
    python3 scripts/util/sdm_cache.py list [--step <s>]
    python3 scripts/util/sdm_cache.py invalidate --step <s> [--engine-version <ev>]
    python3 scripts/util/sdm_cache.py info

Códigos de salida:
    0 — OK
    1 — Error fatal (input ausente, no se pudo escribir)
    2 — OK con advertencias (cache vacío al hacer get, etc.)

Dependencias: Python 3.9+ stdlib.

Documentación normativa: ROADMAP.md Fase 36 (criterios). El plan detallado
está en .kilo/plans/1790264052931-fase-36-cache-viewer-plan.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

INDEX_FILE = "index.json"
_LOCK = threading.Lock()


# ============================================================
# Helpers
# ============================================================


def _canon_params(params: Any) -> str:
    """Render `params` as a canonical JSON string (sorted keys, no spaces)."""
    return json.dumps(params, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, default=str)


def _key_digest(
    source_hash: str,
    step: str,
    engine_version: str,
    script_version: str,
    params: Any,
) -> str:
    """SHA-256 hex (16 chars) of the canonical key components.

    The 16-character hex namespace carries roughly 64 bits of entropy; with
    the project's expected corpus size this is collision-immune in practice.
    """
    canon = (
        f"{source_hash}|{step}|{engine_version}|{script_version}|"
        f"{_canon_params(params)}"
    )
    h = hashlib.sha256(canon.encode("utf-8"))
    return h.hexdigest()[:16]


def _entry_path(cache_dir: Path, step: str, key: str) -> Path:
    return cache_dir / step / f"{key}.json"


def _index_path(cache_dir: Path) -> Path:
    return cache_dir / INDEX_FILE


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tf:
        tf.write(json.dumps(payload, indent=2, ensure_ascii=False))
        tmpname = tf.name
    Path(tmpname).replace(path)


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _ensure_index(cache_dir: Path) -> Dict[str, Any]:
    p = _index_path(cache_dir)
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    try:
        data = _read_json(p)
        if not isinstance(data, dict) or "entries" not in data:
            return {"schema_version": SCHEMA_VERSION, "entries": {}}
        return data
    except Exception:
        return {"schema_version": SCHEMA_VERSION, "entries": {}}


def _write_index(cache_dir: Path, index: Dict[str, Any]) -> None:
    _atomic_write_json(_index_path(cache_dir), index)


def _update_index(
    cache_dir: Path,
    *,
    step: str,
    source_hash: str,
    engine_version: str,
    script_version: str,
    key: str,
    rel_path: str,
    action: str = "upsert",
) -> None:
    """Upsert or remove an entry in `index.json`. Thread-safe via _LOCK."""
    with _LOCK:
        index = _ensure_index(cache_dir)
        entries = index["entries"]
        entry_id = f"{step}|{source_hash}|{engine_version}|{key}"
        if action == "remove":
            entries.pop(entry_id, None)
        else:
            entries[entry_id] = {
                "step": step,
                "source_hash": source_hash,
                "engine_version": engine_version,
                "script_version": script_version,
                "key": key,
                "path": rel_path,
                "mtime": datetime.now(timezone.utc).isoformat(),
            }
        _write_index(cache_dir, index)


# ============================================================
# Public API (used by F19/F25 in F36.1+)
# ============================================================


def cache_get_or_compute(
    *,
    source_hash: str,
    step: str,
    engine_version: str,
    script_version: str,
    params: Any,
    compute_fn: Callable[[], Any],
    cache_dir: Path,
) -> Any:
    """Return cached value if present; otherwise invoke `compute_fn`, persist
    its return value as JSON, and return it.

    Persistence contract:
    - compute_fn() must return JSON-serializable data. If it raises, the
      caller sees the exception and no cache entry is created.
    - Storage: <cache_dir>/<step>/<key>.json where key = 16-char sha256 of
      (source_hash, step, engine_version, script_version, params).
    - On hit, no compute_fn invocation (criterion 1).
    """
    if not source_hash or not step or not engine_version or not script_version:
        raise ValueError(
            "cache_get_or_compute: source_hash, step, engine_version, "
            "script_version are all required (non-empty)."
        )
    key = _key_digest(
        source_hash=source_hash,
        step=step,
        engine_version=engine_version,
        script_version=script_version,
        params=params,
    )
    entry = _entry_path(cache_dir, step, key)
    if entry.exists():
        return _read_json(entry)
    value = compute_fn()
    _atomic_write_json(entry, value)
    rel_path = f"{step}/{key}.json"
    _update_index(
        cache_dir,
        step=step,
        source_hash=source_hash,
        engine_version=engine_version,
        script_version=script_version,
        key=key,
        rel_path=rel_path,
        action="upsert",
    )
    return value


def cache_clear_step(cache_dir: Path, step: str) -> int:
    """Remove all entries of one step. Returns count removed."""
    if not cache_dir.exists():
        return 0
    step_dir = cache_dir / step
    removed = 0
    if step_dir.exists():
        for f in step_dir.glob("*.json"):
            f.unlink()
            removed += 1
        try:
            step_dir.rmdir()
        except OSError:
            pass
    with _LOCK:
        index = _ensure_index(cache_dir)
        before = len(index["entries"])
        index["entries"] = {
            k: v for k, v in index["entries"].items() if not k.startswith(f"{step}|")
        }
        _write_index(cache_dir, index)
    return removed


def cache_clear_engine_version(
    cache_dir: Path, step: str, engine_version: str
) -> int:
    """Selectively invalidate all entries of a step whose engine_version
    matches. Returns count removed."""
    if not cache_dir.exists():
        return 0
    step_dir = cache_dir / step
    removed = 0
    if step_dir.exists():
        for f in step_dir.glob("*.json"):
            try:
                meta = _read_json(f) if str(f).endswith(".json") else {}
            except Exception:
                continue
            if not isinstance(meta, dict):
                continue
            if meta.get("__engine_version__") == engine_version:
                f.unlink()
                removed += 1
    with _LOCK:
        index = _ensure_index(cache_dir)
        prefix = f"{step}|"
        version_prefix = f"{step}|"
        kept = {}
        for k, v in index["entries"].items():
            if k.startswith(prefix) and v.get("engine_version") == engine_version:
                continue
            kept[k] = v
        index["entries"] = kept
        _write_index(cache_dir, index)
    return removed


def list_entries(
    cache_dir: Path, step: Optional[str] = None
) -> List[Dict[str, Any]]:
    index = _ensure_index(cache_dir)
    items: List[Dict[str, Any]] = []
    for k, v in index["entries"].items():
        if step and not k.startswith(f"{step}|"):
            continue
        items.append(v)
    return items


def cache_info(cache_dir: Path) -> Dict[str, Any]:
    """Return summary stats: total entries, by_step, by_engine_version."""
    entries = list_entries(cache_dir)
    by_step: Counter = Counter()
    by_engine: Counter = Counter()
    for e in entries:
        by_step[e["step"]] += 1
        by_engine[e["engine_version"]] += 1
    total_bytes = 0
    if cache_dir.exists():
        for f in cache_dir.rglob("*.json"):
            try:
                total_bytes += f.stat().st_size
            except OSError:
                pass
    return {
        "cache_dir": str(cache_dir),
        "total_entries": len(entries),
        "total_bytes": total_bytes,
        "by_step": dict(by_step),
        "by_engine_version": dict(by_engine),
    }


# ============================================================
# CLI
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdm_cache.py",
        description="F36 — SDM cache (por hash, invalidación selectiva).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Cache key formula:
  sha256(source_hash | step | engine_version | script_version | params)[:16]

Subcomandos:
  put              Almacena un valor desde --value-file
  get              Recupera (imprime stdout; exit 1 si no existe)
  list             Lista entries del index
  invalidate       --step s [--engine-version v] borra selectivamente
  info             Resumen por step y engine_version

Códigos de salida:
  0 OK · 1 error fatal · 2 OK con advertencias (p.ej. get con cache miss)
""",
    )
    p.add_argument(
        "--cache-dir", default=".sdm_cache",
        help="Directorio raíz del cache (default .sdm_cache)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    put = sub.add_parser("put", help="Almacena un entry")
    put.add_argument("--step", required=True)
    put.add_argument("--source-hash", required=True)
    put.add_argument("--engine-version", required=True)
    put.add_argument("--script-version", default="sdm_cache@1.0.0")
    put.add_argument("--params", default="{}", help="JSON (canonical)")
    put.add_argument("--value-file", required=True, help="Ruta al JSON con el valor")

    get = sub.add_parser("get", help="Recupera un entry")
    get.add_argument("--step", required=True)
    get.add_argument("--source-hash", required=True)
    get.add_argument("--engine-version", required=True)
    get.add_argument("--script-version", default="sdm_cache@1.0.0")
    get.add_argument("--params", default="{}", help="JSON (canonical)")

    ls = sub.add_parser("list", help="Lista entries")
    ls.add_argument("--step", default=None)
    ls.add_argument("--json", action="store_true", help="Output JSON")

    inv = sub.add_parser("invalidate", help="Invalida (borra) entries")
    inv.add_argument("--step", required=True)
    inv.add_argument("--engine-version", default=None)

    sub.add_parser("info", help="Resumen stats")

    return p


def _cli_put(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    params = json.loads(args.params or "{}")
    value_path = Path(args.value_file)
    if not value_path.exists():
        sys.stderr.write(f"value-file not found: {value_path}\n")
        return 1
    try:
        value = _read_json(value_path)
    except Exception as e:
        sys.stderr.write(f"failed to parse value-file: {e}\n")
        return 1
    key = _key_digest(
        source_hash=args.source_hash,
        step=args.step,
        engine_version=args.engine_version,
        script_version=args.script_version,
        params=params,
    )
    entry = _entry_path(cache_dir, args.step, key)
    _atomic_write_json(
        entry,
        {"__engine_version__": args.engine_version, "value": value},
    )
    rel_path = f"{args.step}/{key}.json"
    _update_index(
        cache_dir,
        step=args.step,
        source_hash=args.source_hash,
        engine_version=args.engine_version,
        script_version=args.script_version,
        key=key,
        rel_path=rel_path,
        action="upsert",
    )
    sys.stdout.write(f"stored: {rel_path}\n")
    return 0


def _cli_get(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    params = json.loads(args.params or "{}")
    key = _key_digest(
        source_hash=args.source_hash,
        step=args.step,
        engine_version=args.engine_version,
        script_version=args.script_version,
        params=params,
    )
    entry = _entry_path(cache_dir, args.step, key)
    if not entry.exists():
        sys.stderr.write(f"cache miss: {entry}\n")
        return 2
    data = _read_json(entry)
    sys.stdout.write(json.dumps(data.get("value", data), indent=2, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


def _cli_list(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    items = list_entries(cache_dir, step=args.step)
    if args.json:
        sys.stdout.write(json.dumps(items, indent=2, ensure_ascii=False) + "\n")
        return 0
    for e in items:
        sys.stdout.write(
            f"{e['step']}\t{e['source_hash'][:12]}\t{e['engine_version']}\t"
            f"{e['path']}\t{e.get('mtime','')}\n"
        )
    return 0


def _cli_invalidate(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    if args.engine_version:
        removed = cache_clear_engine_version(cache_dir, args.step, args.engine_version)
    else:
        removed = cache_clear_step(cache_dir, args.step)
    sys.stdout.write(
        f"invalidate step={args.step} engine_version={args.engine_version or '*'} "
        f"removed={removed}\n"
    )
    return 0


def _cli_info(args: argparse.Namespace) -> int:
    cache_dir = Path(args.cache_dir).resolve()
    info = cache_info(cache_dir)
    sys.stdout.write(json.dumps(info, indent=2, ensure_ascii=False) + "\n")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "put":
        return _cli_put(args)
    if args.cmd == "get":
        return _cli_get(args)
    if args.cmd == "list":
        return _cli_list(args)
    if args.cmd == "invalidate":
        return _cli_invalidate(args)
    if args.cmd == "info":
        return _cli_info(args)
    sys.stderr.write(f"unknown subcommand: {args.cmd}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
