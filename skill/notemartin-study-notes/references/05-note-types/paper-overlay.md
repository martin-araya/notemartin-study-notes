# Overlay de artículos científicos — `references/05-note-types/paper-overlay.md`

> Documento complementario a `references/05-note-types/chapter-digest.md`. Define el esquema de secciones y pautas de autoría para procesar artículos académicos (arXiv / conferencias / journals) reutilizando el tipo de nota `chapter-digest` sin fragmentar los 15 tipos de notas principales.
>
> Documentos complementarios: `references/01-ingest/arxiv.md` (ingesta y oráculo TeX), `references/03-knowledge/information-units.md` (unidades académicas), `references/04-authoring/block-directives.md` (directivas NoteMark), `references/08-render/notion-md.md` (render para exportar a Notion).

## Índice

1. [Propósito](#1-propósito) · 2. [Estructura canónica de secciones](#2-estructura-canónica-de-secciones) · 3. [Pautas de autoría para papers](#3-pautas-de-autoría-para-papers) · 4. [Directivas NoteMark aplicadas](#4-directivas-notemark-aplicadas) · 5. [Garantía del 98 %](#5-garantía-del-98-)

---

## 1. Propósito

Un artículo de investigación presenta densidad formal y metodológica que difiere de un capítulo de libro técnico estándar. Para cumplir con el objetivo de **completitud ≥ 98 %** hacia Markdown para Notion, este *overlay* organiza el contenido preservando todo el aparato formal (notación, teoremas, algoritmos, experimentos, apéndices y bibliografía).

---

## 2. Estructura canónica de secciones

Cuando el source sea un paper de arXiv, el plan de nota (`note-plan`) adopta la siguiente secuencia de encabezados:

```markdown
# [Título del paper]

## Cabecera
| Campo | Valor |
|---|---|
| **arXiv ID** | `2201.00001` (v3) |
| **Autores** | Danielle C. Maddix, Nadim Saad, Yuyang Wang |
| **Categorías** | math.NA, stat.ML |
| **DOI / URL** | https://arxiv.org/abs/2201.00001 |
| **Fecha** | 2021-12-14 |
| **Fuente TeX** | Disponible |

## TL;DR
Síntesis ejecutiva de 2 a 3 párrafos con el problema abordado, la intuición central de la propuesta y los resultados cuantitativos clave.

## Abstract
Transcripción fiel y completa del resumen del autor.

## Contribuciones principales
Lista numerada de aportes originales declarados por los autores y validados en el texto.

## Notación y definiciones preliminares
Tabla con el glosario de símbolos matemáticos, espacios de definición y operadores fundamentales.

## Método y formulación matemática
Desarrollo conceptual paso a paso de la propuesta, incluyendo todas las ecuaciones numeradas en KaTeX display:
$$
\frac{\partial u}{\partial t} = -\nabla \cdot (vu)
$$

## Teoremas y demostraciones
Enunciados completos de teoremas, lemas y proposiciones:

> 💡 **Theorem 2.1** (Nombre o atribución)
> Enunciado literal y riguroso del teorema.

<details markdown="1">
<summary>Demostración (clic para desplegar)</summary>

Pasos formales de la prueba, justificaciones algebraicas y cierre con símbolo $\blacksquare$.
</details>

## Algoritmos y pseudocódigo
Pasos numerados del algoritmo con sus entradas, salidas e hiperparámetros.

## Configuración experimental
- Datasets (sintéticos y reales, número de nodos, muestras).
- Baselines de comparación.
- Métricas de evaluación ($L_2$ error, RMSE, tiempo de cómputo).

## Resultados y análisis empírico
Tablas comparativas completas con los valores numéricos exactos de las pruebas (sin truncamiento ni aproximaciones vagas).

## Discusión y limitaciones
Supuestos del modelo, casos de fallo conocidos y trabajo futuro planteado por los autores.

## Apéndices técnicos
Derivaciones matemáticas suplementarias, lemas auxiliares y detalles de implementación.

## Referencias bibliográficas
Entradas completas numeradas enlazables desde las citas del cuerpo `[n]`:
- [1] Bakka, H., et al. (2020). The diffusion-based extension of the matérn field to space-time. *arXiv:2006.04917*.
- [2] Borovitskiy, V., et al. (2021). Matérn gaussian processes on graphs. *AISTATS 2021*.

## Autoevaluación
Preguntas conceptuales y de derivación matemática para verificar el entendimiento profundo del paper.
```

---

## 3. Pautas de autoría para papers

1. **Idioma de redacción**: la nota se redacta en español de alta precisión técnica, conservando los términos matemáticos y nombres canónicos en inglés en su primera aparición o en la tabla de símbolos.
2. **Ecuaciones display**: toda fórmula numerada en la fuente debe emitirse como bloque display `$$ ... $$` conservando su número de referencia.
3. **Completitud de tablas**: los valores de error numérico y métricas de desempeño no deben omitirse. Si una tabla tiene 6 modelos y 4 datasets, se transcriben las 24 celdas.
4. **Demostraciones extensas**: para preservar la legibilidad en Notion sin perder contenido, se emplea el bloque colapsable `<details markdown="1">`, que el importador de Notion transforma en un toggle block nativo.

---

## 4. Directivas NoteMark aplicadas

| Elemento | NoteMark (L3) | Markdown para Notion (L4) |
|---|---|---|
| Teorema / Lema | `:::theorem[Theorem 2.1]` | Blockquote con emoji 💡 / callout |
| Prueba / Demostración | `:::proof` | `<details markdown="1"><summary>Demostración</summary>...</details>` |
| Algoritmo | `:::algorithm[Algoritmo 1: Pseudocódigo]` | Bloque de código con pasos numerados |
| Ecuación display | `$$ ... $$` | Bloque KaTeX nativo `$$ ... $$` |
| Cita bibliográfica | `[cite:n]` o `[n]` | Enlace o ancla a `## Referencias bibliográficas` |

---

## 5. Garantía del 98 %

El validador `paper_coverage.py` verifica automáticamente que las unidades de este overlay alcancen la meta:
- Cobertura global de palabras $\ge 98\%$.
- 100 % de fórmulas numeradas, teoremas, algoritmos y tablas presentes.
