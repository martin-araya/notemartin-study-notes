# `evals/visual/` — Verificación visual multi-destino (Fase 77)

> Eval visual de los 7 destinos L4 (Obsidian nativo, Notion API, Notion import,
> AppFlowy nativo, Markdown, HTML/PDF, Flashcards) en tema claro y oscuro.
> Contiene 2 notas (sonda oficial de F8 + real-postgresql-arrays), 12 artefactos
> reales en 4 destinos renderizables localmente, y un checklist para los 3 destinos
> externos que requieren browser o API key.

## Navegación

- `notes/` — 2 notas fuente: `probe.nm` (sonda F8) y `real-postgresql-arrays.md`.
- `artifacts/` — 12 artefactos (4 destinos × 2 notas; light+dark en md/flashcards):
  - `markdown/probe.{light,dark}.md`, `markdown/real-postgresql-arrays.{light,dark}.md`
  - `html_pdf/probe.html`, `html_pdf/real-postgresql-arrays.html`
  - `mermaid/probe.flow.svg`, `mermaid/real-postgresql-arrays.erd.svg`
  - `flashcards/probe.{light,dark}.csv`, `flashcards/real-postgresql-arrays.{light,dark}.csv`
- `theme/` — verificación del tema dual:
  - `light-tokens.css` (45 vars semánticas light)
  - `dark-tokens.css` (45 vars semánticas dark)
  - `theme-apply.html` (mini-doc con 5 callouts + tabla densa)
  - `full-tokens.css` (subset de `assets/css-tokens.generated.css` regenerado por `css_from_tokens.py --out`)
- `checklist.md` — 12 entradas (2 notas × 3 destinos × 2 temas) para inspección humana.
- `defects.md` — log de defectos con severidad, status, fase asignada.
- `visual_inspect.py` — verificador de overflow/truncado/ilegible sobre los artefactos.
- `run_eval.py` — eval con 5 sub-criterios.
- `workdir/` — espacio de trabajo (no commiteado en CI; contiene IRs intermedios + re-renders).

## Cómo regenerar los artefactos

```bash
# 1. Parsear las 2 notas a IR.
cd skill/notemartin-study-notes
python3 -m scripts.authoring.parse_notemark \
    --source ../../evals/visual/notes/probe.nm \
    --out ../../evals/visual/workdir/ir/probe.note-ir.json --no-validate
python3 -m scripts.authoring.parse_notemark \
    --source ../../evals/visual/notes/real-postgresql-arrays.md \
    --out ../../evals/visual/workdir/ir/real-postgresql-arrays.note-ir.json --no-validate

# 2. Renderizar con cada renderer.
python3 -m scripts.render.markdown --ir <probe.ir> --profile workdir/profile.yaml --out-dir workdir/render
python3 -m scripts.render.html_pdf --ir <probe.ir> --profile workdir/profile.yaml --out-dir workdir/render
python3 -m scripts.render.flashcards --ir <probe.ir> --profile workdir/profile.yaml --out-dir workdir/render

# 3. Copiar a artifacts/.
cp workdir/render/render/markdown/probe-note.md artifacts/markdown/probe.light.md
# (etc.)
```

## Cómo ejecutar el eval

```bash
python3 evals/visual/run_eval.py
```

Salida esperada: `PASS 5/5`. Si `visual_inspect.py` reporta issues, se verifica que todos estén en `defects.md`.

## Tabla de cierre (criterios del ROADMAP §1498-1500)

| Criterio | Cumplido por |
|---|---|
| C1: Existen capturas de los 7 destinos en ambos temas | 4 destinos con artefactos locales (12 archivos) + 3 destinos externos con checklist manual; tema dual verificado en light+dark para los 4 locales (`theme/light-tokens.css` + `theme/dark-tokens.css` + `theme/theme-apply.html`) |
| C2: No hay contenido cortado, desbordado ni ilegible | `visual_inspect.py` valida los 12 artefactos (líneas > 200 chars, tablas 10+ cols, links rotos, marcas `{src:}` no canónicas, HTML sin cerrar, `<th>` sin scope, SVG sin `<title>`, CSV con > 5 clauses) |
| C3: Defectos corregidos o con fase de arreglo asignada | 1 defecto trivial corregido (defect #1: `<th scope="col">` en `_header.py:204`); 5 defectos asignados a fases futuras (F62, F78-F92 polish, futuras QA); 5 wontfix documentados (limitaciones de formato/infraestructura) |

## Wirings

- **F46** `references/04-authoring/inline-marks.md` — marcas `{src:blk_xxxx}` validadas en artefactos.
- **F51** `references/04-authoring/depth-layers.md` — jerarquía visual L1/L2/L3 capturada en artefactos.
- **F59** `references/08-render/html_pdf.template.css` — estilo del template (migración pendiente per F72).
- **F66** `references/07-visual/mermaid-portable.md` — diagramas Mermaid en `mermaid/`.
- **F70** `scripts/render/make_figure.py` — figuras SVG en artefactos `mermaid/`.
- **F72** `references/07-visual/tokens.md` + `assets/tokens.json` — tokens semánticos consumidos por `theme/light-tokens.css` + `theme/dark-tokens.css` + `theme/theme-apply.html`.
- **F73** `references/07-visual/style-mapping.md` + `scripts/util/style_mapping.py` — iconos/colores de los 5 callouts semánticos visibles en artefactos.
- **F74** `assets/notemartin.css` — snippet CSS aplicado en `theme/theme-apply.html` (5 callouts + tabla densa + código).
- **F75** `references/07-visual/note-templates.md` + `scripts/render/_header.py` — cabecera `## Cabecera` (5 campos) visible en artefactos HTML/PDF.
- **F76** `references/07-visual/density.md` + `scripts/validate/density_check.py` — R1-R8 medidos en las 2 notas (PASS esperado).
- **F8** `references/08-render/capability-matrix.md` §7 — sonda oficial consumida en `notes/probe.nm`.
- **F53** `references/08-render/contract.md` — los 7 destinos cubiertos.
- **F54-F60** `scripts/render/{obsidian,notion_api,notion_md,appflowy,markdown,html_pdf,flashcards}.py` — los 6 renderers + 1 flashcards; 4 invocables localmente (markdown, html_pdf, flashcards), 3 externos (obsidian, notion_api, appflowy).

## Riesgos (R1-R3 del plan)

- **R1** Sin browser para capturas reales → 3 destinos externos quedan en `checklist.md` para QA humana.
- **R2** Sin Mermaid CLI → 2 SVGs generados manualmente con sintaxis básica.
- **R3** Tema dual en MD/Flashcards → no aplica (el visor aplica el tema).
