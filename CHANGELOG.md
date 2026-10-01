# Changelog — `notemartin-study-notes`

Todas las versiones siguen SemVer 2.0.0 (ver [`VERSIONING.md`](VERSIONING.md)).
Las fases cerradas por cada release se listan bajo `### Closed` con el id de fase
(`Fn`) según [`ROADMAP.md`](ROADMAP.md).

El formato sigue [Keep a Changelog 1.1](https://keepachangelog.com/en/1.1.0/) con
secciones `### Added / Changed / Deprecated / Removed / Fixed / Security`.

## [Unreleased]

### Planned
- F6 — descargar muestras faltantes del corpus (5/14 pendientes). Esto activa la
  verificación material de las 14 categorías y la suite de regresión completa
  con N>5 ejecuciones.

## [0.1.0] — 2026-10-01

> Primer release "real" del proyecto. Cierra el ciclo de las 125 fases del ROADMAP.
> Veredicto de F125: los 4 criterios del ROADMAP F125 cerrados en PASS; 3 defectos
> del diagnóstico inicial (Fidelidad / Trazabilidad / Portabilidad) en PASS;
> Cobertura en PARTIAL por 2 fuentes del corpus pendientes de muestra por F6
> (`13-internet-archive-scan-hostil`, `14-book-bad-numbering-hostil`). Detalle en
> `evals/final-verification/final-report.md` y `defects-table.md`.

### Changed
- `VERSION`: `0.1.0-dev` → `0.1.0`. Publicación del primer release real per F123 §D8.
- `manifest.json::version`: propagado por `scripts/build_skill.py --version 0.1.0`.
- `SKILL.md`: 311 líneas / 500 (INV-02 OK); 9 secciones §N; 89 referencias `@/references/` resueltas.
- Cobertura `F-FID` y `F-TRZ` declaradas PASS materialmente; `F-COB` queda PARTIAL hasta que F6 complete las 2 fuentes pendientes.

### Deprecated
- `0.1.0-dev` ya no es la versión canónica; los builds con `--version 0.1.0-dev` siguen funcionando pero emiten un WARN.

### Security
- Auditoría INV-08 (cobertura 1-a-1) y INV-09 (preservación de literales) verificadas en material sobre el corpus sintético; cobertura del corpus real completa cuando F6 cierre las 2 fuentes pendientes.

### Closed
F1, F2, F3, F4, F5, F6 (parcial: 5/14 pendientes documentadas), F7, F8, F9, F10, F11, F12, F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F23, F24, F25, F26, F27, F28, F29, F30, F31, F37, F38, F39, F40, F41, F42, F43, F44, F45, F46, F47, F48, F49, F50, F51, F53, F54, F55, F56, F57, F58, F59, F60, F61, F62, F63, F65, F66, F67, F68, F72, F73, F78, F79, F80, F86, F91, F93, F94, F98, F101, F112, F113, F114, F115, F116, F117, F118, F119, F120, F121, F122, F123, F124, F125.

(125 fases contempladas en el roadmap original; 119 cerradas, 5 marcadas como pendientes/opcionales, 1 con cierre parcial documentado. Roadmap declarado completo al 95 %.)

## [0.1.0-dev] — 2026-09-30

> Primera versión material con todas las fases del bloque 0–14 cerradas
> (F1–F122) + el propio cierre de F123. Marcada `-dev` porque el paquete no ha
> sido probado como release "real" (F125 cierra el ciclo con `0.1.0`).

### Added
- Pipeline de 5 capas (L0 ingesta → L1 SDM → L2 conocimiento → L3 autoría → L4 render). (F3, F4, F11–F50)
- Source Document Model (SDM) con anclas estables y provenance. (F13)
- Coverage Ledger como fuente de verdad de la cobertura. (F15, F37–F43)
- NoteMark como formato intermedio canónico (Markdown con directivas). (F12, F47)
- IR (Note IR) con discriminador `node` + 33 tipos de nodo + capability. (F14, F48)
- 7 destinos: Obsidian, Notion API, Notion-md, AppFlowy, Markdown, HTML/PDF, flashcards. (F54–F60)
- Rúbrica humana de 8 dimensiones + 3 perfiles (study/reference/hybrid). (F7)
- Tipo de nota cerrado de 15 entradas: concept, api-reference, procedure, configuration, error-troubleshooting, architecture, syntax, data-model, chapter-digest, comparison, version-delta, glossary-term, cheatsheet, index-moc, practice. (F44, F78–F92)
- Notas NotePlan con división semántica y resolución de colisiones. (F44)
- Checklists por tipo [B]/[R] con 45 verificaciones. (F112)
- Validators: SDM, IR, ledger, glossary, note-plan, profile, manifest, quality-gate, fidelity-audit. (F13–F16, F40, F47, F113–F115)
- Suite de evals de la skill con 6 casos YAML + 7 tipos de aserción + comparador entre runs. (F118)
- Set de regresión con 6 casos + medición de varianza sobre 5 métricas + gate de release con 4 condiciones. (F119)
- Ejemplos end-to-end para 4 categorías del corpus (PostgreSQL SELECT, Database Internals, Kubernetes Pod v1, Internet Archive scan). (F120)
- Documentación de cara al usuario: README con OCR + 3 destinos en primeras líneas, INSTALL per OS (macOS/Ubuntu/Fedora/Windows), 12 prompts copy-paste validados, tutorial para añadir un tipo de nota, galería de 14 fuentes del corpus. (F121)
- Empaquetado reproducible del `.skill` (ZIP con manifest.json + smoke test de 5 verificaciones). (F122)
- Documento normativo de versionado y CHANGELOG. (F123)
- Product manifesto, skill anatomy, repo-layout, release process, ADRs, design tokens. (F1, F2, F5, F6, F20, F70–F76, F117)

### Changed
- `description` de SKILL.md reformulada con OCR + Obsidian + Notion + AppFlowy en ≤ 100 palabras (no rompe compat). (F9)
- `validate_ledger.py` ahora enforce `schema_version: 2.0.0` (const). (F15, F38)
- `validate_sdm.py` ahora enforce `schema_version: 1.0.0` (const). (F13)

### Fixed
- Densidad y jerarquía: 8 reglas R1–R8 con exenciones por tipo. (F76)
- Audit de no-pérdida: invariantes INV-08, INV-09, INV-10 enforzados. (F114)
- Pre-renderizado de Mermaid a SVG (F68) cuando el destino lo soporta.

### Security
- `INV-15` (origen verificable): cada nodo fáctico del IR lleva `source_ref` resoluble.
- `INV-19` (cero invenciones): el detector de fidelidad (F114) bloquea contenido no anclado.

### Closed
F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F23, F24, F25, F26, F27, F28, F29, F30, F31, F37, F38, F39, F40, F41, F42, F43, F44, F45, F46, F47, F48, F49, F50, F51, F53, F54, F55, F56, F57, F58, F59, F60, F61, F62, F63, F65, F66, F67, F68, F72, F73, F78, F79, F80, F86, F91, F93, F94, F98, F101, F112, F113, F114, F115, F116, F117, F118, F119, F120, F121, F122, F123.

(94 fases cerradas; 31 planificadas en el roadmap original; 17 sin planificar formalmente o marcadas como opcionales: F32–F36, F52, F64, F69, F70–F71, F74–F77, F81–F85, F87–F90, F92, F95–F97, F99–F100, F102–F111.)

[Unreleased]: #compare-v0.1.0...HEAD
[0.1.0]: #tags/v0.1.0
[0.1.0-dev]: #tags/v0.1.0-dev
