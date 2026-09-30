#!/usr/bin/env python3
"""Validador de autoevaluación — Fase 102.

Aplica las 7 reglas V1-V7 definidas en `references/09-study/self-evaluation.md`
§6 sobre una nota NoteMark (`.md`) o un directorio de notas:

    V1  Existencia y sección: `## Autoevaluación` presente si y solo si el
        note-type no es `index-moc` (V6).
    V2  Tipos asignados coherentes con la tabla §3: las H3 dentro de
        `## Autoevaluación` son exactamente las del note-type (o un superset
        declarado vía `self-evaluation-types` en el frontmatter).
    V3  Forma de cada colapsable: cada bloque `:::collapsible{default_open=false}`
        contiene pregunta + respuesta + línea `> Fundamento:` (regex).
    V4  No copia literal (Jaccard sobre palabras no técnicas ≤ 0.8).
        Implementación simplificada: compara tokens normalizados excluyendo
        la lista cerrada de 45 no-traducibles de F101 §3 (cargada desde
        `references/06-writing/i18n-and-citation.md`).
    V5  Densidad por H3 (3-7 preguntas por H3 de tipo asignado).
    V6  Exención de `index-moc`: sin sección `## Autoevaluación`.
    V7  Wirings cerrados (modo `--check-wirings`): SKILL.md §5.3 menciona
        `self-evaluation.md`; los 15 archivos de `05-note-types/` declaran
        `### Autoevaluación`; `properties.md` cita F102; `anti-patterns.md`
        lista AP13-AP15; `09-study/README.md` no marca F102 como pendiente.

CLI:
    python3 self_eval_check.py --note <path>           # markdown a stdout
    python3 self_eval_check.py --note <path> --json    # JSON estructurado
    python3 self_eval_check.py --note <path> --strict  # warnings → exit 1
    python3 self_eval_check.py --note <path> --allow-violations V5
    python3 self_eval_check.py --notes <dir>           # batch
    python3 self_eval_check.py --check-wirings         # V7 estático

Exit codes:
    0  sin violaciones
    1  alguna violación (o warning si --strict)
    2  error de uso (archivo no encontrado, etc.)

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

# Tabla cerrada de mapeo tipo-de-nota × tipos-de-pregunta (F102 §3).
# `True` = tipo asignado por defecto; `False` = no aplica.
DEFAULT_QUESTION_TYPES: Dict[str, Dict[str, bool]] = {
    "concept":             {"recuerdo": True,  "aplicacion": True,  "diagnostico": False, "decision": True,  "prediccion": False},
    "api-reference":       {"recuerdo": True,  "aplicacion": True,  "diagnostico": False, "decision": False, "prediccion": False},
    "procedure":           {"recuerdo": False, "aplicacion": True,  "diagnostico": False, "decision": False, "prediccion": True},
    "configuration":       {"recuerdo": True,  "aplicacion": False, "diagnostico": False, "decision": True,  "prediccion": False},
    "error-troubleshooting":{"recuerdo": False, "aplicacion": False, "diagnostico": True,  "decision": True,  "prediccion": False},
    "architecture":        {"recuerdo": True,  "aplicacion": False, "diagnostico": False, "decision": True,  "prediccion": False},
    "syntax":              {"recuerdo": True,  "aplicacion": True,  "diagnostico": False, "decision": False, "prediccion": False},
    "data-model":          {"recuerdo": True,  "aplicacion": True,  "diagnostico": False, "decision": False, "prediccion": False},
    "chapter-digest":      {"recuerdo": True,  "aplicacion": False, "diagnostico": False, "decision": True,  "prediccion": False},
    "comparison":          {"recuerdo": False, "aplicacion": True,  "diagnostico": False, "decision": True,  "prediccion": False},
    "version-delta":       {"recuerdo": True,  "aplicacion": False, "diagnostico": False, "decision": False, "prediccion": True},
    "glossary-term":       {"recuerdo": True,  "aplicacion": False, "diagnostico": False, "decision": False, "prediccion": False},
    "cheatsheet":          {"recuerdo": True,  "aplicacion": True,  "diagnostico": False, "decision": False, "prediccion": False},
    "index-moc":           {"recuerdo": False, "aplicacion": False, "diagnostico": False, "decision": False, "prediccion": False},
    "practice":            {"recuerdo": False, "aplicacion": True,  "diagnostico": True,  "decision": False, "prediccion": True},
}

# Tipos en los que la regla §4 de referencia pura aplica: nunca recuerdo en
# estas notas si son 100 % referencia pura. Para `glossary-term`, `cheatsheet`
# e `index-moc` se considera referencia pura por defecto.
REFERENCE_PURE_TYPES: FrozenSet[str] = frozenset({
    "glossary-term", "cheatsheet", "index-moc",
})

# Tipos que NO deben tener sección ## Autoevaluación.
NO_AUTO_EVAL_TYPES: FrozenSet[str] = frozenset({"index-moc"})

# Tipos de pregunta válidos (enum cerrado).
VALID_QUESTION_TYPES: FrozenSet[str] = frozenset({
    "recuerdo", "aplicacion", "diagnostico", "decision", "prediccion",
})

# Mapeo H3 canónica → tipo normalizado.
H3_TO_TYPE: Dict[str, str] = {
    "### Recuerdo": "recuerdo",
    "### Aplicación": "aplicacion",
    "### Diagnóstico": "diagnostico",
    "### Decisión": "decision",
    "### Predicción": "prediccion",
}

# Regex para línea de fundamento.
FUNDAMENTO_RE = re.compile(
    r"^>\s*Fundamento\s*:\s*"
    r"(\{src:blk_[a-z0-9]{4,}\}|\[\[note:[a-z0-9][a-z0-9\-]*(?:#[\w\-§]+)?\]\])",
    re.MULTILINE,
)

# Regex para detectar :::collapsible{default_open=false} ... :::
COLLAPSIBLE_RE = re.compile(
    r":::collapsible\{default_open\s*=\s*false\}\s*\n(.*?)\n\s*:::",
    re.DOTALL,
)

H2_SECTION_RE = re.compile(r"^##\s+([^#].*)$", re.MULTILINE)

JACCARD_THRESHOLD = 0.8


@dataclass
class Violation:
    rule: str
    severity: str  # "error" | "warning"
    location: str  # descripción de dónde (sección, H3, bloque)
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class NoteReport:
    path: str
    note_type: Optional[str] = None
    violations: List[Violation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    @property
    def has_warnings(self) -> bool:
        return any(v.severity == "warning" for v in self.violations)

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "note_type": self.note_type,
            "violations": [v.to_dict() for v in self.violations],
        }


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Extrae el frontmatter YAML mínimo (sin PyYAML). Devuelve (dict, body)."""
    fm: Dict[str, str] = {}
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


