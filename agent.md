# Contrato del agente desarrollador — `agent.md`

> Documento normativo de la **Fase 124** del roadmap. Define cómo el agente humano (no el agente que carga la skill, sino quien mantiene el proyecto `notemartin-study-notes`) opera sobre este repo. Es un sub-producto de F124 — quien usa Kilo Code para mantener el proyecto ve este doc como punto de entrada.
>
> Documentos complementarios: [`CONTRIBUTING.md`](CONTRIBUTING.md) (procedimiento de contribución), [`ROADMAP.md`](ROADMAP.md) (estado del proyecto), [`CHANGELOG.md`](CHANGELOG.md) (F123, bitácora de releases), [`docs/adr/`](docs/adr/) (decisiones arquitectónicas).

## Índice

1. [Quién es](#1-quién-es) · 2. [Responsabilidades](#2-responsabilidades) · 3. [Cómo opera](#3-cómo-opera) · 4. [Estado entre sesiones](#4-estado-entre-sesiones) · 5. [Cambios permitidos](#5-cambios-permitidos)

## 1. Quién es

El agente desarrollador es el humano que escribe PRs, revisa issues, mantiene la skill `notemartin-study-notes`, opera el pipeline de release (F119), empaqueta el `.skill` (F122), versiona (F123). Tiene contexto amplio: roadmap completo, ADRs del proyecto, suite de evals, regresión, contratos de artefactos, política de contribución.

No confundir con **el agente que carga la skill** (esa es la IA que ejecuta `SKILL.md` cuando un usuario invoca la skill sobre una fuente técnica). El agente desarrollador mantiene la skill; el agente que la carga la usa.

## 2. Responsabilidades

El agente desarrollador tiene 6 responsabilidades explícitas:

1. **Mantener el ROADMAP.md actualizado**. Mover casillas `[ ]` → `[x]` con un párrafo `**Estado:** ✅ completado` cuando una fase cierra. Cada fase cerrada referencia las fases vecinas y los criterios cumplidos.
2. **Abrir ADRs antes de cambios de contrato**. Si una decisión afecta al shape de `regions.json`, `summary.json`, `ledger.json`, `note-ir.json`, etc., abrir un ADR con la triada regla→motivación→prueba (per `CONTRIBUTING.md` §2).
3. **Cerrar issues con referencia a fase + ADR**. Cada issue resuelto cita al menos un `FN` y un `ADR-NNNN` o `INV-NN`.
4. **Mantener CHANGELOG.md por cada release**. Per F123: cada release tiene entrada `## [X.Y.Z] - YYYY-MM-DD` con `### Closed: F1, F2, ...`. Mantener el orden cronológico inverso.
5. **Operar scripts de gate antes de cada PR**. Antes de pedir review: `python3 scripts/check_pr.py --branch <branch>`. Antes de un release: `python3 scripts/build_skill.py` + `python3 scripts/smoke_test.py --skill dist/<release>.skill`.
6. **Mantener la suite de evals y la regresión al día**. F118 (6 casos) y F119 (6 casos) deben evolucionar con la skill. Añadir nuevos casos cuando aparece un nuevo tipo de nota, un nuevo destino, o un nuevo patrón de fallo.

## 3. Cómo opera

El agente desarrollador sigue un ciclo de 6 pasos para cada cambio material:

```
1. Lee docs/product-manifesto.md (F1) — qué es y qué no es la skill.
2. Lee ROADMAP.md — qué fases están abiertas, qué fases son vecinas.
3. Lee CONTRIBUTING.md — cómo abrir un PR con la triada regla→motivación→prueba.
4. Para el "por qué" de una decisión: busca en docs/adr/.
5. Para el "qué" de una regla: busca en skill/notemartin-study-notes/references/.
6. Implementa + tests + ADR + CHANGELOG + PR + scripts/check_pr.py.
```

Antes de taggear un release:

```
1. python3 scripts/check_version.py --all   # exit 0
2. python3 scripts/check_pr.py --all       # sin FAIL
3. python3 scripts/build_skill.py --version <X.Y.Z>
4. python3 scripts/smoke_test.py --skill dist/<release>.skill  # 5/5 PASS
5. git tag -a v<X.Y.Z> -m "Release <X.Y.Z>: ver CHANGELOG.md"
```

## 4. Estado entre sesiones

El agente desarrollador retoma el contexto leyendo, en orden:

1. `agent.md` (este doc, ~3 min).
2. `ROADMAP.md` (estado de las fases; qué queda abierto, qué se cerró recientemente).
3. `CHANGELOG.md` (último release; qué cambió desde entonces).
4. `docs/adr/README.md` (ADRs recientes o pendientes).
5. `git log --oneline -20` (commits recientes; qué se movió).

Si una sesión anterior dejó cambios sin commitear, empezar por ahí (no descartar; integrar o revertir).

## 5. Cambios permitidos

**No reabren F124:**
- Reorganizar las secciones de este `agent.md` (sin cambiar el contrato).
- Añadir una nueva responsabilidad a §2 (sin contradecir las existentes).
- Cerrar un ADR con un ADR supersededor (per `docs/adr/README.md` §Reglas).

**Reabren F124:**
- Cambiar el contrato del agente desarrollador (§2-§3).
- Cambiar el procedimiento de retoma entre sesiones (§4).
