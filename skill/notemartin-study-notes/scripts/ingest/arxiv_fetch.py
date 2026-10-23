#!/usr/bin/env python3
"""arxiv_fetch.py — Ingesta y resolución de artículos arXiv (P1).

Resuelve identificadores o URLs de arXiv, consulta metadatos en la API de arXiv,
descarga el PDF (o reutiliza uno local), descarga la fuente LaTeX opcional
y genera `source-meta.yaml` compatible con `build_sdm.py`.

Uso:
    python3 scripts/ingest/arxiv_fetch.py --id 2201.00001 --out-dir .notes-work/ax/ [--with-tex]
    python3 scripts/ingest/arxiv_fetch.py --id https://arxiv.org/abs/2201.00001v3 --out-dir .notes-work/ax/
    python3 scripts/ingest/arxiv_fetch.py --id 2201.00001 --pdf sample.pdf --out-dir .notes-work/ax/

Salidas en --out-dir:
    source.pdf        — archivo PDF del artículo
    source-meta.yaml  — metadatos con id, hash, vendor, product, authors, etc.
    tex/              — código fuente LaTeX extraído (si --with-tex tuvo éxito)
    fetch_summary.json— resumen estructurado de la adquisición

Códigos de salida:
    0 — Éxito
    1 — Error fatal (ID inválido, error de descarga, fallo en metadatos sin fallback)
    2 — Éxito parcial / advertencia (p. ej. PDF descargado pero TeX no disponible)

Dependencias:
    - Python 3.9+ stdlib (urllib, xml.etree, tarfile, gzip, hashlib)
    - PyYAML (opcional; si falta, serializa YAML estándar)
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

USER_AGENT = "notemartin-study-notes/0.2.0 (arXiv paper ingestion; mailto:agent@notemartin.local)"

# Patrones para arXiv ID
# Moderno: YYYY.NNNNN o YYYY.NNNNNvN
# Antiguo: arch-ive/YYMMNNN o arch-ive/YYMMNNNvN
ARXIV_ID_RE = re.compile(
    r"(?:(?:arxiv(?:\.org)?/(?:abs|pdf)/)|(?:arxiv:))?"
    r"(?P<base>(?:(?:\d{4}\.\d{4,5})|(?:[a-zA-Z\-]+/\d{7})))"
    r"(?P<version>v\d+)?"
    r"(?:\.pdf)?$",
    re.IGNORECASE,
)


def parse_arxiv_id(raw: str) -> Dict[str, Any]:
    """Parsea una URL, URI o ID libre de arXiv.

    Ejemplos soportados:
      - '2201.00001' -> base='2201.00001', version=None, canonical='2201.00001'
      - '2201.00001v3' -> base='2201.00001', version='v3', canonical='2201.00001v3'
      - 'hep-th/9901001' -> base='hep-th/9901001', version=None, canonical='hep-th/9901001'
      - 'https://arxiv.org/abs/2201.00001v3' -> canonical='2201.00001v3'
      - 'https://arxiv.org/pdf/2201.00001v3.pdf' -> canonical='2201.00001v3'
      - 'arXiv:2201.00001v3' -> canonical='2201.00001v3'
    """
    clean = raw.strip()
    # Si viene con parámetros de búsqueda, descartarlos
    if "?" in clean:
        clean = clean.split("?", 1)[0]
    # Si termina con .pdf, remover temporalmente para facilitar match
    m = ARXIV_ID_RE.search(clean)
    if not m:
        raise ValueError(f"No se pudo identificar un ID válido de arXiv en: '{raw}'")

    base = m.group("base")
    version = m.group("version")
    canonical = f"{base}{version}" if version else base
    return {
        "raw": raw,
        "base_id": base,
        "version": version,
        "canonical_id": canonical,
        "abs_url": f"https://arxiv.org/abs/{canonical}",
        "pdf_url": f"https://arxiv.org/pdf/{canonical}",
        "eprint_url": f"https://arxiv.org/e-print/{canonical}",
    }


def compute_sha256(path: Path) -> str:
    """Calcula el SHA-256 de un archivo en bloques de 64 KB."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def fetch_api_metadata(
    base_id: str,
    timeout: int = 30,
    user_agent: str = USER_AGENT,
) -> Dict[str, Any]:
    """Consulta la API Atom de arXiv para obtener metadatos bibliográficos."""
    query_url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(base_id)}"
    req = urllib.request.Request(query_url, headers={"User-Agent": user_agent})

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read()

    root = ET.fromstring(content)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    entry = root.find("atom:entry", ns)
    if entry is None:
        raise ValueError(f"La API de arXiv no retornó entradas para el ID: {base_id}")

    # Verificar si es una respuesta de error
    id_elem = entry.find("atom:id", ns)
    title_elem = entry.find("atom:title", ns)
    if title_elem is not None and title_elem.text and "Error" in title_elem.text:
        raise ValueError(f"Error devuelto por la API de arXiv: {title_elem.text.strip()}")

    title = ""
    if title_elem is not None and title_elem.text:
        title = re.sub(r"\s+", " ", title_elem.text).strip()

    summary = ""
    summary_elem = entry.find("atom:summary", ns)
    if summary_elem is not None and summary_elem.text:
        summary = re.sub(r"\s+", " ", summary_elem.text).strip()

    published = ""
    pub_elem = entry.find("atom:published", ns)
    if pub_elem is not None and pub_elem.text:
        # Extraer fecha YYYY-MM-DD
        published = pub_elem.text.split("T")[0]

    updated = ""
    up_elem = entry.find("atom:updated", ns)
    if up_elem is not None and up_elem.text:
        updated = up_elem.text.split("T")[0]

    authors: List[str] = []
    for author in entry.findall("atom:author", ns):
        name_elem = author.find("atom:name", ns)
        if name_elem is not None and name_elem.text:
            authors.append(re.sub(r"\s+", " ", name_elem.text).strip())

    categories: List[str] = []
    for cat in entry.findall("atom:category", ns):
        term = cat.attrib.get("term")
        if term and term not in categories:
            categories.append(term)

    primary_category = ""
    p_cat = entry.find("arxiv:primary_category", ns)
    if p_cat is not None:
        primary_category = p_cat.attrib.get("term", "")

    doi = None
    doi_elem = entry.find("arxiv:doi", ns)
    if doi_elem is not None and doi_elem.text:
        doi = doi_elem.text.strip()

    journal_ref = None
    j_elem = entry.find("arxiv:journal_ref", ns)
    if j_elem is not None and j_elem.text:
        journal_ref = re.sub(r"\s+", " ", j_elem.text).strip()

    comment = None
    c_elem = entry.find("arxiv:comment", ns)
    if c_elem is not None and c_elem.text:
        comment = re.sub(r"\s+", " ", c_elem.text).strip()

    license_url = None
    for link in entry.findall("atom:link", ns):
        if link.attrib.get("rel") == "related" and "licenses" in link.attrib.get("href", ""):
            license_url = link.attrib.get("href")

    return {
        "title": title,
        "abstract": summary,
        "authors": authors,
        "published": published,
        "updated": updated,
        "categories": categories,
        "primary_category": primary_category,
        "doi": doi,
        "journal_ref": journal_ref,
        "comment": comment,
        "license": license_url,
    }


