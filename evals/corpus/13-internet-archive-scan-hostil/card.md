# 13 — Internet Archive scanned book (HOSTIL: torcido + OCR sucio)

## Identificador
`13-internet-archive-scan-hostil`

## Título y autor / fuente
Libro técnico antiguo (sustituto: cualquier escaneo de Internet Archive de un libro técnico de los 60-80 con OCR degradado). Ejemplo: "The Art of Computer Programming, Vol. 1" (Knuth, 1968) o "Operating Systems: Design and Implementation" (Tanenbaum, 1987).

## URL canónica
https://archive.org/details/

## Licencia
Dominio público (títulos anteriores a 1978 en la mayoría de jurisdicciones) o fair use para evaluación. Se elige un título explícitamente en dominio público.

## Formato
PDF generado a partir de imágenes escaneadas (sin capa de texto nativa).

## Páginas
~10 (muestra representativa del estado del escaneo).

## Densidad
- Tablas: baja (código y prosa predominan).
- Código: alta (libro técnico).
- Figuras: media.

## Idioma
inglés.

## Versión del producto
no aplica.

## Presencia
- `tablas`: sí (pocas)
- `codigo`: sí
- `formulas`: sí (en libros de算法)
- `figuras`: sí
- `diagramas_sintaxis`: no
- `cajas_editoriales`: no

## Hostilidad
**`escaneo_torcido`** — el PDF es un escaneo con:
- Inclinación residual (~3-5°).
- Ruido de fondo (manchas, sombras de encuadernación).
- Bordes oscuros y sombra de lomo.
- Confianza media de OCR esperada `< 0.70`.

## OCR requerido
**`sí`** — reintento hasta 2 veces; si la confianza sigue `< 0.70` se bloquea por umbral (`architecture.md` §8 fila L0 reintentos > 2).

## Destinos esperados
Todos (con renderización adaptada por el modo degradado).

## Tipos de nota esperados
- `concept` (conceptos del libro).
- `error-troubleshooting` (entradas con OCR dudoso marcadas para revisión).

## Plan de ingesta
L0 con cadena de preprocesado completa (F19) + OCR multilingüe (F20) + tabla de confusiones (F25); L1 SDM; L2 con unidades `must-keep` reducidas por descarte justificado; L3 con marcado explícito `external` para contenido dudoso; L4 con reporte de degradación.

## Categoría cubierta
**PDF escaneado con OCR sucio** (categoría cubierta por la versión hostile).

## Categoría adicional cubierta
**Escaneo torcido con ruido** (categoría hostile específica).

## Riesgo si falta
Sin esta fuente no se练习a el modo degradado de L0 (`architecture.md` §8 filas L0); los validadores de confianza no tienen caso adversarial.

## Muestra
- Archivo: `sample.pdf` (3-5 páginas con escaneo degradado) — **no descargado en esta fase**.
- Motivo: la búsqueda en Internet Archive requiere selección manual del título exacto y verificación de licencia de dominio público; la fuente hostil exige revisión caso por caso antes de descargar.
- Sustituto propuesto: cualquier escaneo de libro técnico de los 60–70 en `archive.org/details/` con filtro `mediatype:texts` y año ≤ 1972 (dominio público en la mayoría de jurisdicciones).
- Hash sha256: pendiente.
