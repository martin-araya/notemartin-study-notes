#!/usr/bin/env python3
"""arxiv_tex.py — Oráculo de código fuente LaTeX para artículos arXiv (P3).

Analiza el árbol de código fuente TeX descargado (e-print), aplana inclusiones
(\\input / \\include), expande macros del preámbulo (\\newcommand, \\DeclareMathOperator, \\def),
extrae ecuaciones, teoremas, pruebas, algoritmos, tablas y bibliografía (.bbl / thebibliography),
y alinea las ecuaciones con las regiones de fórmulas detectadas en el PDF.

Uso:
    python3 scripts/ingest/arxiv_tex.py --tex-dir <dir> --out-dir <dir>
    python3 scripts/ingest/arxiv_tex.py --tex-dir <dir> --ingest-dir <dir> --out-dir <dir>

Salidas:
    arxiv_tex_manifest.json — catálogo estructurado de entornos LaTeX
    formulas_updated.json   — fórmulas con LaTeX inyectado (si --ingest-dir presente)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def strip_latex_comments(text: str) -> str:
    """Elimina comentarios LaTeX (% no escapados), preservando saltos de línea."""
    cleaned_lines = []
    for line in text.splitlines():
        res = []
        escaped = False
        for ch in line:
            if ch == "\\" and not escaped:
                escaped = True
                res.append(ch)
            elif ch == "%" and not escaped:
                break
            else:
                escaped = False
                res.append(ch)
        cleaned_lines.append("".join(res))
    return "\n".join(cleaned_lines)


def extract_balanced_braces(text: str, start_index: int = 0) -> Tuple[Optional[str], int]:
    """Extrae el contenido entre llaves balanceadas { ... }, soportando llaves anidadas.

    Devuelve (contenido_interno, fin_posicion_en_text) o (None, start_index) si no encuentra.
    """
    brace_start = text.find("{", start_index)
    if brace_start == -1:
        return None, start_index

    depth = 0
    escaped = False
    inner_start = brace_start + 1
    for i in range(brace_start, len(text)):
        ch = text[i]
        if ch == "\\" and not escaped:
            escaped = True
            continue
        if not escaped:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[inner_start:i], i + 1
        escaped = False
    return None, start_index


def find_command_arg(text: str, command: str) -> Optional[str]:
    """Encuentra el primer argumento entre llaves de un comando como \\caption o \\title."""
    pos = 0
    cmd_pattern = re.compile(re.escape(command) + r"\s*\{")
    m = cmd_pattern.search(text)
    if not m:
        return None
    inner, _ = extract_balanced_braces(text, m.start())
    return inner


def find_main_tex(tex_dir: Path) -> Optional[Path]:
    """Encuentra el archivo .tex raíz en un directorio."""
    candidates = list(tex_dir.glob("*.tex")) + list(tex_dir.glob("**/*.tex"))
    # Descartar subdirectorios si hay archivo en la raíz
    root_candidates = [c for c in candidates if c.parent == tex_dir]
    pool = root_candidates if root_candidates else candidates

    best: Optional[Path] = None
    for cand in pool:
        try:
            content = cand.read_text(encoding="utf-8", errors="ignore")
            if "\\documentclass" in content:
                if "\\begin{document}" in content:
                    return cand
                best = cand
        except Exception:
            continue
    return best


def flatten_tex(root_tex: Path, seen: Optional[Set[Path]] = None) -> str:
    """Aplana recursivamente directivas \\input{...} e \\include{...}."""
    if seen is None:
        seen = set()
    root_tex = root_tex.resolve()
    if root_tex in seen or not root_tex.exists():
        return ""
    seen.add(root_tex)

    try:
        content = root_tex.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    content = strip_latex_comments(content)
    base_dir = root_tex.parent

    def _replace_input(match: re.Match) -> str:
        rel = match.group("path").strip()
        if not rel.endswith(".tex"):
            target = base_dir / f"{rel}.tex"
            if not target.exists():
                target = base_dir / rel
        else:
            target = base_dir / rel

        if target.exists() and target not in seen:
            return flatten_tex(target, seen)
        return ""

    pattern = re.compile(r"\\(?:input|include)\s*\{(?P<path>[^}]+)\}")
    flattened = pattern.sub(_replace_input, content)
    return flattened


def extract_macros(preamble: str) -> Dict[str, Dict[str, Any]]:
    """Extrae macros definidas por el autor (\\newcommand, \\def, \\DeclareMathOperator)."""
    macros: Dict[str, Dict[str, Any]] = {}

    # 1. \\DeclareMathOperator{\\name}{val} o \\DeclareMathOperator*{\\name}{val}
    dmo_re = re.compile(r"\\DeclareMathOperator\*?\s*\{\\?(?P<name>[a-zA-Z]+)\}\s*\{(?P<val>[^}]+)\}")
    for m in dmo_re.finditer(preamble):
        name = m.group("name")
        val = m.group("val").strip()
        macros[name] = {"nargs": 0, "body": f"\\operatorname{{{val}}}"}

    # 2. \\newcommand{\\name}[nargs]{body} o \\newcommand{\\name}{body}
    nc_re = re.compile(
        r"\\(?:re)?newcommand\s*\{\\?(?P<name>[a-zA-Z]+)\}(?:\[(?P<nargs>\d+)\])?\s*\{(?P<body>.*?)\}(?=\s*(?:\\[a-zA-Z]|%|$))",
        re.DOTALL,
    )
    for m in nc_re.finditer(preamble):
        name = m.group("name")
        nargs = int(m.group("nargs")) if m.group("nargs") else 0
        body = m.group("body").strip()
        macros[name] = {"nargs": nargs, "body": body}

    # 3. \\def\\name{body}
    def_re = re.compile(r"\\def\s*\\(?P<name>[a-zA-Z]+)\s*\{(?P<body>.*?)\}", re.DOTALL)
    for m in def_re.finditer(preamble):
        name = m.group("name")
        body = m.group("body").strip()
        if name not in macros:
            macros[name] = {"nargs": 0, "body": body}

    return macros


def expand_macros(latex: str, macros: Dict[str, Dict[str, Any]], max_depth: int = 5) -> str:
    """Expande recursivamente macros de autor en una cadena LaTeX."""
    current = latex
    for _ in range(max_depth):
        modified = False
        for name, spec in macros.items():
            nargs = spec["nargs"]
            body = spec["body"]
            if nargs == 0:
                pattern = re.compile(r"\\" + re.escape(name) + r"(?![a-zA-Z])")
                if pattern.search(current):
                    current = pattern.sub(lambda _: body, current)
                    modified = True
            elif nargs == 1:
                pattern = re.compile(r"\\" + re.escape(name) + r"\s*\{(?P<arg>[^}]+)\}")
                if pattern.search(current):
                    current = pattern.sub(lambda m: body.replace("#1", m.group("arg")), current)
                    modified = True
        if not modified:
            break
    return current


def extract_equations(text: str, macros: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extrae entornos de ecuaciones display del texto LaTeX plano."""
    equations: List[Dict[str, Any]] = []
    eq_counter = 1

    # Entornos matemáticos de display comunes
    env_pattern = re.compile(
        r"\\begin\{(?P<env>equation|equation\*|align|align\*|gather|gather\*|multline|multline\*)\}"
        r"(?P<body>.*?)"
        r"\\end\{(?P=env)\}",
        re.DOTALL,
    )

    label_re = re.compile(r"\\label\{(?P<label>[^}]+)\}")
    tag_re = re.compile(r"\\tag\{(?P<tag>[^}]+)\}")

    for m in env_pattern.finditer(text):
        env = m.group("env")
        raw_body = m.group("body").strip()

        # Extraer label y tag
        label_m = label_re.search(raw_body)
        label = label_m.group("label") if label_m else None

        tag_m = tag_re.search(raw_body)
        custom_tag = tag_m.group("tag") if tag_m else None

        is_numbered = not env.endswith("*") or (custom_tag is not None)
        eq_num = custom_tag if custom_tag else (str(eq_counter) if is_numbered else None)

        if is_numbered and not custom_tag:
            eq_counter += 1

        # Limpiar body: remover labels y tags para render limpio en KaTeX
        clean_body = label_re.sub("", raw_body)
        clean_body = tag_re.sub("", clean_body)
        clean_body = re.sub(r"\\nonumber\b", "", clean_body)

        # Expandir macros
        expanded = expand_macros(clean_body.strip(), macros)
        # Normalizar espacios
        normalized = re.sub(r"[ \t]+", " ", expanded).strip()

        equations.append({
            "index": len(equations) + 1,
            "env": env,
            "numbered": is_numbered,
            "number": eq_num,
            "label": label,
            "latex": normalized,
            "raw": raw_body,
        })

    # También capturar $$ ... $$ que no estén dentro de los anteriores
    double_dollar_re = re.compile(r"\$\$(?P<body>.+?)\$\$", re.DOTALL)
    for m in double_dollar_re.finditer(text):
        raw_body = m.group("body").strip()
        if any(raw_body in eq["raw"] for eq in equations):
            continue
        expanded = expand_macros(raw_body, macros)
        equations.append({
            "index": len(equations) + 1,
            "env": "$$",
            "numbered": False,
            "number": None,
            "label": None,
            "latex": re.sub(r"[ \t]+", " ", expanded).strip(),
            "raw": raw_body,
        })

    return equations


