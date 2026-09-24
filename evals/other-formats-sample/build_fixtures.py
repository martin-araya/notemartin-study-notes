#!/usr/bin/env python3
"""build_fixtures.py — Generate synthetic fixtures for F28 eval.

Builds six fixtures:
  - corpus-sample.epub: 2 chapters + image + note.
  - corpus-sample.docx: Heading 1, comment, native table.
  - corpus-sample.pptx: 3 slides + speaker notes.
  - corpus-sample.srt: timestamps + fillers.
  - corpus-sample.vtt: timestamps.
  - corpus-sample.json: Whisper-style transcript.

Writes to evals/other-formats-sample/fixtures/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _build_epub() -> Path:
    """EPUB with 2 chapters, image, and note (manually constructed for parseability)."""
    out = FIXTURES / "corpus-sample.epub"
    import zipfile
    out.unlink(missing_ok=True)
    mimetype = b"application/epub+zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("mimetype", mimetype)
        zf.writestr("META-INF/container.xml",
                    b"""<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles>
<rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
</rootfiles>
</container>""")
        zf.writestr("EPUB/content.opf",
                    b"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Sample</dc:title>
<dc:identifier id="bid">urn:uuid:1</dc:identifier>
<dc:language>en</dc:language>
</metadata>
<manifest>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/>
<item id="c2" href="c2.xhtml" media-type="application/xhtml+xml"/>
<item id="n1" href="n1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx">
<itemref idref="c1"/>
<itemref idref="c2"/>
<itemref idref="n1"/>
</spine>
</package>""")
        zf.writestr("EPUB/toc.ncx",
                    b"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="urn:uuid:1"/><meta name="dtb:depth" content="1"/></head>
<docTitle><text>Sample</text></docTitle>
<navMap>
<navPoint id="nav1" playOrder="1"><navLabel><text>Chapter 1</text></navLabel><content src="c1.xhtml"/></navPoint>
<navPoint id="nav2" playOrder="2"><navLabel><text>Chapter 2</text></navLabel><content src="c2.xhtml"/></navPoint>
<navPoint id="nav3" playOrder="3"><navLabel><text>Notes</text></navLabel><content src="n1.xhtml"/></navPoint>
</navMap>
</ncx>""")
        zf.writestr("EPUB/c1.xhtml",
                    b"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<h1>Chapter 1: Introduction</h1>
<p>Lorem ipsum dolor sit amet.</p>
<p>Consectetur adipiscing elit.</p>
</body></html>""")
        zf.writestr("EPUB/c2.xhtml",
                    b"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<h1>Chapter 2: Methods</h1>
<p>Sed do eiusmod tempor.</p>
</body></html>""")
        zf.writestr("EPUB/n1.xhtml",
                    b"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<p>This is an endnote.</p>
</body></html>""")
    return out


def _build_docx() -> Path:
    """DOCX with Heading 1, comment, native table."""
    out = FIXTURES / "corpus-sample.docx"
    try:
        from docx import Document
    except ImportError:
        return None
    doc = Document()
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph("First paragraph of the document.")
    doc.add_heading("Methods", level=2)
    doc.add_paragraph("Second section with more content.")
    table = doc.add_table(rows=3, cols=3)
    table.cell(0, 0).text = "id"
    table.cell(0, 1).text = "name"
    table.cell(0, 2).text = "value"
    table.cell(1, 0).text = "1"
    table.cell(1, 1).text = "Widget"
    table.cell(1, 2).text = "10.00"
    table.cell(2, 0).text = "2"
    table.cell(2, 1).text = "Gadget"
    table.cell(2, 2).text = "20.00"
    doc.add_paragraph("End of document.")
    doc.save(str(out))
    return out


def _build_pptx() -> Path:
    """PPTX with 3 slides + speaker notes."""
    out = FIXTURES / "corpus-sample.pptx"
    try:
        from pptx import Presentation
    except ImportError:
        return None
    prs = Presentation()
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    slide1.shapes.title.text = "Slide 1: Introduction"
    slide1.placeholders[1].text = "Overview of the topic."
    slide1.notes_slide.notes_text_frame.text = "Speaker notes for slide 1: emphasize the importance."

    slide2 = prs.slides.add_slide(prs.slide_layouts[0])
    slide2.shapes.title.text = "Slide 2: Methods"
    slide2.placeholders[1].text = "Detailed methodology."
    slide2.notes_slide.notes_text_frame.text = "Speaker notes for slide 2: explain each step carefully."

    slide3 = prs.slides.add_slide(prs.slide_layouts[0])
    slide3.shapes.title.text = "Slide 3: Results"
    slide3.placeholders[1].text = "Summary of findings."
    slide3.notes_slide.notes_text_frame.text = ""
    prs.save(str(out))
    return out


def _build_srt() -> Path:
    """SRT with timestamps + filler words."""
    out = FIXTURES / "corpus-sample.srt"
    content = """1
00:00:00,000 --> 00:00:02,500
Hello world.

2
00:00:02,500 --> 00:00:05,000
Um, this is a test.

3
00:00:05,000 --> 00:00:08,000
And uh, we continue with the next phrase.

4
00:00:08,000 --> 00:00:11,000
This is the final segment.
"""
    out.write_text(content, encoding="utf-8")
    return out


def _build_vtt() -> Path:
    """VTT with timestamps."""
    out = FIXTURES / "corpus-sample.vtt"
    content = """WEBVTT

00:00:00.000 --> 00:00:02.500
Hello world.

00:00:02.500 --> 00:00:05.000
Um, this is a test.
"""
    out.write_text(content, encoding="utf-8")
    return out


def _build_json() -> Path:
    """JSON Whisper-style transcript."""
    out = FIXTURES / "corpus-sample.json"
    data = {
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Hello world."},
            {"start": 2.5, "end": 5.0, "text": "Um, this is a test."},
            {"start": 5.0, "end": 8.0, "text": "And uh, we continue."},
        ]
    }
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for fn in (_build_epub, _build_docx, _build_pptx, _build_srt, _build_vtt, _build_json):
        p = fn()
        if p:
            print(f"Wrote {p} ({p.stat().st_size} bytes)")
        else:
            print(f"SKIPPED {fn.__name__} (library missing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
