# Rúbrica de evaluación — `evals/rubric.md`

> Documento normativo de la Fase 7 del roadmap. Define cómo se evalúa una nota del corpus sobre 8 dimensiones con niveles 0–4 y cómo se aplica por perfil (`study` / `reference` / `hybrid`).
>
> Documentos complementarios: `docs/product-manifesto.md` §3 (4 garantías con métrica y mecanismo), `references/00-pipeline/architecture.md` §8 (umbrales del modo degradado), `evals/corpus/coverage.md` (qué categorías cubre el corpus), `AGENT.md` §11 (Pruebas). Este doc los **referencia y completa**, no los repite.

## Índice

1. [Propósito y alcance](#1-propósito-y-alcance) · 2. [Definiciones previas](#2-definiciones-previas) · 3. [Las 8 dimensiones](#3-las-8-dimensiones--niveles-04) · 4. [Pedagogía por perfil](#4-redefinición-de-pedagogía-por-perfil) · 5. [Pesos y mínimos](#5-pesos-y-mínimos-por-perfil) · 6. [Puntuación global](#6-puntuación-global) · 7. [Anclas de calibración](#7-anclas-de-calibración) · 8. [Test criterio 1 (inter-rater)](#8-test-del-criterio-1--inter-rater) · 9. [Test criterio 2](#9-test-del-criterio-2--no-penalizar-referencia-pura) · 10. [Test criterio 3](#10-test-del-criterio-3--dimensión-de-render-existe) · 11. [Cambios permitidos](#11-versión-y-cambios-permitidos)

## 1. Propósito y alcance

Definir cómo se evalúa una nota del corpus sobre 8 dimensiones con niveles 0–4, con el objetivo de cerrar la variabilidad entre evaluadores y permitir la comparación entre iteraciones de la skill.

**No es** el catálogo de checks automatizados (F112), no es el reporte de calidad (F115), no es la suite de evals automatizada (F118), no es la suite de tests de los scripts (que vive en `tests/`). La rúbrica se aplica por humanos o por agentes que simulan evaluación humana; los scripts de `evals/` automatizan solo las dimensiones marcadas como "Detección automática: sí".

## 2. Definiciones previas

- **Nota evaluada:** archivo `notemark/<note-id>.nm` con su `ir/<note-id>.json` correspondiente y, opcionalmente, su `render/<destino>/...`.
- **Perfil:** declarativo en `profile.yaml.targets.use_case_profile ∈ {study, reference, hybrid}`; indica el uso primario de la nota.
- **Ancla:** ejemplo anotado con puntuación esperada; sirve para calibrar evaluadores antes de una ronda.
- **Evaluador:** agente o humano que asigna niveles 0–4 a una nota siguiendo §3.
- **Ronda:** ejecución completa de evaluación sobre un conjunto de notas (≥ 5).

## 3. Las 8 dimensiones — niveles 0–4

Conducta observable, no adjetivos. Las dimensiones marcadas como "Detección automática" pueden ser verificadas por un script del proyecto (F38, F43, F49, F52, F63, F114).

### 3.1 Fidelidad — invariante por perfil

| Nivel | Conducta observable |
|---|---|
| 0 | ≥ 1 valor numérico, nombre de parámetro, código de error o comando inventado (ausente del SDM). |
| 1 | ≥ 1 unidad `must-keep` omitida o mutilada. |
| 2 | Sin invenciones ni omisiones; ≥ 1 unidad reescrita cuando era exigible literal (mensaje de error, default, sintaxis, comando). |
| 3 | Fidelidad plena en unidades `must-keep`; ≥ 1 unidad `context` aproximada. |
| 4 | 100 % unidades con `source_ref` resoluble, 0 invenciones, 0 reescrituras de literales, todas las unidades `context` también con respaldo. |

**Detección automática:** sí (F114).

### 3.2 Cobertura — invariante por perfil

| Nivel | Conducta observable |
|---|---|
| 0 | ≥ 30 % de secciones del SDM sin nota asignada en el ledger. |
| 1 | 10–30 % de secciones sin nota asignada, o con descarte sin motivo de la lista cerrada. |
| 2 | Cobertura ≥ 90 %; todos los descartes con motivo en la lista cerrada. |
| 3 | 100 % `must-keep` con estado terminal; ≤ 5 % unidades `context` omitidas justificadamente. |
| 4 | 100 % `must-keep` con estado terminal; 100 % `context` también asignadas; el reporte responde "¿dónde quedó la sección X.Y.Z?" en una consulta. |

**Detección automática:** sí (F38, F43).

### 3.3 Trazabilidad — invariante por perfil

| Nivel | Conducta observable |
|---|---|
| 0 | ≥ 1 nodo fáctico del IR sin `source_ref`. |
| 1 | ≥ 1 `source_ref` que no resuelve a un bloque del SDM. |
| 2 | Todos los `source_ref` resuelven; ≥ 1 nodo derivado (`derived` o `external`) sin marcado. |
| 3 | Trazabilidad fáctica completa; ≥ 1 enlace bidireccional (nodo↔bloque) ausente en la consulta inversa. |
| 4 | Cada nodo fáctico con `source_ref` resoluble; cada bloque del SDM con unidad asociada aparece en ≥ 1 nota; consulta inversa funciona para todo bloque. |

**Detección automática:** sí (F52).

### 3.4 Pedagogía — **redefinida por perfil** (criterio 2)

Ver §4. En `study`: presencia de elementos pedagógicos. En `reference`: claridad expositiva. En `hybrid`: media 50/50.

### 3.5 Estructura — invariante con ajuste mínimo por perfil

| Nivel | Conducta observable |
|---|---|
| 0 | Sin jerarquía de secciones; ≥ 2 secciones sin encabezado; plantilla del tipo de nota no aplicada. |
| 1 | Jerarquía básica; ≥ 1 desviación mayor de la plantilla del tipo (sección obligatoria ausente). |
| 2 | Estructura conforme al tipo; ≥ 1 desviación menor (orden de sección o sección opcional faltante). |
| 3 | Estructura conforme + capas L1/L2/L3 identificables en notas extensas (≥ 3 secciones). |
| 4 | Estructura conforme + capas aplicadas + checklist propio del tipo cumplido + índice o rutas de lectura presentes. |

**Detección automática:** parcial (F49 + F112).

### 3.6 Componentes — invariante por perfil

| Nivel | Conducta observable |
|---|---|
| 0 | Sin tablas, código o diagramas en temas que los requieren (definidos por tipo de nota en §5-note-types). |
| 1 | ≥ 1 componente crítico ausente (tabla de parámetros sin tabla, error-troubleshooting sin árbol de diagnóstico). |
| 2 | Componentes presentes; ≥ 1 redundante o subutilizado. |
| 3 | Componentes conformes al tipo; ≥ 1 sin marcaje de fuente visible (`{src:...}` ausente). |
| 4 | Componentes conformes + todos con marcaje de fuente + jerarquía visual coherente con tokens (`assets/tokens.json`). |

**Detección automática:** parcial.

### 3.7 Utilidad operativa — **redefinida por perfil** (criterio 2)

Ver §4. En `study`: preguntas + rutas de repaso + flashcards. En `reference`: búsqueda + backlinks + propiedades. En `hybrid`: media 50/50.

### 3.8 Fidelidad de render — **distinta a fidelidad de contenido** (criterio 3)

| Nivel | Conducta observable |
|---|---|
| 0 | ≥ 1 destino con contenido faltante (no es degradación, es pérdida). |
| 1 | ≥ 1 destino con contenido truncado o ilegible. |
| 2 | Todos los destinos con contenido íntegro; ≥ 1 con degradación no documentada en `render-degradation.md`. |
| 3 | Render correcto en todos los destinos activos; degradaciones documentadas. |
| 4 | Render correcto + degradaciones documentadas + cero enlaces rotos + cero imágenes rotas + numeración, índices y callouts consistentes con tokens. |

**Detección automática:** sí (F63 cross_target, F61 linking).

## 4. Redefinición de pedagogía por perfil

Esta sección cierra el criterio 2 del roadmap. La dimensión "pedagogía" se evalúa con criterios distintos según el perfil.

### 4.1 Perfil `study`

| Nivel | Conducta observable |
|---|---|
| 0 | Sin intuición inicial; sin analogías; sin ejemplos. |
| 1 | ≤ 1 elemento pedagógico (analogía, ejemplo, comparación, intuición inicial). |
| 2 | ≥ 2 elementos pedagógicos, sin cierre con resumen o trampas. |
| 3 | ≥ 3 elementos pedagógicos + resumen + ≥ 1 trampa explícita. |
| 4 | ≥ 4 elementos pedagógicos (intuición inicial, analogía, ejemplo, comparación) + resumen + trampas + límites/cuando-NO-usarlo. |

### 4.2 Perfil `reference` — **no exige analogías**

| Nivel | Conducta observable |
|---|---|
| 0 | Prosa ambigua; ≥ 1 afirmación sin cuantificar; ≥ 1 sección sin orden lógico. |
| 1 | ≥ 1 sección con prosa imprecisa; ≥ 1 ambigüedad detectable en la lectura técnica. |
| 2 | Prosa precisa en todas las secciones; ≥ 1 sección con orden débil. |
| 3 | Prosa precisa + orden consistente + todas las secciones enlazadas internamente. |
| 4 | Prosa precisa + orden consistente + secciones enlazadas + terminología uniforme + cero redundancias. |

Una nota api-reference exhaustiva sin analogías puntúa alto en esta dimensión porque cumple los niveles 3–4 sin necesidad de elementos pedagógicos.

### 4.3 Perfil `hybrid`

Media aritmética 50/50 del nivel `study` y `reference`:
`nivel_hybrid = 0.5 × nivel_study + 0.5 × nivel_reference`.

Redondeo al entero más cercano (con `.5` → arriba). Si los dos perfiles discrepan por ≥ 2 niveles, se reabre la nota con justificación.

## 5. Pesos y mínimos por perfil

Pesos suman 1.0 por perfil. El mínimo por dimensión (0–4) es **siempre activo**: si una nota puntúa por debajo, **no** se aprueba aunque la media supere el umbral global.

### 5.1 Perfil `study`

| Dimensión | Peso | Mínimo |
|---|---|---|
| Fidelidad | 0.20 | 3 |
| Cobertura | 0.15 | 3 |
| Trazabilidad | 0.10 | 3 |
| Pedagogía (study) | 0.25 | 2 |
| Estructura | 0.10 | 2 |
| Componentes | 0.05 | 2 |
| Utilidad operativa (study) | 0.10 | 2 |
| Fidelidad de render | 0.05 | 2 |

Suma: **1.00**. Umbral global: **2.5**.

### 5.2 Perfil `reference`

| Dimensión | Peso | Mínimo |
|---|---|---|
| Fidelidad | 0.30 | 3 |
| Cobertura | 0.20 | 3 |
| Trazabilidad | 0.20 | 3 |
| Pedagogía (reference) | 0.10 | 2 |
| Estructura | 0.05 | 2 |
| Componentes | 0.10 | 2 |
| Utilidad operativa (reference) | 0.05 | 2 |
| Fidelidad de render | 0.00 | 2 |

Suma: **1.00**. Umbral global: **2.5**.

**Nota sobre peso 0:** la dimensión con peso 0 no contribuye a la media global, pero su mínimo se mantiene activo. Esto cierra la puerta: si render vale 0, no se aprueba la nota. Evita que un perfil "olvide" evaluar una dimensión cambiando el peso a 0.

### 5.3 Perfil `hybrid`

| Dimensión | Peso | Mínimo |
|---|---|---|
| Fidelidad | 0.25 | 3 |
| Cobertura | 0.175 | 3 |
| Trazabilidad | 0.15 | 3 |
| Pedagogía (híbrida) | 0.175 | 2 |
| Estructura | 0.075 | 2 |
| Componentes | 0.075 | 2 |
| Utilidad operativa (híbrida) | 0.075 | 2 |
| Fidelidad de render | 0.025 | 2 |

Suma: **1.000**. Umbral global: **2.5**.

## 6. Puntuación global

- Para cada dimensión: nivel 0–4 asignado por el evaluador (con anclas como referencia).
- Media ponderada = Σ (peso × nivel).
- Aprobada si: media ≥ 2.5 **y** ninguna dimensión por debajo de su mínimo por dimensión.
- Una nota aprobada en perfil `reference` puede tener pedagogía (reference) = 2 sin penalización global, porque la dimensión está definida por claridad expositiva, no por presencia de analogías.

## 7. Anclas de calibración

6 anclas, 2 por perfil. Cada ancla describe una nota del corpus (o un patrón del corpus) con la puntuación esperada por dimensión.

### ANC-01 — perfil `study`, nota `concept` con todos los elementos

- **Fuente:** patrón de `evals/corpus/02-database-internals-chapter`.
- **Contenido reducido:** nota `concept` sobre almacenamiento distribuido con: intuición inicial, analogía (libro mayor distribuido), ejemplo de Quorum, comparación con Raft, resumen, trampas explícitas (split-brain), cuándo NO usarlo.
- **Puntuación esperada:**

| Dimensión | Nivel |
|---|---|
| Fidelidad | 4 |
| Cobertura | 4 |
| Trazabilidad | 4 |
| Pedagogía (study) | 4 |
| Estructura | 4 |
| Componentes | 3 |
| Utilidad operativa (study) | 3 |
| Fidelidad de render | 3 |

- **Global ponderada:** 0.20·4 + 0.15·4 + 0.10·4 + 0.25·4 + 0.10·4 + 0.05·3 + 0.10·3 + 0.05·3 = 3.75. Aprobada.

### ANC-02 — perfil `study`, nota `procedure` sin analogías

- **Fuente:** patrón de `evals/corpus/07-docker-cli-ref`.
- **Contenido reducido:** nota `procedure` sobre `docker run` con: objetivo, precondiciones, 8 pasos numerados con comando + salida esperada + verificación, rollback, errores frecuentes. Sin analogías; cobertura completa.
- **Puntuación esperada:**

| Dimensión | Nivel |
|---|---|
| Fidelidad | 4 |
| Cobertura | 4 |
| Trazabilidad | 4 |
| Pedagogía (study) | 1 (sin analogías) |
| Estructura | 4 |
| Componentes | 4 |
| Utilidad operativa (study) | 3 |
| Fidelidad de render | 3 |

- **Global ponderada:** 0.20·4 + 0.15·4 + 0.10·4 + 0.25·1 + 0.10·4 + 0.05·4 + 0.10·3 + 0.05·3 = 3.10. Aprobada.

### ANC-03 — perfil `reference`, nota `api-reference` sin analogías (verifica criterio 2)

- **Fuente:** patrón de `evals/corpus/06-kubernetes-api-ref`.
- **Contenido reducido:** nota `api-reference` para Pod v1: propósito, tabla exhaustiva de parámetros (50+ filas), retornos, excepciones, precondiciones, ejemplo mínimo ejecutable, gotchas. Prosa precisa, terminología uniforme, secciones enlazadas, sin analogías.
- **Puntuación esperada:**

| Dimensión | Nivel |
|---|---|
| Fidelidad | 4 |
| Cobertura | 4 |
| Trazabilidad | 4 |
| Pedagogía (reference) | 4 (claridad expositiva; terminología uniforme) |
| Estructura | 4 |
| Componentes | 4 |
| Utilidad operativa (reference) | 4 |
| Fidelidad de render | 2 (peso 0; no aporta) |

- **Global ponderada:** 0.30·4 + 0.20·4 + 0.20·4 + 0.10·4 + 0.05·4 + 0.10·4 + 0.05·4 + 0.00·2 = 4.00. Aprobada con holgura. **Sin penalización por carecer de analogías.**

### ANC-04 — perfil `reference`, nota `configuration` densa en tablas

- **Fuente:** patrón de `evals/corpus/05-iso-sql-tables`.
- **Contenido reducido:** nota `configuration` para parámetros de PostgreSQL con: tabla canónica (ámbito, tipo, default, rango, modificable en caliente, requiere reinicio, versión), combinaciones peligrosas, interacciones, diagrama de dependencias. Terminología uniforme, índice.
- **Puntuación esperada:**

| Dimensión | Nivel |
|---|---|
| Fidelidad | 4 |
| Cobertura | 4 |
| Trazabilidad | 4 |
| Pedagogía (reference) | 3 |
| Estructura | 4 |
| Componentes | 4 |
| Utilidad operativa (reference) | 3 |
| Fidelidad de render | 2 |

- **Global ponderada:** 0.30·4 + 0.20·4 + 0.20·4 + 0.10·3 + 0.05·4 + 0.10·4 + 0.05·3 + 0.00·2 = 3.80. Aprobada.

### ANC-05 — perfil `hybrid`, nota `architecture` con diagrama

- **Fuente:** patrón de `evals/corpus/02-database-internals-chapter`.
- **Contenido reducido:** nota `architecture` sobre arquitectura de un motor: visión general con diagrama Mermaid, componentes y responsabilidades, flujo paso a paso, estructuras en memoria y disco, puntos de fallo, cuellos de botella. Cobertura completa.
- **Puntuación esperada:**

| Dimensión | Nivel |
|---|---|
| Fidelidad | 4 |
| Cobertura | 4 |
| Trazabilidad | 4 |
| Pedagogía (híbrida) | media(study=3, reference=4) = 3.5 → 4 |
| Estructura | 4 |
| Componentes | 4 |
| Utilidad operativa (híbrida) | media(study=2, reference=3) = 2.5 → 3 |
| Fidelidad de render | 3 |

- **Global ponderada:** 0.25·4 + 0.175·4 + 0.15·4 + 0.175·4 + 0.075·4 + 0.075·4 + 0.075·3 + 0.025·3 = 3.85. Aprobada.

### ANC-06 — perfil `study`, nota `chapter-digest` con cobertura parcial

- **Fuente:** patrón de `evals/corpus/02-database-internals-chapter`.
- **Contenido reducido:** nota `chapter-digest` que resume 60 % del capítulo: continuidad hacia atrás y adelante, conceptos nuevos enlazados a nota propia, mecanismos, código, énfasis del autor. Cobertura parcial justificada por descarte `out-of-scope-by-user` para el 40 % restante.
- **Puntuación esperada:**

| Dimensión | Nivel |
|---|---|
| Fidelidad | 4 |
| Cobertura | 3 (60 % justificado) |
| Trazabilidad | 4 |
| Pedagogía (study) | 3 |
| Estructura | 4 |
| Componentes | 3 |
| Utilidad operativa (study) | 3 |
| Fidelidad de render | 3 |

- **Global ponderada:** 0.20·4 + 0.15·3 + 0.10·4 + 0.25·3 + 0.10·4 + 0.05·3 + 0.10·3 + 0.05·3 = 3.35. Aprobada.

## 8. Test del criterio 1 — inter-rater ≤ 1 punto

**Procedimiento documentado** (ejecución material: F118):

1. Seleccionar 5 notas del corpus (1 por perfil: study, reference, hybrid + 2 adicionales).
2. Dos evaluadores independientes puntúan cada dimensión sin ver la puntuación del otro.
3. Cada evaluador pasa primero por las anclas (§7) para calibrarse.
4. Para cada dimensión y cada nota, calcular `|nivel_A − nivel_B|`.
5. Si para alguna dimensión la diferencia es > 1 en alguna nota, el test falla.
6. Si el test falla: reentrenamiento con anclas adicionales; si persiste, reabrir Fase 7 y reformular los descriptores de la dimensión.

El test es ejecutable, no necesariamente ejecutado en esta fase. La ejecución material se difiere a F118.

## 9. Test del criterio 2 — no penalizar referencia pura

**Ancla ANC-03** (perfil `reference`, nota `api-reference` exhaustiva sin analogías) tiene:

- Pedagogía (reference) = **4** (por claridad expositiva y terminología uniforme).
- Global ponderada = **4.00**.

Esta ancla demuestra el criterio: una nota de referencia pura sin analogías no es penalizada. La dimensión pedagogía en `reference` mide claridad, no presencia de analogías.

Verificación cruzada: ANC-04 (otra nota `reference` sin analogías) también aprueba con global ≥ 3.80, confirmando el patrón.

## 10. Test del criterio 3 — dimensión de render existe

La dimensión 8 (fidelidad de render) existe con criterios distintos a la dimensión 1 (fidelidad de contenido):

- **Fidelidad de contenido** (dimensión 1): presencia/ausencia de información fáctica fiel a la fuente.
- **Fidelidad de render** (dimensión 8): presencia/ausencia de degradaciones en la salida por destino; enlaces e imágenes rotas; consistencia con tokens.

Las dos dimensiones son ortogonales: una nota puede tener fidelidad de contenido = 4 y fidelidad de render = 0 (toda la información correcta pero el renderer truncó la mitad en Notion). El peso 0 en `reference.render` solo afecta la media global; el mínimo 2 sigue activo.

## 11. Versión y cambios permitidos

**Versión:** 1.0 — cierre de Fase 7.

**Reabren Fase 7:**

- Cambiar una dimensión (nombre, definición, niveles).
- Cambiar pesos o mínimos por perfil.
- Modificar las anclas (más allá de añadir; modificar cambia el contrato de calibración).
- Cambiar la redefinición de pedagogía por perfil.

**No reabren:**

- Añadir nuevas anclas (extensión, no modificación).
- Añadir dimensiones nuevas (F112 puede proponer; el cambio se decide en una fase posterior con su propia rúbrica).
- Ajustar ejemplos dentro de una dimensión sin cambiar los niveles.
