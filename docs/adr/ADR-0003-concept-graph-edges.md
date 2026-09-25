# ADR-0003 — Fuente de nodos y aristas del grafo de prerrequisitos

**Fecha:** 2026-09-25
**Estado:** aceptada
**Atada a:** F39, F37 (information-units), F34 (provenance)

## Contexto

Fase 39 necesita producir `knowledge/concept-graph.json` a partir del ledger (F15/F38) y del SDM (F13). Tres decisiones que afectan al resto del proyecto:

1. **¿De dónde salen los nodos?** Candidatos:
   - (a) Unidades `type=definition` del ledger — disciplina de fuente única.
   - (b) Bloques `prose` con "X es Y" — heurística ruidosa, muchos falsos positivos.
   - (c) Un nuevo tipo de bloque `concept` en el SDM — invierte la disciplina: el SDM se vuelve fuente directa del grafo, no proyección.
2. **¿De dónde salen las aristas (prerequisites)?** Candidatos:
   - (a) Implícito por orden de sección — automático pero ruidoso.
   - (b) Explícito vía `cross-reference` con `relation: "prerequisite"` — limpio y auditable, requiere que el agente lo declare.
   - (c) Híbrido: primario (b) + heurística secundaria que sugiere sin crear.
3. **¿Qué es un dominio?** Candidatos:
   - (a) `vendor+product` del SDM (F34 provenance).
   - (b) Top-level de `section_path` (e.g. `/ch01`).
   - (c) `source.id`.

Decisión confirmada por el usuario en la fase de planning: **aristas solo desde `cross-reference` con `relation: prerequisite`** (opción 2a pura).

## Decisión

1. **Nodos solo desde unidades `type=definition` del ledger** (opción 1a). Razón: un concepto requiere definición explícita. Coherente con F37 §3 que define `definition` como "Enunciado que define un término técnico o del dominio". `prose` por convención de F13 es no-unidad.

2. **Aristas solo desde `cross-reference` con `content.relation="prerequisite"`** (opción 2a confirmada por usuario). Razón:
   - Disciplina de fuente única: ledger es verdad, grafo es derivado.
   - Auditabilidad: cada arista tiene `source_unit_id` trazable.
   - Cero falsos positivos: si el agente no lo declara, no existe.
   - Coste: el agente debe declarar cada prerrequisito.

3. **Dominio = `vendor+product`** del SDM, fallback `"unknown"` (opción 3a). Razón: coincide con la noción de "obra" del corpus (F6 corpus, F34 provenance); las rutas se generan por obra, no por capítulo.

4. **Dos rutas por dominio: shortest (Dijkstra) + broadest (DFS con poda por out_degree)**. Criterio 3 del roadmap exige "al menos dos rutas por dominio"; las dos estrategias cubren el caso "ir al goal por el camino más corto" y "conocer más contexto en el camino".

5. **Export Mermaid `flowchart LR`** (no DOT/Graphviz). Convención del proyecto (F4, F12, F65). Mantiene INV-06 (sin sintaxis de plataforma de render).

6. **`concept-graph.schema.json` vive en `schemas/` por consistencia**, pero se documenta como derivado del ledger. Modificarlo a mano no reabre F39; el script lo regenera.

7. **`_atomic_write_json` extraído a `scripts/util/_io.py`** y compartido con `ledger.py` (F38). Evita la duplicación que el review de F38 marcó como riesgo.

## Consecuencias

**Gana**:
- El grafo es siempre coherente con el ledger; si el ledger cambia, `concept_graph.py build` regenera.
- Las decisiones de qué es un concepto y qué es un prerrequisito quedan en manos del agente, no de heurísticas opacas.
- F44 (note-plan) puede consumir el grafo con confianza; el orden topológico es correcto por construcción.

**Pierde**:
- El agente tiene más trabajo: declarar cada `definition` y cada `cross-reference` con `relation`.
- Si el corpus tiene muchos conceptos implícitos sin declaración, el grafo queda incompleto. Mitigado por F43 (auditoría) que detecta dominios con cobertura baja.

**Queda atado**:
- F37 §3: tipo `definition` debe estar presente en el ledger para que aparezca en el grafo.
- F38: las unidades `cross-reference` deben llevar `content.relation` y `content.target_concept` para que produzcan aristas.
- F34: el SDM debe llevar `vendor` y `product` para que el grafo tenga dominios útiles (sin ellos, todo cae a `"unknown"`).
- F44: consumidor downstream; cambios aquí pueden forzar una versión mayor del schema.
