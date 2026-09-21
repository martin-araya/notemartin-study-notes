# `notemartin-study-notes`

Skill instalable. Convierte documentación técnica, libros técnicos y PDFs escaneados en notas de estudio completas, trazables y publicables en Obsidian, Notion, AppFlowy, Markdown, HTML/PDF y repaso espaciado.

## Estructura del paquete

| Carpeta | Rol |
|---|---|
| `SKILL.md` | Router N2; < 500 líneas; única carga obligatoria en contexto cuando la skill se dispara. Pendiente F9. |
| `references/` | Prosa normativa para el agente (N3). 12 subcarpetas prefijadas. |
| `schemas/` | JSON Schema versionados de los artefactos del workdir. |
| `scripts/` | Ejecutables invocables; no se leen en contexto. |
| `assets/` | Material copiable (tokens, CSS, plantillas, paletas). |

## Garantías

- **Fidelidad:** 100 % de unidades `must-keep` con `source_ref` resoluble.
- **Cobertura:** el ledger es la fuente de verdad; consulta "¿dónde quedó la sección X.Y.Z?" tiene respuesta única.
- **Trazabilidad:** ida y vuelta nodo↔bloque.
- **Portabilidad:** 7 destinos sin pérdida de contenido fáctico.

Definiciones operativas y métricas en [`docs/product-manifesto.md`](../../docs/product-manifesto.md).

## Inicio rápido

- **Para usar la skill:** consulta `SKILL.md` y la tabla de enrutado (F9).
- **Para extender la skill:** consulta [`docs/repo-layout.md`](../../docs/repo-layout.md) y [`docs/skill-anatomy.md`](../../docs/skill-anatomy.md).
- **Para contribuir:** consulta [`docs/adr/`](../../docs/adr/) antes de proponer una regla nueva.