def extract_theorems(text: str) -> List[Dict[str, Any]]:
    """Extrae entornos de teoremas, lemas, proposiciones, corolarios, definiciones y pruebas."""
    theorems: List[Dict[str, Any]] = []
    kinds = ["theorem", "lemma", "proposition", "corollary", "definition", "claim", "remark"]
    pattern_str = r"\\begin\{(?P<kind>" + "|".join(kinds) + r")\}(?:\[(?P<title>[^\]]+)\])?(?P<body>.*?)\\end\{(?P=kind)\}"
    pattern = re.compile(pattern_str, re.DOTALL | re.IGNORECASE)

    label_re = re.compile(r"\\label\{(?P<label>[^}]+)\}")

    for m in pattern.finditer(text):
        kind = m.group("kind").capitalize()
        title = m.group("title").strip() if m.group("title") else None
        body = m.group("body").strip()

        label_m = label_re.search(body)
        label = label_m.group("label") if label_m else None
        clean_body = label_re.sub("", body).strip()

        theorems.append({
            "index": len(theorems) + 1,
            "kind": kind,
            "title": title,
            "label": label,
            "statement": clean_body,
        })

    # Extraer proofs
    proof_re = re.compile(r"\\begin\{proof\}(?:\[(?P<title>[^\]]+)\])?(?P<body>.*?)\\end\{proof\}", re.DOTALL | re.IGNORECASE)
    for m in proof_re.finditer(text):
        title = m.group("title").strip() if m.group("title") else "Proof"
        body = m.group("body").strip()
        theorems.append({
            "index": len(theorems) + 1,
            "kind": "Proof",
            "title": title,
            "label": None,
            "statement": body,
        })

    return theorems


