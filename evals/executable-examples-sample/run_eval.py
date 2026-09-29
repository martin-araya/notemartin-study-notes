#!/usr/bin/env python3
"""Verificador de la Fase 96 — `executable-examples`.

Ejecuta 16 sub-criterios sobre los deliverables de F96:

  ROADMAP (3):
    C1 — `executable-examples.md` existe, ≤ 600 líneas, contiene las 9
         secciones canónicas.
    C2 — §3 tiene 3 plantillas (DB / redes / CLI) con `## Setup` / `## Acción`
         / `## Resultado` / `## Limpieza` cada una.
    C3 — §5 tiene ≥ 5 anti-ejemplos NE1-NEN.

  Positivos (4):
    C4 — Las 3 notas base tienen las 4 secciones canónicas en orden.
    C5 — Las 3 notas base tienen cabecera `> **Entorno:**` con ≥ 4 campos.
    C6 — Las 3 notas base declaran limpieza (`## Limpieza` o "No requiere").
    C7 — `notes/anti-missing-cleanup.md` falla C6 a propósito (test negativo).

  Negativos y reglas (3):
    C8 — Wirings cerrados (`06-writing/README.md` y `SKILL.md`).
    C9 — Cada nota base tiene ≥ 1 anclaje visual en `## Resultado`.
    C10 — Ninguna nota base tiene "depende de / asumiendo / suponiendo"
          sin bloque `## Setup` o cabecera `> **Entorno:**`.

  Derivados (6):
    D1 — `wc -l executable-examples.md` ≤ 600.
    D2 — 9 secciones canónicas presentes (alias de C1).
    D3 — §4 tabla de 3 niveles con umbrales numéricos.
    D4 — §7 tiene ≥ 8 señales D1-D10 algorítmicas.
    D5 — Las 3 notas base pasan `density_check.py --strict` exit 0.
    D6 — Wirings cerrados (alias de C8).

Uso:
    python3 evals/executable-examples-sample/build_fixtures.py --force
    python3 evals/executable-examples-sample/run_eval.py

Salida esperada: PASS 16/16.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "06-writing" / "executable-examples.md"
WRITING_README = SKILL_DIR / "references" / "06-writing" / "README.md"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
DENSITY_CHECK = SKILL_DIR / "scripts" / "validate" / "density_check.py"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Anatomía del mínimo reproducible",
    "## §3 · Plantillas canónicas",
    "## §4 · Escalado mínimo / realista / límite",
    "## §5 · Ejemplos negativos",
    "## §6 · Declaración de entorno",
    "## §7 · Señales de diagnóstico",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

POSITIVE_NOTES = ("db-postgres-count.md", "net-tcpdump-syn.md", "cli-docker-run.md")
NEGATIVE_NOTE = "anti-missing-cleanup.md"

SECTION_RE = re.compile(r"^##\s+(Setup|Acci[oó]n|Resultado|Limpieza)\s*$", re.MULTILINE)


class EvalResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    @property
    def status(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _section_text(text: str, header_prefix: str) -> str:
    """Devuelve el texto de la sección H2 o H3 que empieza con header_prefix.

    El fin se determina por el siguiente encabezado de nivel `<=` al del
    inicio, igual que en `evals/intuition-first-sample/run_eval.py`.
    """
    lines = text.split("\n")
    start = None
    start_level = 2
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        if (line.startswith("## ") or line.startswith("### ")) and stripped.startswith(header_prefix):
            start = i
            start_level = len(line) - len(line.lstrip("#"))
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("#"):
            current_level = len(lines[j]) - len(lines[j].lstrip("#"))
            if current_level <= start_level:
                end = j
                break
    return "\n".join(lines[start:end])


def _all_section_headers(text: str) -> List[str]:
    """Devuelve los headers H2 en orden, normalizados."""
    out = []
    for line in text.split("\n"):
        if line.startswith("## ") and not line.startswith("### "):
            out.append(line[3:].strip())
    return out


def check_c1_doc_structure(result: EvalResult) -> None:
    if not DOC_PATH.exists():
        result.fail("C1-doc-structure", f"no existe {DOC_PATH}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("C1-doc-structure", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    for header in EXPECTED_SECTIONS:
        if header not in text:
            result.fail("C1-doc-structure", f"falta sección {header}")
            return
    result.ok("C1-doc-structure")


def _strip_fenced_code(text: str) -> str:
    """Elimina bloques de código fenceado (``` o ~~~) para no contar
    headers internos como Markdown real. Reemplaza por líneas vacías
    preservando offsets para regex posteriores."""
    lines = text.split("\n")
    out = []
    in_fence = False
    fence_marker = None
    for line in lines:
        stripped = line.lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = stripped[:3]
                out.append("")
            else:
                out.append(line)
        else:
            if stripped.startswith(fence_marker):
                in_fence = False
            out.append("")
    return "\n".join(out)


def _find_subheader_block(text: str, header_id: str) -> str:
    """Busca un encabezado `### {header_id}` en texto con code fences
    eliminados y devuelve el bloque desde ahí hasta el siguiente header
    H3/H2 (excluyendo el final)."""
    lines = text.split("\n")
    start = None
    start_level = 3
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(" + re.escape(header_id) + r")\b", line)
        if m:
            start = i
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#{1,3})\s", lines[j])
        if m:
            current_level = len(m.group(1))
            if current_level <= start_level:
                end = j
                break
    return "\n".join(lines[start:end])


def _find_h3_section(text: str, header_id: str) -> str:
    """Busca un encabezado `### {header_id}` en el texto y devuelve el
    bloque hasta el siguiente H3 o H2, **ignorando headers que estén
    dentro de bloques de código fenceado** (`notemark`, ` ``` `, etc.).

    Esto es necesario porque las plantillas de §3.1/§3.2/§3.3 viven
    dentro de un bloque ```notemark``` que contiene H2 internos
    (`## Setup`, `## Acción`, …) que queremos ver, no romper.
    """
    lines = text.split("\n")
    start = None
    start_level = 3
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(" + re.escape(header_id) + r")\b", line)
        if m:
            start = i
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    in_fence = False
    fence_marker = None
    for j in range(start + 1, len(lines)):
        stripped = lines[j].lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = stripped[:3]
                continue
            m = re.match(r"^(#{1,3})\s", lines[j])
            if m:
                current_level = len(m.group(1))
                if current_level <= start_level:
                    end = j
                    break
        else:
            if stripped.startswith(fence_marker):
                in_fence = False
    return "\n".join(lines[start:end])


def check_c2_templates(result: EvalResult) -> None:
    raw_text = DOC_PATH.read_text(encoding="utf-8")
    # Las plantillas §3.1/§3.2/§3.3 son H3 headings en el cuerpo del doc;
    # sus contenidos (## Setup, ## Acción, etc.) están dentro de bloques
    # ```notemark```, así que NO strippeamos code fences: los queremos ver.
    for sub_id in ("§3.1", "§3.2", "§3.3"):
        sec_sub = _find_h3_section(raw_text, sub_id)
        if not sec_sub:
            result.fail("C2-templates", f"falta plantilla §3 ({sub_id})")
            return
        for stage in ("Setup", "Acción", "Resultado", "Limpieza"):
            if f"## {stage}" not in sec_sub:
                result.fail(
                    "C2-templates",
                    f"§3 {sub_id} no contiene '## {stage}'",
                )
                return
    result.ok("C2-templates")


def check_c3_antiexamples(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec5 = _section_text(text, "§5")
    if not sec5:
        result.fail("C3-antiexamples", "no se encontró §5")
        return
    nes = re.findall(r"\*\*NE(\d+)\*\*", sec5)
    if len(set(nes)) < 5:
        result.fail("C3-antiexamples", f"§5 lista {len(set(nes))} anti-ejemplos NE* (esperaba ≥ 5)")
        return
    result.ok("C3-antiexamples")


def _note_has_canonical_sections(text: str) -> bool:
    """Verifica que las 4 secciones Setup/Acción/Resultado/Limpieza aparecen en orden canónico."""
    headers = []
    for line in text.split("\n"):
        m = SECTION_RE.match(line)
        if m:
            headers.append(m.group(1).lower())
    # Aceptar "Setup", "Accion"/"Acción", "Resultado", "Limpieza"
    expected = ["setup", "acción", "resultado", "limpieza"]
    return headers == expected


def _note_has_cleanup(text: str) -> bool:
    return bool(
        re.search(r"^##\s+Limpieza\s*$", text, re.MULTILINE)
        or re.search(r"^>\s+No requiere\s+(setup|limpieza)", text, re.MULTILINE | re.IGNORECASE)
    )


def _note_has_entorno(text: str) -> bool:
    m = re.search(r"^>\s+\*\*Entorno:\*\*\s+(.+)$", text, re.MULTILINE)
    if not m:
        return False
    # ≥ 4 campos: producto, OS, cliente, datos semilla (separados por · o ,)
    content = m.group(1)
    fields = [f.strip() for f in re.split(r"[·•|]", content) if f.strip()]
    return len(fields) >= 4


def check_c4_sections_order(result: EvalResult) -> None:
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        if not path.exists():
            result.fail("C4-sections-order", f"falta nota {path}")
            return
        text = path.read_text(encoding="utf-8")
        if not _note_has_canonical_sections(text):
            result.fail(
                "C4-sections-order",
                f"{fname}: secciones Setup/Acción/Resultado/Limpieza no están en orden canónico",
            )
            return
    result.ok("C4-sections-order")


def check_c5_entorno(result: EvalResult) -> None:
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        if not _note_has_entorno(text):
            result.fail(
                "C5-entorno",
                f"{fname}: falta cabecera '> **Entorno:** ...' con ≥ 4 campos",
            )
            return
    result.ok("C5-entorno")


def check_c6_cleanup_positive(result: EvalResult) -> None:
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        if not _note_has_cleanup(text):
            result.fail(
                "C6-cleanup-positive",
                f"{fname}: falta '## Limpieza' o '> No requiere ...'",
            )
            return
    result.ok("C6-cleanup-positive")


def check_c7_cleanup_negative(result: EvalResult) -> None:
    path = NOTES_DIR / NEGATIVE_NOTE
    if not path.exists():
        result.fail("C7-cleanup-negative", f"falta fixture negativa {path}")
        return
    text = path.read_text(encoding="utf-8")
    if _note_has_cleanup(text):
        result.fail(
            "C7-cleanup-negative",
            f"{NEGATIVE_NOTE}: el fixture NEGATIVO no debe tener limpieza (rompe el test)",
        )
        return
    result.ok("C7-cleanup-negative")


def check_c8_wirings_closed(result: EvalResult) -> None:
    if not WRITING_README.exists():
        result.fail("C8-wirings-closed", f"no existe {WRITING_README}")
        return
    rread = WRITING_README.read_text(encoding="utf-8")
    if re.search(r"\[pendiente\s+F96\]", rread):
        result.fail("C8-wirings-closed", "06-writing/README.md sigue marcando [pendiente F96]")
        return
    if "executable-examples.md" not in rread:
        result.fail("C8-wirings-closed", "06-writing/README.md no menciona executable-examples.md")
        return
    if not SKILL_MD_PATH.exists():
        result.fail("C8-wirings-closed", f"no existe {SKILL_MD_PATH}")
        return
    if "executable-examples.md" not in SKILL_MD_PATH.read_text(encoding="utf-8"):
        result.fail("C8-wirings-closed", "SKILL.md no menciona executable-examples.md")
        return
    result.ok("C8-wirings-closed")


def check_c9_visual_anchors(result: EvalResult) -> None:
    """Cada nota base tiene ≥ 1 bloque de código (anclaje visual) en `## Resultado`."""
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        sec = _section_text(text, "Resultado")
        if not sec:
            result.fail("C9-visual-anchors", f"{fname}: no se encontró ## Resultado")
            return
        # ≥ 1 bloque de código o `:::example`.
        has_code = "```" in sec or ":::example" in sec
        if not has_code:
            result.fail(
                "C9-visual-anchors",
                f"{fname}: ## Resultado no tiene bloque de código (anclaje visual R3)",
            )
            return
    result.ok("C9-visual-anchors")


def check_c10_no_implicit_state(result: EvalResult) -> None:
    """Sin estado implícito: ningún 'asumiendo/suponiendo/depende de' sin Setup o Entorno."""
    pattern = re.compile(
        r"\b(asumiendo|suponiendo|depende de|se asume)\b",
        re.IGNORECASE,
    )
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        text = path.read_text(encoding="utf-8")
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        # Cada match debe estar seguido (en las siguientes 200 chars) de un
        # bloque ## Setup o cabecera > **Entorno:**.
        for m in matches:
            start = m.start()
            window = text[start:start + 500]
            has_justification = (
                re.search(r"##\s+Setup", window) is not None
                or re.search(r"\*\*Entorno:\*\*", window) is not None
            )
            if not has_justification:
                result.fail(
                    "C10-no-implicit-state",
                    f"{fname}: '{m.group(0)}' sin ## Setup o **Entorno:** cercano",
                )
                return
    result.ok("C10-no-implicit-state")


def check_d1_line_limit(result: EvalResult) -> None:
    if not DOC_PATH.exists():
        result.fail("D1-line-limit", f"no existe {DOC_PATH}")
        return
    n = sum(1 for _ in DOC_PATH.open(encoding="utf-8"))
    if n > DOC_LINE_LIMIT:
        result.fail("D1-line-limit", f"{n} líneas > {DOC_LINE_LIMIT}")
        return
    result.ok("D1-line-limit")


def check_d2_sections(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [h for h in EXPECTED_SECTIONS if h not in text]
    if missing:
        result.fail("D2-sections", f"faltan {len(missing)} secciones")
        return
    result.ok("D2-sections")


def check_d3_scaling_table(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec4 = _section_text(text, "§4")
    if not sec4:
        result.fail("D3-scaling", "no se encontró §4")
        return
    levels = ("mínimo", "realista", "límite")
    if not all(l in sec4 for l in levels):
        result.fail("D3-scaling", f"§4 no menciona los 3 niveles {levels}")
        return
    # Umbrales numéricos: líneas de código (regex `\d+ l[ií]neas` o `< N`).
    if not re.search(r"\d+\s*[-–]\s*\d+|\<\s*\d+|\>\s*\d+", sec4):
        result.fail("D3-scaling", "§4 no tiene umbrales numéricos en la tabla")
        return
    result.ok("D3-scaling")


def check_d4_signals(result: EvalResult) -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    sec7 = _section_text(text, "§7")
    if not sec7:
        result.fail("D4-signals", "no se encontró §7")
        return
    sigs = re.findall(r"\*\*D(\d+)\*\*", sec7)
    if len(set(sigs)) < 8:
        result.fail("D4-signals", f"§7 lista {len(set(sigs))} señales D* (esperaba ≥ 8)")
        return
    has_algo = bool(re.search(r"regex|conteo|presencia|ratio", sec7, re.IGNORECASE))
    if not has_algo:
        result.fail("D4-signals", "§7 no menciona métodos algorítmicos")
        return
    result.ok("D4-signals")


def check_d5_density(result: EvalResult) -> None:
    if not DENSITY_CHECK.exists():
        result.fail("D5-density", f"no existe {DENSITY_CHECK}; F76 no cerrada")
        return
    failed_notes = []
    for fname in POSITIVE_NOTES:
        path = NOTES_DIR / fname
        try:
            proc = subprocess.run(
                ["python3", str(DENSITY_CHECK), "--note", str(path), "--strict"],
                capture_output=True, text=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            result.fail("D5-density", f"density_check falló para {fname}: {e}")
            return
        if proc.returncode != 0:
            failed_notes.append(f"{fname} (exit {proc.returncode})")
    if failed_notes:
        result.fail("D5-density", f"density_check --strict falla en: {', '.join(failed_notes)}")
        return
    result.ok("D5-density")


def check_d6_wirings_alias(result: EvalResult) -> None:
    check_c8_wirings_closed(result)
    if result.passed and result.passed[-1] == "C8-wirings-closed":
        result.passed[-1] = "D6-wirings-alias"
    elif result.failed and result.failed[-1][0] == "C8-wirings-closed":
        name, detail = result.failed[-1]
        result.failed[-1] = ("D6-wirings-alias", detail)


CHECKS = (
    check_c1_doc_structure,
    check_c2_templates,
    check_c3_antiexamples,
    check_c4_sections_order,
    check_c5_entorno,
    check_c6_cleanup_positive,
    check_c7_cleanup_negative,
    check_c8_wirings_closed,
    check_c9_visual_anchors,
    check_c10_no_implicit_state,
    check_d1_line_limit,
    check_d2_sections,
    check_d3_scaling_table,
    check_d4_signals,
    check_d5_density,
    check_d6_wirings_alias,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args = parser.parse_args()

    result = EvalResult()
    for fn in CHECKS:
        fn(result)

    for name in result.passed:
        print(f"[PASS] {name}")
    for name, detail in result.failed:
        print(f"[FAIL] {name}: {detail}")
    print(f"\n{result.status}")
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
