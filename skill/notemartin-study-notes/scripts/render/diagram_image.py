#!/usr/bin/env python3
"""diagram_image.py — F68 · Pre-renderizado de diagramas Mermaid a imagen.

Convierte bloques `:::diagram` de archivos NoteMark (`.nm`/`.md`) en SVG
(y opcionalmente PNG) en tema claro y oscuro, usando el CLI de Mermaid
(`mmdc` — `@mermaid-js/mermaid-cli`). Cuando `mmdc` no está disponible,
degrada a `native_mermaid` (criterio D-01): el bloque ```mermaid ``` queda
tal cual y el código fuente plegable se incluye en el manifest.

Cubre los 3 criterios de la Fase 68:
- C1: todo diagrama del corpus tiene versión imagen disponible (SVG/PNG
  cuando `mmdc` está; código fuente en manifest siempre).
- C2: el mismo código produce el mismo archivo (hash determinista;
  caché por hash; reproducibilidad bit-a-bit cuando `mmdc` está).
- C3: el código fuente plegable (`source_code`) acompaña siempre a la imagen
  en el `manifest.json`.

Uso:
    python3 scripts/render/diagram_image.py --source <path>
                                             [--out-dir <dir>]
                                             [--cache-dir <dir>]
                                             [--theme {light,dark,both}]
                                             [--format {svg,png,both}]
                                             [--mmdc <path>]
                                             [--no-fallback]
                                             [--force]
                                             [--json]
                                             [--max-width N] [--max-height N]
                                             [--fail-on {error,warning,info}]

Dependencias: Python 3.9+ stdlib puro (mmdc opcional).
Códigos de salida:
    0 — OK (todos los bloques procesados; puede haber warnings).
    1 — Algún bloque falló pero el resto OK (degradación parcial).
    2 — Error fatal (mmdc no disponible con --no-fallback, paths faltantes).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Comparte atomic_write_json con F38+.
_IO_PATH = Path(__file__).resolve().parent.parent / "util" / "_io.py"
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json


EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_FATAL = 2

SCHEMA_VERSION = "1.0.0"

DEFAULT_CACHE_DIR = Path(".cache/diagram-image")
DEFAULT_OUT_DIR = Path("render/diagram-image")
DEFAULT_THEME = "light"
DEFAULT_FORMAT = "svg"
DEFAULT_MAX_WIDTH = 1200
DEFAULT_MAX_HEIGHT = 800
DEFAULT_TIMEOUT = 30  # seconds per block


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class Block:
    block_index: int
    directive_src: str
    directive_alt: str
    diagram_type: str  # WP-N o "" si desconocido
    raw_content: str


@dataclass
class RenderResult:
    block_index: int
    directive_src: str
    diagram_type: str
    diagram_hash: str
    image_svg_path: Optional[str]  # relative to out-dir
    image_png_path: Optional[str]
    source_code_folded: bool
    source_code: str
    cache_hit: bool
    fallback_used: Optional[str]  # "native_mermaid" o None
    mmdc_version: Optional[str]
    errors: List[str] = field(default_factory=list)


@dataclass
class Degradation:
    block_index: int
    rule_id: str
    severity: str
    message: str
    fallback_used: Optional[str] = None


@dataclass
class Manifest:
    schema_version: str = SCHEMA_VERSION
    generated_at: str = ""
    source: str = ""
    ir_sha256: str = ""
    mmdc_available: bool = False
    mmdc_version: Optional[str] = None
    theme: str = DEFAULT_THEME
    format: str = DEFAULT_FORMAT
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)


@dataclass
class Report:
    schema_version: str = SCHEMA_VERSION
    generated_at: str = ""
    files: List[str] = field(default_factory=list)
    blocks_total: int = 0
    blocks_rendered: int = 0
    blocks_cache_hit: int = 0
    blocks_fallback: int = 0
    blocks_failed: int = 0
    degradations: List[Degradation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Extracción de bloques (compatible con F67)
# ---------------------------------------------------------------------------


RE_DIAGRAM_BLOCK = re.compile(
    r':::diagram(?P<attrs>(?:\s+[a-zA-Z\-]+="[^"]*")*)\s*\n'
    r'```mermaid\n(?P<content>.*?)```\s*\n'
    r':::',
    re.DOTALL,
)


def extract_diagrams(text: str) -> List[Tuple[int, Dict[str, str], str]]:
    """Devuelve lista de (block_index, attrs, content)."""
    out: List[Tuple[int, Dict[str, str], str]] = []
    for i, m in enumerate(RE_DIAGRAM_BLOCK.finditer(text)):
        attrs = parse_attrs(m.group("attrs") or "")
        content = m.group("content")
        out.append((i, attrs, content))
    return out


def parse_attrs(attrs: str) -> Dict[str, str]:
    """Extrae src=\"...\" alt=\"...\" del bloque :::diagram."""
    result: Dict[str, str] = {}
    for m in re.finditer(r'([a-zA-Z\-]+)="([^"]*)"', attrs):
        result[m.group(1)] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Detección de tipo y hash