def _parse_question_types(fm: Dict[str, str]) -> Optional[List[str]]:
    """Lee `self-evaluation-types` del frontmatter. Devuelve None si ausente."""
    raw = fm.get("self-evaluation-types")
    if raw is None:
        return None
    raw = raw.strip()
    if raw in ("[]", ""):
        return []
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        items = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
        return [_normalize_type(x) for x in items]
    return [_normalize_type(x) for x in raw.split(",") if x.strip()]


def _normalize_type(s: str) -> str:
    s = s.strip().lower()
    repl = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}
    for k, v in repl.items():
        s = s.replace(k, v)
    return s


def _extract_autoeval_h3(body: str) -> Tuple[Optional[str], Dict[str, str]]:
    """Devuelve (contenido de la sección ## Autoevaluación o None, dict de H3→contenido)."""
    sections: Dict[str, str] = {}
    current_h2: Optional[str] = None
    current_h3: Optional[str] = None
    buffer: List[str] = []
    h3_sections: Dict[str, str] = {}

    def flush_h3() -> None:
        if current_h3 is not None:
            h3_sections[current_h3] = "\n".join(buffer).strip()

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## ") and not line.startswith("### "):
            flush_h3()
            current_h3 = None
            buffer = []
            current_h2 = line[3:].strip()
            sections[current_h2] = ""
        elif line.startswith("### "):
            flush_h3()
            current_h3 = line[4:].strip()
            buffer = []
        else:
            if current_h3 is not None:
                buffer.append(raw_line)
            if current_h2 is not None and current_h3 is None:
                sections.setdefault(current_h2, "")
                sections[current_h2] += raw_line + "\n"
    flush_h3()
    autoeval = sections.get("Autoevaluación") or sections.get("Autoevaluacion")
    return autoeval, h3_sections


def _split_collapsibles(content: str) -> List[str]:
    return COLLAPSIBLE_RE.findall(content)


