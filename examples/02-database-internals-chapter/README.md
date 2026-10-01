# 02-database-internals-chapter

Ejemplo end-to-end de F120. Categoría ROADMAP: **study** /
**concept**. Fuente: `evals/corpus/02-database-internals-chapter/`.

## Qué demuestra

- Cadena L0 → L1 → L2 → L3 → L4 sobre la fuente `02-database-internals-chapter`.
- Validadores pasan: ver `reports/validator-suite.json`.
- Renderiza en los 3 destinos ricos (Obsidian, Notion API, AppFlowy) + 2 bonus (Notion-md, HTML/PDF).
- Capturas SVG en `render/<destino>/captures/02-database-internals-chapter-main.svg`.

## Particularidad

Muestra real del corpus; usar el sample.html/pdf/png de `evals/corpus/`.

## Cómo regenerar

```bash
python examples/build_examples.py --example 02-database-internals-chapter
```

Con capturas reales (Playwright):

```bash
pip install playwright && playwright install chromium
python examples/build_examples.py --example 02-database-internals-chapter --real-captures
```

## Estado

**Validadores:** PASS
**Renders:** PASS
**Resultado:** PASS
