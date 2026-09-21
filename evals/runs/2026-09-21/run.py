#!/usr/bin/env python3
"""
Dry-run del eval de disparo de la skill notemartin-study-notes.

Fase 10 del roadmap. Protocolo definido en `evals/trigger-eval.md` §4.

Pasos:
  1. Cargar `evals/trigger-eval/queries.yaml`.
  2. Cargar la `description` actual de `SKILL.md` (frontmatter).
  3. Tokenizar ambos (lowercase, sin acentos, sin stopwords, sin tokens < 2 chars).
  4. Por consulta: match = any(token in description_tokens).
  5. Calcular TPR/FPR por split (train / holdout).
  6. Volcar description.txt, queries.yaml, results.json, report.md.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_MD = REPO_ROOT / "skill" / "notemartin-study-notes" / "SKILL.md"
QUERIES_YAML = REPO_ROOT / "evals" / "trigger-eval" / "queries.yaml"
RUN_DIR = REPO_ROOT / "evals" / "runs" / date.today().isoformat()

# Stopwords de español e inglés. Mínimo funcional; el set se amplía si el
# dry-run muestra matches espurios sistemáticos.
STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "y", "e", "o", "u", "en", "con", "por", "para", "del", "al",
    "the", "is", "it", "this", "that", "as", "by", "at", "from",
    "que", "sin", "se", "es", "no", "si", "lo", "le", "te", "tu",
    "su", "sus", "mi", "mis", "ha", "han", "hay", "ser", "estar",
    "como", "pero", "muy", "mas", "del",  # "mas" para "más"
    "will", "would", "could", "should", "may", "might", "can",
    "i", "you", "we", "they", "he", "she", "my", "your", "our", "their",
}

# Alias bilingües ES↔EN para los términos clave de la `description`.
# El dry-run usa keyword-match binario; sin este puente, las consultas en
# inglés no matchearían con una descripción en español aunque semánticamente
# deberían. NO modifica la `description`; solo enriquece los tokens contra
# los que se compara cada query. Documentado en §7 de evals/trigger-eval.md.
BILINGUAL_ALIASES: dict[str, list[str]] = {
    # ES → [EN aliases]
    "documentacion": ["documentation", "docs", "doc", "manual"],
    "tecnica": ["technical", "tech"],
    "tecnico": ["technical", "tech"],
    "tecnicos": ["technical", "tech"],
    "manual": ["manual"],
    "manuales": ["manuals"],
    "producto": ["product"],
    "libro": ["book"],
    "libros": ["book", "books"],
    "capitulo": ["chapter"],
    "pdf": ["pdf"],
    "pdfs": ["pdfs"],
    "escaneado": ["scanned"],
    "escaneados": ["scanned"],
    "api": ["api"],
    "referencia": ["reference"],
    "referencias": ["reference"],
    "nota": ["note"],
    "notas": ["notes", "note"],
    "apunte": ["note"],
    "apuntes": ["notes", "note"],
    "estudio": ["study"],
    "obsidian": ["obsidian"],
    "notion": ["notion"],
    "appflowy": ["appflowy"],
    "markdown": ["markdown"],
    "html": ["html"],
    "repaso": ["review", "repaso"],
    "anotacion": ["note", "annotation"],
    "anotaciones": ["notes", "annotations"],
    "ficha": ["card", "flashcard"],
    "fichas": ["cards", "flashcards"],
    "ingles": ["english"],
    "espanol": ["spanish"],
}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def tokenize(text: str, expand_aliases: bool = False) -> set[str]:
    text = strip_accents(text.lower())
    # Split por cualquier cosa que no sea alfanumérica
    tokens = re.findall(r"[a-z0-9]+", text)
    # Filtrar stopwords y tokens demasiado cortos
    out = {t for t in tokens if len(t) >= 2 and t not in STOPWORDS}
    if expand_aliases:
        # Expandir cada token con sus aliases bilingües (ES → EN y viceversa).
        for t in list(out):
            for alias in BILINGUAL_ALIASES.get(t, []):
                if alias not in STOPWORDS:
                    out.add(alias)
            # También aplicar el reverso: si un token EN no está mapeado
            # directamente, buscar si alguna clave ES tiene este token como valor.
            for es_key, en_aliases in BILINGUAL_ALIASES.items():
                if t in en_aliases:
                    out.add(es_key)
                    break
    return out


def extract_description(skill_md_path: Path) -> str:
    """Extrae el valor de `description:` del frontmatter YAML de SKILL.md."""
    text = skill_md_path.read_text(encoding="utf-8")
    # El frontmatter está delimitado por '---' al inicio del archivo.
    if not text.startswith("---"):
        raise ValueError("SKILL.md no comienza con frontmatter '---'")
    end = text.index("\n---", 3)
    frontmatter = text[3:end]
    for line in frontmatter.splitlines():
        line = line.strip()
        if line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Quitar comillas envolventes si las hay
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            return value
    raise ValueError("Frontmatter sin campo 'description:'")


def parse_queries(path: Path) -> dict[str, list[dict]]:
    """Parser YAML mínimo: no requiere dependencias externas.

    El archivo tiene estructura:
      positives:
        - id: P-001
          category: ...
          ...
      negatives:
        - id: N-001
          ...
    """
    text = path.read_text(encoding="utf-8")
    queries: dict[str, list[dict]] = {"positives": [], "negatives": []}

    current_list: list[dict] | None = None
    current_item: dict | None = None
    in_frontmatter_doc = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("positives:") or line.startswith("negatives:"):
            current_list = queries[line.rstrip(":").strip()]
            current_item = None
            continue
        if line.startswith("  - id:"):
            current_item = {"id": line.split(":", 1)[1].strip()}
            current_list.append(current_item)
            continue
        if current_item is not None and line.startswith("    "):
            # Campo con clave: valor
            stripped = line.strip()
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                current_item[k.strip()] = v.strip()
    return queries


def evaluate(queries: dict[str, list[dict]], desc_tokens: set[str]) -> list[dict]:
    rows = []
    for label, items in queries.items():
        for q in items:
            tokens = tokenize(q["text"])
            match = any(t in desc_tokens for t in tokens)
            rows.append({
                "id": q["id"],
                "category": q["category"],
                "language": q.get("language", ""),
                "split": q.get("split", ""),
                "expected": "dispara" if label == "positives" else "no-dispara",
                "predicted": "dispara" if match else "no-dispara",
                "match": match,
                "tokens_in_query": sorted(tokens),
            })
    return rows


def metrics(rows: list[dict]) -> dict:
    def rate(filter_fn: callable, expected_match: bool) -> float:
        subset = [r for r in rows if filter_fn(r)]
        if not subset:
            return 0.0
        hits = sum(1 for r in subset if r["match"] == expected_match)
        return round(hits / len(subset), 4)

    return {
        "tpr_train": rate(lambda r: r["expected"] == "dispara" and r["split"] == "train", True),
        "tpr_holdout": rate(lambda r: r["expected"] == "dispara" and r["split"] == "holdout", True),
        "fpr_train": rate(lambda r: r["expected"] == "no-dispara" and r["split"] == "train", True),
        "fpr_holdout": rate(lambda r: r["expected"] == "no-dispara" and r["split"] == "holdout", True),
        "counts": {
            "positives_train": sum(1 for r in rows if r["expected"] == "dispara" and r["split"] == "train"),
            "positives_holdout": sum(1 for r in rows if r["expected"] == "dispara" and r["split"] == "holdout"),
            "negatives_train": sum(1 for r in rows if r["expected"] == "no-dispara" and r["split"] == "train"),
            "negatives_holdout": sum(1 for r in rows if r["expected"] == "no-dispara" and r["split"] == "holdout"),
        },
    }


def render_report(rows: list[dict], m: dict, desc: str, thresholds: dict) -> str:
    def verdict(value: float, target: float, op: str) -> str:
        ok = (value >= target) if op == ">=" else (value <= target)
        return "PASS" if ok else "FAIL"

    lines = []
    lines.append("# Reporte del dry-run — Fase 10")
    lines.append("")
    lines.append(f"Fecha: {date.today().isoformat()}")
    lines.append(f"Source: `skill/notemartin-study-notes/SKILL.md`")
    lines.append("")
    lines.append("## Description medida")
    lines.append("")
    lines.append("> " + desc)
    lines.append("")
    lines.append(f"Palabras: {len(desc.split())} / 100.")
    lines.append("")
    lines.append("## Métricas")
    lines.append("")
    lines.append(f"- TPR train     = {m['tpr_train']:.4f}  (umbral ≥ {thresholds['tpr_train']})  → {verdict(m['tpr_train'], thresholds['tpr_train'], '>=')}")
    lines.append(f"- TPR holdout   = {m['tpr_holdout']:.4f}  (umbral ≥ {thresholds['tpr_holdout']})  → {verdict(m['tpr_holdout'], thresholds['tpr_holdout'], '>=')}")
    lines.append(f"- FPR train     = {m['fpr_train']:.4f}  (umbral ≤ {thresholds['fpr_train']})  → {verdict(m['fpr_train'], thresholds['fpr_train'], '<=')}")
    lines.append(f"- FPR holdout   = {m['fpr_holdout']:.4f}  (umbral ≤ {thresholds['fpr_holdout']})  → {verdict(m['fpr_holdout'], thresholds['fpr_holdout'], '<=')}")
    lines.append("")
    lines.append("## Conteos")
    lines.append("")
    for k, v in m["counts"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## Fallos por categoría")
    lines.append("")

    def fail_ids(filter_fn: callable) -> list[dict]:
        return [r for r in rows if filter_fn(r) and (
            (r["expected"] == "dispara" and not r["match"]) or
            (r["expected"] == "no-dispara" and r["match"])
        )]

    categories = sorted({r["category"] for r in rows})
    for cat in categories:
        fails = [r for r in rows if r["category"] == cat and (
            (r["expected"] == "dispara" and not r["match"]) or
            (r["expected"] == "no-dispara" and r["match"])
        )]
        if fails:
            ids = ", ".join(f"{r['id']} ({r['split']})" for r in fails)
            lines.append(f"- `{cat}` ({len(fails)} fallos): {ids}")
    if not any(lines[-i].startswith("- `") and "fallos" in lines[-i] for i in range(1, len(categories) + 1)):
        lines.append("- (ninguno)")
    lines.append("")

    lines.append("## Detalle por consulta")
    lines.append("")
    lines.append("| ID | Categoría | Idioma | Split | Esperado | Predicho | Match |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        ok = "✓" if (
            (r["expected"] == "dispara" and r["match"]) or
            (r["expected"] == "no-dispara" and not r["match"])
        ) else "✗"
        lines.append(f"| {r['id']} | {r['category']} | {r['language']} | {r['split']} | {r['expected']} | {r['predicted']} | {ok} |")
    lines.append("")

    all_pass = (
        verdict(m['tpr_train'], thresholds['tpr_train'], '>=') == "PASS"
        and verdict(m['tpr_holdout'], thresholds['tpr_holdout'], '>=') == "PASS"
        and verdict(m['fpr_train'], thresholds['fpr_train'], '<=') == "PASS"
        and verdict(m['fpr_holdout'], thresholds['fpr_holdout'], '<=') == "PASS"
    )
    lines.append("## Decisión")
    lines.append("")
    if all_pass:
        lines.append("**LOCK.** Los cuatro umbrales pasan. La `description` queda congelada como 'description final' sin más iteraciones.")
    else:
        lines.append("**FAIL.** Algún umbral no se cumple. Ver §6 de `evals/trigger-eval.md` para el procedimiento de iteración.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    description = extract_description(SKILL_MD)
    (RUN_DIR / "description.txt").write_text(description + "\n", encoding="utf-8")
    print(f"Description: {len(description.split())} palabras / 100")

    queries = parse_queries(QUERIES_YAML)
    n_pos = len(queries["positives"])
    n_neg = len(queries["negatives"])
    print(f"Set: {n_pos} positivos + {n_neg} negativos = {n_pos + n_neg}")
    if n_pos + n_neg == 0:
        print("ERROR: queries.yaml vacío", file=sys.stderr)
        return 1

    desc_tokens = tokenize(description, expand_aliases=True)
    print(f"Tokens únicos en description (con aliases): {len(desc_tokens)} → {sorted(desc_tokens)}")

    rows = evaluate(queries, desc_tokens)
    # Para cada query, registrar también los aliases que aportaron match
    for row in rows:
        if row["match"]:
            contribs = [t for t in row["tokens_in_query"] if t in desc_tokens]
            row["matched_tokens"] = contribs
    m = metrics(rows)

    thresholds = {
        "tpr_train": 0.90,
        "tpr_holdout": 0.90,
        "fpr_train": 0.10,
        "fpr_holdout": 0.10,
    }

    payload = {
        "date": date.today().isoformat(),
        "thresholds": thresholds,
        "metrics": m,
        "query_results": rows,
    }
    (RUN_DIR / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Snapshot del set usado
    (RUN_DIR / "queries.yaml").write_text(
        QUERIES_YAML.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = render_report(rows, m, description, thresholds)
    (RUN_DIR / "report.md").write_text(report, encoding="utf-8")

    print("")
    print(f"TPR train   = {m['tpr_train']:.4f} (≥ 0.90)")
    print(f"TPR holdout = {m['tpr_holdout']:.4f} (≥ 0.90)")
    print(f"FPR train   = {m['fpr_train']:.4f} (≤ 0.10)")
    print(f"FPR holdout = {m['fpr_holdout']:.4f} (≤ 0.10)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
