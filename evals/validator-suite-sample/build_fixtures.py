#!/usr/bin/env python3
"""
build_fixtures.py — Genera la batería de fixtures para evals/validator-suite-sample.

Crea 9 categorías × 3-5 defectos inyectados. Los golden se toman
prestados de fixtures ya existentes en el repo (no se duplican).

Salida:
  evals/validator-suite-sample/fixtures/
    profile/  sdm/  ledger/  notemark/  links/  images/  properties/
    tables/   lengths/   destinations/
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"


def write(rel: str, content: str) -> None:
    p = FIX / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def json_write(rel: str, obj) -> None:
    write(rel, json.dumps(obj, indent=2, ensure_ascii=False))


# ────────────────────────────────────────────────────────────────────
# profile / 3 defects
# ────────────────────────────────────────────────────────────────────
json_write("profile/unknown-target/profile.yaml", {
    "language": "es",
    "ocr_engine": "tesseract",
    "targets": ["obsidian", "magic_place"],   # V-PROF-01
    "notes": {"tags_prefix": "type/"},
})

json_write("profile/bad-ocr/profile.yaml", {
    "language": "es",
    "ocr_engine": "magic_reader",   # V-PROF-06
    "targets": ["obsidian"],
    "notes": {"tags_prefix": "type/"},
})

json_write("profile/unknown-language/profile.yaml", {
    "language": "klingon",   # V-PROF-05
    "ocr_engine": "tesseract",
    "targets": ["obsidian"],
    "notes": {"tags_prefix": "type/"},
})

# ────────────────────────────────────────────────────────────────────
# sdm / 3 defects
# ────────────────────────────────────────────────────────────────────
json_write("sdm/bad-id/sdm.json", {
    "source": {"hash": "0" * 64},
    "sections": [
        {"id": "abc", "blocks": [
            {"id": "nothex", "anchor": {"page": 1}, "content": {"type": "prose", "text": "x"}, "source": "native"},
        ]},
    ],
})

json_write("sdm/missing-anchor/sdm.json", {
    "source": {"hash": "0" * 64},
    "sections": [
        {"id": "abc123456789", "blocks": [
            {"id": "aabbccddeeff", "anchor": {}, "content": {"type": "prose", "text": "x"}, "source": "native"},
        ]},
    ],
})

json_write("sdm/duplicate-id/sdm.json", {
    "source": {"hash": "0" * 64},
    "sections": [
        {"id": "abc123456789", "blocks": [
            {"id": "aabbccddeeff", "anchor": {"page": 1}, "content": {"type": "prose", "text": "x"}, "source": "native"},
            {"id": "aabbccddeeff", "anchor": {"page": 2}, "content": {"type": "prose", "text": "y"}, "source": "native"},
        ]},
    ],
})

# ────────────────────────────────────────────────────────────────────
# ledger / 3 defects
# ────────────────────────────────────────────────────────────────────
json_write("ledger/must-keep-pending/ledger.json", {
    "entries": [
        {"unit_id": "u1", "criticity": "must-keep", "state": "pending",
         "source_block_ids": ["aabbccddeeff"], "discard_reason": None,
         "target_note": None},   # V-LED-01
    ],
})

json_write("ledger/bad-discard-reason/ledger.json", {
    "entries": [
        {"unit_id": "u2", "criticity": "redundant", "state": "discarded",
         "source_block_ids": ["aabbccddeeff"], "discard_reason": "too-redundant"},    # V-LED-02
    ],
})

json_write("ledger/missing-target-note/ledger.json", {
    "entries": [
        {"unit_id": "u3", "criticity": "must-keep", "state": "kept",
         "source_block_ids": ["aabbccddeeff"], "discard_reason": None,
         "target_note": None},   # V-LED-03
    ],
})

# ────────────────────────────────────────────────────────────────────
# notemark / 3 defects
# ────────────────────────────────────────────────────────────────────
write("notemark/no-frontmatter/note.nm", """\
# Concept test

## TL;DR
Short summary.

## Problema
Body.
""")

write("notemark/bad-directive/note.nm", """\
---
title: Bad
note-type: concept
status: draft
---

# Concept test

## TL;DR
Short.

## Problema
Body.

:::mystery
content
:::
""")

write("notemark/bad-src-mark/note.nm", """\
---
title: Bad
note-type: concept
status: draft
---

# Concept test

## TL;DR
Short.

## Problema
Body with {src:blk_notvalidhex} here.
""")

# ────────────────────────────────────────────────────────────────────
# links / 3 defects
# ────────────────────────────────────────────────────────────────────
write("links/unresolved-target/note-a.nm", """\
---
title: A
note-type: concept
status: draft
---

