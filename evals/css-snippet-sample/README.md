# `evals/css-snippet-sample/` — Fase 74

Verificador de la Fase 74 (snippet CSS para Obsidian). Cubre los 3 criterios del ROADMAP §1453-1455 con 6 sub-criterios:

| Criterio | Qué verifica | Método |
|---|---|---|
| **C1** | `assets/notemartin.css` existe y ≤ 400 líneas | `wc -l` |
| **C2** | `assets/css-tokens.generated.css` existe y comienza con la cabecera `/* Auto-generated from assets/tokens.json` | `head -1` |
| **C3** | El CSS generado contiene las 9 × 5 = 45 variables semánticas (cada `--semantic-<name>-{fg,bg,border,fgOnBg,borderContrast}`) | in-process: bucle de validación |
| **C4** | Tema dual: bloque `@media (prefers-color-scheme: dark)` con overrides de las 45 vars | regex + in-process |
| **C5** | INV-14: el snippet NO contiene literales hex ni `rgba()` en valores CSS (excluyendo comentarios) | regex con `^\s*[a-zA-Z\-]+\s*:` |
| **C6** | El generador `css_from_tokens.py` es determinista (2 invocaciones idénticas + coincide con el archivo en disco) | in-process: `render()` 2 veces + SHA256 |

## Uso

```bash
# Generar fixtures y ejecutar
python3 evals/css-snippet-sample/run_eval.py

# Forzar regeneración de golden
python3 evals/css-snippet-sample/run_eval.py --regen
```

## Salida esperada

```
============================================================
Fase 74 — Snippet CSS para Obsidian
============================================================
  PASS  C1-notemartin-size (363 líneas ≤ 400)
  PASS  C2-generated-exists (cabecera OK, primera línea: /* Auto-generated from assets/tokens.json...)
  PASS  C3-semantic-coverage (9 × 5 = 45 vars semánticas presentes en light + dark)
  PASS  C4-dark-theme (45/45 vars semánticas redefinidas en dark)
  PASS  C5-no-css-literals (0 literales hex/rgba en valores CSS de notemartin.css)
  PASS  C6-deterministic (2 invocaciones idénticas, sha256=...)
============================================================
PASS 6/6
```

Exit code `0` si todos pasan; `1` si alguno falla.

## Archivos

- `build_fixtures.py` — genera `fixtures/css-tokens.generated.golden.{json,css}` y `fixtures/notemartin.snapshot.json` (resumen del snippet: clases, líneas, SHA256).
- `run_eval.py` — los 6 sub-criterios documentados arriba.
- `fixtures/` — snapshots deterministas (SHA256) para detectar drift.

## Wirings

- Cierra los 3 criterios de `ROADMAP.md` §1453-1455 para Fase 74.
- El criterio C5 (sin literales en valores CSS) es el más estricto: garantiza que el snippet no viola INV-14, dejando toda dependencia de color en `css-tokens.generated.css` (generado desde `tokens.json`).
- El criterio C6 (determinismo) detecta drift entre el generador y el archivo en disco: si alguien edita `css-tokens.generated.css` a mano, el eval falla y exige regenerar.

## Excepción vigente

`references/08-render/html_pdf.template.css` (F59) sigue con literales hex — su migración a `var(--token)` se difiere a una fase futura (decisión F74 explícita del alcance "Solo snippet + generador"). El eval F72 lo excluye vía `--glob`.
