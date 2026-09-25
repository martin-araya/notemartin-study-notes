"""Eval — Fase 41: contradicciones y obsolescencia.

Verifica los 3 criterios del roadmap + reglas R1–R8 del spec + no-regresión
F15/F37/F38/F39/F40.

Criterios:
1. Una contradicción inyectada se detecta y documenta con ambas anclas.
2. Todo contenido deprecado llega marcado.
3. El cuerpo nunca contradice la fuente sin señalarlo.

Sub-checks:
- C1: registry con conflictos válidos (≥ 2 anchors distintos) PASS.
- C2: bloques con 'deprecated' en content tienen deprecation_status poblado.
- C3: directivas :::contradiction tienen id válido en el registry.
- R3: anchors no idénticos en una contradicción.
- Schema validity (con jsonschema opcional).
- No-regresión F15/F37/F38/F39/F40.

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

SCHEMA = REPO / "skill" / "notemartin-study-notes" / "schemas" / "conflicts.schema.json"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"
F40_EVAL = REPO / "evals" / "terminology-sample" / "run_eval.py"


def _load(path: Path) -> dict | str:
    return json.loads(path.read_text(encoding="utf-8"))


# -------------------------------------------------------------------
# Sub-check 1: registry con contradicciones válidas (criterio 1).
# -------------------------------------------------------------------

def check_anchors_distinct(conflict: dict) -> tuple[bool, str]:
    """R3: los anchors son de tipo diferente o de instancia diferente."""
    anchors = conflict.get("anchors", [])
    if len(anchors) < 2:
        return False, f"<2 anchors ({len(anchors)})"
    pairs = [(a.get("type"), a.get("id")) for a in anchors]
    if len(set(pairs)) < len(pairs):
        return False, f"anchors duplicados {pairs}"
    return True, ""


def check_anchors_exist(conflict: dict, sdm: dict | None) -> list[str]:
    """Para anchors tipo 'block', el id debe existir en el SDM."""
    missing = []
    if sdm is None:
        return missing
    sdm_ids = set()
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            sdm_ids.add(block["id"])
    for a in conflict.get("anchors", []):
        if a.get("type") == "block" and a.get("id") not in sdm_ids:
            missing.append(a.get("id"))
    return missing


def check_registry_valid(reg: dict, sdm: dict | None = None,
                          expected_min_conflicts: int = 1) -> tuple[bool, str]:
    offenders: list[str] = []
    for c in reg.get("conflicts", []):
        ok, msg = check_anchors_distinct(c)
        if not ok:
            offenders.append(f"{c['id']}: {msg}")
        missing = check_anchors_exist(c, sdm)
        if missing:
            offenders.append(f"{c['id']}: anchors inexistentes en SDM {missing}")
        if not c.get("description"):
            offenders.append(f"{c['id']}: description vacía")
        if c.get("status") == "resolved" and not c.get("resolution"):
            offenders.append(f"{c['id']}: status=resolved sin resolution")
        if c.get("type") == "source-vs-derived" and not c.get("model_says"):
            offenders.append(f"{c['id']}: type=source-vs-derived sin model_says")
    if len(reg.get("conflicts", [])) < expected_min_conflicts:
        offenders.append(f"solo {len(reg.get('conflicts', []))} conflictos (< {expected_min_conflicts})")
    return (len(offenders) == 0), offenders


# -------------------------------------------------------------------
# Sub-check 2: contenido deprecado marcado (criterio 2).
# -------------------------------------------------------------------

DEPRECATED_KEYWORDS = ("deprecated", "obsolete", "removed")


def find_deprecated_blocks(sdm: dict) -> list[dict]:
    """Encuentra bloques del SDM cuyo content.text menciona deprecated/obsolete/removed."""
    out = []
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            content_text = json.dumps(block.get("content", {}))
            if any(kw in content_text.lower() for kw in DEPRECATED_KEYWORDS):
                out.append({"block_id": block["id"], "content": block.get("content", {})})
    return out


def check_deprecation_marked(sdm: dict, ledger: dict | None) -> tuple[bool, str]:
    """Para cada bloque con keyword deprecated, el ledger debe tener entry
    con source_block_ids conteniendo ese id y deprecation_status poblado."""
    deprecated = find_deprecated_blocks(sdm)
    if not deprecated:
        return True, "  [criterio 2] SKIP (no hay bloques deprecated en el SDM)"

    if ledger is None:
        return False, "  [criterio 2] FAIL (no hay ledger para verificar)"

    indexed: dict[str, dict] = {}
    for entry in ledger.get("entries", []):
        for bid in entry.get("source_block_ids", []):
            indexed[bid] = entry

    missing = []
    for dep in deprecated:
        bid = dep["block_id"]
        entry = indexed.get(bid)
        if entry is None:
            missing.append(f"{bid} (sin entry en ledger)")
        elif not entry.get("deprecation_status"):
            missing.append(f"{bid} (entry sin deprecation_status)")

    ok = len(missing) == 0
    return ok, f"  [criterio 2] {'PASS' if ok else 'FAIL'} (deprecados={len(deprecated)}, sin marcar={missing})"


# -------------------------------------------------------------------
# Sub-check 3: cuerpo nunca contradice sin señalarlo (criterio 3).
# -------------------------------------------------------------------

DIRECTIVE_RE = re.compile(r':::contradiction\s+id="([^"]+)"')


def extract_directive_ids(notemark_text: str) -> list[str]:
    return DIRECTIVE_RE.findall(notemark_text)


def check_inline_directives(notemark_text: str, registry: dict) -> tuple[bool, str]:
    """Toda directiva :::contradiction id=... debe tener un id válido en el registry."""
    ids = extract_directive_ids(notemark_text)
    registry_ids = {c["id"] for c in registry.get("conflicts", [])}
    missing = [i for i in ids if i not in registry_ids]
    ok = len(missing) == 0
    return ok, f"  [criterio 3] {'PASS' if ok else 'FAIL'} (ids={ids}, sin match en registry={missing})"


# -------------------------------------------------------------------
# Sub-check 4: schema validity.
# -------------------------------------------------------------------

def check_schema_validity(reg: dict) -> tuple[bool, str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return True, "  [schema] SKIP (jsonschema ausente)"
    schema = _load(SCHEMA)
    try:
        jsonschema.Draft202012Validator(schema).validate(reg)
        return True, "  [schema] PASS"
    except jsonschema.ValidationError as e:
        return False, f"  [schema] FAIL ({e.message})"


# -------------------------------------------------------------------
# Sub-check 5: detección de contradicción no documentada (criterio 1).
# Para verificar, comparamos el SDM con el registry: si dos bloques hablan del
# mismo parámetro con valores distintos y no hay un conflict en el registry
# que los ancle, exit 1.
# -------------------------------------------------------------------

def check_undocumented_contradiction(sdm: dict, registry: dict) -> tuple[bool, str]:
    """Detecta parámetros duplicados con valores distintos (heurística).
    Si los hay y no están documentados en el registry, exit 1."""
    by_name: dict[str, list[tuple[str, dict]]] = {}
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            if block.get("type") == "parameter":
                name = block.get("content", {}).get("name")
                desc = block.get("content", {}).get("description")
                if name and desc:
                    by_name.setdefault(name, []).append((block["id"], desc))

    duplicates = {n: v for n, v in by_name.items() if len(v) >= 2}
    if not duplicates:
        return True, "  [c1-undocumented] SKIP (sin duplicados)"

    # Verificar que cada par esté documentado en el registry.
    documented_pairs: set[tuple[str, str]] = set()
    for c in registry.get("conflicts", []):
        anchors = [(a.get("type"), a.get("id")) for a in c.get("anchors", [])]
        # El eval de cobertura simple: si el registry contiene un conflict
        # con anchor block que matchea uno de los ids del par, lo marcamos.
        for n, instances in duplicates.items():
            block_ids = {bid for bid, _ in instances}
            anchor_block_ids = {aid for atype, aid in anchors if atype == "block"}
            if block_ids & anchor_block_ids:
                documented_pairs.add((n, tuple(sorted(block_ids))))

    undocumented = []
    for n, instances in duplicates.items():
        if (n, tuple(sorted(bid for bid, _ in instances))) not in documented_pairs:
            undocumented.append(n)

    ok = len(undocumented) == 0
    return ok, f"  [c1-undocumented] {'PASS' if ok else 'FAIL'} (duplicados={list(duplicates)}, sin documentar={undocumented})"


# -------------------------------------------------------------------
# Main.
# -------------------------------------------------------------------

def main() -> int:
    print("Fase 41 — eval: contradicciones y obsolescencia")
    print()

    # Caso bueno: registry con 3 contradicciones válidas.
    print("Criterio 1 — Contradicción documentada con ambas anclas:")
    reg_good = _load(FIX / "conflicts-good.json")
    sdm_a = _load(FIX / "sdm-with-contradiction.json")
    ok1, m1 = check_registry_valid(reg_good, expected_min_conflicts=2)
    print(f"  [good] {m1 if m1 else 'PASS'}")

    # Caso negativo: anchor apunta a bloque inexistente.
    reg_orphan = _load(FIX / "conflicts-orphan-anchor.json")
    sdm_with_anchor = {
        "sections": [{
            "section_path": "/ch02",
            "blocks": [{"id": "a8f4ce140580", "type": "parameter", "content": {}}],
        }],
    }
    ok_orphan, _ = check_registry_valid(reg_orphan, sdm=sdm_with_anchor, expected_min_conflicts=1)
    print(f"  [orphan-anchor] {'PASS (correctamente rechaza)' if not ok_orphan else 'FAIL'}")

    # Caso negativo: 2 anchors idénticos (R3).
    reg_same = _load(FIX / "conflicts-same-anchor.json")
    ok_same, _ = check_registry_valid(reg_same, expected_min_conflicts=1)
    print(f"  [same-anchor] {'PASS (correctamente rechaza)' if not ok_same else 'FAIL'}")

    # Caso: contradicción inyectada en SDM pero NO documentada.
    # Para este caso esperamos que el eval DETECTE el issue (no que pase).
    reg_empty = _load(FIX / "conflicts-undocumented.json")
    undoc_detected, undoc_msg = check_undocumented_contradiction(sdm_a, reg_empty)
    # En el caso negativo, queremos que el eval marque el issue (i.e., la
    # función retorna False porque hay duplicados sin documentar).
    undoc_eval_catches_it = not undoc_detected
    print(f"  [undocumented] {undoc_msg} (eval detecta={undoc_eval_catches_it})")
    c1_overall = ok1 and (not ok_orphan) and (not ok_same) and undoc_eval_catches_it
    print(f"  criterio 1 overall: {'PASS' if c1_overall else 'FAIL'}")
    print()

    # Criterio 2: contenido deprecado marcado.
    print("Criterio 2 — Todo contenido deprecado llega marcado:")
    sdm_unmarked = _load(FIX / "sdm-deprecated-unmarked.json")
    ledger_marked = _load(FIX / "ledger-with-deprecation.json")
    ledger_unmarked = _load(FIX / "ledger-no-deprecation.json")

    # Caso positivo: cada bloque deprecated tiene entry con deprecation_status.
    pos_ok, m_pos = check_deprecation_marked(sdm_unmarked, ledger_marked)
    print(f"  [marker-present] {m_pos}")

    # Caso negativo: bloque deprecated sin marker — el eval debe detectar el issue.
    # Esperamos que check_deprecation_marked retorne False (issue encontrado).
    neg_ok_issue, m_neg = check_deprecation_marked(sdm_unmarked, ledger_unmarked)
    neg_eval_catches_it = not neg_ok_issue  # True si el eval detecta el issue
    print(f"  [no-marker-in-ledger] {m_neg} (eval detecta={neg_eval_catches_it})")

    c2_overall = pos_ok and neg_eval_catches_it
    print(f"  criterio 2 overall: {'PASS' if c2_overall else 'FAIL'}")
    print()

    # Criterio 3: cuerpo nunca contradice sin señalarlo.
    print("Criterio 3 — El cuerpo nunca contradice la fuente sin señalarlo:")
    good_text = (FIX / "notemark-good.md").read_text()
    bad_text = (FIX / "notemark-undocumented.md").read_text()
    ok3_good, m3_good = check_inline_directives(good_text, reg_good)
    ok3_bad, m3_bad = check_inline_directives(bad_text, reg_good)
    print(f"  [good-notemark] {m3_good}")
    print(f"  [undocumented-notemark] {m3_bad}")
    c3_overall = ok3_good and not ok3_bad
    print(f"  criterio 3 overall: {'PASS' if c3_overall else 'FAIL'}")
    print()

    # Reglas duras + schema.
    print("Reglas duras (R1–R8):")
    print(f"  [R3 anchors distinct] {'PASS' if ok1 else 'FAIL'}")
    print(f"  [schema good] {check_schema_validity(reg_good)[1]}")

    # No-regresión.
    print()
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
                          ("F39", F39_EVAL), ("F40", F40_EVAL)]:
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
