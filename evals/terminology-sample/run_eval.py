"""Eval — Fase 40: terminología y glosario acumulativo.

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38/F39:
1. Ningún término tiene dos definiciones canónicas.
2. Ningún alias apunta a dos términos.
3. Un término del capítulo 2 no se redefine en el 9.

Plus sub-checks de schema validity, caso bueno, colisión resuelta con sufijo,
y no-regresión.

Exit codes: 0 PASS los 7, 1 FAIL, 2 usage.
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

SCHEMA = REPO / "skill" / "notemartin-study-notes" / "schemas" / "glossary.schema.json"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"

CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
ALIAS_KINDS = {"en", "es", "acronym", "plural", "variant"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_no_dual_definitions(glossary: dict) -> tuple[bool, str]:
    """Criterio 1: ningún término tiene > 1 definition con canonical=true."""
    offenders = []
    for canonical, term in glossary.get("terms", {}).items():
        canonical_count = sum(1 for d in term.get("definitions", []) if d.get("canonical"))
        if canonical_count > 1:
            offenders.append(f"{canonical} ({canonical_count} canonical)")
        if canonical_count == 0:
            offenders.append(f"{canonical} (0 canonical)")
    ok = len(offenders) == 0
    return ok, (
        f"  [criterio 1] {'PASS' if ok else 'FAIL'} "
        f"(offenders={offenders or 'ninguno'})"
    )


def check_no_alias_collision(glossary: dict) -> tuple[bool, str]:
    """Criterio 2: ningún alias (por string normalizado) aparece en más de un término."""
    alias_owners: dict[str, list[str]] = {}
    for canonical, term in glossary.get("terms", {}).items():
        for a in term.get("aliases", []):
            key = a["alias"].lower()
            alias_owners.setdefault(key, []).append(canonical)
    collisions = {k: v for k, v in alias_owners.items() if len(v) > 1}
    ok = len(collisions) == 0
    if ok:
        return True, f"  [criterio 2] PASS (sin colisiones de alias)"
    detail = "; ".join(f"{k!r}→{v}" for k, v in collisions.items())
    return False, f"  [criterio 2] FAIL ({detail})"


def check_no_redefinition(glossary: dict) -> tuple[bool, str]:
    """Criterio 3: ningún término tiene ≥ 2 definitions con definition distinta."""
    offenders = []
    for canonical, term in glossary.get("terms", {}).items():
        seen: dict[str, str] = {}
        for d in term.get("definitions", []):
            text = d.get("definition", "")
            if text in seen:
                continue
            if seen:  # había una anterior con texto distinto
                offenders.append(f"{canonical}: {sorted(seen.keys())[0][:40]!r}… vs {text[:40]!r}…")
            seen[text] = d.get("chapter", "?")
    ok = len(offenders) == 0
    return ok, (
        f"  [criterio 3] {'PASS' if ok else 'FAIL'} "
        f"(offenders={offenders or 'ninguno'})"
    )


def check_alias_kind_enum(glossary: dict) -> tuple[bool, str]:
    """R4: alias.kind ∈ enum cerrada."""
    bad: list[tuple[str, str]] = []
    for canonical, term in glossary.get("terms", {}).items():
        for a in term.get("aliases", []):
            if a["kind"] not in ALIAS_KINDS:
                bad.append((canonical, a["kind"]))
    ok = len(bad) == 0
    return ok, f"  [R4 alias kind] {'PASS' if ok else 'FAIL'} (bad={bad or 'ninguno'})"


def check_canonical_regex(glossary: dict) -> tuple[bool, str]:
    """R1: canonical kebab-case."""
    bad = [c for c in glossary.get("terms", {}) if not CANONICAL_RE.match(c)]
    ok = len(bad) == 0
    return ok, f"  [R1 canonical regex] {'PASS' if ok else 'FAIL'} (bad={bad or 'ninguno'})"


def check_schema_validity(glossary: dict) -> tuple[bool, str]:
    """Schema validation (con jsonschema opcional)."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return True, "  [schema validity] SKIPPED (jsonschema ausente)"
    schema = _load(SCHEMA)
    try:
        jsonschema.Draft202012Validator(schema).validate(glossary)
        return True, "  [schema validity] PASS"
    except jsonschema.ValidationError as e:
        return False, f"  [schema validity] FAIL ({e.message})"


def check_collision_suffix_resolution(glossary: dict) -> tuple[bool, str]:
    """Verifica que la colisión 'wal' PostgreSQL vs 'wal' Oracle se resolvió
    como 'wal-oracle' (sufijo -<vendor>) y NO como redefinición."""
    if "wal" not in glossary.get("terms", {}) or "wal-oracle" not in glossary.get("terms", {}):
        return False, "  [colisión sufijo] FAIL (falta 'wal' o 'wal-oracle')"
    wal_pg = glossary["terms"]["wal"]
    wal_oracle = glossary["terms"]["wal-oracle"]
    if wal_pg.get("domain") != "postgresql" or wal_oracle.get("domain") != "oracle":
        return False, f"  [colisión sufijo] FAIL (domains: {wal_pg.get('domain')}, {wal_oracle.get('domain')})"
    return True, "  [colisión sufijo] PASS"