def download_file(
    url: str,
    target_path: Path,
    timeout: int = 45,
    user_agent: str = USER_AGENT,
) -> bool:
    """Descarga un archivo con urllib respetando el User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as f:
                shutil.copyfileobj(resp, f)
        return True
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP Error {e.code} al descargar {url}: {e.reason}\n")
        return False
    except Exception as e:
        sys.stderr.write(f"Error al descargar {url}: {e}\n")
        return False


def unpack_eprint(
    archive_path: Path,
    dest_dir: Path,
) -> Tuple[bool, List[str]]:
    """Desempaqueta un archivo de código fuente LaTeX de arXiv.

    arXiv puede devolver:
    - Tarball comprimido con gzip (.tar.gz)
    - Archivo .tex único comprimido con gzip (.gz)
    - Archivo tar sin comprimir
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted_files: List[str] = []

    # Intento 1: es un tarfile (comprimido o no)
    try:
        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as tar:
                # Extracción segura: evitar traversal de directorios (path traversal)
                safe_members = []
                for m in tar.getmembers():
                    norm_path = os.path.normpath(m.name)
                    if not norm_path.startswith("..") and not os.path.isabs(norm_path):
                        safe_members.append(m)
                tar.extractall(path=dest_dir, members=safe_members)
                extracted_files = [m.name for m in safe_members]
                return True, extracted_files
    except Exception:
        pass

    # Intento 2: archivo gzip con un solo archivo .tex
    try:
        with gzip.open(archive_path, "rb") as gz:
            content = gz.read()
            # Si parece texto o contiene \documentclass o \begin
            if b"\\documentclass" in content or b"\\begin{" in content or b"\\def" in content:
                out_tex = dest_dir / "main.tex"
                out_tex.write_bytes(content)
                return True, ["main.tex"]
    except Exception:
        pass

    return False, []


