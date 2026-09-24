#!/usr/bin/env python3
"""web_docs.py — F29 web documentation multi-page.

Consume un mirror local de documentación HTML multipágina y produce
`sections.json` con el orden del índice preservado, texto limpio (sin boilerplate:
nav/menus/banners/footers), URL canónica por sección y versión del producto
detectada. BFS desde `--index`; limpia boilerplate por selectores CSS y ARIA
roles; respeta `robots.txt` opcional.

Uso:
    python3 scripts/ingest/web_docs.py \
        --source <dir> \
        --base-url <url> \
        --out-dir <dir> \
        [--index <path>] [--respect-robots-txt] [--max-depth N] [--max-pages N] \
        [--allow-domain <domain>] [--json-only]

Salidas (en <out-dir>/ingest/web_docs/):
    sections.json — array de secciones en orden del índice
    metadata.json — global con total_pages, product_version, warnings

Códigos de salida:
    0 — OK
    1 — Error fatal (input missing, robots.txt prohíbe TODO)
    2 — OK con advertencias (páginas omitidas, versión no detectada)

Dependencias:
    - Python 3.9+ stdlib (html.parser)

Documentación normativa: references/01-ingest/web-docs.md.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import re
import sys
import tempfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SCHEMA_VERSION = "1.0.0"

# ============================================================
# Constants (per references/01-ingest/web-docs.md)
# ============================================================

MAX_PAGES_DEFAULT = 500
MAX_DEPTH_DEFAULT = 5
MIN_TEXT_LENGTH = 50

BOILERPLATE_SELECTORS = (
    "nav",
    "header.navbar", "header.topbar",
    "div.navbar", "div.topbar",
    "footer",
    "aside",
    "div.sidebar", "div.sidebar-left", "div.sidebar-right",
    "div.banner", "div.cookie-banner", "div.alert-banner",
)

BOILERPLATE_ROLES = ("banner", "navigation", "complementary")

VERSION_PATTERNS = [
    re.compile(r"/v(\d+\.\d+\.\d+)/"),
    re.compile(r"/(\d+\.\d+)/"),
]


# ============================================================
# Helpers
# ============================================================

def sha256_dir(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(path)).encode("utf-8")
            h.update(rel + b"\0")
            with open(p, "rb") as f:
                for block in iter(lambda: f.read(65536), b""):
                    h.update(block)
    return h.hexdigest()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


# ============================================================
# HTML parsing
# ============================================================

class HTMLCleaner(html.parser.HTMLParser):
    """Strips boilerplate tags and extracts metadata."""

    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img",
        "input", "link", "meta", "param", "source", "track", "wbr",
    }

    SKIP_TAGS = BOILERPLATE_SELECTORS + ("script", "style", "noscript", "header", "footer")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._title: List[str] = []
        self._title_depth = 0
        self._in_main = False
        self._main_depth = 0
        self._main_text: List[str] = []
        self._headings: List[Dict[str, Any]] = []
        self._current_heading: Optional[Dict[str, Any]] = None
        self._current_heading_depth = 0
        self._current_anchor_id: Optional[str] = None
        self._canonical_url: Optional[str] = None
        self._product: Optional[str] = None
        self._version: Optional[str] = None
        self._title_set = False
        self._internal_links: List[Dict[str, str]] = []
        self._current_link_href: Optional[str] = None
        self._current_link_text: List[str] = []
        self._current_link_depth = 0

    @property
    def title(self) -> str:
        return "".join(self._title).strip()

    @property
    def main_text(self) -> str:
        return " ".join(t.strip() for t in self._main_text if t.strip())

    @property
    def headings(self) -> List[Dict[str, Any]]:
        return self._headings

    @property
    def canonical_url(self) -> Optional[str]:
        return self._canonical_url

    @property
    def product(self) -> Optional[str]:
        return self._product

    @property
    def version(self) -> Optional[str]:
        return self._version

    @property
    def internal_links(self) -> List[Dict[str, str]]:
        return self._internal_links

    def _should_skip(self, tag: str, attrs: Dict[str, Optional[str]]) -> bool:
        if tag in self.SKIP_TAGS:
            return True
        if attrs.get("role") in BOILERPLATE_ROLES:
            return True
        for cls_key in ("class", "id"):
            cls = attrs.get(cls_key) or ""
            for sel in BOILERPLATE_SELECTORS:
                if sel in cls:
                    return True
        return False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = dict(attrs)
        if tag == "link" and attr_dict.get("rel") == "canonical":
            self._canonical_url = attr_dict.get("href")
            return
        if tag == "meta":
            name = (attr_dict.get("name") or "").lower()
            content = attr_dict.get("content") or ""
            if name == "product" or name == "docfx:product":
                self._product = content
            elif name == "version":
                self._version = content
            return
        # Always process <a> for crawl links, even inside boilerplate
        if tag == "a":
            href = attr_dict.get("href") or ""
            self._current_link_href = href
            self._current_link_text = []
            self._current_link_depth = 1
        if self._should_skip(tag, attr_dict):
            self._skip_depth += 1
            return
        if tag == "main" or (attr_dict.get("role") == "main"):
            self._in_main = True
            self._main_depth = 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self._current_heading = {"level": level, "text": "", "anchor": None}
            self._current_heading_depth = 1
            anchor_id = attr_dict.get("id")
            if anchor_id:
                self._current_heading["anchor"] = anchor_id
            self._current_anchor_id = anchor_id
            self._title_set = (level == 1)
        # Note: <a> handling is before _should_skip check above

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link_href:
            text = "".join(self._current_link_text).strip()
            self._internal_links.append({"text": text, "href": self._current_link_href})
            self._current_link_href = None
            self._current_link_text = []
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag == "main" and self._in_main:
            self._in_main = False
            self._main_depth = 0
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._current_heading:
            if self._current_heading["text"]:
                self._headings.append(self._current_heading)
            self._current_heading = None
            self._current_heading_depth = 0
            self._current_anchor_id = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_main:
            self._main_text.append(data)
        if self._current_heading is not None:
            self._current_heading["text"] += data
        if self._current_link_href is not None:
            self._current_link_text.append(data)

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = dict(attrs)
        if tag == "meta":
            name = (attr_dict.get("name") or "").lower()
            content = attr_dict.get("content") or ""
            if name == "product" or name == "docfx:product":
                self._product = content
            elif name == "version":
                self._version = content


def parse_html(html_str: str) -> HTMLCleaner:
    parser = HTMLCleaner()
    try:
        parser.feed(html_str)
        parser.close()
    except Exception:
        pass
    return parser


def extract_text_from_main(html_str: str) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, str]], Optional[str], Optional[str], Optional[str]]:
    """Returns (text, headings, internal_links, canonical_url, product, version)."""
    parser = parse_html(html_str)
    title_text = parser.title
    text = parser.main_text or title_text
    return (
        text,
        parser.headings,
        parser.internal_links,
        parser.canonical_url,
        parser.product,
        parser.version,
    )


# ============================================================
# robots.txt
# ============================================================

def parse_robots_txt(content: str, base_url: str) -> List[str]:
    disallowed = []
    for line in content.splitlines():
        line = line.strip()
        if line.lower().startswith("disallow:"):
            pattern = line.split(":", 1)[1].strip()
            if pattern and pattern != "/":
                disallowed.append(pattern)
    return disallowed


def is_allowed(url_path: str, disallowed_patterns: List[str]) -> bool:
    for pat in disallowed_patterns:
        if url_path.startswith(pat):
            return False
    return True


# ============================================================
# Version detection
# ============================================================

def detect_version(base_url: str, product_meta: Optional[str], version_meta: Optional[str]) -> Optional[str]:
    if version_meta:
        return version_meta
    if product_meta:
        parts = product_meta.replace(",", " ").split()
        for p in parts:
            if re.match(r"^\d+\.\d+", p):
                return p
    for pat in VERSION_PATTERNS:
        m = pat.search(base_url)
        if m:
            return m.group(1)
    return None


# ============================================================
# URL utilities
# ============================================================

def normalize_url(href: str, base_url: str) -> str:
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("/"):
        m = re.match(r"^(https?://[^/]+)", base_url)
        if m:
            return m.group(1) + href
    if href.startswith("#"):
        return base_url + href
    if href.startswith("mailto:"):
        return href
    m = re.match(r"^(https?://[^/]+/[^/]*)", base_url)
    if m:
        base_dir = m.group(1)
        return base_dir + "/" + href
    return base_url.rstrip("/") + "/" + href


# ============================================================
# Crawl
# ============================================================

def crawl_site(
    source_dir: Path,
    base_url: str,
    index_path: str = "index.html",
    max_depth: int = MAX_DEPTH_DEFAULT,
    max_pages: int = MAX_PAGES_DEFAULT,
    respect_robots: bool = False,
    allow_domain: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    warnings: List[str] = []
    disallowed: List[str] = []
    if respect_robots:
        robots_path = source_dir / "robots.txt"
        if robots_path.exists():
            try:
                disallowed = parse_robots_txt(robots_path.read_text(encoding="utf-8"), base_url)
            except Exception as e:
                warnings.append(f"failed to parse robots.txt: {e}")

    index_file = source_dir / index_path
    if not index_file.exists():
        raise RuntimeError(f"index file not found: {index_file}")

    index_html = index_file.read_text(encoding="utf-8", errors="replace")
    index_text, index_headings, index_links, index_canonical, index_product, index_version_meta = extract_text_from_main(index_html)
    index_version = detect_version(base_url, index_product, index_version_meta)

    product_name = index_product
    domain_m = re.match(r"^(https?://[^/]+)(/.*)?$", base_url)
    domain_name = domain_m.group(1) if domain_m else ""
    base_path = domain_m.group(2) or "" if domain_m else ""
    if allow_domain is None:
        # Allow domain = scheme + host + base path (e.g., https://example.com/docs/)
        allow_domain = domain_name + base_path.rstrip("/") if base_path else domain_name

    visited: Set[str] = set()
    sections: List[Dict[str, Any]] = []
    queue = deque([(index_path, 0)])
    visited.add(index_path)

    while queue:
        if len(sections) >= max_pages:
            warnings.append(f"max_pages={max_pages} reached; truncating")
            break
        url_path, depth = queue.popleft()
        if depth > max_depth:
            continue
        local_path = source_dir / url_path
        if not local_path.exists():
            warnings.append(f"missing local file: {url_path}")
            continue
        if not is_allowed(url_path, disallowed):
            warnings.append(f"disallowed by robots.txt: {url_path}")
            continue
        html_str = local_path.read_text(encoding="utf-8", errors="replace")
        text, headings, links, canonical, prod_meta, ver_meta = extract_text_from_main(html_str)
        if len(text) < MIN_TEXT_LENGTH and not headings:
            warnings.append(f"page too short: {url_path}")

        canonical_url = canonical or normalize_url(url_path, base_url)
        if "://" not in canonical_url:
            canonical_url = base_url.rstrip("/") + "/" + url_path.lstrip("/")

        version = detect_version(base_url, prod_meta, ver_meta) or index_version
        if prod_meta:
            product_name = prod_meta

        headings_list = [
            {
                "level": h["level"],
                "text": h["text"].strip(),
                "anchor": h["anchor"] or "",
            }
            for h in headings
        ]

        first_heading_text = headings_list[0]["text"] if headings_list else ""
        section = {
            "url_path": url_path,
            "canonical_url": canonical_url,
            "level": headings_list[0]["level"] if headings_list else 1,
            "title": first_heading_text or url_path,
            "text": text,
            "headings": headings_list,
            "links_internal": links,
            "page_metadata": {
                "product": product_name,
                "version": version,
                "domain": domain_name,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        sections.append(section)

        for link in links:
            href = link.get("href", "")
            if not href or href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            normalized = normalize_url(href, base_url)
            if allow_domain and not normalized.startswith(allow_domain):
                continue
            local_target = source_dir / href.lstrip("/")
            if not local_target.exists():
                continue
            if is_allowed(href, disallowed):
                if href not in visited:
                    visited.add(href)
                    queue.append((href, depth + 1))

    if not sections:
        raise RuntimeError("no sections extracted")

    metadata = {
        "source_url": base_url,
        "index_url": normalize_url(index_path, base_url),
        "total_pages": len(sections),
        "product_version": detect_version(base_url, product_name, index_version),
        "domain": domain_name,
        "allowed_prefixes": [base_url.replace(domain_name, "")] if domain_name else [],
        "disallowed_patterns": disallowed,
        "boilerplate_selectors_removed": list(BOILERPLATE_SELECTORS),
        "warnings": warnings,
    }

    return sections, metadata


# ============================================================
# Entry point
# ============================================================

def run(
    source_dir: Path,
    base_url: str,
    out_dir: Path,
    index: str = "index.html",
    max_depth: int = MAX_DEPTH_DEFAULT,
    max_pages: int = MAX_PAGES_DEFAULT,
    respect_robots: bool = False,
    allow_domain: Optional[str] = None,
    json_only: bool = False,
) -> int:
    source_dir = Path(source_dir).resolve()
    if not source_dir.exists():
        print(f"ERROR: source dir not found: {source_dir}", file=sys.stderr)
        return 1

    warnings: List[str] = []
    try:
        sections, metadata = crawl_site(
            source_dir=source_dir,
            base_url=base_url,
            index_path=index,
            max_depth=max_depth,
            max_pages=max_pages,
            respect_robots=respect_robots,
            allow_domain=allow_domain,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out_web_dir = out_dir / "ingest" / "web_docs"
    out_web_dir.mkdir(parents=True, exist_ok=True)

    sections_payload = {
        "schema_version": SCHEMA_VERSION,
        "source_url": base_url,
        "total_pages": len(sections),
        "sections": sections,
    }
    metadata["schema_version"] = SCHEMA_VERSION
    metadata["source"] = {
        "dir": str(source_dir),
        "base_url": base_url,
        "index": index,
        "hash": sha256_dir(source_dir),
    }

    atomic_write_text(out_web_dir / "sections.json",
                       json.dumps(sections_payload, indent=2, ensure_ascii=False))
    atomic_write_text(out_web_dir / "metadata.json",
                       json.dumps(metadata, indent=2, ensure_ascii=False))

    if not json_only:
        md_lines = [f"# Web Docs — `{source_dir.name}`", ""]
        md_lines.append(f"- **Source URL:** {base_url}")
        md_lines.append(f"- **Total pages:** {len(sections)}")
        md_lines.append(f"- **Product version:** {metadata['product_version']}")
        md_lines.append(f"- **Domain:** {metadata['domain']}")
        if warnings:
            md_lines.append("")
            md_lines.append("## Advertencias")
            for w in warnings:
                md_lines.append(f"- {w}")
        atomic_write_text(out_web_dir / "web_docs.md", "\n".join(md_lines) + "\n")

    return 2 if warnings else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="web_docs.py",
        description="F29 — Web documentation multi-page to sections.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Constantes (references/01-ingest/web-docs.md):
  MAX_PAGES_DEFAULT      = 500   máximo de páginas a crawlear
  MAX_DEPTH_DEFAULT      = 5     profundidad máxima del BFS
  MIN_TEXT_LENGTH        = 50    mínimo de chars para considerar "contenido"
  BOILERPLATE_SELECTORS  = nav, header.navbar, footer, aside, div.sidebar, ...
  BOILERPLATE_ROLES      = banner, navigation, complementary
  VERSION_PATTERNS       = /v\\d+\\.\\d+\\.\\d+/, /\\d+\\.\\d+/

Códigos de salida:
  0 OK
  1 error fatal
  2 OK con advertencias
""",
    )
    parser.add_argument("--source", required=True, help="Directorio con archivos HTML (descargado con wget)")
    parser.add_argument("--base-url", required=True, help="URL base canónica del sitio")
    parser.add_argument("--out-dir", required=True, help="Directorio de salida (ingest/web_docs/)")
    parser.add_argument("--index", default="index.html", help="Archivo índice (default: index.html)")
    parser.add_argument("--max-depth", type=int, default=MAX_DEPTH_DEFAULT, help=f"Profundidad máxima (default {MAX_DEPTH_DEFAULT})")
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES_DEFAULT, help=f"Máximo de páginas (default {MAX_PAGES_DEFAULT})")
    parser.add_argument("--respect-robots-txt", action="store_true", help="Respetar robots.txt")
    parser.add_argument("--allow-domain", default=None, help="Dominio permitido (default: extraído de --base-url)")
    parser.add_argument("--json-only", action="store_true", help="Solo escribir JSON (no web_docs.md)")
    args = parser.parse_args(argv)

    code = run(
        Path(args.source),
        args.base_url,
        Path(args.out_dir),
        index=args.index,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        respect_robots=args.respect_robots_txt,
        allow_domain=args.allow_domain,
        json_only=args.json_only,
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
