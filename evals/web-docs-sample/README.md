# Web docs eval — `evals/web-docs-sample/`

Eval de F29. Verifica los 3 criterios del roadmap:

1. El orden reproduce el índice del sitio.
2. El boilerplate no aparece en el SDM.
3. Cada sección conserva su URL profunda.

## Cómo se corre

```bash
python3 evals/web-docs-sample/run_eval.py
```

Esperado: `3 PASS, 0 FAIL`.

## Estructura

```
evals/web-docs-sample/
├── README.md
├── build_fixtures.py             genera docs-site/ con 5 archivos HTML
├── run_eval.py                   ejecuta web_docs.py y valida los 3 criterios
├── docs-site/
│   ├── index.html                 página principal con <nav> + canonical + meta product/version
│   ├── intro.html                 1ra sección
│   ├── install.html               2da sección con canonical URL
│   ├── config.html                3ra sección
│   └── api.html                   4ta sección
└── expected/
    ├── order.json                  4 secciones en orden esperado
    ├── no-boilerplate.json         boilerplate strings a evitar (nav, footer, banner)
    └── canonical-urls.json         prefix esperado para canonical_url
```

## Cobertura

| Fixture | criterion 1 | criterion 2 | criterion 3 |
|---|---|---|---|
| `docs-site/index.html` | n/a (es el índice) | ✓ sin boilerplate | ✓ canonical = base_url/index.html |
| `docs-site/intro.html` | ✓ 1ra en orden | ✓ sin boilerplate | ✓ canonical = /docs/intro.html |
| `docs-site/install.html` | ✓ 2da en orden | ✓ sin boilerplate | ✓ canonical = /docs/install.html |
| `docs-site/config.html` | ✓ 3ra en orden | ✓ sin boilerplate | ✓ canonical = /docs/config.html |
| `docs-site/api.html` | ✓ 4ta en orden | ✓ sin boilerplate | ✓ canonical = /docs/api.html |

## Verificación de los 3 criterios del roadmap

| Criterio | Cómo se cumple |
|---|---|
| Orden reproduce el índice | `_criterion_1_order_reproduces_index` lee `sections.json` y verifica que el orden es `intro.html -> install.html -> config.html -> api.html`. |
| Sin boilerplate | `_criterion_2_no_boilerplate` busca las cadenas "Skip to content", "All rights reserved", "Accept cookies" en el `text` de cada sección. Si alguna aparece, FAIL. |
| URL profunda | `_criterion_3_canonical_url_deep` verifica que cada `canonical_url` empieza con `https://example.com/docs/` (no es solo el host raíz). |

## Regenerar los fixtures

```bash
python3 evals/web-docs-sample/build_fixtures.py
```

Dependencias: ninguna (solo Python stdlib).

## Lo que **no** cubre

- Descarga de URLs remotas (wget se hace fuera de F29).
- Robots.txt con `Disallow: /` (F29 emite warning con exit code 0; no hay fixture con este caso).
- HTML muy grande (>500 páginas). F29 corta con `--max-pages`.
- Productos con versiones no detectables. F29 emite warning con `product_version: null`.
