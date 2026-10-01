# 06-kubernetes-api-ref

Ejemplo end-to-end de F120. Categoría ROADMAP: **reference** /
**api-reference**. Fuente: `evals/corpus/06-kubernetes-api-ref/`.

## Qué demuestra

- Cadena L0 → L1 → L2 → L3 → L4 sobre la fuente `06-kubernetes-api-ref`.
- Validadores pasan: ver `reports/validator-suite.json`.
- Renderiza en los 3 destinos ricos (Obsidian, Notion API, AppFlowy) + 2 bonus (Notion-md, HTML/PDF).
- Capturas SVG en `render/<destino>/captures/06-kubernetes-api-ref-main.svg`.

## Particularidad

Muestra real del corpus; usar el sample.html/pdf/png de `evals/corpus/`.

## Cómo regenerar

```bash
python examples/build_examples.py --example 06-kubernetes-api-ref
```

Con capturas reales (Playwright):

```bash
pip install playwright && playwright install chromium
python examples/build_examples.py --example 06-kubernetes-api-ref --real-captures
```

## Estado

**Validadores:** PASS
**Renders:** PASS
**Resultado:** PASS
