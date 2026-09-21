#!/usr/bin/env python3
"""Genera, valida y compara la nota sonda de `notemartin-study-notes`.

La nota sonda (probe.nm) ejercita las 14 capacidades declaradas en
`references/08-render/capability-matrix.md` y se publica en cada destino
real para validar la matriz.

Uso:
    python3 build_probe_note.py --output evals/probe/probe.nm
    python3 build_probe_note.py --check evals/probe/probe.nm
    python3 build_probe_note.py --diff [evals/probe/probe.nm]

Sin dependencias externas. La sonda es determinista: dos invocaciones con
los mismos argumentos producen el mismo archivo byte a byte.
"""

import argparse
import hashlib
import sys
from pathlib import Path

CHECKSUM_FILE = Path(__file__).parent.parent.parent / "evals" / "probe" / ".probe.sha256"

SECTIONS = [
    # (nombre_elemento, marcador_esperado_en_la_nota)
    ("frontmatter YAML", "---\ntitle:"),
    ("encabezado h1", "\n# Probe Note\n"),
    ("encabezado h2", "\n## Section heading\n"),
    ("encabezado h3", "\n### Subsection heading\n"),
    ("termino y source_ref", "[[term:"),
    ("source_ref inline", "{src:blk_"),
    ("tabla simple", "| name | type |\n| --- | --- |"),
    ("directiva param-table", ":::param-table"),
    ("codigo python", "def hello(name: str)"),
    ("consola", "```bash\n$ docker run"),
    ("latex inline", " $E = mc^2$ "),
    ("latex bloque", "$$\n\\sum_"),
    ("callout note", ":::note\n"),
    ("callout tip", ":::tip\n"),
    ("callout warning", ":::warning\n"),
    ("callout danger", ":::danger\n"),
    ("callout example", ":::example\n"),
    ("plegable", ":::collapsible\n"),
    ("columnas", ":::columns\n"),
    ("lista bullets", "- item 1"),
    ("lista numerada", "1. item 1"),
    ("checklist", "- [x] tarea completada"),
    ("cita", "> \"La fidelidad"),
    ("mermaid", "```mermaid\ngraph TD"),
    ("figura con source_ref", ":::figure\n"),
    ("enlace externo", "[sitio oficial](https://example.com)"),
    ("enlace entre notas", "[[note:"),
    ("derived marker", "{derived}"),
    ("external marker", "{external}"),
    ("layer marker", "{layer:l2}"),
    ("placeholder", "{{nombre}"),
]


def build_probe() -> str:
    """Construye la sonda como string determinista."""
    parts = []
    parts.append(_frontmatter())
    parts.append(_body())
    return "\n".join(parts) + "\n"


def _frontmatter() -> str:
    return (
        "---\n"
        "title: \"Probe Note\"\n"
        "note-type: probe\n"
        "tags: [probe, f008, capability-matrix]\n"
        "source: capability-matrix\n"
        "source-type: synthetic\n"
        "vendor: notemartin-study-notes\n"
        "product: notemartin-study-notes\n"
        "product-version: 0.1.0\n"
        "source-anchor: synthetic\n"
        "source-url: https://github.com/notemartin-study-notes\n"
        "retrieved: 2026-09-21\n"
        "language: en\n"
        "coverage: full\n"
        "status: draft\n"
        "difficulty: n/a\n"
        "review-next: none\n"
        "aliases: [probe, nota-sonda]\n"
        "related: [references/08-render/capability-matrix.md]\n"
        "---"
    )


