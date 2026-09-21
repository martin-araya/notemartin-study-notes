# `references/08-render/`

Reglas de L4: matriz de capacidades, contrato de renderer, enlaces, publicación idempotente, migración entre destinos.

## Orden de lectura

Cargar al renderizar o re-renderizar. `contract.md` siempre; el resto según el destino activo.

## Estado actual

- `capability-matrix.md` `[pendiente F8]`
- `contract.md` `[pendiente F53]`
- `linking.md` `[pendiente F61]`
- `publishing.md` `[pendiente F62]`
- `migration.md` `[pendiente F64]`

## Quién lee / quién produce

| Archivo | Lee | Produce |
|---|---|---|
| `capability-matrix.md` | F53, renderers L4 | F8 |
| `contract.md` | Renderers L4, agente al decidir | F53 |
| `linking.md` | Renderers L4 | F61 |
| `publishing.md` | F55, F57, F62 | F62 |
| `migration.md` | F64 | F64 |