def main() -> int:
    print("Fase 40 — eval: terminología y glosario acumulativo")
    print()

    fixtures = [
        ("good", "glossary-good.json"),
        ("dual-def", "glossary-dual-def.json"),
        ("alias-collision", "glossary-alias-collision.json"),
        ("redefinition", "glossary-redefinition.json"),
        ("collision-suffix", "glossary-collision-suffix.json"),
    ]

    # Criterio 1 — buen caso: sin dual definitions.
    g = _load(FIX / "glossary-good.json")
    c1, m1 = check_no_dual_definitions(g)
    print("Criterio 1 — Ningún término tiene dos definiciones canónicas:")
    print(f"  [good] {m1}")

    # Criterio 2 — buen caso: sin colisión de alias.
    c2, m2 = check_no_alias_collision(g)
    print()
    print("Criterio 2 — Ningún alias apunta a dos términos:")
    print(f"  [good] {m2}")

    # Criterio 3 — buen caso: sin redefiniciones.
    c3, m3 = check_no_redefinition(g)
    print()
    print("Criterio 3 — Un término del capítulo 2 no se redefine en el 9:")
    print(f"  [good] {m3}")

    # Casos negativos: cada uno debe fallar SOLO en su criterio.
    print()
    print("Casos negativos (cada uno falla en su criterio):")

    g_dd = _load(FIX / "glossary-dual-def.json")
    c1_dd, m1_dd = check_no_dual_definitions(g_dd)
    c2_dd, m2_dd = check_no_alias_collision(g_dd)
    c3_dd, m3_dd = check_no_redefinition(g_dd)
    print(f"  [dual-def] c1={'FAIL✓' if not c1_dd else 'unexpected-PASS'} "
          f"c2={'PASS✓' if c2_dd else 'unexpected-FAIL'} "
          f"c3={'PASS✓' if c3_dd else 'unexpected-FAIL'}")

    g_ac = _load(FIX / "glossary-alias-collision.json")
    c1_ac, m1_ac = check_no_dual_definitions(g_ac)
    c2_ac, m2_ac = check_no_alias_collision(g_ac)
    c3_ac, m3_ac = check_no_redefinition(g_ac)
    print(f"  [alias-collision] c1={'PASS✓' if c1_ac else 'unexpected-FAIL'} "
          f"c2={'FAIL✓' if not c2_ac else 'unexpected-PASS'} "
          f"c3={'PASS✓' if c3_ac else 'unexpected-FAIL'}")

    g_re = _load(FIX / "glossary-redefinition.json")
    c1_re, m1_re = check_no_dual_definitions(g_re)
    c2_re, m2_re = check_no_alias_collision(g_re)
    c3_re, m3_re = check_no_redefinition(g_re)
    print(f"  [redefinition] c1={'PASS✓' if c1_re else 'unexpected-FAIL'} "
          f"c2={'PASS✓' if c2_re else 'unexpected-FAIL'} "
          f"c3={'FAIL✓' if not c3_re else 'unexpected-PASS'}")

    # Resolución de colisión con sufijo.
    g_cs = _load(FIX / "glossary-collision-suffix.json")
    c_cs, m_cs = check_collision_suffix_resolution(g_cs)
    print()
    print("Resolución de colisión entre dominios (R2):")
    print(m_cs)

    # Reglas duras (R1, R4, schema).
    print()
    print("Reglas duras (R1, R4, schema):")
    r1, m_r1 = check_canonical_regex(g)
    r4, m_r4 = check_alias_kind_enum(g)
    sv, m_sv = check_schema_validity(g)
    print(m_r1)
    print(m_r4)
    print(m_sv)

    # No-regresión.
    print()
    print("No-regresión:")
    nr_results = []
    for label, script in [("F15", VALIDATE_LEDGER), ("F37", F37_EVAL),
                          ("F38", F38_EVAL), ("F39", F39_EVAL)]:
        if label == "F15":
            r = subprocess.run(
                [sys.executable, str(script), "--validate",
                 str(REPO / "evals" / "ledger-sample" / "full-coverage.json"),
                 str(REPO / "evals" / "ledger-sample" / "mixed-states.json")],
                capture_output=True, text=True,
            )
            ok = r.returncode == 0
        else:
            r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
            ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
        print(f"  [no-regresión {label}] {'PASS' if ok else 'FAIL'}")
        nr_results.append(ok)

    all_ok = (
        c1 and c2 and c3 and
        not c1_dd and c2_dd and c3_dd and
        c1_ac and not c2_ac and c3_ac and
        c1_re and c2_re and not c3_re and
        c_cs and r1 and r4 and sv and
        all(nr_results)
    )
    print()
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