def emit_source_meta_yaml(data: Dict[str, Any], target_path: Path) -> None:
    """Serializa los metadatos como YAML conforming a build_sdm.py."""
    if yaml is not None:
        with open(target_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        return

    # Fallback sin PyYAML: formato manual limpio
    prod_esc = str(data.get("product", "")).replace('"', '\\"')
    lines: List[str] = [
        f"id: \"{data['id']}\"",
        f"hash: \"{data['hash']}\"",
        f"algorithm: \"{data.get('algorithm', 'sha256')}\"",
        f"vendor: \"{data.get('vendor', 'arXiv')}\"",
        f"product: \"{prod_esc}\"",
        f"url: \"{data.get('url', '')}\"",
        f"language: \"{data.get('language', 'en')}\"",
        f"format: \"{data.get('format', 'pdf')}\"",
    ]
    if data.get("version"):
        lines.append(f"version: \"{data['version']}\"")
    if data.get("date"):
        lines.append(f"date: \"{data['date']}\"")
    if data.get("arxiv_id"):
        lines.append(f"arxiv_id: \"{data['arxiv_id']}\"")
    if data.get("arxiv_version"):
        lines.append(f"arxiv_version: \"{data['arxiv_version']}\"")
    if data.get("doi"):
        lines.append(f"doi: \"{data['doi']}\"")
    if data.get("license"):
        lines.append(f"license: \"{data['license']}\"")
    if data.get("journal_ref"):
        jref_esc = str(data["journal_ref"]).replace('"', '\\"')
        lines.append(f"journal_ref: \"{jref_esc}\"")

    lines.append(f"tex_available: {str(bool(data.get('tex_available'))).lower()}")

    if data.get("authors"):
        lines.append("authors:")
        for auth in data["authors"]:
            clean_auth = str(auth).replace('"', '\\"')
            lines.append(f"  - \"{clean_auth}\"")

    if data.get("categories"):
        lines.append("categories:")
        for cat in data["categories"]:
            lines.append(f"  - \"{cat}\"")

    if data.get("abstract"):
        clean_abs = str(data["abstract"]).replace('"', '\\"')
        lines.append(f"abstract: \"{clean_abs}\"")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def fetch_arxiv_paper(
    identifier: str,
    out_dir: Path,
    with_tex: bool = False,
    local_pdf: Optional[Path] = None,
    local_tex: Optional[Path] = None,
    mock_metadata: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    delay: float = 0.0,
) -> Tuple[int, Dict[str, Any]]:
    """Pipeline principal de adquisición de arXiv."""
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    info = parse_arxiv_id(identifier)
    base_id = info["base_id"]
    version = info["version"]
    canonical_id = info["canonical_id"]

    # 1. Obtener metadatos
    meta: Dict[str, Any] = {}
    if mock_metadata:
        meta = mock_metadata
    else:
        try:
            meta = fetch_api_metadata(base_id, timeout=timeout)
        except Exception as e:
            sys.stderr.write(f"Aviso: no se pudo consultar API de arXiv ({e}).\n")
            # Fallback básico si falla red
            meta = {
                "title": f"arXiv:{canonical_id}",
                "abstract": "",
                "authors": [],
                "published": "",
                "updated": "",
                "categories": [],
                "primary_category": "",
                "doi": None,
                "journal_ref": None,
                "comment": None,
                "license": None,
            }

    # 2. Obtener PDF
    pdf_target = out_dir / "source.pdf"
    if local_pdf and local_pdf.exists():
        if local_pdf.resolve() != pdf_target:
            shutil.copy2(local_pdf, pdf_target)
    else:
        if delay > 0:
            time.sleep(delay)
        ok = download_file(info["pdf_url"], pdf_target, timeout=timeout)
        if not ok:
            sys.stderr.write(f"Error fatal: no se pudo descargar PDF de {info['pdf_url']}\n")
            return 1, {"error": "pdf_download_failed"}

    pdf_hash = compute_sha256(pdf_target)

    # 3. Obtener TeX e-print opcional
    tex_available = False
    extracted_files: List[str] = []
    tex_dir = out_dir / "tex"

    if with_tex:
        archive_path = out_dir / "_eprint_source.tmp"
        if local_tex and local_tex.exists():
            shutil.copy2(local_tex, archive_path)
            tex_available, extracted_files = unpack_eprint(archive_path, tex_dir)
            if archive_path.exists():
                archive_path.unlink()
        else:
            if delay > 0:
                time.sleep(delay)
            dl_ok = download_file(info["eprint_url"], archive_path, timeout=timeout)
            if dl_ok and archive_path.exists() and archive_path.stat().st_size > 0:
                tex_available, extracted_files = unpack_eprint(archive_path, tex_dir)
                archive_path.unlink()
            else:
                if archive_path.exists():
                    archive_path.unlink()
                tex_available = False

    # 4. Construir y escribir source-meta.yaml
    pub_date = meta.get("published") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    source_meta_payload = {
        "id": f"arxiv:{canonical_id}",
        "hash": pdf_hash,
        "algorithm": "sha256",
        "vendor": "arXiv",
        "product": meta.get("title") or f"arXiv:{canonical_id}",
        "url": info["abs_url"],
        "language": "en",
        "format": "pdf",
        "version": version or (f"v1" if not version else version),
        "date": pub_date,
        "authors": meta.get("authors") or [],
        "arxiv_id": base_id,
        "arxiv_version": version,
        "categories": meta.get("categories") or [],
        "doi": meta.get("doi"),
        "license": meta.get("license"),
        "journal_ref": meta.get("journal_ref"),
        "abstract": meta.get("abstract"),
        "tex_available": tex_available,
    }

    meta_file = out_dir / "source-meta.yaml"
    emit_source_meta_yaml(source_meta_payload, meta_file)

    summary = {
        "status": "success",
        "canonical_id": canonical_id,
        "base_id": base_id,
        "version": version,
        "title": source_meta_payload["product"],
        "authors_count": len(source_meta_payload["authors"]),
        "pdf_path": str(pdf_target),
        "pdf_sha256": pdf_hash,
        "source_meta_path": str(meta_file),
        "tex_available": tex_available,
        "tex_files": extracted_files,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_file = out_dir / "fetch_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return 0, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Adquisición de artículos y metadatos arXiv (P1)")
    parser.add_argument("--id", required=True, help="arXiv ID o URL (e.g. 2201.00001, https://arxiv.org/abs/...)")
    parser.add_argument("--out-dir", required=True, type=Path, help="Directorio destino para PDF y metadatos")
    parser.add_argument("--with-tex", action="store_true", help="Descargar y desempaquetar código fuente LaTeX")
    parser.add_argument("--pdf", type=Path, default=None, help="Ruta a PDF local para evitar descarga")
    parser.add_argument("--tex-archive", type=Path, default=None, help="Ruta a archivo .tar.gz o .gz local de LaTeX")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout de peticiones HTTP en segundos")
    parser.add_argument("--delay", type=float, default=0.0, help="Pausa en segundos entre peticiones de red")
    parser.add_argument("--json-only", action="store_true", help="Solo emitir JSON en stdout")

    args = parser.parse_args()

    rc, summary = fetch_arxiv_paper(
        identifier=args.id,
        out_dir=args.out_dir,
        with_tex=args.with_tex,
        local_pdf=args.pdf,
        local_tex=args.tex_archive,
        timeout=args.timeout,
        delay=args.delay,
    )

    if args.json_only:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        if rc == 0:
            print(f"arXiv ingest OK: {summary['canonical_id']}")
            print(f"  Título: {summary['title']}")
            print(f"  PDF: {summary['pdf_path']} (sha256: {summary['pdf_sha256'][:12]}...)")
            print(f"  Metadata: {summary['source_meta_path']}")
            print(f"  TeX disponible: {summary['tex_available']} ({len(summary.get('tex_files', []))} archivos)")
        else:
            print(f"arXiv ingest FAILED: {summary.get('error')}", file=sys.stderr)

    return rc


if __name__ == "__main__":
    sys.exit(main())
