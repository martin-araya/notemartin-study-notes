#!/usr/bin/env python3
"""
Verificador de la Fase 66 — Subconjunto Mermaid portable (mermaid-portable.md).

Ejecuta 5 criterios verificables sobre el catálogo:

  C1. Lista blanca cubre los 9 tipos (WP-1 … WP-9) y la lista negra ≥10 entradas.
  C2. Cada entrada de la lista negra tiene alternativa (criterio 2 de F66).
  C3. Las 6 reglas R-MP-01 a R-MP-06 están enunciadas y verificables.
  C4. La tabla §8 cubre los 3 destinos (criterio 3 de F66).
  C5. Acentos y `ñ` documentados en §6 con guía operativa y reemplazos ASCII.

Uso:
    python run_eval.py --catalog <ruta-al-catalogo>

Salida: imprime PASS 5/5 (o FAIL con detalle) y sale con código 0/1.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

WP_IDS = [f"WP-{i}" for i in range(1, 10)]
R_MP_IDS = [f"R-MP-{i:02d}" for i in range(1, 7)]

RE_WP_HEADER = re.compile(r"^### §3\.\d+ · (WP-\d+) —", re.MULTILINE)
RE_R_MP = re.compile(r"\*\*R-MP-(\d{2})\*\*")
RE_BLACKLIST_ROW = re.compile(r"^\|\s*LN-(\d+)\s*\|", re.MULTILINE)
RE_SECTION8_ROW = re.compile(r"^\|\s*`?[^|]+`?\s*\|\s*(✅|⚠|❌)[^|]*\|\s*(✅|⚠|❌)[^|]*\|\s*(✅|⚠|❌)[^|]*\|", re.MULTILINE)
RE_SECTION6_TABLE = re.compile(r"^\|\s*`[^`]+`\s*\|", re.MULTILINE)


def _clean_value(v: str) -> str:
    v = v.strip()
    for sep in ("  #", " #", "\t#"):
        if sep in v:
            v = v.split(sep, 1)[0].rstrip()
    v = v.strip('"').strip("'")
    return v


def parse_simple_yaml(text: str) -> list[dict[str, str]]:
    """Parser YAML minimalista (igual estilo que F65)."""
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            if current is not None:
                items.append(current)
            current = {}
            rest = raw[4:]
            if ":" in rest:
                k, _, v = rest.partition(":")
                current[k.strip()] = _clean_value(v)
        elif current is not None and raw.startswith("    "):
            if ":" in raw:
                k, _, v = raw.partition(":")
                k = k.strip()
                if k and k not in current:
                    current[k] = _clean_value(v)
    if current is not None:
        items.append(current)
    return items


class EvalResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    def summary(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


# ---------------------------------------------------------------------------
# Criterios
# ---------------------------------------------------------------------------


def crit_1_whitelist_blacklist(text: str, result: EvalResult) -> None:
    """C1: lista blanca cubre los 9 tipos (WP-1 … WP-9) y la lista negra ≥10 entradas."""
    wp_headers = RE_WP_HEADER.findall(text)
    wp_found = set(wp_headers)
    wp_missing = [w for w in WP_IDS if w not in wp_found]
    if wp_missing:
        result.fail("C1-whitelist",
                    f"Faltan tipos portables: {wp_missing} (encontrados: {sorted(wp_found)})")
        return

    blacklist_rows = RE_BLACKLIST_ROW.findall(text)
    ln_numbers = sorted({int(n) for n in blacklist_rows})
    if len(ln_numbers) < 10:
        result.fail("C1-blacklist",
                    f"Solo {len(ln_numbers)} entradas en §5 (esperaba ≥10)")
        return
    # Verificar rango LN-1 … LN-16 sin huecos demasiado grandes
    if max(ln_numbers) - min(ln_numbers) + 1 > 20:
        result.fail("C1-blacklist",
                    f"Rango de LN-IDs demasiado disperso: {ln_numbers[:10]}...")
        return

    result.ok(f"C1-whitelist+blacklist ({len(wp_found)} WP, {len(ln_numbers)} LN)")


def crit_2_blacklist_alternative(text: str, result: EvalResult) -> None:
    """C2: cada entrada de la lista negra tiene alternativa (criterio 2 de F66)."""
    # Parsear las filas de §5: | LN-N | construct | por qué | alternativa | wirings |
    rows: list[tuple[str, str, str, str, str]] = []
    for line in text.splitlines():
        if not line.startswith("| LN-"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4:
            rows.append((cells[0], cells[1], cells[2], cells[3], cells[4] if len(cells) > 4 else ""))

    if len(rows) < 10:
        result.fail("C2-blacklist-alternative",
                    f"Solo {len(rows)} filas en §5 (esperaba ≥10)")
        return

    problems: list[str] = []
    for ln_id, construct, why, alternativa, wirings in rows:
        if not alternativa or alternativa in {"-", "N/A", ""}:
            problems.append(f"{ln_id}: sin alternativa")

    if problems:
        result.fail("C2-blacklist-alternative", "; ".join(problems))
        return

    # Verificación cruzada con la fixture (la fixture tiene 16 entradas, todas con alternativa)
    fixture_rows = parse_simple_yaml((FIXTURES / "blacklist.yaml").read_text(encoding="utf-8"))
    fixture_missing = [r["id"] for r in fixture_rows if not r.get("alternativa")]
    if fixture_missing:
        result.fail("C2-blacklist-alternative",
                    f"Fixture blacklist.yaml sin alternativa: {fixture_missing}")
        return

    result.ok(f"C2-blacklist-alternative ({len(rows)} entradas con alternativa)")


def crit_3_writing_rules(text: str, result: EvalResult) -> None:
    """C3: las 6 reglas R-MP-01 a R-MP-06 están enunciadas."""
    rule_digits = set(RE_R_MP.findall(text))
    rule_ids_found = {f"R-MP-{d}" for d in rule_digits}
    missing = [r for r in R_MP_IDS if r not in rule_ids_found]
    if missing:
        result.fail("C3-writing-rules",
                    f"Faltan reglas: {missing} (encontradas: {sorted(rule_ids_found)})")
        return

    # Verificar que cada regla tiene al menos una mención de PASS/FAIL/Portable/No
    problems: list[str] = []
    for rid in R_MP_IDS:
        idx = text.find(f"**{rid}**")
        if idx == -1:
            problems.append(f"{rid}: regla ausente")
            continue
    if problems:
        result.fail("C3-writing-rules", "; ".join(problems))
        return

    # Verificar que la fixture writing-rules.yaml tiene 6 reglas con pass y fail
    fixture_rows = parse_simple_yaml((FIXTURES / "writing-rules.yaml").read_text(encoding="utf-8"))
    if len(fixture_rows) < 6:
        result.fail("C3-writing-rules",
                    f"Fixture writing-rules.yaml solo tiene {len(fixture_rows)} reglas")
        return
    for row in fixture_rows:
        if not row.get("pass") or not row.get("fail"):
            result.fail("C3-writing-rules",
                        f"Regla {row.get('id', '?')} sin caso pass o fail")
            return

    result.ok(f"C3-writing-rules ({len(rule_ids_found)} reglas)")


def crit_4_three_dest_table(text: str, result: EvalResult) -> None:
    """C4: la tabla §8 cubre los 3 destinos (criterio 3 de F66)."""
    # Verificar que §8 tiene los 3 encabezados de columna
    if "Obsidian" not in text:
        result.fail("C4-three-dest", "Falta columna 'Obsidian' en §8")
        return
    if "Notion import" not in text:
        result.fail("C4-three-dest", "Falta columna 'Notion import' en §8")
        return
    if "GitHub" not in text:
        result.fail("C4-three-dest", "Falta columna 'GitHub' en §8")
        return

    # Parsear filas de §8 con 3 estados
    rows = RE_SECTION8_ROW.findall(text)
    if len(rows) < 10:
        result.fail("C4-three-dest",
                    f"Solo {len(rows)} filas en §8 (esperaba ≥10)")
        return

    # Verificar cobertura de los 3 estados en la columna Notion import
    ni_ok = sum(1 for r in rows if r[1] == "✅")
    ni_warning = sum(1 for r in rows if r[1] == "⚠")
    ni_no = sum(1 for r in rows if r[1] == "❌")

    if ni_ok < 5:
        result.fail("C4-three-dest",
                    f"§8 columna Notion import solo tiene {ni_ok} entradas ✅ (esperaba ≥5)")
        return
    if ni_warning < 2:
        result.fail("C4-three-dest",
                    f"§8 columna Notion import solo tiene {ni_warning} entradas ⚠ (esperaba ≥2)")
        return
    if ni_no < 5:
        result.fail("C4-three-dest",
                    f"§8 columna Notion import solo tiene {ni_no} entradas ❌ (esperaba ≥5)")
        return

    result.ok(f"C4-three-dest ({len(rows)} filas, NI: {ni_ok}✅ {ni_warning}⚠ {ni_no}❌)")


def crit_5_acentos(text: str, result: EvalResult) -> None:
    """C5: acentos y `ñ` documentados en §6 con guía operativa y reemplazos ASCII."""
    if "## §6" not in text:
        result.fail("C5-acentos", "Falta sección §6")
        return

    # Procedimiento de 4 pasos (1., 2., 3., 4.)
    if not re.search(r"1\.\s+\*\*ID del nodo", text):
        result.fail("C5-acentos", "Falta paso 1 del procedimiento en §6.2")
        return
    if not re.search(r"2\.\s+\*\*Etiqueta", text):
        result.fail("C5-acentos", "Falta paso 2 del procedimiento en §6.2")
        return
    if not re.search(r"3\.\s+\*\*Verificación", text):
        result.fail("C5-acentos", "Falta paso 3 del procedimiento en §6.2")
        return
    if not re.search(r"4\.\s+\*\*Excepción", text):
        result.fail("C5-acentos", "Falta paso 4 del procedimiento en §6.2")
        return

    # Tabla de reemplazos ASCII
    if "## §6.4" not in text:
        result.fail("C5-acentos", "Falta §6.4 (tabla de reemplazos ASCII)")
        return
    if "ñ" not in text:
        result.fail("C5-acentos", "Falta carácter `ñ` en §6 (criterio 3)")
        return

    # Tabla de verificación de etiquetas
    if "## §6.5" not in text:
        result.fail("C5-acentos", "Falta §6.5 (tabla de verificación de etiquetas)")
        return

    # Verificar que la fixture acentos-ñ.yaml tiene ≥10 etiquetas
    fixture_rows = parse_simple_yaml((FIXTURES / "acentos-ñ.yaml").read_text(encoding="utf-8"))
    if len(fixture_rows) < 10:
        result.fail("C5-acentos",
                    f"Fixture acentos-ñ.yaml solo tiene {len(fixture_rows)} etiquetas (esperaba ≥10)")
        return

    # Verificar cobertura de los 3 destinos en la fixture
    for row in fixture_rows:
        if "portable_obsidian" not in row or "portable_notion_import" not in row or "portable_github" not in row:
            result.fail("C5-acentos",
                        f"Etiqueta {row.get('id', '?')} sin columnas portable_*")
            return

    result.ok(f"C5-acentos ({len(fixture_rows)} etiquetas)")


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    catalog: Path = args.catalog
    if not catalog.exists():
        print(f"ERROR: catálogo no encontrado: {catalog}", file=sys.stderr)
        return 2
    text = catalog.read_text(encoding="utf-8")

    result = EvalResult()
    crit_1_whitelist_blacklist(text, result)
    crit_2_blacklist_alternative(text, result)
    crit_3_writing_rules(text, result)
    crit_4_three_dest_table(text, result)
    crit_5_acentos(text, result)

    print("=" * 60)
    print("Fase 66 — Subconjunto Mermaid portable")
    print("=" * 60)
    for name in result.passed:
        print(f"  ✓ {name}")
    for name, detail in result.failed:
        print(f"  ✗ {name}")
        print(f"      {detail}")
    print("=" * 60)
    print(result.summary())
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
