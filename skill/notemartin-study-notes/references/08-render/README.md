# `references/08-render/`

Reglas de L4: matriz de capacidades, contrato de renderer, enlaces, publicación idempotente, migración entre destinos.

## Orden de lectura

Cargar al renderizar o re-renderizar. `contract.md` siempre; el resto según el destino activo.

## Estado actual

- `capability-matrix.md` `[existente]` — F8: matriz 14×7 con cero ⚠.
- `contract.md` `[existente]` — F53: contrato del renderer + tabla cerrada de degradación (20 filas = 20 celdas ❌ de F8).
- `linking.md` `[existente]` — F61: spec de resolución de enlaces por destino + 2 pasadas + link debt registry + tabla de backlinks por destino.
- `publishing.md` `[existente]` — F62: spec de publicación idempotente con manifest por destino, detección de ediciones manuales (hash comparison), preservación de comentarios via `<!-- user-content -->`, workflow CLI plan/publish/status/mark-edited.
- `migration.md` `[pendiente F64]`

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `capability-matrix.md` | F53, renderers L4 | F8 |
| `contract.md` | Renderers L4, agente al decidir | F53 |
| `linking.md` | Renderers L4 | F61 |
| `publishing.md` | F55, F57, F62 | F62 |
| `migration.md` | F64 | F64 |
