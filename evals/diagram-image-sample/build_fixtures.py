#!/usr/bin/env python3
"""
Genera fixtures reproducibles para evals/diagram-image-sample/.

Crea un archivo `diagrams.nm` con 5 diagramas Mermaid representativos
(WP-1 flowchart, WP-2 sequence, WP-3 state, WP-4 er, WP-6 gantt) y un
profile mínimo.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "diagram-image-sample" / "fixtures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_diagrams_nm(out: Path) -> None:
    """Genera diagrams.nm con 5 diagramas variados."""
    content = '''---
title: "Diagrams test for F68"
note-type: probe
status: draft
---

# Diagrams test for F68

:::diagram src="blk_diag_wp1" alt="WP-1 flowchart simple"
```mermaid
flowchart TD
    A["Inicio"] --> B{"¿Condición?"}
    B -->|sí| C["Sí"]
    B -->|no| D["No"]
```
:::

:::diagram src="blk_diag_wp2" alt="WP-2 sequence"
```mermaid
sequenceDiagram
    participant C as Cliente
    participant S as Servidor
    C->>S: Petición
    S-->>C: Respuesta
```
:::

:::diagram src="blk_diag_wp3" alt="WP-3 state machine"
```mermaid
stateDiagram-v2
    [*] --> Inactivo
    Inactivo --> Activo: iniciar
    Activo --> [*]: terminar
```
:::

:::diagram src="blk_diag_wp4" alt="WP-4 er diagram"
```mermaid
erDiagram
    CLIENTE ||--o{ PEDIDO : realiza
    PEDIDO ||--|{ LINEA : contiene
```
:::

:::diagram src="blk_diag_wp6" alt="WP-6 gantt"
```mermaid
gantt
    title Proyecto
    dateFormat YYYY-MM-DD
    section Fase 1
        Tarea A :a1, 2026-01-01, 30d
        Tarea B :a2, after a1, 20d
```
:::
'''
    write(out / "diagrams.nm", content)


def build_profile(out: Path) -> None:
    """Genera un profile mínimo."""
    content = '''---
name: diagram-image-test
targets:
  appflowy:
    output_dir: appflowy
  markdown:
    output_dir: markdown
profile_version: "1.0.0"
'''
    write(out / "profile.yaml", content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIXTURES_DIR)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    build_diagrams_nm(out)
    build_profile(out)
    print(f"Fixtures generadas en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
