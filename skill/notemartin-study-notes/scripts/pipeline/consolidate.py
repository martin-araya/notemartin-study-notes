#!/usr/bin/env python3
"""consolidate.py — F109 orquestador de pases de consolidación.

Ejecuta 5 pases secuenciales (link-debt, glossary, indices, cheatsheets,
consistency) sobre el workdir. Cada pase es idempotente (CON-R1) y no
modifica inputs (CON-R3). El orquestador `run-all` los ejecuta en orden
y registra cada run en `manifest.json::consolidation_runs[]`.

Uso (CLI):
    consolidate.py run-all --workdir DIR [--strategy {default,consolidate}]
                           [--irs-glob 'ir/*.json'] [--notemark-glob 'notemark/*.nm']
    consolidate.py pass-link-debt --workdir DIR [--irs-glob ...] [--notemark-glob ...]
    consolidate.py pass-glossary --workdir DIR
    consolidate.py pass-indices --workdir DIR
    consolidate.py pass-cheatsheets --workdir DIR
    consolidate.py pass-consistency --workdir DIR [--threshold 0.6]

Códigos: 0 OK · 1 validación (CON-R* violado) · 2 uso (paths faltantes).
Dependencias: Python 3.9+ stdlib puro. Sin jsonschema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
MANIFEST_BAK_SUFFIX = ".bak"
REPORTS_SUBDIR = "reports"
DEFAULT_IR_GLOB = "ir/*.json"
DEFAULT_NOTEMARK_GLOB = "notemark/*.nm"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

ERR_NO_WORKDIR = "CON_NO_WORKDIR"
ERR_INVALID_PASS = "CON_INVALID_PASS"
ERR_IR_GLOB_EMPTY = "CON_IR_GLOB_EMPTY"
ERR_RUN_FAILED = "CON_RUN_FAILED"

PASS_NAMES = ["link-debt", "glossary", "indices", "cheatsheets", "consistency"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + MANIFEST_BAK_SUFFIX)
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


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        Path(tmp).replace(path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_or_create_manifest(workdir: Path) -> Dict[str, Any]:
    manifest_path = workdir / "manifest.json"
    if manifest_path.exists():
        return _read_json(manifest_path)
    return {
        "schema_version": "1.0.0",
        "source": {"id": "synthetic", "path": str(workdir),
                    "hash": "0" * 64, "algorithm": "sha256"},
        "current_stage": "none",
        "stage_progress": {},
        "published_notes": [],
        "link_debt": [],
        "consolidation_runs": [],
        "last_modified": _utc_now_iso(),
    }


def _save_manifest(workdir: Path, manifest: Dict[str, Any]) -> None:
    manifest["last_modified"] = _utc_now_iso()
    _atomic_write_json(workdir / "manifest.json", manifest)


# ============================================================
# Pase 1 — link-debt
# ============================================================


def _iter_link_targets(workdir: Path, irs_glob: str) -> List[Tuple[Path, str]]:
    """Retorna lista de (path, target) para todos los link-note con target."""
    results: List[Tuple[Path, str]] = []
    pattern = irs_glob
    if not os.path.isabs(pattern):
        pattern = str(workdir / pattern)
    import glob as _glob
    for path_str in _glob.glob(pattern):
        path = Path(path_str)
        try:
            ir = _read_json(path)
        except Exception:
            continue
        note_id = ir.get("note_id", "")

        def walk(node: Any) -> None:
            if not isinstance(node, dict):
                return
            if node.get("node") == "link-note":
                target = node.get("attrs", {}).get("target", "")
                results.append((path, target, note_id))
            for c in node.get("children", []) or []:
                walk(c)

        for b in ir.get("blocks", []) or []:
            walk(b)
    return results


def _iter_note_ids(workdir: Path, irs_glob: str) -> Dict[str, Path]:
    """Retorna mapa note_id → path para todos los IRs del glob."""
    out: Dict[str, Path] = {}
    pattern = irs_glob
    if not os.path.isabs(pattern):
        pattern = str(workdir / pattern)
    import glob as _glob
    for path_str in _glob.glob(pattern):
        path = Path(path_str)
        try:
            ir = _read_json(path)
        except Exception:
            continue
        nid = ir.get("note_id", "")
        if nid:
            out[nid] = path
    return out


def _pass_link_debt(workdir: Path, irs_glob: str) -> Tuple[int, Path]:
    note_ids = _iter_note_ids(workdir, irs_glob)
    targets = _iter_link_targets(workdir, irs_glob)
    manifest = _load_or_create_manifest(workdir)
    debt = manifest.setdefault("link_debt", [])
    existing = {(d.get("from_note"), d.get("target"), d.get("kind"))
                 for d in debt if isinstance(d, dict)}
    now = _utc_now_iso()
    new_entries: List[Dict[str, Any]] = []
    incoming: Dict[str, int] = {}
    # Detectar broken-wikilink + missing-target.
    for path, target, parent_id in targets:
        incoming[path] = incoming.get(path, 0)
        if target is None or target == "":
            key = (parent_id, target or "", "missing-target")
            if key not in existing:
                new_entries.append({
                    "from_note": parent_id, "target": target or "",
                    "kind": "missing-target", "detected_at": now,
                })
        elif target not in note_ids:
            key = (parent_id, target, "broken-wikilink")
            if key not in existing:
                new_entries.append({
                    "from_note": parent_id, "target": target,
                    "kind": "broken-wikilink", "detected_at": now,
                })
        else:
            incoming[target] = incoming.get(target, 0) + 1
    # Detectar orphan-note: nota sin ningún incoming link.
    for nid, path in note_ids.items():
        if incoming.get(nid, 0) == 0:
            key = (nid, nid, "orphan-note")
            if key not in existing:
                new_entries.append({
                    "from_note": nid, "target": nid,
                    "kind": "orphan-note", "detected_at": now,
                })
    debt.extend(new_entries)
    manifest["link_debt"] = debt
    _save_manifest(workdir, manifest)
    # Generar reporte. NOTA: el contenido es DETERMINISTA — solo contiene
    # el estado actual de `link_debt[]` (count_by_kind, total); NO incluye
    # `new_entries` para garantizar idempotencia entre runs (CON-R1).
    reports_dir = workdir / REPORTS_SUBDIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now,
        "total_link_debt": len(debt),
        "count_by_kind": {
            "broken-wikilink": sum(1 for d in debt if d.get("kind") == "broken-wikilink"),
            "missing-target": sum(1 for d in debt if d.get("kind") == "missing-target"),
            "orphan-note": sum(1 for d in debt if d.get("kind") == "orphan-note"),
            "redirected": sum(1 for d in debt if d.get("kind") == "redirected"),
            "external-dead": sum(1 for d in debt if d.get("kind") == "external-dead"),
        },
    }
    report_path = reports_dir / "report-link-debt.json"
    _atomic_write_json(report_path, report)
    # Las nuevas entradas (delta) se persisten en un archivo separado para
    # inspección; este SÍ cambia entre runs (es el delta del run actual).
    if new_entries:
        delta_path = reports_dir / "link-debt-delta.json"
        _atomic_write_json(delta_path, {
            "schema_version": SCHEMA_VERSION,
            "generated_at": now,
            "delta": new_entries,
        })
    return EXIT_OK, report_path


# ============================================================
# Pase 2 — glossary
# ============================================================


def _pass_glossary(workdir: Path) -> Tuple[int, Path]:
    glossary_path = workdir / "knowledge" / "glossary.json"
    if not glossary_path.exists():
        reports_dir = workdir / REPORTS_SUBDIR
        reports_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _utc_now_iso(),
            "glossary_exists": False,
            "r3_violations": [],
            "new_term_candidates": [],
        }
        report_path = reports_dir / "report-glossary.json"
        _atomic_write_json(report_path, report)
        return EXIT_OK, report_path
    glossary = _read_json(glossary_path)
    # R3: alias único.
    alias_to_terms: Dict[str, List[str]] = {}
    for t in glossary.get("terms", []):
        canonical = t.get("canonical", "").strip().lower()
        for a in t.get("aliases", []) or []:
            if isinstance(a, dict):
                alias_norm = re.sub(r"[^a-z0-9]+", "-", a.get("alias", "").lower()).strip("-")
            else:
                alias_norm = re.sub(r"[^a-z0-9]+", "-", str(a).lower()).strip("-")
            if not alias_norm:
                continue
            alias_to_terms.setdefault(alias_norm, []).append(t.get("canonical", ""))
    r3_violations = [
        {"alias": a, "terms": terms}
        for a, terms in alias_to_terms.items() if len(terms) > 1
    ]
    # R8: nuevos términos en IRs concept/glossary-term.
    new_term_candidates: List[Dict[str, str]] = []
    known_canonicals = {t.get("canonical", "").strip().lower()
                         for t in glossary.get("terms", [])}
    known_aliases = set(alias_to_terms.keys())
    import re as _re
    SECTION_RE = _re.compile(
        r"^##\s+(?:Definici[oó]n|TL;DR)\s*\n(.*?)(?=^##\s+|\Z)",
        _re.MULTILINE | _re.DOTALL,
    )
    import glob as _glob
    for path_str in _glob.glob(str(workdir / "ir" / "*.json")):
        try:
            ir = _read_json(Path(path_str))
        except Exception:
            continue
        note_type = ir.get("note_type") or ir.get("frontmatter", {}).get("note-type", "")
        if note_type not in ("concept", "glossary-term"):
            continue
        body = json.dumps(ir)
        m = SECTION_RE.search(body)
        if not m:
            continue
        text = m.group(1)[:500]
        # Heurística simple: tokens capitalized de 3+ letras.
        tokens = _re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)
        for t in tokens:
            norm = t.lower()
            if norm in known_canonicals or norm in known_aliases:
                continue
            new_term_candidates.append({
                "candidate": t, "note_id": ir.get("note_id", ""),
            })
    reports_dir = workdir / REPORTS_SUBDIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "glossary_exists": True,
        "r3_violations": r3_violations,
        "new_term_candidates": new_term_candidates[:50],
    }
    report_path = reports_dir / "report-glossary.json"
    _atomic_write_json(report_path, report)
    return (EXIT_VALIDATION if r3_violations else EXIT_OK), report_path


# ============================================================
# Pase 3 — indices
# ============================================================


def _pass_indices(workdir: Path) -> Tuple[int, Path]:
    by_type: Dict[str, int] = {}
    by_chapter: Dict[str, int] = {}
    import glob as _glob
    for path_str in _glob.glob(str(workdir / "ir" / "*.json")):
        try:
            ir = _read_json(Path(path_str))
        except Exception:
            continue
        nt = ir.get("note_type") or ir.get("frontmatter", {}).get("note-type", "unknown")
        by_type[nt] = by_type.get(nt, 0) + 1
        # Buscar book-state.json para chapter info.
        book_state_path = workdir / "book-state.json"
        if book_state_path.exists():
            book_state = _read_json(book_state_path)
            nid = ir.get("note_id", "")
            for ch in book_state.get("chapters", []):
                if nid in (ch.get("notes") or []):
                    by_chapter[ch["id"]] = by_chapter.get(ch["id"], 0) + 1
                    break
    reports_dir = workdir / REPORTS_SUBDIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "by_type": by_type,
        "by_chapter": by_chapter,
        "total_notes": sum(by_type.values()),
    }
    report_path = reports_dir / "index-moc-summary.json"
    _atomic_write_json(report_path, report)
    return EXIT_OK, report_path


# ============================================================
# Pase 4 — cheatsheets
# ============================================================


def _pass_cheatsheets(workdir: Path) -> Tuple[int, Path]:
    cheatsheets: List[Dict[str, str]] = []
    import glob as _glob
    for path_str in _glob.glob(str(workdir / "ir" / "*.json")):
        try:
            ir = _read_json(Path(path_str))
        except Exception:
            continue
        nt = ir.get("note_type") or ir.get("frontmatter", {}).get("note-type", "")
        if nt != "cheatsheet":
            continue
        fm = ir.get("frontmatter", {}) or {}
        cheatsheets.append({
            "note_id": ir.get("note_id", ""),
            "title": fm.get("title", ir.get("title", "")),
            "source_anchor": fm.get("source-anchor", fm.get("source_anchor", "")),
        })
    reports_dir = workdir / REPORTS_SUBDIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    index_path = reports_dir / "cheatsheets-index.json"
    _atomic_write_json(index_path, {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "cheatsheets": cheatsheets,
        "count": len(cheatsheets),
    })
    paths_path = reports_dir / "study-paths.json"
    _atomic_write_json(paths_path, {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "paths": [
            {"id": "MVP", "steps": [c["note_id"] for c in cheatsheets[:3]]},
        ] if cheatsheets else [],
        "note": "stub; F104 paths will refine",
    })
    return EXIT_OK, index_path


# ============================================================
# Pase 5 — consistency (delega en F108)
# ============================================================


def _pass_consistency(workdir: Path, threshold: Optional[float],
                        detector_path: Path) -> Tuple[int, Path]:
    reports_dir = workdir / REPORTS_SUBDIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "consistency-report.json"
    args = [sys.executable, str(detector_path), "scan",
            "--workdir", str(workdir),
            "--json-out", str(out_path)]
    if threshold is not None:
        args.extend(["--threshold", str(threshold)])
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        sys.stderr.write(f"FAIL: detect.py rc={proc.returncode}\n{proc.stderr}\n")
        return EXIT_VALIDATION, out_path
    return EXIT_OK, out_path


# ============================================================
# Orquestador run-all
# ============================================================


def _find_detector(workdir: Path) -> Path:
    candidates = [
        workdir.parent.parent / "skill" / "notemartin-study-notes" / "scripts" / "dedup" / "detect.py",
        workdir.parent / "scripts" / "dedup" / "detect.py",
        Path(__file__).resolve().parents[2] / "scripts" / "dedup" / "detect.py",
        Path("/Users/martin/Desktop/projects/notemartin-study-notes/skill/notemartin-study-notes/scripts/dedup/detect.py"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("dedup/detect.py no encontrado")


def cmd_run_all(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}: {workdir}\n")
        return EXIT_USAGE
    irs_glob = args.irs_glob or DEFAULT_IR_GLOB
    strategy = args.strategy or "default"
    import uuid as _uuid
    run_id = str(_uuid.uuid4())
    started_at = _utc_now_iso()
    manifest = _load_or_create_manifest(workdir)
    runs = manifest.setdefault("consolidation_runs", [])
    run_entry: Dict[str, Any] = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": None,
        "status": "running",
        "strategy": strategy,
        "passes": [],
    }
    runs.append(run_entry)
    _save_manifest(workdir, manifest)

    pass_results: List[Dict[str, Any]] = []
    failed: Optional[str] = None

    def _record_pass(name: str, rc: int, sha_input: Optional[str],
                       sha_output: str, duration_ms: int) -> None:
        pass_results.append({
            "name": name,
            "exit_code": rc,
            "sha256_input": sha_input,
            "sha256_output": sha_output,
            "duration_ms": duration_ms,
            "started_at": _utc_now_iso(),
            "finished_at": _utc_now_iso(),
        })

    def _sha_workdir_reports() -> str:
        """Hash del contenido SEMÁNTICO de reports/ (excluye .bak y generated_at).
        Garantiza que `after_sha256` sea estable entre runs sin cambios en inputs
        (CON-R1)."""
        rep = workdir / REPORTS_SUBDIR
        if not rep.exists():
            return _sha256_bytes(b"")
        h = hashlib.sha256()
        for p in sorted(rep.rglob("*")):
            if not p.is_file():
                continue
            if p.suffix == ".bak":
                continue
            if p.suffix == ".json":
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    data.pop("generated_at", None)
                    text = json.dumps(data, indent=2, sort_keys=True,
                                       ensure_ascii=False)
                except Exception:
                    text = p.read_text(encoding="utf-8")
            else:
                text = p.read_text(encoding="utf-8")
            h.update(text.encode("utf-8"))
        return h.hexdigest()

    before_sha = _sha_workdir_reports()

    # Pase 1.
    p1_started = _utc_now_iso()
    rc1, p1_path = _pass_link_debt(workdir, irs_glob)
    p1_finished = _utc_now_iso()
    _record_pass("link-debt", rc1, None,
                  _sha256_file(p1_path) or "",
                  _duration_ms(p1_started, p1_finished))
    if rc1 != EXIT_OK:
        failed = "link-debt"

    if failed is None:
        p2_started = _utc_now_iso()
        rc2, p2_path = _pass_glossary(workdir)
        p2_finished = _utc_now_iso()
        _record_pass("glossary", rc2, None,
                      _sha256_file(p2_path) or "",
                      _duration_ms(p2_started, p2_finished))
        # rc2 puede ser 1 si hay R3 violations; no aborta run-all.

    if failed is None:
        p3_started = _utc_now_iso()
        rc3, p3_path = _pass_indices(workdir)
        p3_finished = _utc_now_iso()
        _record_pass("indices", rc3, None,
                      _sha256_file(p3_path) or "",
                      _duration_ms(p3_started, p3_finished))
        if rc3 != EXIT_OK:
            failed = "indices"

    if failed is None:
        p4_started = _utc_now_iso()
        rc4, p4_path = _pass_cheatsheets(workdir)
        p4_finished = _utc_now_iso()
        _record_pass("cheatsheets", rc4, None,
                      _sha256_file(p4_path) or "",
                      _duration_ms(p4_started, p4_finished))
        if rc4 != EXIT_OK:
            failed = "cheatsheets"

    if failed is None:
        try:
            detector = _find_detector(workdir)
        except FileNotFoundError as e:
            sys.stderr.write(f"FAIL: {ERR_RUN_FAILED}: {e}\n")
            failed = "consistency"
            p5_path = workdir / REPORTS_SUBDIR / "consistency-report.json"
        else:
            p5_started = _utc_now_iso()
            rc5, p5_path = _pass_consistency(workdir, args.threshold, detector)
            p5_finished = _utc_now_iso()
            _record_pass("consistency", rc5, None,
                          _sha256_file(p5_path) or "",
                          _duration_ms(p5_started, p5_finished))
            if rc5 != EXIT_OK:
                failed = "consistency"

    after_sha = _sha_workdir_reports()
    manifest = _load_or_create_manifest(workdir)
    runs = manifest.setdefault("consolidation_runs", [])
    for r in runs:
        if r.get("run_id") == run_id:
            r["finished_at"] = _utc_now_iso()
            r["status"] = "failed" if failed else "done"
            r["passes"] = pass_results
            r["before_sha256"] = before_sha
            r["after_sha256"] = after_sha
            break
    _save_manifest(workdir, manifest)
    if failed:
        sys.stderr.write(f"FAIL: {ERR_RUN_FAILED} (pase {failed})\n")
        return EXIT_VALIDATION
    sys.stdout.write(
        f"OK — run-all done ({len(pass_results)} pases; after_sha256={after_sha[:12]}...)\n"
    )
    return EXIT_OK


def _duration_ms(start_iso: str, end_iso: str) -> int:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        s = datetime.strptime(start_iso, fmt)
        e = datetime.strptime(end_iso, fmt)
        return max(0, int((e - s).total_seconds() * 1000))
    except Exception:
        return 0


# ============================================================
# CLI wrappers para pases individuales
# ============================================================


def cmd_pass_link_debt(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}\n")
        return EXIT_USAGE
    rc, _ = _pass_link_debt(workdir, args.irs_glob or DEFAULT_IR_GLOB)
    return rc


def cmd_pass_glossary(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}\n")
        return EXIT_USAGE
    rc, _ = _pass_glossary(workdir)
    return rc


def cmd_pass_indices(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}\n")
        return EXIT_USAGE
    rc, _ = _pass_indices(workdir)
    return rc


def cmd_pass_cheatsheets(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}\n")
        return EXIT_USAGE
    rc, _ = _pass_cheatsheets(workdir)
    return rc


def cmd_pass_consistency(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}\n")
        return EXIT_USAGE
    try:
        detector = _find_detector(workdir)
    except FileNotFoundError as e:
        sys.stderr.write(f"FAIL: {ERR_RUN_FAILED}: {e}\n")
        return EXIT_VALIDATION
    rc, _ = _pass_consistency(workdir, args.threshold, detector)
    return rc


# ============================================================
# CLI main
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F109 — Orquestador de pases de consolidación.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run-all", help="Ejecuta los 5 pases en orden")
    p_run.add_argument("--workdir", required=True)
    p_run.add_argument("--strategy", default="default",
                        choices=["default", "consolidate", "single-chunk"])
    p_run.add_argument("--irs-glob", default=DEFAULT_IR_GLOB)
    p_run.add_argument("--notemark-glob", default=DEFAULT_NOTEMARK_GLOB)
    p_run.add_argument("--threshold", type=float, default=None)
    p_run.set_defaults(func=cmd_run_all)

    p_link = sub.add_parser("pass-link-debt", help="Solo pase 1")
    p_link.add_argument("--workdir", required=True)
    p_link.add_argument("--irs-glob", default=DEFAULT_IR_GLOB)
    p_link.add_argument("--notemark-glob", default=DEFAULT_NOTEMARK_GLOB)
    p_link.set_defaults(func=cmd_pass_link_debt)

    p_gloss = sub.add_parser("pass-glossary", help="Solo pase 2")
    p_gloss.add_argument("--workdir", required=True)
    p_gloss.set_defaults(func=cmd_pass_glossary)

    p_idx = sub.add_parser("pass-indices", help="Solo pase 3")
    p_idx.add_argument("--workdir", required=True)
    p_idx.set_defaults(func=cmd_pass_indices)

    p_cht = sub.add_parser("pass-cheatsheets", help="Solo pase 4")
    p_cht.add_argument("--workdir", required=True)
    p_cht.set_defaults(func=cmd_pass_cheatsheets)

    p_cons = sub.add_parser("pass-consistency", help="Solo pase 5 (F108)")
    p_cons.add_argument("--workdir", required=True)
    p_cons.add_argument("--threshold", type=float, default=None)
    p_cons.set_defaults(func=cmd_pass_consistency)

    return p


import re  # noqa: F811  (also imported at top)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())