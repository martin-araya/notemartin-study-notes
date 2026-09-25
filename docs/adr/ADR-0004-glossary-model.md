# ADR-0004 — Modelo del glosario acumulativo (Fase 40)

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F40, INV-04 (separación de concerns), F15 (ledger como fuente), F37 (taxonomía)

## Contexto

Fase 40 debe formalizar el glosario acumulativo entre capítulos. `manifest.schema.json::glossary` (línea 33, 102-105) ya reserva un mapa `{term: description}`, pero esa estructura es insuficiente para los 3 criterios del roadmap:

1. Ningún término tiene dos definiciones canónicas.
2. Ningún alias apunta a dos términos.
3. Un término del capítulo 2 no se redefine en el 9.

El mapa plano de manifest no soporta aliases, no trackea chapters, y no permite historial de definiciones. La alternativa es crear `knowledge/glossary.json` con estructura rica.

Las alternativas consideradas:

1. **Reemplazar `manifest.glossary`** con la estructura rica — descarta: el manifest es state transient (counters), el glosario es knowledge acumulativo.
2. **Solo enricher `manifest.glossary`** sin crear archivo separado — descarta: el manifest ya tiene 5+ responsabilidades; añadirle aliases y definiciones rompe la cohesión.
3. **Crear `knowledge/glossary.json` separado** (elegida).

## Decisión

1. **`knowledge/glossary.json` separado del manifest**. Convive con `manifest.glossary` (que sigue siendo un mapa `{term: description}` para otros fines). El nuevo spec se enfoca en la estructura rica necesaria para los 3 criterios.

2. **Término canónico en kebab-case + sufijo `-<vendor>` en colisión** (decisión confirmada por el usuario en planning). Razón:
   - Coherencia con F39 (`concept_id` con misma regex).
   - Sufijo simple, legible, sin prefijo `vendor:` ni sub-glosarios por dominio.
   - Vendor se extrae del `source` del SDM (F34 provenance).

3. **Definitions array en lugar de single field**. Cada término tiene al menos una entrada; **exactamente una** con `canonical: true`. Las demás son `historical` (refinamiento legítimo) o `conflicting` (redefinición, criterio 3). Esto permite detectar redefiniciones sin rechazar refinamientos.

4. **Aliases con kind enum cerrada**: `en`, `es`, `acronym`, `plural`, `variant`. Razón: enum cerrada evita proliferación; extensible en versiones menores. El matching es case-insensitive sobre el string (R3): un mismo alias string no puede apuntar a dos términos aunque difieran en `kind`. El `kind` es metadata sobre el alias, no un desambiguador.

5. **No hay script de mantenimiento en la skill**. Razón: la lógica de "¿este texto es un alias conocido?" es semántica; el spec la guía (matching CI contra canonical + aliases), pero la decisión de cuándo propagar el canónico retroactivamente es del agente. Coherente con F15/F37/F39 donde el agente decide; el script contabiliza/verifica.

6. **`needs_review: true` no bloquea**. Coherente con F39: la decisión humana (rechazar, refinar, descartar) queda fuera del script. El eval marca el problema; el agente decide.

7. **Schema `glossary.schema.json` aditivo** — `additionalProperties: false` en root y en cada `$defs/term`/`alias`/`definitionEntry`. Cambios incompatibles → versión mayor.

## Consecuencias

**Gana**:
- Los 3 criterios del roadmap son verificables algorítmicamente por el eval.
- El glosario crece entre capítulos sin perder historial.
- Las colisiones entre dominios se resuelven con sufijo sin perder información.
- El agente tiene una guía clara de qué hacer cuando introduce un término.

**Pierde**:
- Dos archivos (`manifest.glossary` y `glossary.json`) podrían confundirse. Mitigado por documentación clara: `manifest.glossary` es contador/preview; `glossary.json` es knowledge.
- Sin script de mantenimiento, la calidad depende de la disciplina del agente. Mitigado por F43 auditoría + F118 evals.

**Queda atado**:
- F15: el `content.term` introducido en F37 es la fuente para poblar el glosario.
- F39: `related_concepts` referencia `concept_id` del grafo.
- F44: note-plan consulta el glosario para normalizar términos en las notas.
