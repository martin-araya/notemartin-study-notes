#!/usr/bin/env python3
"""run_eval.py — eval de P2.a (normalización de texto de papers).

Criterios:
  C1  ligaduras: ﬁ ﬂ ﬃ ﬄ → letras; el original queda registrado (reversible).
  C2  índices matemáticos: sub/sup no son `footnote`; una nota al pie real sí lo es.
  C3  guiones de fin de línea: `simu-`+`late` se une; `real-`+`world` conserva guion;
      el vocabulario del documento decide `physics-based`; no se pierde contenido.
  C4  estampa arXiv: reconocida y devuelta como metadato; una cita `arXiv:1809.11165` no.
  C5  corpus 04 (sample.pdf): 0 ligaduras, footnote < 50 % de la línea base, estampa
      `2201.00001 v3 math.NA`, y ningún carácter se pierde (≤ ±1 % de letras).

Uso:  python3 evals/paper-text-sample/run_eval.py
Esperado: todos PASS (exit 0). Con fallos, exit 1.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skill" / "notemartin-study-notes"
sys.path.insert(0, str(SKILL / "scripts" / "util"))
import paper_text as pt  # noqa: E402

RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))


def frag(text, x0=100.0, y0=500.0, size=10.0, font="NimbusRomNo9L-Regu", role="body"):
    return {"page": 1, "bbox": [x0, y0, x0 + len(text) * size * 0.5, y0 + size],
            "font_name": font, "font_size": size, "text": text, "role": role}


def c1():
    print("=== C1 ligaduras ===")
    f = frag("Tra\ufb03c \ufb02ow and \ufb01nite \ufb00 \ufb04")
    n = pt.apply_ligature_normalization([f])
    check("texto normalizado", f["text"] == "Traffic flow and finite ff ffl", repr(f["text"]))
    check("original registrado", n == 1 and f["normalizations"][0]["original"].startswith("Tra\ufb03c"))
    g = frag("sin ligaduras")
    check("sin cambios si no hay ligaduras", pt.apply_ligature_normalization([g]) == 0 and "normalizations" not in g)


def c2():
    print("=== C2 índices vs notas al pie ===")
    parent = frag("L", x0=100, y0=500, size=10, font="CMMI10")
    sub = frag("adv", x0=107, y0=498.0, size=7, font="CMMI7", role="footnote")
    sup = frag("2", x0=107, y0=504.5, size=7, font="CMR7", role="footnote")
    note = frag("Work conducted during an internship with Amazon AI", x0=108, y0=82, size=7.97,
                role="footnote")
    frags = [parent, sub, sup, note]
    pt.mark_scripts(frags, body_size=10.0)
    check("subíndice → body + script=sub", sub["role"] == "body" and sub.get("script") == "sub")
    check("superíndice → body + script=sup", sup["role"] == "body" and sup.get("script") == "sup")
    check("nota al pie real conserva footnote", note["role"] == "footnote" and "script" not in note)
    glyph = frag("v/", x0=300, y0=300, size=8.9, font="CMMI9", role="footnote")
    pt.mark_scripts([glyph], body_size=10.0)
    check("glifo matemático aislado no es footnote", glyph["role"] == "body")


def c3():
    print("=== C3 guiones de fin de línea ===")
    f1 = frag("the method to simu-")
    f2 = frag("late the model and test", y0=488)
    pt.dehyphenate([f1, f2])
    check("simu-/late → simulate", f1["text"] == "the method to simulate" and f2["text"].startswith("the model"),
          f"{f1['text']!r} | {f2['text']!r}")
    check("operación registrada en ambos", f1["normalizations"][0]["type"] == "dehyphenate"
          and f2["normalizations"][0]["type"] == "dehyphenate_source")

    g1, g2 = frag("on synthetic and real-"), frag("world data from", y0=488)
    pt.dehyphenate([g1, g2])
    check("real-/world conserva guion", g1["text"] == "on synthetic and real-world", g1["text"])

    vocab = pt.build_vocab([[frag("physics-based models are physics-based")]])
    h1, h2 = frag("Additional physics-"), frag("based methods exist", y0=488)
    pt.dehyphenate([h1, h2], vocab)
    check("vocabulario del documento decide physics-based", h1["text"] == "Additional physics-based", h1["text"])

    k1, k2 = frag("a very long decom-"), frag("position of the matrix", y0=488)
    before = (k1["text"] + " " + k2["text"]).replace("-", "").replace(" ", "")
    pt.dehyphenate([k1, k2])
    after = (k1["text"] + " " + k2["text"]).replace("-", "").replace(" ", "")
    check("no se pierden letras", before == after, f"{k1['text']!r}")

    e1, e2 = frag("fin de párrafo y guion-"), frag("Mayúscula sigue", y0=488)
    pt.dehyphenate([e1, e2])
    check("no une si la siguiente empieza en mayúscula", e1["text"].endswith("guion-"))

    h = frag("Title text here-", role="heading")
    pt.dehyphenate([h, frag("lower start", y0=488)])
    check("no toca encabezados", h["text"].endswith("here-"))


def c4():
    print("=== C4 estampa arXiv ===")
    s = pt.detect_arxiv_stamp("arXiv:2201.00001v3  [math.NA]  17 Feb 2022")
    check("estampa nueva", s == {"id": "2201.00001", "version": "v3", "category": "math.NA",
                                 "date": "17 Feb 2022"}, str(s))
    old = pt.detect_arxiv_stamp("arXiv:hep-th/9901001v2 [hep-th] 5 Jan 1999")
    check("estampa de ID antiguo", old is not None and old["id"] == "hep-th/9901001", str(old))
    check("una cita no es estampa", pt.detect_arxiv_stamp("arXiv:1809.11165") is None)
    check("texto normal no es estampa", pt.detect_arxiv_stamp("See arXiv:2201.00001 for details") is None)


def letters(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text))


def c5():
    print("=== C5 corpus 04 ===")
    pdf = REPO / "evals" / "corpus" / "04-arxiv-two-column" / "sample.pdf"
    if not pdf.exists():
        check("sample.pdf presente", False, str(pdf))
        return
    script = SKILL / "scripts" / "ingest" / "pdf_native.py"
    with tempfile.TemporaryDirectory() as tmp:
        runs = {}
        for label, extra in (("on", []), ("off", ["--no-paper-normalize"])):
            out = Path(tmp) / label
            subprocess.run([sys.executable, str(script), "--source", str(pdf), "--out-dir", str(out),
                            "--json-only", *extra], capture_output=True, text=True)
            runs[label] = json.loads((out / "fragments.json").read_text(encoding="utf-8"))

    def frags(d):
        return [f for p in d["pages"] for f in p["fragments"]]

    on, off = frags(runs["on"]), frags(runs["off"])
    lig = sum(1 for f in on if re.search("[\ufb00-\ufb06]", f["text"]))
    check("0 ligaduras sin normalizar", lig == 0, f"{lig}")
    fn_on = sum(1 for f in on if f["role"] == "footnote")
    fn_off = sum(1 for f in off if f["role"] == "footnote")
    check("footnote < 50 % de la línea base", fn_on < 0.5 * fn_off, f"{fn_on} vs {fn_off}")
    ax = runs["on"].get("arxiv") or {}
    check("estampa arXiv capturada", ax.get("id") == "2201.00001" and ax.get("version") == "v3"
          and ax.get("category") == "math.NA", str(ax))
    check("modo off no cambia el esquema base", "arxiv" not in runs["off"] and "paper_normalization" not in runs["off"])
    l_on = letters(" ".join(f["text"] for f in on))
    l_off = letters(" ".join(f["text"] for f in off))
    # Las ligaduras expanden 1 carácter a 2-3 letras: se compara contra el texto base ya expandido.
    expanded = letters(pt.normalize_ligatures(" ".join(f["text"] for f in off)))
    check("no se pierden letras (±1 %)", abs(l_on - expanded) <= 0.01 * expanded,
          f"on={l_on} off_expandido={expanded} (off crudo={l_off})")


def main() -> int:
    c1(); c2(); c3(); c4(); c5()
    passed, failed = sum(RESULTS), len(RESULTS) - sum(RESULTS)
    print(f"\nResultado: {passed} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
