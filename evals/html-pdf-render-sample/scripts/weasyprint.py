"""weasyprint — Stub mínimo para el eval battery del renderer HTML/PDF (F59).

Este módulo provee una clase `HTML` y un método `write_pdf` que crean
un archivo PDF trivial (header %PDF-1.4 + %EOF). NO renderiza
contenido real; es solo un marcador para verificar que el code path
de weasyprint se ejecuta correctamente durante los tests.
"""

from __future__ import annotations


class _PDFWriter:
    def __init__(self, target: str) -> None:
        self.target = target

    def write_pdf(self) -> None:
        import pathlib
        p = pathlib.Path(self.target)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4\n%mock weasyprint stub\n%%EOF\n")


class HTML:
    """Stub que produce un PDF trivial."""

    def __init__(self, *args, **kwargs) -> None:
        self._args = args
        self._kwargs = kwargs

    def write_pdf(self, target: str) -> "_PDFWriter":
        w = _PDFWriter(target)
        w.write_pdf()
        return w
