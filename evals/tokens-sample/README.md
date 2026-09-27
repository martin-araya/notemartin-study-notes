# `evals/tokens-sample/` — Fase 72

Verificador de la Fase 72 (design tokens). Cubre los 3 criterios de cierre del ROADMAP §1422-1425 con 5 sub-criterios (C1, C2, C3, C3b, C4):

| Criterio | Qué verifica | Comando |
|---|---|---|
| **C1** — Schema cerrado | `assets/tokens.json` tiene `$version` semver, las 6 claves top-level obligatorias y los 9 nombres canónicos de `semantic.*` (sin extras). | Verificación in-process con `json.load` |
| **C2** — Contraste WCAG AA | Los 18 pares `fgOnBg` vs `bg` (9 tokens × 2 modos) tienen ratio ≥ 4.5:1. | Invoca `scripts/validate/contrast_check.py --min-ratio 4.5 --mode both`; exige exit 0 |
| **C3** — `make_figure.py` migrado | El script no contiene literales hex/rgb tras la migración a tokens (regex con lookbehind para evitar falsos positivos en `hex_to_rgb`, `lstrip("#")`). | Verificación in-process con `HEX_LITERAL_RE` |
| **C3b** — Loader funcional | `scripts/util/tokens.py:resolve_token()` resuelve los 9 `semantic.<name>.{light,dark}.fgOnBg` a hex `#RRGGBB` válidos. | `import scripts.util.tokens; load_tokens(); resolve_token(...)` |
| **C4** — INV-14 | Ningún archivo del skill contiene literales de color fuera de `assets/tokens.json` y la excepción documentada `references/08-render/html_pdf.template.css` (migración pendiente a F74). | `rg -nP '(?<![A-Za-z_])#[0-9A-Fa-f]{3,8}\b\|(?<![A-Za-z_])rgba?\('` con globs de exclusión |

## Uso

```bash
# Generar fixtures y ejecutar
python3 evals/tokens-sample/run_eval.py

# Forzar regeneración de fixtures (tokens.golden.json + expected/contrast-report.md)
python3 evals/tokens-sample/run_eval.py --regen
```

## Salida esperada

```
============================================================
Fase 72 — Design tokens
============================================================
  PASS  C1-schema (9/9 semánticos, $version=1.0.0, 6/6 top-keys)
  PASS  C2-contrast (18/18 PASS AA, exit 0)
  PASS  C3-make-figure (0 literales de color en make_figure.py)
  PASS  C3b-loader (9 semánticos × 2 modos = 18 hex resueltos)
  PASS  C4-inv14 (0 literales fuera de tokens.json y html_pdf.template.css)
============================================================
PASS 5/5
```

Exit code `0` si todos pasan; `1` si alguno falla.

## Archivos

- `build_fixtures.py` — genera `fixtures/tokens.golden.json` (snapshot de los 9 hex `fgOnBg` y `bg` por modo) y `expected/contrast-report.md`.
- `run_eval.py` — los 5 sub-criterios documentados arriba.
- `fixtures/tokens.golden.json` — snapshot esperado al cierre de F72.
- `expected/contrast-report.md` — tabla WCAG documentada para inspección humana.

## Dependencias

Python 3.9+ stdlib puro. `rg` (ripgrep) necesario para C4; presente en macOS por defecto y en la mayoría de Linux con `apt install ripgrep` / `brew install ripgrep`.

## Wirings

- Cierra los 3 criterios de `ROADMAP.md` §1422-1425 para Fase 72.
- Complementa `references/07-visual/tokens.md` (documentación) y `references/07-visual/accessibility.md` (reglas WCAG).
- F74 (`assets/notemartin.css`) deberá añadir un C5 que verifique 0 literales en `html_pdf.template.css` (cierre completo de INV-14).
