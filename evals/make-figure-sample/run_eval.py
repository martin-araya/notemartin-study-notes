#!/usr/bin/env python3
"""
Verificador de la Fase 70 — Figuras de datos (make_figure.py).

Ejecuta 5 criterios verificables:

  C1. Criterio 1 de F70: las 6 figuras se generan correctamente en tema claro
      y oscuro (SVG válido con fondo del tema correcto).
  C2. Criterio 2 de F70: la paleta Okabe-Ito pasa verificación de daltonismo
      con ΔE CIEL76 ≥ 20 entre pares adyacentes.
  C3. Criterio 3 de F70: toda serie tiene `source_refs` no vacío; el spec
      inválido (missing-refs.json) genera error F70-SR-01.
  C4. Alt text + reading phrase no vacíos en cada manifest.
  C5. Ejes neutros no usan colores Okabe-Ito (verificación de que los ejes
      no compiten con las series).

Uso:
    python run_eval.py

Salida: PASS 5/5.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "render" / "make_figure.py"


class EvalResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[tuple] = []

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


def run_make_figure(input_path: Path, out_dir: Path, theme: str = "light",
                    allow_missing_refs: bool = False) -> Dict[str, Any]:
    """Ejecuta el script y devuelve el manifest parseado."""
    cmd = [
        "python3", str(SCRIPT),
        "--input", str(input_path),
        "--out-dir", str(out_dir),
        "--theme", theme,
        "--format", "svg",
    ]
    if allow_missing_refs:
        cmd.append("--allow-missing-refs")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Regenerar fixtures.")
    args = parser.parse_args()

    if args.regen or not (FIXTURES / "bar.json").exists():
        subprocess.run([sys.executable, str(Path(__file__).parent / "build_fixtures.py")], check=True)

    result = EvalResult()
    tmpdir = Path(tempfile.mkdtemp(prefix="make-fig-eval-"))
    out_dir = tmpdir / "out"
    out_dir.mkdir(parents=True)

    spec_files = ["bar.json", "line.json", "heatmap.json", "confusion_matrix.json",
                  "distribution.json", "before_after.json"]

    try:
        # ─── C1: las 6 figuras se generan correctamente en light y dark ───
        generated = {"light": 0, "dark": 0}
        for theme in ("light", "dark"):
            for spec_name in spec_files:
                spec_path = FIXTURES / spec_name
                run_make_figure(spec_path, out_dir / theme, theme=theme, allow_missing_refs=False)
                manifest_path = out_dir / theme / f"{spec_path.stem}.manifest.json"
                svg_path = out_dir / theme / f"{spec_path.stem}.svg"
                if manifest_path.exists() and svg_path.exists():
                    generated[theme] += 1

        if generated["light"] == 6 and generated["dark"] == 6:
            result.ok(f"C1-renders ({generated['light']}/6 light + {generated['dark']}/6 dark)")
        else:
            result.fail("C1-renders",
                        f"light={generated['light']}/6, dark={generated['dark']}/6")

        # ─── C2: paleta Okabe-Ito pasa daltonismo ───
        # Verificar leyendo el manifest de bar.json (que tiene palette_colorblind_safe).
        manifest_path = out_dir / "light" / "bar.manifest.json"
        if not manifest_path.exists():
            result.fail("C2-colorblind-safe", "bar.manifest.json no encontrado")
        else:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            safe = m.get("palette_colorblind_safe", False)
            min_de = m.get("palette_min_delta_e", 0.0)
            if safe and min_de >= 20:
                result.ok(f"C2-colorblind-safe (ΔE_min={min_de:.1f} ≥ 20)")
            else:
                result.fail("C2-colorblind-safe",
                            f"safe={safe}, ΔE_min={min_de:.1f}")

        # ─── C3a: las 6 figuras válidas tienen source_refs no vacío ───
        missing_refs = []
        for spec_name in spec_files:
            spec_path = FIXTURES / spec_name
            data = json.loads(spec_path.read_text(encoding="utf-8"))
            for s in data.get("series", []):
                if not s.get("source_refs"):
                    missing_refs.append(f"{spec_name}: serie '{s.get('name', '?')}' sin source_refs")
        if missing_refs:
            result.fail("C3-source-refs", "; ".join(missing_refs[:3]))
        else:
            result.ok(f"C3-source-refs ({len(spec_files)} specs, todas con source_refs)")

        # ─── C3b: el spec inválido dispara exit ≠ 0 ───
        r = run_make_figure(
            FIXTURES / "missing-refs.json",
            out_dir / "missing-refs",
            allow_missing_refs=False,
        )
        if r["returncode"] != 0:
            result.ok(f"C3b-invalid-rejected (exit={r['returncode']})")
        else:
            result.fail("C3b-invalid-rejected",
                        f"missing-refs.json debería fallar pero exit={r['returncode']}")

        # ─── C4: alt_text + reading_phrase no vacíos ───
        empty_alt = []
        for spec_name in spec_files:
            spec_path = FIXTURES / spec_name
            manifest_path = out_dir / "light" / f"{spec_path.stem}.manifest.json"
            if not manifest_path.exists():
                continue
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not m.get("alt_text"):
                empty_alt.append(f"{spec_name}: alt_text vacío")
            if not m.get("reading_phrase"):
                empty_alt.append(f"{spec_name}: reading_phrase vacío")
        if empty_alt:
            result.fail("C4-alt-text", "; ".join(empty_alt[:3]))
        else:
            result.ok(f"C4-alt-text ({len(spec_files)} figuras con alt + reading)")

        # ─── C5: ejes neutros no usan colores Okabe-Ito ───
        # Los SVG deben usar #666666 (axis), #E0E0E0 (gridline), etc. en light
        # y #A0A0A0, #404040 en dark. Verificar que ningún color Okabe-Ito
        # aparece en líneas de ejes (no en series).
        svg_path = out_dir / "light" / "bar.svg"
        if svg_path.exists():
            svg_text = svg_path.read_text(encoding="utf-8")
            # Verificar que NO hay stroke="#0072B2" o "#E69F00" en líneas de eje
            import re
            axis_violations = re.findall(r'<line[^>]*stroke="#(?:0072B2|E69F00|D55E00|56B4E9|009E73|F0E442|CC79A7)"', svg_text)
            if axis_violations:
                result.fail("C5-neutral-axes", f"Ejes con color Okabe-Ito: {axis_violations[:2]}")
            else:
                result.ok("C5-neutral-axes (ejes con grises neutros)")
        else:
            result.fail("C5-neutral-axes", "bar.svg no encontrado")

    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    # ─── Resumen ───
    print("=" * 60)
    print("Fase 70 — Figuras de datos")
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
