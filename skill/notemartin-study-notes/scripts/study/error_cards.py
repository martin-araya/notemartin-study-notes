#!/usr/bin/env python3
"""Generador de tarjetas prioritarias desde living-docs de errores — Fase 103.

Implementa las 4 reglas C1-C4 definidas en
`references/09-study/error-log.md` §7:

  C1 — Una entrada, una tarjeta (rechaza si no genera).
  C2 — Anverso = primer bloque `:::code` de `### Comando erróneo` (≥ 3 palabras).
  C3 — Reverso = primer bloque `:::code` de `### Corrección` + `[[note:id]]`.
  C4 — Tag = `priority-error`, scheduling = `review-next` de la entrada.

Antes de generar, valida AP16 (lenguaje de evaluación personal) cargando
la lista cerrada de 16 frases prohibidas desde
`references/09-study/error-log.md` §4 (anchor `{#lista-cerrada-prohibidos}`).

CLI:
    python3 error_cards.py --domain postgresql                      # un dominio
    python3 error_cards.py --domain postgresql --format anki-csv    # formato Anki
    python3 error_cards.py --domain postgresql --out-dir /tmp/cards
    python3 error_cards.py --errors-dir /path/to/study/errors

Exit codes:
    0  OK (≥ 1 tarjeta generada)
    1  ninguna tarjeta generada o alguna rechazada por C1-C4 / AP16
    2  error de uso o lista cerrada no encontrada

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


DOC_PATH = (
    Path(__file__).resolve().parents[4]
    / "skill" / "notemartin-study-notes" / "references" / "09-study" / "error-log.md"
)

ERROR_H3_RE = re.compile(r"^###\s+Error\s+([\w\-]+(?:-[\w\-]+)*)\s*$", re.MULTILINE)
CODE_BLOCK_RE = re.compile(
    r":::code\s*\n(.*?)\n\s*:::",
    re.DOTALL,
)
NOTE_LINK_RE = re.compile(r"\[\[note:([a-z0-9][a-z0-9\-]*(?:#[\w\-§]+)?)\]\]")


@dataclass
class Card:
    domain: str
    error_id: str
    anverso: str
    reverso: str
    note_link: str
    review_next: str
    source_path: Path


@dataclass
class GenerationReport:
    cards: List[Card] = field(default_factory=list)
    rejected: List[Tuple[Path, str, str]] = field(default_factory=list)
    ap16_detected: List[Tuple[Path, str]] = field(default_factory=list)


def _load_prohibited_list(doc_path: Path) -> List[str]:
    """Carga la lista cerrada de 16 frases prohibidas desde §4 del doc principal.

    Busca el anchor `{#lista-cerrada-prohibidos}` y parsea las 16 frases
    de la columna 2 de la tabla. Si el anchor no se encuentra, falla
    con `prohibited-list-not-found`.
    """
    if not doc_path.exists():
        raise FileNotFoundError(f"doc principal no encontrado: {doc_path}")

    text = doc_path.read_text(encoding="utf-8")
    if "{#lista-cerrada-prohibidos}" not in text:
        raise ValueError(
            "prohibited-list-not-found: anchor {#lista-cerrada-prohibidos} "
            f"ausente en {doc_path}"
        )

    sec4_match = re.search(
        r"## §4 · Lenguaje de evaluación personal.*?(?=^## §5)",
        text, re.MULTILINE | re.DOTALL,
    )
    if not sec4_match:
        raise ValueError("no se encuentra §4 en el doc principal")

    sec4 = sec4_match.group(0)
    # Frases en la columna 2 (celda con la frase prohibida).
    rows = re.findall(
        r"^\|\s*\d+\s*\|\s*[^\|]+\|\s*\"([^\"]+)\"",
        sec4, re.MULTILINE,
    )
    if len(rows) < 12:
        raise ValueError(
            f"§4 tiene {len(rows)} frases (esperaba ≥ 12): {rows}"
        )
    return rows


def _parse_frontmatter(text: str) -> Tuple[dict, str]:
    fm: dict = {}
    if not text.startswith("---"):
        return fm, text
    end = text.find("\n---", 3)
    if end < 0:
        return fm, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, body


def _extract_section(body: str, h4: str) -> str:
    pattern = re.compile(
        rf"^####\s+{re.escape(h4)}\s*$(.*?)(?=^####\s+|^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def _first_code_block(text: str) -> str:
    m = CODE_BLOCK_RE.search(text)
    return m.group(1).strip() if m else ""


def _has_autocritica(prosa: str, prohibited: List[str]) -> Optional[str]:
    """Busca frases prohibidas en prosa narrativa. Devuelve la frase matchada o None.

    Heurística R-E6: omite líneas que estén dentro de bloques `:::code`
    verbatim (mensajes de error literales contienen palabras como "fail").
    La prosa se recibe ya extraída fuera de code fences.
    """
    prosa_l = prosa.lower()
    for frase in prohibited:
        norm = frase.lower()
        norm = re.sub(r"\s*x\b", "", norm)
        norm = norm.strip()
        if not norm:
            continue
        if norm in prosa_l:
            return frase
    return None


def _strip_code_blocks(text: str) -> str:
    """Quita bloques `:::code` para obtener solo prosa narrativa."""
    return CODE_BLOCK_RE.sub("", text)


def _generate_for_file(
    path: Path,
    domain: str,
    prohibited: List[str],
    report: GenerationReport,
) -> List[Card]:
    text = path.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(text)

    matches = list(ERROR_H3_RE.finditer(body))
    cards: List[Card] = []
    for idx, m in enumerate(matches):
        error_id = m.group(1)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        section = body[start:end]

        # C2: anverso verbatim del primer code block de Comando erróneo.
        cmd_section = _extract_section(section, "Comando erróneo")
        anverso = _first_code_block(cmd_section)
        if len(anverso.split()) < 3:
            report.rejected.append((path, error_id, "anverso-too-short"))
            continue

        # C3: reverso del primer code block de Corrección + note link.
        corr_section = _extract_section(section, "Corrección")
        reverso_code = _first_code_block(corr_section)
        note_match = NOTE_LINK_RE.search(corr_section)
        note_link = f"[[note:{note_match.group(1)}]]" if note_match else ""
        if not reverso_code:
            report.rejected.append((path, error_id, "missing-correction"))
            continue
        if not note_link:
            report.rejected.append((path, error_id, "missing-canonical-link"))
            continue
        reverso = f"{reverso_code}  📚 {note_link}"

        # C4: review-next.
        repaso = _extract_section(section, "Repaso")
        rn_match = re.search(r"review-next:\s*(\d{4}-\d{2}-\d{2})", repaso, re.IGNORECASE)
        if not rn_match:
            report.rejected.append((path, error_id, "missing-review-next"))
            continue
        review_next = rn_match.group(1)

        # AP16: detectar autocrítica en prosa narrativa.
        prosa_total = _strip_code_blocks(section)
        prohibited_match = _has_autocritica(prosa_total, prohibited)
        if prohibited_match:
            report.ap16_detected.append((path, f"{error_id}: '{prohibited_match}'"))
            report.rejected.append((path, error_id, "card-rejected-autocritica"))
            continue

        cards.append(Card(
            domain=domain,
            error_id=error_id,
            anverso=anverso,
            reverso=reverso,
            note_link=note_link,
            review_next=review_next,
            source_path=path,
        ))

    return cards


def _format_obsidian_sr(card: Card) -> str:
    """Formato Obsidian Spaced Repetition plugin."""
    return (
        f"¿{card.anverso}? :: {card.reverso}  "
        f"#priority-error ⏰ {card.review_next}"
    )


def _format_anki_csv(card: Card) -> List[str]:
    """Formato Anki CSV (RFC 4180)."""
    return [card.anverso, card.reverso, "priority-error", card.review_next]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="error_cards.py",
        description="Genera tarjetas prioritarias desde living-docs de errores (Fase 103).",
    )
    parser.add_argument("--domain", type=str, required=True,
                        help="dominio (kebab-case slug)")
    parser.add_argument("--format", choices=["obsidian-sr", "anki-csv"],
                        default="obsidian-sr",
                        help="formato de salida (default: obsidian-sr)")
    parser.add_argument("--errors-dir", type=Path, default=Path("study/errors"),
                        help="directorio con living-docs (default: study/errors/)")
    parser.add_argument("--out-dir", type=Path, default=Path("."),
                        help="directorio de salida (default: cwd)")
    args = parser.parse_args(argv)

    if not args.errors_dir.exists():
        print(f"[ERROR] no existe --errors-dir: {args.errors_dir}",
              file=sys.stderr)
        return 2

    try:
        prohibited = _load_prohibited_list(DOC_PATH)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    report = GenerationReport()
    all_cards: List[Card] = []
    for path in sorted(args.errors_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(text)
        if fm.get("note-type") != "error-log":
            continue
        if fm.get("domain", "").strip() != args.domain:
            continue
        cards = _generate_for_file(path, args.domain, prohibited, report)
        all_cards.extend(cards)

    if not all_cards:
        print(f"[INFO] ninguna tarjeta generada para dominio '{args.domain}'")
        if report.rejected:
            print("[INFO] entradas rechazadas:")
            for path, eid, reason in report.rejected:
                print(f"  - {path.name} › {eid}: {reason}")
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"priority-error-{args.domain}"

    if args.format == "obsidian-sr":
        out_path = args.out_dir / f"{output_name}.md"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(f"# Tarjetas prioritarias — {args.domain}\n\n")
            f.write("```\n")
            for card in all_cards:
                f.write(_format_obsidian_sr(card) + "\n")
            f.write("```\n")
    else:
        out_path = args.out_dir / f"{output_name}.csv"
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(["Pregunta", "Respuesta", "Tags", "Review-next"])
            for card in all_cards:
                writer.writerow(_format_anki_csv(card))

    print(f"[OK] {len(all_cards)} tarjetas generadas en {out_path}")
    if report.rejected:
        print(f"[INFO] {len(report.rejected)} entradas rechazadas:")
        for path, eid, reason in report.rejected:
            print(f"  - {path.name} › {eid}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
