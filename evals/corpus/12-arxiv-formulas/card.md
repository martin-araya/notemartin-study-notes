# 12 — arXiv paper (dense formulas)

## Identificador
`12-arxiv-formulas`

## Título y autor / fuente
Preprint arXiv con densidad alta de fórmulas matemáticas. Sustituto concreto: cualquier preprint de math.OC, cs.LG, o physics con LaTeX math denso.

## URL canónica
https://arxiv.org/list/math.OC/recent

## Licencia
Variable; se elige preprint con CC-BY 4.0 explícito.

## Formato
PDF nativo LaTeX.

## Páginas
~15.

## Densidad
- Tablas: baja.
- Código: no.
- Figuras: baja.
- Fórmulas: muy alta (5-10 ecuaciones por página).

## Idioma
inglés.

## Versión del producto
no aplica.

## Presencia
- `tablas`: no
- `codigo`: no
- `formulas`: sí
- `figuras`: sí (pocas)
- `diagramas_sintaxis`: no
- `cajas_editoriales`: no

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Todos.

## Tipos de nota esperados
- `concept` (conceptos formalizados).
- `comparison` (variantes formales).

## Plan de ingesta
L0 nativo (PDF); L1 SDM con detección de fórmulas (F24); L2 unidades `formula`; L3 con `:::equation` (F45); L4 a todos los destinos.

## Categoría cubierta
Documento con fórmulas.

## Riesgo si falta
Sin esta fuente no se练习a el OCR de fórmulas (F24) ni el nodo `equation` (F14, F45).

## Muestra
- Archivo: `sample.pdf` (preprint arXiv con fórmulas, 765 KB).
- Comando de descarga: `curl -sSL --max-time 30 -o sample.pdf https://arxiv.org/pdf/2301.00001`
- Hash sha256: `a288e5a34c387ec36329091d6359470e84e098cb8dc91efbfcd320adf286f66a` (765 699 bytes).
- Nota: la URL exacta puede no corresponder al mismo paper en el futuro; mientras el sha256 verifique, la muestra es válida para reproducir el eval.
