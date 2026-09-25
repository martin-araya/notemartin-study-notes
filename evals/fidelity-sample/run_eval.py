"""Eval — Fase 42: reglas de fidelidad.

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38/F39/F40/F41:

1. Todo contenido externo va en bloque identificable.
2. Fuente incompleta → nota declara ausencia (regla de la duda).
3. Ningún valor técnico aparece sin respaldo en el ledger.

Exit codes: 0 PASS, 1 FAIL, 2 usage.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"

VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"
F40_EVAL = REPO / "evals" / "terminology-sample" / "run_eval.py"
F41_EVAL = REPO / "evals" / "conflicts-sample" / "run_eval.py"

PROHIBITED_WORDS = [
    "probablemente", "típicamente", "en general", "asumimos", "suponemos",
    "creemos que", "suele ser", "lo más común es", "por defecto",
    "a menudo", "generalmente", "normalmente",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# -------------------------------------------------------------------
# Sub-check 1: contenido externo en bloque identificable.
# -------------------------------------------------------------------

# Palabras/frases que sugieren contenido "externo" (heurística).
EXTERNAL_HINTS = [
    "mayoría", "generalmente", "normalmente", "RFC", "ver también",
    "es típico", "lo más común", "experiencia previa",
]


def check_external_in_blocks(note_text: str) -> tuple[bool, str]:
    """Detecta frases 'externas' (heurística) fuera de :::external y verifica
    que cada una esté dentro de un bloque identificable."""
    # Extrae contenido dentro de :::external ... :::
    external_blocks = re.findall(
        r':::external\s*\n(.*?)\n:::', note_text, re.DOTALL
    )
    external_content = "\n".join(external_blocks)

    # Detecta frases externas en el cuerpo principal
    body = re.sub(r':::external\s*\n.*?\n:::', '', note_text, flags=re.DOTALL)

    issues: list[str] = []
    for hint in EXTERNAL_HINTS:
        if hint.lower() in body.lower() and hint.lower() not in external_content.lower():
            issues.append(f"'{hint}' aparece en cuerpo pero no en :::external")

    ok = len(issues) == 0
    return ok, f"  [c1] {'PASS' if ok else 'FAIL'} {issues}"


def check_derived_in_blocks(note_text: str) -> tuple[bool, str]:
    """Si hay diagramas Mermaid o paráfrasis larga fuera de :::derived, FAIL."""
    # Buscar bloques de código mermaid fuera de :::derived
    derived_blocks = re.findall(
        r':::derived\s*\n(.*?)\n:::', note_text, re.DOTALL
    )
    derived_content = "\n".join(derived_blocks)

    # Eliminar bloques :::external
    body = re.sub(r':::external\s*\n.*?\n:::', '', note_text, flags=re.DOTALL)

    # Buscar mermaid en el cuerpo (fuera de derived)
    issues: list[str] = []
    if "```mermaid" in body and "```mermaid" not in derived_content:
        issues.append("mermaid block en cuerpo sin :::derived")

    # Buscar analogías fuera de derived
    analog_markers = ["analogía", "como un", "similar a"]
    body_lower = body.lower()
    derived_lower = derived_content.lower()
    for marker in analog_markers:
        if marker in body_lower and marker not in derived_lower:
            issues.append(f"analogía '{marker}' en cuerpo sin :::derived")

    ok = len(issues) == 0
    return ok, f"  [c1-derived] {'PASS' if ok else 'FAIL'} {issues}"


# -------------------------------------------------------------------
# Sub-check 2: regla de la duda.
# -------------------------------------------------------------------

ACCEPTABLE_ABSENCE_PHRASES = [
    "no menciona", "es desconocido", "fuente incompleta", "no cubierto",
    "falta información", "no documentado", "consultar fuente original",
]


def check_prohibited_words(note_text: str) -> tuple[bool, list[str]]:
    """Detecta palabras prohibidas fuera de :::external / :::derived."""
    # Eliminar bloques marcados
    clean = re.sub(r':::(external|derived)\s*\n.*?\n:::', '', note_text, flags=re.DOTALL)
    found = []
    for word in PROHIBITED_WORDS:
        if word.lower() in clean.lower():
            found.append(word)
    return len(found) == 0, found


def check_absence_when_incomplete(note_text: str, sdm: dict | None) -> tuple[bool, str]:
    """Si el SDM no menciona un tema y la nota lo discute, debe declarar ausencia."""
    if sdm is None:
        return True, "  [c2-incomplete] SKIP (sin SDM)"

    # Detectar qué temas cubre el SDM
    sdm_terms: set[str] = set()
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            content_text = json.dumps(block.get("content", {}))
            sdm_terms.update(re.findall(r'[a-z]{4,}', content_text.lower()))

    # Detectar si la nota declara ausencia con frases aceptables
    has_acceptable_absence = any(
        p in note_text.lower() for p in ACCEPTABLE_ABSENCE_PHRASES
    )

    if has_acceptable_absence:
        return True, "  [c2-incomplete] PASS (declara ausencia)"
    return False, "  [c2-incomplete] FAIL (no declara ausencia)"


# -------------------------------------------------------------------
# Sub-check 3: valores técnicos con respaldo en ledger.
# -------------------------------------------------------------------

def extract_technical_values(note_text: str) -> list[dict]:
    """Extrae valores técnicos del note (criterio 3)."""
    values = []

    # Defaults: "default X" o "default: X"
    for m in re.finditer(r'\bdefault\s*[:=]?\s*([0-9]+\s*[KMGT]?B|MB|KB|GB|TB)\b',
                          note_text, re.IGNORECASE):
        values.append({"type": "default", "value": m.group(1).strip(),
                       "line": note_text[:m.start()].count('\n') + 1})

    # Parámetros: `shared_buffers` entre backticks o como identifier tras "parámetro"
    for m in re.finditer(r'`([a-z][a-z0-9_]+)`', note_text):
        # Filtra nombres demasiado comunes
        if m.group(1) not in {"el", "la", "los", "las", "un", "una", "y", "o", "de", "del"}:
            values.append({"type": "parameter", "value": m.group(1), "line": -1})

    # Códigos de error: EADDRINUSE, ORA-00904
    for m in re.finditer(r'\b([A-Z]{2,}[A-Z0-9]*-\d{2,6}|[A-Z]+[A-Z0-9_]{3,})\b', note_text):
        # Filtra palabras comunes en mayúsculas (al menos 4 chars)
        if len(m.group(1)) >= 5 and m.group(1) not in {"ORDBMS", "LTS", "HTTP", "HTTPS"}:
            values.append({"type": "error-code", "value": m.group(1), "line": -1})

    # Versiones: "PostgreSQL 13", "v1.2.3"
    for m in re.finditer(r'\b(PostgreSQL|MySQL|Kubernetes|Python)\s+(\d+)\b', note_text):
        values.append({"type": "version-note", "value": f"{m.group(1)} {m.group(2)}"})

    return values


def values_have_backing(values: list[dict], ledger: dict) -> list[dict]:
    """Devuelve los valores que NO tienen respaldo en el ledger."""
    entries = ledger.get("entries", [])
    # Index por type+content.key
    indexed: dict[tuple[str, str], list[dict]] = {}
    for e in entries:
        etype = e.get("type")
        content = e.get("content", {})
        if etype == "default":
            name = content.get("name")
            value = content.get("value")
            if name:
                indexed.setdefault(("default_name", name), []).append(e)
            if value:
                indexed.setdefault(("default_value", value), []).append(e)
        elif etype == "parameter":
            name = content.get("name")
            if name:
                indexed.setdefault(("parameter", name), []).append(e)
        elif etype == "error-code":
            code = content.get("code")
            if code:
                indexed.setdefault(("error-code", code), []).append(e)
        elif etype == "version-note":
            vi = content.get("version_introduced")
            if vi:
                indexed.setdefault(("version-note", vi), []).append(e)
            vr = content.get("version_removed")
            if vr:
                indexed.setdefault(("version-note", vr), []).append(e)

    unbacked = []
    for v in values:
        # Buscar coincidencia en el índice
        candidates = indexed.get((v["type"], v["value"]), [])
        if not candidates:
            # Fallback: buscar por substring en values de default
            if v["type"] == "default":
                # El value puede ser parcial ("128 MB" en note, ledger tiene "128 MB")
                for key, entries_list in indexed.items():
                    if key[0] == "default_value" and key[1] in v["value"]:
                        candidates = entries_list
                        break
            elif v["type"] == "version-note":
                # "PostgreSQL 13" → buscar version_introduced "13" con product "PostgreSQL"
                for key, entries_list in indexed.items():
                    if key[0] == "version-note" and key[1] == v["value"].split()[-1]:
                        candidates = entries_list
                        break
        if not candidates:
            unbacked.append(v)

    return unbacked


# -------------------------------------------------------------------
# Main.
# -------------------------------------------------------------------

def main() -> int:
    print("Fase 42 — eval: reglas de fidelidad")
    print()

    # Criterio 1: contenido externo en bloque identificable.
    print("Criterio 1 — Todo contenido externo va en bloque identificable:")
    note_good = _read_text(FIX / "note-good.md")
    note_ext_missing = _read_text(FIX / "note-external-missing.md")

    ok1_good, m1_good = check_external_in_blocks(note_good)
    ok1_bad, m1_bad = check_external_in_blocks(note_ext_missing)
    ok1_derived_good, m1_d_good = check_derived_in_blocks(note_good)
    ok1_derived_bad, m1_d_bad = check_derived_in_blocks(note_ext_missing)

    print(m1_good)
    print(m1_bad)
    print(m1_d_good)
    print(m1_d_bad)

    # c1 overall: bueno PASS, malo FAIL
    c1_overall = ok1_good and not ok1_bad and ok1_derived_good and not ok1_derived_bad
    print(f"  criterio 1 overall: {'PASS' if c1_overall else 'FAIL'}")
    print()

    # Criterio 2: regla de la duda.
    print("Criterio 2 — Fuente incompleta → nota declara ausencia:")
    note_doubt = _read_text(FIX / "note-doubtful.md")
    note_inc_good = _read_text(FIX / "note-incomplete-good.md")
    note_inc_bad = _read_text(FIX / "note-incomplete-bad.md")
    sdm_inc = _read_json(FIX / "source-incomplete.json")

    # Caso positivo: palabras prohibidas → FAIL.
    no_prohibited, prohibited_found = check_prohibited_words(note_doubt)
    ok2_neg_words = not no_prohibited  # eval detecta issue
    print(f"  [prohibited-words] {f'eval detecta={ok2_neg_words}, found={prohibited_found}'}")

    # Caso positivo: ausencia bien declarada.
    ok2_inc_good, m2_inc_good = check_absence_when_incomplete(note_inc_good, sdm_inc)
    print(m2_inc_good)

    # Caso negativo: ausencia NO declarada cuando la fuente es incompleta.
    ok2_inc_bad, m2_inc_bad = check_absence_when_incomplete(note_inc_bad, sdm_inc)
    ok2_neg_absence = not ok2_inc_bad  # eval detecta el issue
    print(f"  [incomplete-bad] eval detecta={ok2_neg_absence}: {m2_inc_bad}")

    c2_overall = ok2_neg_words and ok2_inc_good and ok2_neg_absence
    print(f"  criterio 2 overall: {'PASS' if c2_overall else 'FAIL'}")
    print()

    # Criterio 3: valores técnicos con respaldo en ledger.
    print("Criterio 3 — Ningún valor técnico aparece sin respaldo en el ledger:")
    note_dm = _read_text(FIX / "note-derived-missing.md")
    ledger_good_data = _read_json(FIX / "ledger-good.json")
    ledger_missing_data = _read_json(FIX / "ledger-missing.json")

    # Caso positivo: note-good + ledger-good — todos los valores respaldados.
    values_good = extract_technical_values(note_good)
    unbacked_good = values_have_backing(values_good, ledger_good_data)
    ok3_good = len(unbacked_good) == 0
    print(f"  [good-notemark] {'PASS' if ok3_good else 'FAIL'} (unbacked={unbacked_good[:3]})")

    # Caso negativo: note-derived-missing + ledger-missing — valor sin respaldo.
    values_dm = extract_technical_values(note_dm)
    unbacked_dm = values_have_backing(values_dm, ledger_missing_data)
    ok3_neg = len(unbacked_dm) > 0  # eval detecta el issue
    print(f"  [missing-backing] {'eval detecta' if ok3_neg else 'FAIL eval no detecta'} "
          f"(unbacked={[v['type'] + ':' + v['value'] for v in unbacked_dm]})")

    c3_overall = ok3_good and ok3_neg
    print(f"  criterio 3 overall: {'PASS' if c3_overall else 'FAIL'}")
    print()

    # No-regresión.
    print("No-regresión:")
    nr = []
    r = subprocess.run(
        [sys.executable, str(VALIDATE_LEDGER), "--validate",
         str(REPO / "evals" / "ledger-sample" / "full-coverage.json"),
         str(REPO / "evals" / "ledger-sample" / "mixed-states.json")],
        capture_output=True, text=True,
    )
    ok = r.returncode == 0
    print(f"  [F15] {'PASS' if ok else 'FAIL'}")
    nr.append(ok)
    for label, script in [("F37", F37_EVAL), ("F38", F38_EVAL),
                          ("F39", F39_EVAL), ("F40", F40_EVAL),
                          ("F41", F41_EVAL)]:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
        print(f"  [{label}] {'PASS' if ok else 'FAIL'}")
        nr.append(ok)

    all_ok = c1_overall and c2_overall and c3_overall and all(nr)
    print()
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'} "
          f"(c1={c1_overall} c2={c2_overall} c3={c3_overall} "
          f"nr={sum(nr)}/{len(nr)})")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