def _split_blocks_by_h3(content: str) -> Dict[str, List[str]]:
    """Divide el contenido por H3 dentro de ## Autoevaluación."""
    blocks: Dict[str, List[str]] = {}
    current_h3: Optional[str] = None
    buffer: List[str] = []
    for line in content.splitlines():
        if line.startswith("### "):
            if current_h3 is not None:
                blocks[current_h3] = _split_collapsibles("\n".join(buffer))
            current_h3 = line[4:].strip()
            buffer = []
        else:
            buffer.append(line)
    if current_h3 is not None:
        blocks[current_h3] = _split_collapsibles("\n".join(buffer))
    return blocks


def _tokenize(text: str) -> List[str]:
    """Tokeniza: split por whitespace, lowercase, quita puntuación."""
    text = text.lower()
    text = re.sub(r"[\.,;:!\?\(\)\[\]\{\}\<\>\"'\*`~#/\\|]", " ", text)
    return [t for t in text.split() if t]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _load_no_translatable(repo_root: Path) -> FrozenSet[str]:
    """Carga la lista cerrada de 45 no-traducibles de F101 §3 desde el doc
    normativo. Devuelve un set de tokens en lowercase."""
    path = repo_root / "skill" / "notemartin-study-notes" / "references" / "06-writing" / "i18n-and-citation.md"
    if not path.exists():
        return frozenset()
    text = path.read_text(encoding="utf-8")
    tokens: set = set()
    in_table = False
    for line in text.splitlines():
        if "Lista cerrada de no-traducibles" in line or "lista cerrada de no-traducibles" in line:
            in_table = True
            continue
        if in_table:
            if line.startswith("## "):
                break
            if line.startswith("|") and not line.startswith("|---"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) >= 2:
                    for cell in cells[1:]:
                        for tok in _tokenize(cell):
                            tokens.add(tok)
    return frozenset(tokens)


def _check_wirings(repo_root: Path) -> List[Violation]:
    """V7: wirings cerrados."""
    violations: List[Violation] = []
    skill_md = repo_root / "skill" / "notemartin-study-notes" / "SKILL.md"
    if not skill_md.exists():
        violations.append(Violation("V7", "error", "SKILL.md", "no existe"))
        return violations
    skill_text = skill_md.read_text(encoding="utf-8")
    if "self-evaluation.md" not in skill_text:
        violations.append(Violation(
            "V7", "error", "SKILL.md §5.3",
            "no menciona self-evaluation.md (F102)",
        ))

    note_types_dir = repo_root / "skill" / "notemartin-study-notes" / "references" / "05-note-types"
    expected_types = list(DEFAULT_QUESTION_TYPES.keys())
    for nt in expected_types:
        path = note_types_dir / f"{nt}.md"
        if not path.exists():
            violations.append(Violation(
                "V7", "error", f"05-note-types/{nt}.md",
                "no existe",
            ))
            continue
        text = path.read_text(encoding="utf-8")
        # Aceptar tanto `### Autoevaluación` como `### §2.5 · Autoevaluación`.
        if not re.search(r"^###\s+(?:§\S+\s+·\s+)?Autoevaluaci[oó]n", text, re.MULTILINE):
            violations.append(Violation(
                "V7", "error", f"05-note-types/{nt}.md",
                "no declara la sub-sección ### Autoevaluación",
            ))

    properties_path = repo_root / "skill" / "notemartin-study-notes" / "references" / "04-authoring" / "properties.md"
    if properties_path.exists():
        text = properties_path.read_text(encoding="utf-8")
        if "F102" not in text:
            violations.append(Violation(
                "V7", "error", "04-authoring/properties.md",
                "no cita F102",
            ))

    ap_path = repo_root / "skill" / "notemartin-study-notes" / "references" / "06-writing" / "anti-patterns.md"
    if ap_path.exists():
        text = ap_path.read_text(encoding="utf-8")
        for ap in ("AP13", "AP14", "AP15"):
            if ap not in text:
                violations.append(Violation(
                    "V7", "error", "06-writing/anti-patterns.md",
                    f"no lista {ap}",
                ))

    study_readme = repo_root / "skill" / "notemartin-study-notes" / "references" / "09-study" / "README.md"
    if study_readme.exists():
        text = study_readme.read_text(encoding="utf-8")
        if "[pendiente F102]" in text:
            violations.append(Violation(
                "V7", "error", "09-study/README.md",
                "aún marca self-evaluation.md como [pendiente F102]",
            ))

    return violations