def extract_algorithms(text: str) -> List[Dict[str, Any]]:
    """Extrae entornos de algoritmos (algorithm / algorithmic)."""
    algorithms: List[Dict[str, Any]] = []
    alg_re = re.compile(r"\\begin\{algorithm\}(?P<body>.*?)\\end\{algorithm\}", re.DOTALL)
    caption_re = re.compile(r"\\caption\{(?P<caption>[^}]+)\}")
    label_re = re.compile(r"\\label\{(?P<label>[^}]+)\}")

    for m in alg_re.finditer(text):
        body = m.group("body").strip()
        caption = find_command_arg(body, "\\caption")

        label_m = label_re.search(body)
        label = label_m.group("label") if label_m else None

        # Líneas de pseudocódigo
        lines = []
        for line in body.splitlines():
            line_str = line.strip()
            if line_str.startswith("\\caption") or line_str.startswith("\\label"):
                continue
            if line_str in ("\\begin{algorithmic}", "\\end{algorithmic}"):
                continue
            if line_str:
                lines.append(line_str)

        algorithms.append({
            "index": len(algorithms) + 1,
            "caption": caption,
            "label": label,
            "lines": lines,
            "raw": body,
        })

    return algorithms


def extract_tables(text: str) -> List[Dict[str, Any]]:
    """Extrae tablas LaTeX (table / tabular)."""
    tables: List[Dict[str, Any]] = []
    tab_re = re.compile(r"\\begin\{table\*?\}(?P<body>.*?)\\end\{table\*?\}", re.DOTALL)
    tabular_re = re.compile(r"\\begin\{tabular\}\s*\{(?P<cols>[^}]+)\}(?P<rows>.*?)\\end\{tabular\}", re.DOTALL)
    label_re = re.compile(r"\\label\{(?P<label>[^}]+)\}")

    for m in tab_re.finditer(text):
        body = m.group("body").strip()
        caption = find_command_arg(body, "\\caption")
        label_m = label_re.search(body)
        label = label_m.group("label") if label_m else None

        tabular_m = tabular_re.search(body)
        parsed_rows: List[List[str]] = []
        headers: List[str] = []
        if tabular_m:
            raw_rows = tabular_m.group("rows").strip()
            # Dividir por \\
            row_lines = [r.strip() for r in raw_rows.split("\\\\") if r.strip()]
            for r in row_lines:
                # Quitar booktabs
                clean_r = re.sub(r"\\(?:toprule|midrule|bottomrule|hline)", "", r).strip()
                if not clean_r:
                    continue
                cells = [c.strip() for c in clean_r.split("&")]
                if not headers:
                    headers = cells
                else:
                    parsed_rows.append(cells)

        tables.append({
            "index": len(tables) + 1,
            "caption": caption,
            "label": label,
            "headers": headers,
            "rows": parsed_rows,
        })

    return tables


