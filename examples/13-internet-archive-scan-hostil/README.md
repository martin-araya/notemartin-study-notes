# 13-internet-archive-scan-hostil

Ejemplo end-to-end de F120. Categoría ROADMAP: **hybrid** /
**concept**. Fuente: `evals/corpus/13-internet-archive-scan-hostil/`.

## Qué demuestra

- Cadena L0 → L1 → L2 → L3 → L4 sobre la fuente `13-internet-archive-scan-hostil`.
- Validadores pasan: ver `reports/validator-suite.json`.
- Renderiza en los 3 destinos ricos (Obsidian, Notion API, AppFlowy) + 2 bonus (Notion-md, HTML/PDF).
- Capturas SVG en `render/<destino>/captures/13-internet-archive-scan-hostil-main.svg`.

## Particularidad

Muestra del corpus pendiente por F6; usa fixture sintético de F19.

## Cómo regenerar

```bash
python examples/build_examples.py --example 13-internet-archive-scan-hostil
```

Con capturas reales (Playwright):

```bash
pip install playwright && playwright install chromium
python examples/build_examples.py --example 13-internet-archive-scan-hostil --real-captures
```

## Estado

**Validadores:** PASS
**Renders:** PASS
**Resultado:** PASS
