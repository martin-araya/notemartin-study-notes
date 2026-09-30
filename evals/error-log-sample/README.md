# `evals/error-log-sample/` — Fase 103 `Registro de errores propios`

Eval de la Fase 103 — patrón meta-documental del living-doc de errores
propios: frontmatter `note-type: error-log` (fuera de los 15 cerrados),
plantilla cerrada de 5 H4 (`Concepto` / `Comando erróneo` / `Corrección`
/ `Origen` / `Repaso`), lista cerrada de **16 frases de evaluación
personal prohibidas** en 4 categorías (autoestima negativa, autocrítica
emocional, exasperación, derrotismo), 3 scripts (`error_log_query.py`
con Q1-Q4; `error_cards.py` con C1-C4; `error_log_check.py` con R-E1
a R-E7), y AP16 extendido en `references/06-writing/anti-patterns.md`.

## Estructura

| Archivo / carpeta | Rol |
|---|---|
| `notes/error-log-good-postgresql.md` | **Positivo**: living-doc PostgreSQL con 3 entradas (ERROR-PG-001, ERROR-PG-002, ERROR-PG-003), verbatim de comandos y mensajes, `[[note:id]]` canónico, `review-next` vencido para PG-001. |
| `notes/error-log-good-docker.md` | **Positivo**: living-doc Docker con 2 entradas (ERROR-DOCKER-001, ERROR-DOCKER-002), comandos y correcciones verbatim. |
| `notes/error-log-bad-autocritica.md` | **Negativo**: entrada con "soy malo en X" en `### Concepto` (falla R-E5 / AP16). |
| `notes/error-log-bad-no-fundamento.md` | **Negativo**: entrada sin `[[note:id]]` en `### Corrección` (falla R-E4). |
| `notes/error-log-bad-no-repaso.md` | **Negativo**: entrada sin `### Repaso` + `review-next` (falla R-E3). |
| `notes/error-log-bad-verbatim-modificado.md` | **Negativo**: comando erróneo en prosa en lugar de bloque `:::code` (falla R-E2). |
| `build_fixtures.py` | Regenera las 6 notas inline. Idempotente; `--force` regenera. |
| `run_eval.py` | Batería de 16 sub-criterios (3 ROADMAP + 3 estructura + 3 scripts + 1 negativos + 3 density/wirings + 3 derivados). |

## Modo de uso

```bash
# Regenera fixtures y ejecuta el eval.
python3 evals/error-log-sample/build_fixtures.py --force
python3 evals/error-log-sample/run_eval.py

# Solo evalúa (asume fixtures ya generadas).
python3 evals/error-log-sample/run_eval.py
```

## Batería (16 sub-criterios)

### Criterios ROADMAP (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C1** | La consulta de repaso vencido funciona donde hay soporte | `error_log_query.py --due --domain postgresql` devuelve ≥ 1 entrada vencida (alias de C7). |
| **C2** | Los errores registrados pueden generar tarjetas | `error_cards.py --domain postgresql --format obsidian-sr` genera ≥ 1 tarjeta con tag `#priority-error` (alias de C8). |
| **C3** | La plantilla no contiene lenguaje de evaluación personal | `error_log_check.py --strict` pasa en los 2 living-docs buenos (C9) y falla en los 4 negativos (C10). |

### Estructura del doc (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C4** | `error-log.md` existe, ≤ 600 líneas, 9 secciones canónicas §1-§9 | Estructura del doc |
| **C5** | §3 plantilla NoteMark con los 5 H4 (`Concepto`, `Comando erróneo`, `Corrección`, `Origen`, `Repaso`) en orden | Forma de la entrada |
| **C6** | §4 lista cerrada ≥ 16 frases en 4 categorías | Criterio #3 ROADMAP (sin autocrítica) |

### Scripts (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C7** | `error_log_query.py --due --domain postgresql` devuelve ≥ 1 entrada vencida | Criterio #1 ROADMAP (consulta de repaso vencido) |
| **C8** | `error_cards.py --domain postgresql --format obsidian-sr` genera ≥ 1 tarjeta con tag `#priority-error` | Criterio #2 ROADMAP (tarjetas prioritarias) |
| **C9** | `error_log_check.py --strict` pasa en los 2 living-docs buenos | E1-E7 verificadas |

### Negativos (1)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C10** | `error_log_check.py --strict` falla en los 4 living-docs negativos | Casos negativos |

### Density + wirings (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **C11** | Las 6 notas fixture pasan `density_check.py --strict` exit 0 | R1-R8 F76 (con exención R3/R5/R8 en `## Resumen de errores` / `## Errores registrados`) |
| **C12** | Wirings cerrados: `SKILL.md §5.3` menciona `error-log.md`; `references/09-study/README.md` marca `error-log.md` como `publicado`; `references/06-writing/anti-patterns.md` §2 lista `AP16`; `references/05-note-types/error-troubleshooting.md` §6 lista `**F103-1**` + `**F103-2**`; `references/04-authoring/properties.md` §5.16 cita `F103` | Wirings |
| **C13** | `error_log_check.py --notes <dir>` (batch) pasa con 2 archivos buenos | Modo batch |

### Derivados (3)

| # | Sub-criterio | Verifica |
|---|---|---|
| **D1** | `wc -l error-log.md` ≤ 600 | INV-02 |
| **D2** | 9 secciones canónicas §1-§9 presentes | Estructura |
| **D3** | §4 lista cerrada ≥ 16 entradas (alias C6) | Lista cerrada |

## Salida esperada

```
PASS 16/16
  [PASS] C4
  [PASS] C5
  [PASS] C6
  [PASS] C7
  [PASS] C8
  [PASS] C9
  [PASS] C10
  [PASS] C11
  [PASS] C12
  [PASS] C13
  [PASS] D1
  [PASS] D2
  [PASS] D3
  [PASS] C1-roadmap-repaso-vencido
  [PASS] C2-roadmap-tarjetas-prioritarias
  [PASS] C3-roadmap-sin-autocritica
```

## Wirings (fases relacionadas)

- **F45** `references/04-authoring/block-directives.md` §10.4 — `:::code` se
  reutiliza para bloques verbatim del comando erróneo y la corrección.
- **F46** `references/04-authoring/inline-marks.md` — `{src:blk_xxxx}` y
  `[[note:id#§N]]` para el enlace canónico.
- **F47** `references/04-authoring/properties.md` §5.16 — `review-next`
  controla el scheduling por entrada.
- **F62** `scripts/render/flashcards.py` — F103 introduce el atributo
  `is_priority_card=true` (extensión compatible con D1) para inyectar
  las tarjetas prioritarias en el deck estándar.
- **F82** `references/05-note-types/error-troubleshooting.md` §6 —
  checklist extendido con `**F103-1**` y `**F103-2**`.
- **F98** `references/06-writing/paraphrase.md` §2 L1-L2 — el comando
  erróneo y la corrección son literales protegidos.
- **F100** `references/06-writing/anti-patterns.md` §2 — AP16 específico
  del registro de errores.
- **F101** `references/06-writing/i18n-and-citation.md` §3 — la lista
  de 45 no-traducibles se aplica al comando erróneo y a la corrección.
- **F102** `references/09-study/self-evaluation.md` §7 — F103 publica
  el segundo archivo de `09-study/`.

## Sin dependencias externas

Python 3.9+ stdlib puro + invocación de `density_check.py` (F76) y
`error_log_check.py` (F103). Las 6 notas se generan inline en
`build_fixtures.py` para evitar divergencia entre fixtures y la regla
que verifican.