def check_note(
    path: Path,
    repo_root: Path,
    no_translatable: FrozenSet[str],
    allow_violations: FrozenSet[str] = frozenset(),
    strict: bool = False,
) -> NoteReport:
    report = NoteReport(path=str(path))
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    note_type = fm.get("note-type")
    report.note_type = note_type

    if note_type is None:
        report.violations.append(Violation(
            "V0", "error", "frontmatter",
            "falta `note-type` en el frontmatter",
        ))
        return report

    if note_type not in DEFAULT_QUESTION_TYPES:
        report.violations.append(Violation(
            "V0", "error", "frontmatter",
            f"`note-type: {note_type}` no está en la tabla cerrada de 15 tipos",
        ))
        return report

    # V6: index-moc no debe tener ## Autoevaluación.
    has_autoeval_section = bool(
        re.search(r"^##\s+Autoevaluaci[oó]n\s*$", body, re.MULTILINE)
    )

    if note_type in NO_AUTO_EVAL_TYPES:
        if has_autoeval_section:
            report.violations.append(Violation(
                "V6", "error", "## Autoevaluación",
                "index-moc no debe tener sección ## Autoevaluación (V6)",
            ))
        return report

    # V1: existe ## Autoevaluación si y solo si el note-type lo requiere.
    if not has_autoeval_section:
        report.violations.append(Violation(
            "V1", "error", "## Autoevaluación",
            f"falta la sección `## Autoevaluación` para note-type `{note_type}` (V1)",
        ))
        return report

    # Extraer H3 dentro de ## Autoevaluación.
    _, h3_sections = _extract_autoeval_h3(body)
    h3_blocks = {h3: _split_collapsibles(content) for h3, content in h3_sections.items()
                 if any(_normalize_type(h3) == t for t in VALID_QUESTION_TYPES)
                 and h3 in ("Recuerdo", "Aplicación", "Diagnóstico", "Decisión", "Predicción")}

    declared_types = _parse_question_types(fm)
    default_map = DEFAULT_QUESTION_TYPES[note_type]
    default_set = {t for t, on in default_map.items() if on}

    # V2: tipos asignados coherentes.
    actual_h3_types = set()
    for h3 in h3_blocks.keys():
        t = _normalize_type(h3)
        if t in VALID_QUESTION_TYPES:
            actual_h3_types.add(t)

    if declared_types is None:
        expected = default_set
        source = "default §3"
    else:
        unknown = set(declared_types) - VALID_QUESTION_TYPES
        if unknown:
            report.violations.append(Violation(
                "V2", "error", "frontmatter self-evaluation-types",
                f"tipos desconocidos: {sorted(unknown)}",
            ))
        # Superset check: declarado ⊇ default.
        missing = default_set - set(declared_types)
        if missing:
            report.violations.append(Violation(
                "V2", "error", "frontmatter self-evaluation-types",
                f"declarado es subset del default §3 — faltan: {sorted(missing)}",
            ))
        expected = set(declared_types)
        source = "self-evaluation-types (frontmatter)"

    missing_h3 = expected - actual_h3_types
    if missing_h3:
        report.violations.append(Violation(
            "V2", "error", "## Autoevaluación",
            f"H3 faltantes para tipos asignados ({source}): {sorted(missing_h3)}",
        ))

    forbidden_h3 = actual_h3_types - expected
    # AP15 / §4: para tipos de referencia pura estricta (glossary-term,
    # index-moc), el default §3 manda incluso sobre self-evaluation-types.
    if note_type == "glossary-term":
        forbidden_h3 = actual_h3_types - default_set
    if forbidden_h3:
        if note_type == "glossary-term":
            report.violations.append(Violation(
                "V2", "error", "## Autoevaluación",
                f"`glossary-term` es referencia pura estricta: solo admite "
                f"`### Recuerdo`; presentes no permitidos: "
                f"{sorted(forbidden_h3)} (AP15 / §4)",
            ))
        else:
            report.violations.append(Violation(
                "V2", "error", "## Autoevaluación",
                f"H3 no asignados a `{note_type}` ({source}): {sorted(forbidden_h3)}",
            ))

    # V3, V4, V5: por cada H3 de tipo válido.
    for h3, collapsibles in h3_blocks.items():
        h3_type = _normalize_type(h3)
        if h3_type not in VALID_QUESTION_TYPES:
            continue

        # V5: 3-7 preguntas.
        if "V5" not in allow_violations:
            if len(collapsibles) < 3:
                sev = "error" if strict else "warning"
                report.violations.append(Violation(
                    "V5", sev, f"### {h3}",
                    f"solo {len(collapsibles)} preguntas (mínimo 3)",
                ))
            elif len(collapsibles) > 7:
                report.violations.append(Violation(
                    "V5", "error", f"### {h3}",
                    f"{len(collapsibles)} preguntas (máximo 7)",
                ))

        for idx, block in enumerate(collapsibles, 1):
            location = f"### {h3} › collapsable #{idx}"

            # V3: línea de Fundamento.
            if not FUNDAMENTO_RE.search(block):
                report.violations.append(Violation(
                    "V3", "error", location,
                    "falta línea `> Fundamento: …` (V3 / AP14)",
                ))

            # V4: Jaccard sobre palabras no técnicas.
            # Extraer la respuesta: todo el bloque menos la pregunta inicial
            # y la línea de Fundamento.
            lines = [l for l in block.splitlines() if l.strip()]
            if len(lines) < 2:
                report.violations.append(Violation(
                    "V3", "error", location,
                    "el bloque no contiene pregunta + respuesta",
                ))
                continue
            response_lines = lines[1:]
            response_lines = [
                l for l in response_lines
                if not FUNDAMENTO_RE.match(l)
            ]
            response_text = "\n".join(response_lines)

            tokens = _tokenize(response_text)
            tokens = [t for t in tokens if t not in no_translatable]
            # V4 estático: si la respuesta tiene 0 tokens no-técnicos,
            # la "reformulación" es solo términos verbatim → posible copia.
            # El Jaccard real sobre el bloque referenciado se delega al
            # evaluador externo (ver F102 §6 V4 + AP13) — el validador
            # solo emite un warning si la respuesta es trivialmente corta.
            if len(tokens) < 2:
                report.violations.append(Violation(
                    "V4", "warning", location,
                    f"respuesta tiene solo {len(tokens)} tokens no-técnicos "
                    "— reformulación trivial; verificar Jaccard ≤ 0.8 manualmente",
                ))

    return report