def extract_bibliography(tex_dir: Path, text: str) -> List[Dict[str, Any]]:
    """Extrae referencias bibliográficas desde archivos .bbl o entorno thebibliography."""
    references: List[Dict[str, Any]] = []

    # 1. Buscar archivo .bbl
    bbl_files = list(tex_dir.glob("*.bbl"))
    bbl_content = ""
    if bbl_files:
        try:
            bbl_content = bbl_files[0].read_text(encoding="utf-8", errors="ignore")
        except Exception:
            bbl_content = ""

    src_text = bbl_content if bbl_content else text

    # Parsear \\bibitem[label]{key} entry...
    bibitem_re = re.compile(
        r"\\bibitem(?:\[(?P<label>[^\]]*)\])?\{(?P<key>[^}]+)\}(?P<entry>.*?)(?=\\bibitem|\\end\{thebibliography\}|$)",
        re.DOTALL,
    )

    for m in bibitem_re.finditer(src_text):
        label = m.group("label").strip() if m.group("label") else None
        key = m.group("key").strip()
        entry_raw = m.group("entry").strip()

        # Limpiar comandos comunes de formateo en bibitem
        clean_entry = re.sub(r"\\(?:newblock|em|bf|it|url|href\{[^}]*\}|newblock)\b", "", entry_raw)
        clean_entry = re.sub(r"[\{\}]", "", clean_entry)
        clean_entry = re.sub(r"\s+", " ", clean_entry).strip()

        references.append({
            "index": len(references) + 1,
            "key": key,
            "label": label,
            "text": clean_entry,
        })

    return references


def parse_tex_source(tex_dir: Path) -> Dict[str, Any]:
    """Procesa el árbol de código fuente TeX completo y devuelve el manifiesto del oráculo."""
    main_tex = find_main_tex(tex_dir)
    if not main_tex:
        return {"error": "no_main_tex_found"}

    flattened = flatten_tex(main_tex)
    if not flattened:
        return {"error": "empty_tex_content"}

    # Dividir preámbulo y cuerpo
    doc_split = re.split(r"\\begin\{document\}", flattened, maxsplit=1)
    preamble = doc_split[0]
    body = doc_split[1] if len(doc_split) > 1 else flattened

    macros = extract_macros(preamble)
    equations = extract_equations(body, macros)
    theorems = extract_theorems(body)
    algorithms = extract_algorithms(body)
    tables = extract_tables(body)
    references = extract_bibliography(tex_dir, body)

    # Extraer título si es posible
    raw_title = find_command_arg(preamble, "\\title")
    title = None
    if raw_title:
        title = re.sub(r"\\[a-zA-Z]+|\{|\}", "", raw_title)
        title = re.sub(r"\s+", " ", title).strip()

    return {
        "main_tex": str(main_tex.relative_to(tex_dir)),
        "title": title,
        "macros_count": len(macros),
        "macros": macros,
        "equations_count": len(equations),
        "equations": equations,
        "theorems_count": len(theorems),
        "theorems": theorems,
        "algorithms_count": len(algorithms),
        "algorithms": algorithms,
        "tables_count": len(tables),
        "tables": tables,
        "references_count": len(references),
        "references": references,
    }