# A

## TL;DR
x

## Problema
See [[note:nonexistent-target]] for more.
""")

write("links/no-intro/note-b.nm", """\
---
title: B
note-type: concept
status: draft
---

# B

## TL;DR
x

## Problema
Body.
x[[note:short-link]]
""")

# Two-note circular fixture.
write("links/cycle/note-x.nm", """\
---
title: X
note-type: concept
status: draft
---

# X

## TL;DR
x

## Problema
See [[note:y]].
""")

write("links/cycle/note-y.nm", """\
---
title: Y
note-type: concept
status: draft
---

# Y

## TL;DR
y

## Problema
See [[note:x]].
""")

# ────────────────────────────────────────────────────────────────────
# images / 3 defects (skip real binary; use textual patterns)
# ────────────────────────────────────────────────────────────────────
write("images/no-alt/note.nm", """\
---
title: img
note-type: concept
status: draft
---

# img

## TL;DR
x

## Problema
![](assets/missing.png)

A second paragraph.
""")

write("images/unresolvable/note.nm", """\
---
title: img
note-type: concept
status: draft
---

# img

## TL;DR
x

## Problema
![alt text](assets/does-not-exist.png)
""")

write("images/bad-format/note.nm", """\
---
title: img
note-type: concept
status: draft
---

# img

## TL;DR
x

## Problema
![alt text](fixtures/bad.tiff)
""")
# Create the .tiff with size > 0 so V-IMG-04 triggers.
(FIX / "images" / "bad-format" / "fixtures").mkdir(parents=True, exist_ok=True)
(FIX / "images" / "bad-format" / "fixtures" / "bad.tiff").write_bytes(b"\x00\x00")

# ────────────────────────────────────────────────────────────────────
# properties / 3 defects
# ────────────────────────────────────────────────────────────────────
write("properties/no-frontmatter/note.nm", """\
# No frontmatter

## TL;DR
x
""")

write("properties/bad-status/note.nm", """\
---
title: Bad status
note-type: concept
status: zombie
---

# Bad

## TL;DR
x
""")

write("properties/bad-reading-time/note.nm", """\
---
title: Bad reading-time
note-type: concept
status: draft
reading-time-minutes: zero
---

# Bad

## TL;DR
x
""")

# ────────────────────────────────────────────────────────────────────
# tables / 3 defects
# ────────────────────────────────────────────────────────────────────
write("tables/single-row/note.nm", """\
---
title: Tab
note-type: concept
status: draft
---

# Tab

## TL;DR
x

## Tabla

| Col1 | Col2 |
| --- | --- |
| only |
""")

write("tables/empty-cells/note.nm", """\
---
title: Tab
note-type: concept
status: draft
---

# Tab

## TL;DR
x

## Tabla

| Col1 | Col2 |
| --- | --- |
| a | |
| b | c |
""")

write("tables/inconsistent-cols/note.nm", """\
---
title: Tab
note-type: concept
status: draft
---

# Tab

## TL;DR
x

## Tabla

| A | B | C |
| --- | --- | --- |
| 1 | 2 |
| 4 | 5 | 6 |
""")

# ────────────────────────────────────────────────────────────────────
# lengths / 3 defects
# ────────────────────────────────────────────────────────────────────
write("lengths/tldr-too-long/note.nm", """\
---
title: Long
note-type: concept
status: draft
---

# Long

## TL;DR
""" + " ".join(["palabra"] * 75) + """

## Problema
x
""")

write("lengths/cheatsheet-too-long/note.nm", """\
---
title: Big
note-type: cheatsheet
status: draft
---

# Big

## TL;DR
x

## Comandos
""" + "\n".join([
    "| cmd | desc | link |",
    "| --- | --- | --- |",
] + [f"| c{i} | d{i} | [[note:t{i}]] |" for i in range(85)]) + "\n")

write("lengths/empty-section/note.nm", """\
---
title: Empty
note-type: concept
status: draft
---

# Empty

## TL;DR
x

## Problema
Some body.

## EmptySection
""")


# ────────────────────────────────────────────────────────────────────
# destinations / 1 defect (missing artifact)
# ────────────────────────────────────────────────────────────────────
# We just point the validator at a workdir with no render/ subdir.
(FIX / "destinations" / "no-render").mkdir(parents=True, exist_ok=True)
(FIX / "destinations" / "no-render" / "ir").mkdir(parents=True, exist_ok=True)
json_write("destinations/no-render/ir/n1.note-ir.json", {
    "note_id": "n1",
    "nodes": [],
})


def main() -> None:
    print(f"fixtures written under {FIX}")


if __name__ == "__main__":
    main()