def format_markdown(reports: List[NoteReport]) -> str:
    lines: List[str] = ["# self_eval_check — reporte\n"]
    if not reports:
        lines.append("Sin notas analizadas.")
        return "\n".join(lines) + "\n"
    for r in reports:
        lines.append(f"## `{r.path}`  (note-type: `{r.note_type}`)\n")
        if not r.violations:
            lines.append("- ✅ sin violaciones\n")
        else:
            for v in r.violations:
                icon = "❌" if v.severity == "error" else "⚠️"
                lines.append(f"- {icon} **{v.rule}** ({v.severity}) — {v.location}: {v.message}")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="self_eval_check.py",
        description="Validador de autoevaluación por tipo (Fase 102).",
    )
    parser.add_argument("--note", type=Path, help="Ruta a una nota NoteMark (.md)")
    parser.add_argument("--notes", type=Path, help="Directorio con notas NoteMark")
    parser.add_argument("--check-wirings", action="store_true",
                        help="Solo valida V7 (wirings cerrados)")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Warnings se convierten en exit 1")
    parser.add_argument("--allow-violations", type=str, default="",
                        help="Reglas a ignorar (ej. V5)")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[4]
    no_translatable = _load_no_translatable(repo_root)
    allow = frozenset(s.strip() for s in args.allow_violations.split(",") if s.strip())

    if args.check_wirings:
        violations = _check_wirings(repo_root)
        if args.json:
            print(json.dumps({"rule": "V7", "violations": [v.to_dict() for v in violations]}, indent=2))
        else:
            if not violations:
                print("PASS V7 wirings cerrados")
                return 0
            for v in violations:
                print(f"[FAIL] V7 ({v.location}): {v.message}")
            return 1

    if not args.note and not args.notes:
        parser.error("debes pasar --note, --notes, o --check-wirings")

    paths: List[Path] = []
    if args.note:
        paths.append(args.note)
    if args.notes:
        paths.extend(sorted(args.notes.rglob("*.md")))

    reports: List[NoteReport] = []
    for p in paths:
        if not p.exists():
            print(f"[ERROR] archivo no encontrado: {p}", file=sys.stderr)
            return 2
        reports.append(check_note(p, repo_root, no_translatable, allow, args.strict))

    if args.json:
        out = {
            "total": len(reports),
            "errors": sum(1 for r in reports if r.has_errors),
            "warnings": sum(1 for r in reports if r.has_warnings),
            "reports": [r.to_dict() for r in reports],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(reports))

    has_errors = any(r.has_errors for r in reports)
    has_warnings = any(r.has_warnings for r in reports)
    if has_errors:
        return 1
    if has_warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