def align_equations_with_regions(
    tex_equations: List[Dict[str, Any]],
    formula_regions: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    """Alinea ecuaciones del oráculo TeX con regiones del PDF detectadas por formulas.py.

    Estrategia de alineación:
    1. Si la región del PDF tiene un número (e.g. '(1)', '1'), match con la ecuación con ese número.
    2. Las ecuaciones restantes se alinean secuencialmente por orden de aparición en el documento.
    """
    updated_regions = [dict(r) for r in formula_regions]
    matched_count = 0
    used_tex_indices: Set[int] = set()

    # Paso 1: Match por número de ecuación
    for reg in updated_regions:
        reg_num = reg.get("number_str") or reg.get("number")
        if reg_num:
            clean_num = str(reg_num).strip("() []{}.,")
            for eq in tex_equations:
                if eq["index"] in used_tex_indices:
                    continue
                eq_num = str(eq.get("number") or "").strip("() []{}.,")
                if eq_num and eq_num == clean_num:
                    reg["latex"] = eq["latex"]
                    reg["latex_source"] = "tex"
                    reg["tex_label"] = eq.get("label")
                    reg["pending"] = False
                    used_tex_indices.add(eq["index"])
                    matched_count += 1
                    break

    # Paso 2: Match secuencial para regiones pendientes
    remaining_tex = [eq for eq in tex_equations if eq["index"] not in used_tex_indices]
    tex_idx = 0
    for reg in updated_regions:
        if reg.get("latex_source") == "tex":
            continue
        if tex_idx < len(remaining_tex):
            eq = remaining_tex[tex_idx]
            reg["latex"] = eq["latex"]
            reg["latex_source"] = "tex"
            reg["tex_label"] = eq.get("label")
            reg["pending"] = False
            used_tex_indices.add(eq["index"])
            matched_count += 1
            tex_idx += 1

    return updated_regions, matched_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Oráculo LaTeX para arXiv (P3)")
    parser.add_argument("--tex-dir", required=True, type=Path, help="Directorio con código fuente LaTeX descomprimido")
    parser.add_argument("--out-dir", required=True, type=Path, help="Directorio destino para manifiesto y salidas")
    parser.add_argument("--ingest-dir", type=Path, default=None, help="Directorio con salidas de formulas.py para alinear")
    parser.add_argument("--json-only", action="store_true", help="Solo emitir JSON en stdout")

    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = parse_tex_source(args.tex_dir)

    manifest_path = args.out_dir / "arxiv_tex_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    aligned_count = 0
    if args.ingest_dir and args.ingest_dir.exists():
        # Buscar formulas.json
        formulas_files = list(args.ingest_dir.glob("**/formulas.json"))
        if formulas_files:
            formulas_file = formulas_files[0]
            try:
                formulas_data = json.loads(formulas_file.read_text(encoding="utf-8"))
                regions = formulas_data.get("regions", formulas_data if isinstance(formulas_data, list) else [])
                updated_regs, aligned_count = align_equations_with_regions(manifest.get("equations", []), regions)
                if isinstance(formulas_data, dict):
                    formulas_data["regions"] = updated_regs
                    formulas_data["tex_aligned_count"] = aligned_count
                    out_formulas = formulas_data
                else:
                    out_formulas = updated_regs
                (args.out_dir / "formulas_updated.json").write_text(
                    json.dumps(out_formulas, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except Exception as e:
                sys.stderr.write(f"Aviso al alinear con formulas.json: {e}\n")

    if args.json_only:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        if "error" in manifest:
            print(f"Error procesando TeX: {manifest['error']}", file=sys.stderr)
            return 1
        print(f"arXiv TeX Oracle procesado exitosamente:")
        print(f"  Archivo principal: {manifest['main_tex']}")
        print(f"  Macros de preámbulo: {manifest['macros_count']}")
        print(f"  Ecuaciones extraídas: {manifest['equations_count']}")
        print(f"  Teoremas y pruebas: {manifest['theorems_count']}")
        print(f"  Algoritmos: {manifest['algorithms_count']}")
        print(f"  Tablas: {manifest['tables_count']}")
        print(f"  Referencias bibliográficas: {manifest['references_count']}")
        if args.ingest_dir:
            print(f"  Fórmulas alineadas con regiones: {aligned_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