def _body() -> str:
    return r"""
# Probe Note

Esta nota ejercita las 14 capacidades de la matriz de capacidades. Se regenera con `python3 scripts/util/build_probe_note.py --output evals/probe/probe.nm`.

## Section heading

Texto de prueba con término canónico [[term:concepto-demostrado]] y marca de fuente {src:blk_a91f0}.

### Subsection heading

Subsección con marca de capa {layer:l2}.

:::note
Callout de tipo nota. Texto del callout.
:::

:::tip
Callout de tipo consejo.
:::

:::warning
Callout de tipo advertencia.
:::

:::danger
Callout de tipo peligro.
:::

:::example
Callout de tipo ejemplo.
:::

:::collapsible
Contenido plegable. Este bloque se puede expandir o colapsar.
:::

:::columns
Columna izquierda.

Columna derecha.
:::

#### Tablas

Tabla simple:

| name | type |
| --- | --- |
| foo | string |
| bar | integer |

Tabla con directiva param-table:

:::param-table
| parametro | tipo | default | rango |
| --- | --- | --- | --- |
| max_connections | integer | 100 | 1-10000 |
| shared_buffers | bytes | 128MB | 8MB- |
:::

#### Código y consola

Bloque de código:

```python
def hello(name: str) -> str:
    return f"Hello, {name}"

print(hello("world"))
```

Bloque de consola:

```bash
$ docker run -d --name web nginx:alpine
$ docker ps --filter name=web
```

#### Ecuaciones

Inline: la fórmula de Einstein $E = mc^2$ describe la equivalencia masa-energía.

Bloque:

$$
\sum_{i=1}^{n} w_i x_i = b
$$

#### Diagramas y figuras

Diagrama Mermaid:

```mermaid
graph TD
  A[Source] --> B{Ingesta}
  B -->|nativo| C[SDM]
  B -->|escaneado| D[OCR]
  C --> E[Knowledge]
  D --> E
  E --> F[NoteMark]
```

Figura con alt text y source_ref:

:::figure
![Diagrama de la cadena de ingesta](assets/ingesta.png){src:blk_fig01}
:::

#### Enlaces

Enlace externo: [sitio oficial](https://example.com).

Enlace entre notas: ver [[note:concepto-demostrado]] para más detalles.

#### Marcadores de procedencia

Este párrafo es derivado del contenido fuente. {derived}

Este párrafo es conocimiento externo al documento. {external}

#### Placeholder

Sustituye {{nombre}} por el valor real antes de publicar.

#### Listas

Lista de bullets:

- item 1
- item 2
- item 3

Lista numerada:

1. item 1
2. item 2
3. item 3

Checklist:

- [x] tarea completada
- [ ] tarea pendiente

#### Cita

> "La fidelidad al documento original es la promesa principal de la skill." — Manifiesto del producto
"""


def check_probe(path: Path) -> int:
    """Verifica que la sonda contiene todos los elementos esperados."""
    if not path.exists():
        print(f"ERROR: {path} no existe", file=sys.stderr)
        return 1
    content = path.read_text(encoding="utf-8")
    missing = [name for name, marker in SECTIONS if marker not in content]
    if missing:
        print(f"ERROR: {len(missing)} elementos faltantes:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 1
    print(f"OK: {len(SECTIONS)} elementos presentes en {path}")
    return 0


def diff_probe(path: Path) -> int:
    """Compara el archivo actual contra el hash guardado en `.probe.sha256`."""
    if not CHECKSUM_FILE.exists():
        print(f"INFO: no hay hash previo en {CHECKSUM_FILE}; nada que comparar")
        return 0
    expected = CHECKSUM_FILE.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected == actual:
        print(f"OK: hash idéntico ({actual})")
        return 0
    print(f"DIFF: hash difiere\n  esperado: {expected}\n  actual:   {actual}")
    return 1


def save_checksum(path: Path) -> None:
    """Guarda el hash sha256 del archivo generado."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.write_text(digest + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera y valida la nota sonda.")
    parser.add_argument("--output", type=Path, help="Ruta de salida para la sonda generada.")
    parser.add_argument("--check", type=Path, help="Verifica que la sonda contiene los 22 elementos.")
    parser.add_argument("--diff", type=Path, nargs="?", const=True, default=False,
                        help="Compara contra el hash previo (ruta implícita si no se da).")
    args = parser.parse_args()

    if args.check:
        return check_probe(args.check)

    if args.diff:
        target = args.diff if isinstance(args.diff, Path) else Path("evals/probe/probe.nm")
        return diff_probe(target)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        content = build_probe()
        args.output.write_text(content, encoding="utf-8")
        save_checksum(args.output)
        print(f"OK: sonda generada en {args.output} ({len(content)} bytes)")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
