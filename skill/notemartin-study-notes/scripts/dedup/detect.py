#!/usr/bin/env python3
"""detect.py — F108 detector de duplicados entre notas.

Escanea todos los IRs / NoteMark files del workdir y produce una lista
de pares candidatos a `merge` / `specialize` / `split` por matching de
término canónico, alias, y similitud textual.

Uso (CLI):
    detect.py scan --workdir DIR [--strategy {default,consolidate,single-chunk}]
                   [--threshold 0.6] [--json-out PATH]
    detect.py inspect --pair NOTE_A NOTE_B --workdir DIR
    detect.py explain --candidate-id N --workdir DIR
    detect.py verify --workdir DIR   # recall contra fixtures inyectadas

Uso como biblioteca:
    from detect import Detector, Candidate
    det = Detector(workdir=Path("."), glossary=Path("glossary.json"))
    cands = det.scan()

Códigos de salida: 0 OK · 1 validación · 2 uso.
Dependencias: Python 3.9+ stdlib puro. Sin jsonschema.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
DEFAULT_SIMILARITY_THRESHOLD = 0.6
MIN_NOTES_TO_RUN = 5
SUPPORTED_NOTE_TYPES = {
    "concept", "glossary-term", "procedure", "api-reference",
    "configuration", "error-troubleshooting", "architecture",
    "syntax", "data-model", "comparison",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)
SECTION_TEXT_RE = re.compile(
    r"^##\s+(?:Definici[oó]n|TL;DR|Resumen)\s*\n(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)


# ============================================================
# Utilidades de extracción
# ============================================================


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    fm: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None
    for line in fm_raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current_list is not None:
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue
        m_kv = re.match(r"^([a-z0-9_-]+):\s*(.*)$", stripped)
        if not m_kv:
            continue
        key, value = m_kv.group(1), m_kv.group(2).strip()
        if value == "":
            fm[key] = []
            current_list = fm[key]
            current_key = key
            continue
        current_list = None
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if inner:
                fm[key] = [
                    p.strip().strip('"').strip("'")
                    for p in inner.split(",")
                ]
            else:
                fm[key] = []
        elif value.startswith('"') and value.endswith('"'):
            fm[key] = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            fm[key] = value[1:-1]
        elif re.match(r"^-?\d+$", value):
            fm[key] = int(value)
        elif value.lower() in ("true", "false"):
            fm[key] = value.lower() == "true"
        else:
            fm[key] = value
        current_key = key
    return fm, body


def _extract_section_text(body: str) -> str:
    m = SECTION_TEXT_RE.search(body)
    if m:
        return m.group(1).strip()
    # Fallback: primer párrafo no vacío.
    for para in body.split("\n\n"):
        para = para.strip()
        if para and not para.startswith("#") and not para.startswith("|"):
            return para
    return ""


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _aliases_from_frontmatter(fm: Dict[str, Any]) -> List[str]:
    raw = fm.get("aliases", [])
    if isinstance(raw, list):
        return [str(a) for a in raw]
    if isinstance(raw, str):
        return [raw]
    return []


def _slugify_for_id(text: str) -> str:
    return _normalize(text)[:64].strip("-") or "x"


@dataclass
class NoteRecord:
    note_id: str
    title: str
    note_type: str
    aliases: List[str]
    body_text: str
    fm: Dict[str, Any]
    path: Path

    def canonicals(self) -> List[str]:
        """Términos canónicos derivados del note_id + title + aliases."""
        return [self.note_id, _normalize(self.title)] + [
            _normalize(a) for a in self.aliases
        ]

    def key(self) -> str:
        return self.note_id


# ============================================================
# Modelo: Candidate
# ============================================================


@dataclass
class Candidate:
    pair: List[str]
    scores: Dict[str, float]
    suggested_action: str
    confidence: float
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "scores": self.scores,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


# ============================================================
# Detector
# ============================================================


class Detector:
    def __init__(
        self,
        workdir: Path,
        glossary: Optional[Path] = None,
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ):
        self.workdir = Path(workdir).resolve()
        self.threshold = threshold
        self.glossary_terms: List[Dict[str, Any]] = []
        self.glossary_aliases: Dict[str, str] = {}
        if glossary and glossary.exists():
            data = json.loads(glossary.read_text(encoding="utf-8"))
            self.glossary_terms = data.get("terms", [])
            for t in self.glossary_terms:
                canonical = _normalize(t.get("canonical", ""))
                if canonical:
                    self.glossary_aliases[canonical] = t.get("canonical", "")
                for a in t.get("aliases", []):
                    if isinstance(a, dict):
                        alias_norm = _normalize(a.get("alias", ""))
                        if alias_norm:
                            self.glossary_aliases[alias_norm] = t.get("canonical", "")

    def load_notes(self) -> List[NoteRecord]:
        notes: List[NoteRecord] = []
        seen_ids: Dict[str, NoteRecord] = {}
        for path in self.workdir.rglob("*"):
            if path.suffix not in (".md", ".nm"):
                continue
            try:
                text = _read_text(path)
            except (UnicodeDecodeError, OSError):
                continue
            fm, body = _parse_frontmatter(text)
            note_id = fm.get("note-id") or fm.get("title") or path.stem
            note_id = str(note_id).strip()
            if not note_id:
                note_id = path.stem
            note_id_slug = _slugify_for_id(note_id)
            note_id = note_id_slug
            note_type = str(fm.get("note-type", "")).strip()
            if note_type not in SUPPORTED_NOTE_TYPES:
                continue
            title = str(fm.get("title", "")).strip()
            aliases = _aliases_from_frontmatter(fm)
            body_text = _extract_section_text(body)
            rec = NoteRecord(
                note_id=note_id,
                title=title,
                note_type=note_type,
                aliases=aliases,
                body_text=body_text,
                fm=fm,
                path=path,
            )
            if note_id in seen_ids:
                continue
            seen_ids[note_id] = rec
            notes.append(rec)
        return notes

    @staticmethod
    def _canonical_score(a: NoteRecord, b: NoteRecord,
                        glossary_aliases: Dict[str, str]) -> float:
        a_terms = set(a.canonicals())
        b_terms = set(b.canonicals())
        if a_terms & b_terms:
            return 1.0
        # Cross with glossary.
        if glossary_aliases:
            for term in a_terms:
                if term in glossary_aliases:
                    canonical = _normalize(glossary_aliases[term])
                    if canonical in b_terms:
                        return 1.0
            for term in b_terms:
                if term in glossary_aliases:
                    canonical = _normalize(glossary_aliases[term])
                    if canonical in a_terms:
                        return 1.0
        return 0.0

    @staticmethod
    def _alias_score(a: NoteRecord, b: NoteRecord) -> float:
        a_aliases = {_normalize(x) for x in a.aliases if x}
        b_aliases = {_normalize(x) for x in b.aliases if x}
        if not a_aliases or not b_aliases:
            return 0.0
        return 1.0 if a_aliases & b_aliases else 0.0

    @staticmethod
    def _similarity_score(a: NoteRecord, b: NoteRecord) -> float:
        if not a.body_text or not b.body_text:
            return 0.0
        return difflib.SequenceMatcher(
            None, a.body_text[:4000], b.body_text[:4000]
        ).ratio()

    def evaluate_pair(self, a: NoteRecord, b: NoteRecord) -> Optional[Candidate]:
        if a.note_id == b.note_id:
            return None
        canonical = self._canonical_score(a, b, self.glossary_aliases)
        alias = self._alias_score(a, b)
        sim = self._similarity_score(a, b)
        combined = max(canonical, alias, sim)
        # Si NO hay match canónico/alias y la similitud es muy baja,
        # descartar (no es candidato).
        if sim < 0.3 and canonical == 0.0 and alias == 0.0:
            return None
        # Si solo hay similitud y está por debajo del umbral de specialize
        # (0.4), descartar.
        if canonical == 0.0 and alias == 0.0 and sim < 0.4:
            return None
        # Decide action.
        if canonical >= 1.0 or alias >= 1.0:
            action = "merge"
            conf = 0.95
            rationale = (
                f"canonical match" if canonical >= 1.0 else "alias match"
            )
            if sim >= 0.3 and sim < 0.5:
                # High overlap on name but divergent text: conflict (F41).
                action = "conflict"
                conf = 0.7
                rationale += f"; similarity {sim:.2f} suggests conflict"
        elif sim >= 0.85:
            action = "merge"
            conf = sim
            rationale = f"similarity {sim:.2f} ≥ 0.85"
        elif sim >= 0.6:
            action = "specialize"
            conf = sim
            rationale = f"similarity {sim:.2f} suggests specialization"
        else:
            action = "review"
            conf = combined
            rationale = f"combined {combined:.2f} below merge threshold"
        return Candidate(
            pair=sorted([a.note_id, b.note_id]),
            scores={
                "canonical": round(canonical, 3),
                "alias": round(alias, 3),
                "similarity": round(sim, 3),
                "combined": round(combined, 3),
            },
            suggested_action=action,
            confidence=round(conf, 3),
            rationale=rationale,
        )

    def scan(self) -> List[Candidate]:
        notes = self.load_notes()
        if len(notes) < MIN_NOTES_TO_RUN:
            sys.stderr.write(
                f"WARN: corpus tiene {len(notes)} notas (< {MIN_NOTES_TO_RUN}); "
                f"scan produce 0 candidatos\n"
            )
            return []
        candidates: List[Candidate] = []
        for i in range(len(notes)):
            for j in range(i + 1, len(notes)):
                if notes[i].note_type != notes[j].note_type:
                    continue
                cand = self.evaluate_pair(notes[i], notes[j])
                if cand is not None:
                    candidates.append(cand)
        candidates.sort(key=lambda c: (-c.confidence, c.pair))
        return candidates


# ============================================================
# CLI
# ============================================================


def cmd_scan(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: workdir no encontrado: {workdir}\n")
        return EXIT_USAGE
    glossary = Path(args.glossary).resolve() if args.glossary else None
    threshold = args.threshold if args.threshold is not None else DEFAULT_SIMILARITY_THRESHOLD
    det = Detector(workdir=workdir, glossary=glossary, threshold=threshold)
    candidates = det.scan()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "workdir": str(workdir),
        "strategy": args.strategy,
        "threshold": threshold,
        "candidate_count": len(candidates),
        "candidates": [c.to_dict() for c in candidates],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.json_out:
        out = Path(args.json_out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        sys.stdout.write(f"OK — wrote {len(candidates)} candidates to {out}\n")
    else:
        sys.stdout.write(text + "\n")
    return EXIT_OK


def cmd_inspect(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    glossary = Path(args.glossary).resolve() if args.glossary else None
    det = Detector(workdir=workdir, glossary=glossary)
    notes = {n.note_id: n for n in det.load_notes()}
    if args.pair[0] not in notes or args.pair[1] not in notes:
        sys.stderr.write(
            f"FAIL: una o ambas notas no encontradas: {args.pair}\n"
        )
        return EXIT_USAGE
    cand = det.evaluate_pair(notes[args.pair[0]], notes[args.pair[1]])
    if cand is None:
        sys.stdout.write(
            f"OK — par {args.pair} no es candidato (combined<threshold)\n"
        )
        return EXIT_OK
    sys.stdout.write(json.dumps(cand.to_dict(), indent=2, ensure_ascii=False) + "\n")
    return EXIT_OK


def cmd_explain(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    glossary = Path(args.glossary).resolve() if args.glossary else None
    det = Detector(workdir=workdir, glossary=glossary)
    candidates = det.scan()
    if args.candidate_id < 0 or args.candidate_id >= len(candidates):
        sys.stderr.write(
            f"FAIL: candidate-id fuera de [0, {len(candidates) - 1}]\n"
        )
        return EXIT_USAGE
    c = candidates[args.candidate_id]
    sys.stdout.write(json.dumps(c.to_dict(), indent=2, ensure_ascii=False) + "\n")
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    """Recall contra fixtures inyectadas. El fixture debe tener un archivo
    `expected/candidates.json` con la lista de pares ground-truth."""
    workdir = Path(args.workdir).resolve()
    expected_path = workdir / "expected" / "candidates.json"
    if not expected_path.exists():
        sys.stderr.write(f"FAIL: {expected_path} no existe\n")
        return EXIT_USAGE
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_pairs = {
        tuple(sorted(c["pair"])) for c in expected.get("candidates", [])
    }
    det = Detector(workdir=workdir, glossary=None,
                    threshold=DEFAULT_SIMILARITY_THRESHOLD)
    actual = det.scan()
    actual_pairs = {tuple(sorted(c.pair)) for c in actual}
    if not expected_pairs:
        sys.stderr.write("FAIL: expected_pairs vacío\n")
        return EXIT_USAGE
    hits = expected_pairs & actual_pairs
    recall = len(hits) / len(expected_pairs)
    sys.stdout.write(
        f"recall: {recall:.2f} ({len(hits)}/{len(expected_pairs)})\n"
        f"actual: {len(actual_pairs)} pairs; expected: {len(expected_pairs)} pairs\n"
    )
    return EXIT_OK if recall >= 0.8 else EXIT_VALIDATION


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F108 — Detector de duplicados entre notas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Escanear corpus y emitir candidatos")
    p_scan.add_argument("--workdir", required=True)
    p_scan.add_argument("--strategy", default="default",
                        choices=["default", "consolidate", "single-chunk"])
    p_scan.add_argument("--threshold", type=float, default=None)
    p_scan.add_argument("--glossary", default=None)
    p_scan.add_argument("--json-out", default=None)
    p_scan.set_defaults(func=cmd_scan)

    p_inspect = sub.add_parser("inspect", help="Evaluar un par específico")
    p_inspect.add_argument("--workdir", required=True)
    p_inspect.add_argument("--pair", nargs=2, required=True, metavar=("NOTE_A", "NOTE_B"))
    p_inspect.add_argument("--glossary", default=None)
    p_inspect.set_defaults(func=cmd_inspect)

    p_explain = sub.add_parser("explain", help="Explicar candidato N")
    p_explain.add_argument("--workdir", required=True)
    p_explain.add_argument("--candidate-id", type=int, required=True)
    p_explain.add_argument("--glossary", default=None)
    p_explain.set_defaults(func=cmd_explain)

    p_verify = sub.add_parser("verify", help="Recall contra fixtures inyectadas")
    p_verify.add_argument("--workdir", required=True)
    p_verify.set_defaults(func=cmd_verify)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())