# ---------------------------------------------------------------------------


PORTABLE_TYPES: Dict[str, str] = {
    "flowchart": "WP-1",
    "graph": "WP-1",
    "sequencediagram": "WP-2",
    "stateDiagram-v2": "WP-3",
    "statediagram-v2": "WP-3",
    "statediagram": "WP-3",
    "erdiagram": "WP-4",
    "classdiagram": "WP-5",
    "gantt": "WP-6",
    "gitgraph": "WP-7",
    "pie": "WP-8",
}


def detect_type(first_line: str) -> str:
    """Detecta el tipo Mermaid (WP-N) o '' si no se reconoce."""
    s = first_line.strip().split()
    if not s:
        return ""
    return PORTABLE_TYPES.get(s[0].lower(), "")


def compute_diagram_hash(
    diagram_code: str,
    theme: str,
    format_: str,
    ir_sha256: str = "",
) -> str:
    """Hash SHA256 determinista del (código, tema, formato, ir_sha256)."""
    h = hashlib.sha256()
    h.update(diagram_code.encode("utf-8"))
    h.update(b"\x00")
    h.update(theme.encode("utf-8"))
    h.update(b"\x00")
    h.update(format_.encode("utf-8"))
    h.update(b"\x00")
    h.update(ir_sha256.encode("ascii"))
    return h.hexdigest()


