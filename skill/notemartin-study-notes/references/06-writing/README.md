# `references/06-writing/`

Reglas de redacción: intuición, analogías, ejemplos, comparaciones, parafraseo, voz, anti-patrones.

## Orden de lectura

Cargar al redactar prosa en L3.

## Estado actual

Materializados:

- `intuition-first.md` F94 — patrón de 5 etapas (Problema → Intuición → Analogía → Definición formal → Confirmación), excepción `reference-pure` acotada, 10 señales de diagnóstico algorítmicas, ejemplos BD (MVCC) + redes (TCP 3WHS).
- `analogies.md` F95 — catálogo de 12 patrones (P1-P12), banco reutilizable de 18 entradas (E1-E18) con `Rotura:` explícito en cada una, regla universal de rotura, árbol de decisión, 8 anti-patrones.
- `executable-examples.md` F96 — mínimo reproducible (Setup → Acción → Resultado → Limpieza), 3 plantillas canónicas (DB / redes / CLI), 3 niveles de escalado (mínimo / realista / límite), 8 anti-ejemplos (NE1-NE8), cabecera `> **Entorno:**` con 4 campos cerrados, 10 señales de diagnóstico algorítmicas.
- `comparisons.md` F97 — 5 formas canónicas (F1 tabla lado a lado / F2 jerarquía por relajación / F3 matriz de decisión / F4 tabla de trade-offs / F5 párrafo de síntesis), 3 plantillas (DB / protocolos / arquitectura), 5 marcas de comparación derivada, 8 anti-patrones, 10 señales algorítmicas.
- `paraphrase.md` F98 — lista cerrada de 8 tipos de literales protegidos (L1-L8), técnica de enumeración de unidades en 4 pasos, tabla de 13 reformulaciones prohibidas (P1-P13), 7 anti-patrones (AP1-AP7), 3 verificaciones algorítmicas V1-V3 (INV-09 + INV-10 normativizados).
- `voice-style.md` F99 — 8 reglas verificables R1-R8 (frases cortas, voz activa, sin adjetivos valorativos, sin relleno, segunda persona en procedimientos, tiempos consistentes, sin nominalizaciones, sin subjuntivo dudoso), lista cerrada de 20 adjetivos valorativos V1-V20, tabla de persona por 13 secciones, 8 anti-patrones AP1-AP8, plantilla de verificación con 8 preguntas binarias.
- `anti-patterns.md` F100 — 12 anti-patrones transversales AP1-AP12 (transcripción disfrazada, definición circular, callout decorativo, tabla de una fila útil, analogía sin mapeo, diagrama que repite el texto, enlace sin contexto, volcado de viñetas, marketing copiado, código sin caption, mermaid syntax error silencioso, sección vacía), 10 señales algorítmicas S1-S10, checklist de 12 items integrable en `concept.md §6`, referencias cruzadas a F94-F99.
- `i18n-and-citation.md` F101 — lista cerrada de **45 no-traducibles** en 8 categorías (12 identificadores PG, 8 parámetros CLI, 6 mensajes de error, 3 códigos HTTP, 6 comandos shell, 3 sintaxis de funciones, 3 versiones de protocolo, 4 headers HTTP), regla de idioma por `language` ∈ {`es`, `en`, `es-en`, `en-es`}, formato de **primera aparición bilingüe** `[[en:term]]` / `[[es:term]]` + glosario al pie, plantilla de **bloque de procedencia** al pie con 4 campos cerrados (Fuente / Versión / Fecha de recuperación / URL/anchor), 8 señales algorítmicas S1-S8, 7 anti-patrones AP1-AP7.

Pendientes:

(ninguno — el bloque 06 está completo).

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| [`intuition-first.md`](intuition-first.md) | Agente al redactar prosa pedagógica | F94 |
| [`analogies.md`](analogies.md) | Agente al elegir/crear analogía | F95 |
| [`executable-examples.md`](executable-examples.md) | Agente al redactar ejemplo ejecutable | F96 |
| [`comparisons.md`](comparisons.md) | Agente al construir comparación correcta | F97 |
| [`paraphrase.md`](paraphrase.md) | Agente al parafrasear preservando literales | F98 |
| [`voice-style.md`](voice-style.md) | Agente al aplicar voz y estilo consistentes | F99 |
| [`anti-patterns.md`](anti-patterns.md) | Agente y revisor al diagnosticar AP transversales | F100 |
| [`i18n-and-citation.md`](i18n-and-citation.md) | Agente bilingüe al redactar prosa i18n | F101 |

## Restricción

Sin ejemplos de ML o visión por computador (INV-15). Dominios válidos: bases de datos, redes, sistemas, documentación de producto, herramientas CLI, etc.
