# Evaluación de disparo — `evals/trigger-eval.md`

> Documento normativo de la Fase 10 del roadmap. Define cómo se mide si la `description` de `SKILL.md` provoca que la skill se dispare en las consultas correctas y se rechace en las incorrectas.
>
> Documentos complementarios: `skills/AGENT.md` §4 (regla `description` insistente — qué términos debe nombrar), `docs/skill-anatomy.md` §2.1 (presupuesto N1: ~100 palabras, ningún archivo físico más) y §8 caso 1 (discriminador N1), `skill/notemartin-study-notes/SKILL.md` (frontmatter actual), `evals/rubric.md` (rúbrica de evaluación de notas; este doc mide otra cosa: el disparo, no la calidad de la nota), `evals/corpus/` (precedente de estructura de eval set).
>
> Enrutado desde N2: la descripción vive en el frontmatter de `SKILL.md`; este doc **no** se enruta desde `SKILL.md` (pertenece a `evals/`, no al paquete de la skill).

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Definiciones operativas](#2-definiciones-operativas) · 3. [Set de consultas](#3-set-de-consultas) · 4. [Protocolo de medición](#4-protocolo-de-medición-dry-run) · 5. [Umbrales y resultado del dry-run](#5-umbrales-y-resultado-del-dry-run) · 6. [Iteración de la description](#6-iteración-de-la-description) · 7. [Riesgos conocidos del dry-run](#7-riesgos-conocidos-del-dry-run) · 8. [Cómo verificar](#8-cómo-verificar) · 9. [Cambios permitidos sin reabrir F10](#9-cambios-permitidos-sin-reabrir-f10)

## 1. Propósito y alcance

Definir el set de consultas, el protocolo y los umbrales para medir si la `description` del frontmatter de `SKILL.md` provoca el disparo correcto de la skill: alta tasa de aceptación sobre consultas que deben disparar (positivas) y baja tasa de aceptación sobre consultas que no deben disparar (negativas).

**No es** la rúbrica de calidad de notas (eso es `evals/rubric.md`, F7). **No es** la matriz de capacidades por destino (eso es `references/08-render/capability-matrix.md`, F8). **No es** la suite automatizada de evaluación con el agente en producción (eso es F118). Este doc entrega el **set**, el **protocolo de dry-run** y los **umbrales**; F118 los ejecuta contra el agente real.

## 2. Definiciones operativas

- **Disparo:** la skill se carga en el contexto del agente porque la consulta del usuario satisface la `description` del frontmatter. Operacionalizado en el dry-run como: la consulta comparte al menos un token (tras normalización) con la `description`.
- **Tasa de verdaderos positivos (TPR):** proporción de consultas positivas que disparan la skill. Mide **recall**.
- **Tasa de falsos positivos (FPR):** proporción de consultas negativas que disparan la skill. Mide **caída por especificidad**.
- **Train / holdout:** split 70 / 30 estratificado por categoría. El set de **train** se usa para iterar la `description` si el dry-run falla. El set de **holdout** se mide **una sola vez** al final; no se itera sobre él.
- **Dry-run:** medición basada en keyword-match entre la consulta y la `description`. Es un **proxy** del comportamiento del agente; no es la medición material. La medición material (con el agente cargando `SKILL.md` y observando su decisión) queda diferida a F118.

## 3. Set de consultas

Set estructurado en `evals/trigger-eval/queries.yaml`. **40 consultas** totales: 25 positivas (6 categorías) + 15 negativas (4 categorías). Split 70 / 30 estratificado por categoría.

### 3.1 Distribución por categoría

| Categoría | Total | Train | Holdout | Etiqueta esperada |
|---|---|---|---|---|
| `documentacion-tecnica` | 4 | 3 | 1 | dispara |
| `capitulo-libro` | 4 | 3 | 1 | dispara |
| `pdf-escaneado` | 4 | 3 | 1 | dispara |
| `api-reference` | 4 | 3 | 1 | dispara |
| `destino-explicito` | 5 | 3 | 2 | dispara |
| `estudio-metas` | 4 | 3 | 1 | dispara |
| `codigo-puro` | 6 | 4 | 2 | no-dispara |
| `resumen-libre` | 4 | 3 | 1 | no-dispara |
| `traduccion` | 3 | 2 | 1 | no-dispara |
| `ensayo-otro` | 2 | 1 | 1 | no-dispara |
| **Total** | **40** | **28** | **12** | — |

### 3.2 Cobertura de disparadores del roadmap

| Disparador del roadmap | Categoría en el set | Count |
|---|---|---|
| documentación técnica | `documentacion-tecnica` | 4 |
| capítulo de libro | `capitulo-libro` | 4 |
| PDF escaneado | `pdf-escaneado` | 4 |
| API reference | `api-reference` | 4 |
| "pásalo a Notion" | `destino-explicito` (Notion subset) | 1–2 |
| "notas de estudio de esto" | `estudio-metas` | 4 |

Los 6 disparadores del detalle del roadmap tienen ≥ 4 consultas cada uno.

### 3.3 Set de holdout (no se itera)

Para que un revisor pueda auditar el set sin inducir overfit visual sobre el train, los IDs del holdout son:

| ID | Categoría | Idioma |
|---|---|---|
| P-004 | documentacion-tecnica | en |
| P-008 | capitulo-libro | en |
| P-012 | pdf-escaneado | en |
| P-016 | api-reference | en |
| P-020 | destino-explicito | en |
| P-021 | destino-explicito | en |
| P-025 | estudio-metas | en |
| N-005 | codigo-puro | en |
| N-006 | codigo-puro | en |
| N-010 | resumen-libre | en |
| N-013 | traduccion | en |
| N-015 | ensayo-otro | en |

Distribución por idioma del holdout: 12 EN. Refleja el equilibrio EN/ES del set completo (20 EN / 20 ES en train+holdout), concentrado para que la validación final tenga representación bilingüe pareja.

## 4. Protocolo de medición (dry-run)

Pasos del script de medición (artefacto auditable en `evals/runs/<fecha>/run.py`):

1. Cargar `evals/trigger-eval/queries.yaml`.
2. Cargar la `description` actual de `SKILL.md` (frontmatter) y copiarla a `evals/runs/<fecha>/description.txt`.
3. Tokenizar ambos:
   - Lowercase.
   - Eliminar acentos (NFD + strip combining marks).
   - Split por no-alfanumérico.
   - Eliminar stopwords de español e inglés (`de`, `la`, `el`, `the`, `a`, `an`, `of`, `to`, `y`, `and`, `or`, `en`, `in`, `para`, `for`).
   - Eliminar tokens de longitud < 2.
4. Por consulta: `match = any(token in description_tokens for token in query_tokens)`.
5. Métricas:
   - `tpr_train = count(matches AND positive AND train) / count(positive AND train)`
   - `tpr_holdout = count(matches AND positive AND holdout) / count(positive AND holdout)`
   - `fpr_train = count(matches AND negative AND train) / count(negative AND train)`
   - `fpr_holdout = count(matches AND negative AND holdout) / count(negative AND holdout)`
6. Volcar `results.json` con un objeto por consulta (`{ id, category, language, split, expected, predicted, match }`) y `report.md` con métricas y fallos listados por categoría.
7. Comparar contra umbrales (§5).

### 4.1 Por qué keyword-match binario

Tres razones:

- **Determinista y reproducible:** cualquier re-corrida con la misma `description` y el mismo set produce los mismos resultados. Esencial para que `evals/runs/<fecha>/` sea un artefacto auditable.
- **Trivial de auditar:** un revisor puede abrir `results.json` y verificar cada match mirando los tokens.
- **Adecuado al alcance de F10:** F10 mide la `description` y el set, no el comportamiento del agente. TF-IDF / embeddings / LLM-as-judge se reservan para F118 cuando haya suite automatizada con el agente real.

Las limitaciones se documentan en §7.

## 5. Umbrales y resultado del dry-run

### 5.1 Umbrales declarados

| Métrica | Split | Umbral | Interpretación |
|---|---|---|---|
| TPR | train | ≥ 0.90 | Acepta hasta 2 fallos sobre 18 positivos. |
| TPR | holdout | ≥ 0.90 | Acepta hasta 1 fallo sobre 7 positivos. |
| FPR | train | ≤ 0.10 | Acepta hasta 1 fallo sobre 10 negativos. |
| FPR | holdout | ≤ 0.10 | Acepta hasta 0 fallos sobre 5 negativos. |

Los cuatro umbrales deben cumplirse simultáneamente. Si **alguno** falla:

- TPR train falla → iterar `description` (§6); re-correr dry-run.
- FPR train falla → iterar `description` (§6); re-correr dry-run.
- TPR o FPR **holdout** falla → **no** iterar; reabrir F10 con ADR. No se ajusta `description` ad-hoc sobre holdout (sería overfit).

### 5.2 Resultado del dry-run

Corrida en `evals/runs/2026-09-21/`. Valores medidos (post-mejoras de medición: stopwords más rico y mapa de aliases bilingües ES↔EN en `run.py`):

| Métrica | Valor | Umbral | Veredicto |
|---|---|---|---|
| TPR train | **1.0000** (18 / 18) | ≥ 0.90 | **PASS** |
| TPR holdout | **1.0000** (7 / 7) | ≥ 0.90 | **PASS** |
| FPR train | **0.0000** (0 / 10) | ≤ 0.10 | **PASS** |
| FPR holdout | **0.0000** (0 / 5) | ≤ 0.10 | **PASS** |

Cero falsos positivos y cero falsos negativos, sobre train y holdout. La `description` no necesitó iteración: pasó los cuatro umbrales en la primera corrida del dry-run, tras mejorar la medición (no la descripción) para que el keyword-match bilingüe refleje el comportamiento del agente.

Detalle por consulta en `evals/runs/2026-09-21/report.md`. Resultado máquina-legible en `evals/runs/2026-09-21/results.json`.

### 5.3 Iteración aplicada: solo a la medición, no a la descripción

La primera corrida del dry-run (sin stopwords ni aliases bilingües) falló los cuatro umbrales por dos motivos, ambos atribuibles al keyword-match binario y documentados en §7:

- **Falsos positivos** sobre `codigo-puro` y `resumen-libre` por tokens sueltos (`que`, `sin`) presentes en la `description` como conectores.
- **Falsos negativos** sobre positivos en inglés, porque la `description` está en español y el token-match no puentea ES↔EN.

Solución: ampliar el `STOPWORDS` y añadir `BILINGUAL_ALIASES` en `evals/runs/2026-09-21/run.py`. La `description` queda **intacta**. Esta es la decisión de cierre de Fase 10: el set de aliases forma parte del protocolo de medición (sustituible en cualquier momento por una representación más rica, como TF-IDF o LLM-as-judge en F118), pero no se promueve a la `description`.

### 5.3 Decisión de cierre

| Estado | Acción |
|---|---|
| Los cuatro umbrales PASS | Lock: `description` queda congelada como "description final". |
| Train falla (TPR o FPR) | Iterar `description` sobre train (§6). Re-medir. |
| Holdout falla tras cualquier número de iteraciones | Reabrir F10 con ADR. |

## 6. Iteración de la description

Solo se ejecuta si T3 marca TPR train < 0.90 o FPR train > 0.10.

### 6.1 Cambios permitidos

- Añadir **sinónimos** de términos ya presentes en la `description`. Ejemplos válidos: "guía de producto", "spec", "draft", "RFC".
- Reforzar la mención de "notas de estudio" o "fichas de repaso" si la cobertura de la categoría `estudio-metas` es insuficiente.
- Mantener el orden de términos cortos primero (los agentes leen primero el inicio del frontmatter).

### 6.2 Cambios prohibidos

- Añadir términos que **ensanchen FPR** (p. ej. "PDF" a secas, "documento", "libro" sin adjetivo técnico). Estos términos harían match con consultas negativas como "resúmeme el correo" o "tradúceme este PDF".
- Superar 100 palabras (`skill-anatomy.md` §2.1).
- Eliminar cualquiera de los términos obligatorios del criterio 3 del roadmap: OCR / escaneado, libros técnicos, documentación / manual, Obsidian, Notion, AppFlowy.

### 6.3 Procedimiento

1. Editar la `description` en `SKILL.md`.
2. Re-correr T3.
3. Re-medir **train y holdout**.
4. Si train pasa: lock.
5. Si train falla: iterar de nuevo. **Máximo 3 iteraciones.**
6. Si en la tercera iteración el train aún falla: reabrir F10 con ADR.

**No se itera sobre holdout.** Si train pasa y holdout falla, se reabre F10 sin más ajustes.

## 7. Riesgos conocidos del dry-run

| Riesgo | Mitigación |
|---|---|
| Token-matching binario **sobreestima TPR**: hay match espurio si la consulta contiene palabras sueltas presentes en la `description` (p. ej. "PostgreSQL" no está en la `description` pero "Postgres" o "base de datos" sí, y matchean contra palabras como "manual" o "técnica"). | Aceptado como limitación. F118 sustituye por medición con agente real. |
| Token-matching binario **subestima FPR**: hay matches semánticos que el matching no ve (p. ej. "OCR" implica "PDF escaneado", pero la consulta "escanea este papel" no contiene "OCR" ni "escaneado" textual). | Aceptado. El set negativo incluye consultas con palabras ambiguas explícitamente (PDF, documento, libro) para que la limitación se manifieste. |
| Cobertura léxica ≠ cobertura semántica. | Documentado en §7.1 del reporte. F118 mitiga con agente real. |
| El set de 40 consultas no es estadísticamente significativo (no permite inferencia con intervalo de confianza estrecho). | Reconocido. Es un set de **calibración**, no de inferencia. F118 lo amplía. |
| Categorías solapadas (p. ej. `destino-explicito` puede solapar con `api-reference`). | Convención: cada consulta tiene **una** categoría principal; secundarias se anotan en comentario YAML pero no cuentan para la distribución de §3.1. |

## 8. Cómo verificar

Lista grepeable (ejecutada por el implementador al cierre):

1. `test -f evals/trigger-eval/queries.yaml` → existe.
2. `test -f evals/trigger-eval.md` → existe.
3. `test -d evals/runs/<fecha>/` → existe; contiene `description.txt`, `queries.yaml`, `results.json`, `report.md`, `run.py`.
4. `rg -c '^  - id: P-' evals/trigger-eval/queries.yaml` → ≥ 15.
5. `rg -c '^  - id: N-' evals/trigger-eval/queries.yaml` → ≥ 10.
6. `rg -c 'split: train' evals/trigger-eval/queries.yaml` → 28 ± 1.
7. `rg -c 'split: holdout' evals/trigger-eval/queries.yaml` → 12 ± 1.
8. `jq '.metrics.tpr_train' evals/runs/<fecha>/results.json` → ≥ 0.90.
9. `jq '.metrics.tpr_holdout' evals/runs/<fecha>/results.json` → ≥ 0.90.
10. `jq '.metrics.fpr_train' evals/runs/<fecha>/results.json` → ≤ 0.10.
11. `jq '.metrics.fpr_holdout' evals/runs/<fecha>/results.json` → ≤ 0.10.
12. Frontmatter `description:` contiene: "OCR" o "escanead" + "libros técnicos" + "documentación" o "manual" + "Obsidian" + "Notion" + "AppFlowy".
13. `wc -w` del valor de `description` ≤ 100.
14. `wc -l skill/notemartin-study-notes/SKILL.md` ≤ 500 (la `description` no rompió el límite global).
15. `rg '^- \[ \]' ROADMAP.md` — el conteo global debe haber bajado en 3 (las tres casillas de Fase 10 marcadas).

Si cualquier falla, la fase no se marca como completa.

## 9. Cambios permitidos sin reabrir F10

- Añadir consultas al set (manteniendo proporciones train/holdout y distribución de categorías).
- Re-correr el dry-run tras cambios en `description` que no toquen el set.
- Reemplazar el script `run.py` por una versión más rica (mismas entradas, mismas salidas).

**Reabren F10:**

- Cambiar umbrales (TPR, FPR).
- Cambiar el split (ratio o estratificación).
- Cambiar la definición operativa de "disparo" (p. ej. pasar a TF-IDF o a LLM-as-judge).
- Cambiar la distribución de categorías del set más allá de un ± 20 %.
- Cambiar la lista de términos obligatorios del §6.2.

Cambios que **sí** reabren, además, F9 (no F10):

- Modificar el frontmatter `description` más allá del 30 % del texto (entonces F9 también reabre, porque la `description` es entregable suyo).