def compute_ir_sha256(text: str) -> str:
    """Hash SHA256 del archivo fuente (para invalidación de caché)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Caché
# ---------------------------------------------------------------------------


@dataclass
class CacheEntry:
    svg: Optional[str] = None
    png: Optional[str] = None
    mtime: float = 0.0


class Cache:
    """Caché por hash en disco. Index: <hash>.json con paths relativos."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, diagram_hash: str, theme: str) -> Optional[Dict[str, str]]:
        """Devuelve {svg, png} paths si el hash está en caché; None si no."""
        idx_path = self.cache_dir / f"{diagram_hash}-{theme}.json"
        if not idx_path.exists():
            return None
        try:
            return json.loads(idx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def put(
        self,
        diagram_hash: str,
        theme: str,
        svg_path: Optional[Path],
        png_path: Optional[Path],
    ) -> None:
        """Registra el render en el index de caché."""
        idx_path = self.cache_dir / f"{diagram_hash}-{theme}.json"
        entry = {
            "svg": str(svg_path) if svg_path else None,
            "png": str(png_path) if png_path else None,
            "mtime": _dt.datetime.now(_dt.timezone.utc).timestamp(),
        }
        idx_path.write_text(json.dumps(entry), encoding="utf-8")

    def clear(self) -> int:
        """Vacía la caché. Devuelve el número de archivos eliminados."""
        n = 0
        for p in self.cache_dir.glob(f"*-{DEFAULT_THEME}.json"):
            p.unlink()
            n += 1
        for p in self.cache_dir.glob(f"*-dark.json"):
            p.unlink()
            n += 1
        # También eliminar imágenes huérfanas
        for p in self.cache_dir.glob("*.svg"):
            p.unlink()
            n += 1
        for p in self.cache_dir.glob("*.png"):
            p.unlink()
            n += 1
        return n


# ---------------------------------------------------------------------------
# Detección de mmdc
# ---------------------------------------------------------------------------


def find_mmdc(mmdc_path: Optional[str] = None) -> Optional[Path]:
    """Devuelve la ruta al binario `mmdc` o None si no está disponible."""
    if mmdc_path:
        p = Path(mmdc_path)
        if p.exists() and os.access(p, os.X_OK):
            return p
        return None
    found = shutil.which("mmdc")
    if found:
        return Path(found)
    return None


def get_mmdc_version(mmdc_path: Path) -> Optional[str]:
    """Devuelve la versión de mmdc o None si no se puede obtener."""
    try:
        result = subprocess.run(
            [str(mmdc_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or result.stderr.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


PUPPETEER_CONFIG = {
    "args": ["--no-sandbox", "--disable-setuid-sandbox"],
}


def make_mmdc_config(theme: str) -> str:
    """Genera un archivo de configuración JSON para mmdc."""
    config = {
        "theme": "default" if theme == "light" else "dark",
        "securityLevel": "loose",
        "flowchart": {"htmlLabels": True, "useMaxWidth": True},
        "themeVariables": {
            "fontFamily": "system-ui, -apple-system, sans-serif",
            "fontSize": "14px",
        },
    }
    return json.dumps(config)


def render_with_mmdc(
    diagram_code: str,
    theme: str,
    format_: str,
    out_svg: Optional[Path],
    out_png: Optional[Path],
    mmdc_path: Path,
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[Optional[Path], Optional[Path], List[str]]:
    """Invoca mmdc y devuelve (svg_path, png_path, errors)."""
    errors: List[str] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="mmdc-"))
    try:
        # Escribir el código del diagrama a un archivo temporal
        mmd_path = tmpdir / "diagram.mmd"
        mmd_path.write_text(diagram_code, encoding="utf-8")

        # Escribir config temporal
        config_path = tmpdir / "config.json"
        config_path.write_text(make_mmdc_config(theme), encoding="utf-8")

        # Generar SVG
        if out_svg:
            try:
                result = subprocess.run(
                    [
                        str(mmdc_path),
                        "--input", str(mmd_path),
                        "--output", str(out_svg),
                        "--configFile", str(config_path),
                        "--puppeteerConfig", json.dumps(PUPPETEER_CONFIG),
                        "--quiet",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if result.returncode != 0:
                    errors.append(f"mmdc svg failed: {result.stderr.strip()[:200]}")
                    out_svg = None
            except subprocess.TimeoutExpired:
                errors.append(f"mmdc svg timeout after {timeout}s")
                out_svg = None
            except FileNotFoundError:
                errors.append("mmdc binary not found")
                return None, None, errors

        # Generar PNG
        if out_png:
            try:
                # mmdc produce PNG con escala; usar --scale para mejor calidad
                result = subprocess.run(
                    [
                        str(mmdc_path),
                        "--input", str(mmd_path),
                        "--output", str(out_png),
                        "--configFile", str(config_path),
                        "--puppeteerConfig", json.dumps(PUPPETEER_CONFIG),
                        "--scale", "2",
                        "--backgroundColor", "transparent",
                        "--quiet",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if result.returncode != 0:
                    errors.append(f"mmdc png failed: {result.stderr.strip()[:200]}")
                    out_png = None
            except subprocess.TimeoutExpired:
                errors.append(f"mmdc png timeout after {timeout}s")
                out_png = None

        return out_svg, out_png, errors
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Procesamiento de bloques
# ---------------------------------------------------------------------------


def render_block(
    block: Block,
    out_dir: Path,
    cache: Cache,
    mmdc_path: Optional[Path],
    mmdc_version: Optional[str],
    theme: str,
    format_: str,
    ir_sha256: str,
    force: bool,
    no_fallback: bool,
    max_width: int,
    max_height: int,
    timeout: int,
) -> RenderResult:
    """Procesa un bloque: detecta tipo, hashea, consulta caché, renderiza o degrada."""
    diagram_hash = compute_diagram_hash(block.raw_content, theme, format_, ir_sha256)

    result = RenderResult(
        block_index=block.block_index,
        directive_src=block.directive_src,
        diagram_type=block.diagram_type,
        diagram_hash=diagram_hash,
        image_svg_path=None,
        image_png_path=None,
        source_code_folded=True,
        source_code=block.raw_content,
        cache_hit=False,
        fallback_used=None,
        mmdc_version=mmdc_version,
    )

    # Si mmdc no está disponible, degradar
    if mmdc_path is None:
        result.fallback_used = "native_mermaid"
        if no_fallback:
            result.errors.append("mmdc not available and --no-fallback set")
        return result

    # Consultar caché (a menos que --force)
    if not force:
        cached = cache.get(diagram_hash, theme)
        if cached:
            result.cache_hit = True
            result.image_svg_path = cached.get("svg")
            result.image_png_path = cached.get("png")
            return result

    # Renderizar
    diagrams_subdir = out_dir / "diagrams"
    diagrams_subdir.mkdir(parents=True, exist_ok=True)
    note_id = block.directive_src or f"block-{block.block_index}"

    svg_name = f"{note_id}-{block.block_index}-{theme}.svg" if format_ in ("svg", "both") else None
    png_name = f"{note_id}-{block.block_index}-{theme}.png" if format_ in ("png", "both") else None

    svg_target = diagrams_subdir / svg_name if svg_name else None
    png_target = diagrams_subdir / png_name if png_name else None

    out_svg, out_png, errors = render_with_mmdc(
        diagram_code=block.raw_content,
        theme=theme,
        format_=format_,
        out_svg=svg_target,
        out_png=png_target,
        mmdc_path=mmdc_path,
        timeout=timeout,
    )

    if errors:
        result.errors.extend(errors)

    if out_svg:
        result.image_svg_path = str(out_svg.relative_to(out_dir))
    if out_png:
        result.image_png_path = str(out_png.relative_to(out_dir))

    # Registrar en caché solo si se generó al menos una imagen
    if out_svg or out_png:
        cache.put(diagram_hash, theme, out_svg, out_png)
    else:
        result.fallback_used = "native_mermaid"

    return result


# ---------------------------------------------------------------------------
# Reporte + Manifiesto
# ---------------------------------------------------------------------------


def build_manifest(
    source: str,
    ir_sha256: str,
    mmdc_available: bool,
    mmdc_version: Optional[str],
    theme: str,
    format_: str,
    results: List[RenderResult],
) -> Manifest:
    m = Manifest()
    m.generated_at = _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")
    m.source = source
    m.ir_sha256 = ir_sha256
    m.mmdc_available = mmdc_available
    m.mmdc_version = mmdc_version
    m.theme = theme
    m.format = format_

    for r in results:
        m.blocks.append({
            "block_index": r.block_index,
            "directive_src": r.directive_src,
            "diagram_type": r.diagram_type,
            "diagram_hash": r.diagram_hash,
            "image_svg_path": r.image_svg_path,
            "image_png_path": r.image_png_path,
            "source_code_folded": r.source_code_folded,
            "source_code": r.source_code,
            "cache_hit": r.cache_hit,
            "fallback_used": r.fallback_used,
            "mmdc_version": r.mmdc_version,
            "errors": r.errors,
        })

    cache_hits = sum(1 for r in results if r.cache_hit)
    fallbacks = sum(1 for r in results if r.fallback_used)
    rendered = sum(1 for r in results if (r.image_svg_path or r.image_png_path) and not r.fallback_used)
    failed = sum(1 for r in results if r.errors)

    m.summary = {
        "blocks_total": len(results),
        "blocks_rendered": rendered,
        "blocks_cache_hit": cache_hits,
        "blocks_fallback": fallbacks,
        "blocks_failed": failed,
    }
    return m


def build_report(files: List[str], results: List[RenderResult], degradations: List[Degradation]) -> Report:
    rep = Report()
    rep.generated_at = _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")
    rep.files = files
    rep.blocks_total = len(results)
    rep.blocks_rendered = sum(1 for r in results if (r.image_svg_path or r.image_png_path) and not r.fallback_used)
    rep.blocks_cache_hit = sum(1 for r in results if r.cache_hit)
    rep.blocks_fallback = sum(1 for r in results if r.fallback_used)
    rep.blocks_failed = sum(1 for r in results if r.errors)
    rep.degradations = degradations
    return rep


def render_manifest_markdown(manifest: Manifest) -> str:
    out: List[str] = []
    out.append(f"# Diagram Image Manifest (schema {manifest.schema_version})")
    out.append("")
    out.append(f"- **Generated:** {manifest.generated_at}")
    out.append(f"- **Source:** `{manifest.source}`")
    out.append(f"- **IR sha256:** `{manifest.ir_sha256}`")
    out.append(f"- **mmdc available:** {manifest.mmdc_available}")
    if manifest.mmdc_version:
        out.append(f"- **mmdc version:** {manifest.mmdc_version}")
    out.append(f"- **Theme:** {manifest.theme}")
    out.append(f"- **Format:** {manifest.format}")
    out.append("")
    out.append("## Summary")
    out.append("")
    for k, v in manifest.summary.items():
        out.append(f"- **{k}**: {v}")
    out.append("")
    out.append("## Blocks")
    out.append("")
    for b in manifest.blocks:
        out.append(f"### Block {b['block_index']} — `{b['directive_src'] or '(sin-src)'}`")
        out.append(f"- Type: {b['diagram_type'] or 'unknown'}")
        out.append(f"- Hash: `{b['diagram_hash'][:16]}...`")
        if b['image_svg_path']:
            out.append(f"- SVG: `{b['image_svg_path']}`")
        if b['image_png_path']:
            out.append(f"- PNG: `{b['image_png_path']}`")
        if b['cache_hit']:
            out.append(f"- Cache hit: ✓")
        if b['fallback_used']:
            out.append(f"- Fallback: `{b['fallback_used']}`")
        out.append("- Source (folded):")
        out.append("")
        out.append("```mermaid")
        out.append(b['source_code'])
        out.append("```")
        out.append("")
    return "\n".join(out)


def render_report_markdown(report: Report) -> str:
    out: List[str] = []
    out.append(f"# Diagram Image Report (schema {report.schema_version})")
    out.append("")
    out.append(f"- **Generated:** {report.generated_at}")
    out.append(f"- **Files:** {len(report.files)}")
    out.append(f"- **Blocks total:** {report.blocks_total}")
    out.append(f"- **Blocks rendered:** {report.blocks_rendered}")
    out.append(f"- **Cache hits:** {report.blocks_cache_hit}")
    out.append(f"- **Fallbacks:** {report.blocks_fallback}")
    out.append(f"- **Failed:** {report.blocks_failed}")
    out.append("")
    if report.degradations:
        out.append("## Degradations")
        out.append("")
        out.append("| Block | Rule | Severity | Message | Fallback |")
        out.append("|---|---|---|---|---|")
        for d in report.degradations:
            out.append(
                f"| {d.block_index} | {d.rule_id} | {d.severity} | {d.message} | {d.fallback_used or ''} |"
            )
    else:
        out.append("## Degradations")
        out.append("")
        out.append("(none)")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------


def process_file(
    path: Path,
    out_dir: Path,
    cache: Cache,
    mmdc_path: Optional[Path],
    mmdc_version: Optional[str],
    theme: str,
    format_: str,
    force: bool,
    no_fallback: bool,
    max_width: int,
    max_height: int,
    timeout: int,
) -> Tuple[Manifest, Report]:
    text = path.read_text(encoding="utf-8")
    ir_sha256 = compute_ir_sha256(text)
    blocks_raw = extract_diagrams(text)
    blocks: List[Block] = []
    for idx, attrs, content in blocks_raw:
        first_line = next((ln for ln in content.splitlines() if ln.strip()), "")
        blocks.append(Block(
            block_index=idx,
            directive_src=attrs.get("src", ""),
            directive_alt=attrs.get("alt", ""),
            diagram_type=detect_type(first_line),
            raw_content=content,
        ))

    results: List[RenderResult] = []
    degradations: List[Degradation] = []

    for block in blocks:
        r = render_block(
            block=block,
            out_dir=out_dir,
            cache=cache,
            mmdc_path=mmdc_path,
            mmdc_version=mmdc_version,
            theme=theme,
            format_=format_,
            ir_sha256=ir_sha256,
            force=force,
            no_fallback=no_fallback,
            max_width=max_width,
            max_height=max_height,
            timeout=timeout,
        )
        results.append(r)
        if r.fallback_used:
            degradations.append(Degradation(
                block_index=block.block_index,
                rule_id="D-01",
                severity="warning",
                message=f"mmdc no disponible; usando bloque mermaid nativo",
                fallback_used=r.fallback_used,
            ))
        for err in r.errors:
            degradations.append(Degradation(
                block_index=block.block_index,
                rule_id="D-03" if "timeout" in err.lower() else "D-04",
                severity="error",
                message=err,
                fallback_used=r.fallback_used,
            ))

    manifest = build_manifest(
        source=str(path),
        ir_sha256=ir_sha256,
        mmdc_available=mmdc_path is not None,
        mmdc_version=mmdc_version,
        theme=theme,
        format_=format_,
        results=results,
    )
    report = build_report([str(path)], results, degradations)
    return manifest, report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="diagram_image.py",
        description="F68 — Pre-renderizado de diagramas Mermaid a imagen.",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--source", type=Path, help="Archivo .nm o .md a procesar.")
    src.add_argument("--glob", type=str, help="Patrón glob para múltiples archivos.")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directorio de salida (default: render/diagram-image/).")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="Directorio de caché (default: .cache/diagram-image/).")
    p.add_argument("--theme", choices=["light", "dark", "both"], default=DEFAULT_THEME, help="Tema (default: light).")
    p.add_argument("--format", choices=["svg", "png", "both"], dest="format_", default=DEFAULT_FORMAT, help="Formato (default: svg).")
    p.add_argument("--mmdc", type=str, default=None, help="Ruta al binario mmdc (default: PATH).")
    p.add_argument("--no-fallback", action="store_true", help="Exit 2 si mmdc no está disponible.")
    p.add_argument("--force", action="store_true", help="Ignorar caché y re-renderizar.")
    p.add_argument("--cache-clear", action="store_true", help="Vaciar la caché antes de procesar.")
    p.add_argument("--max-width", type=int, default=DEFAULT_MAX_WIDTH, help="Ancho del viewport.")
    p.add_argument("--max-height", type=int, default=DEFAULT_MAX_HEIGHT, help="Alto del viewport.")
    p.add_argument("--fail-on", choices=["error", "warning", "info"], default="error", help="Severidad que causa exit ≠ 0 (default: error).")
    p.add_argument("--json", action="store_true", help="Salida solo JSON (manifest).")
    return p.parse_args(argv)


SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def severity_at_least(sev: str, threshold: str) -> bool:
    return SEVERITY_ORDER[sev] <= SEVERITY_ORDER[threshold]


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if not args.source and not args.glob:
        print("ERROR: se requiere --source o --glob", file=sys.stderr)
        return EXIT_FATAL

    if args.cache_clear:
        cache = Cache(args.cache_dir)
        n = cache.clear()
        print(f"Cache cleared: {n} files removed", file=sys.stderr)

    mmdc_path = find_mmdc(args.mmdc)
    mmdc_version = get_mmdc_version(mmdc_path) if mmdc_path else None
    if mmdc_path is None and args.no_fallback:
        print("ERROR: mmdc no disponible y --no-fallback activo", file=sys.stderr)
        return EXIT_FATAL

    cache = Cache(args.cache_dir)

    # Procesar uno o varios archivos
    files: List[Path] = []
    if args.source:
        if not args.source.exists():
            print(f"ERROR: --source no encontrado: {args.source}", file=sys.stderr)
            return EXIT_FATAL
        files = [args.source]
    else:
        files = sorted(Path(".").glob(args.glob))
        files = [f for f in files if f.is_file() and f.suffix in (".md", ".nm")]
        if not files:
            print(f"ERROR: --glob no encontró archivos: {args.glob}", file=sys.stderr)
            return EXIT_FATAL

    themes_to_process: List[str] = ["light", "dark"] if args.theme == "both" else [args.theme]

    all_results: List[RenderResult] = []
    all_degradations: List[Degradation] = []
    all_manifests: List[Manifest] = []
    processed_files: List[str] = []

    for theme in themes_to_process:
        for f in files:
            manifest, report = process_file(
                path=f,
                out_dir=args.out_dir,
                cache=cache,
                mmdc_path=mmdc_path,
                mmdc_version=mmdc_version,
                theme=theme,
                format_=args.format_,
                force=args.force,
                no_fallback=args.no_fallback,
                max_width=args.max_width,
                max_height=args.max_height,
                timeout=DEFAULT_TIMEOUT,
            )
            all_results.extend(manifest.blocks)  # type: ignore[arg-type]
            all_degradations.extend(report.degradations)
            all_manifests.append(manifest)
            processed_files.append(str(f))

    # Salidas
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Reporte JSON (degradaciones)
    last_report = build_report(processed_files, [], all_degradations)
    _atomic_write_json(args.out_dir / "render-degradation.json", asdict(last_report))
    (args.out_dir / "render-degradation.md").write_text(
        render_report_markdown(last_report), encoding="utf-8"
    )

    # Manifests (uno por archivo × tema)
    for manifest in all_manifests:
        slug = re.sub(r"[^A-Za-z0-9._-]", "_", Path(manifest.source).stem)
        suffix = f"-{manifest.theme}" if len(themes_to_process) > 1 else ""
        manifest_path = args.out_dir / f"manifest-{slug}{suffix}.json"
        _atomic_write_json(manifest_path, asdict(manifest))
        md_path = args.out_dir / f"manifest-{slug}{suffix}.md"
        md_path.write_text(render_manifest_markdown(manifest), encoding="utf-8")

    if args.json:
        # Salida JSON: el último manifest
        print(json.dumps(asdict(all_manifests[-1]) if all_manifests else {}, indent=2))
    else:
        # Salida Markdown por defecto
        if all_manifests:
            print(render_manifest_markdown(all_manifests[-1]))

    # Determinar exit code
    any_fail = any(
        severity_at_least(d.severity, args.fail_on) for d in all_degradations
    )
    if any_fail and args.fail_on == "error":
        return EXIT_PARTIAL
    if any_fail and args.fail_on == "warning":
        return EXIT_PARTIAL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
