---
title: "Rust 1.80 — Map of Content"
note-type: index-moc
status: draft
tags: [type/index-moc, domain/programming, product/rust]
source: "Rust 1.80 docs"
source-type: docs
source-anchor: "std"
retrieved: 2026-09-27
vendor: Rust Foundation
product: Rust
product-version: "1.80"
related: "[[note:rust-ownership]], [[note:rust-cheatsheet]]"
---

# Rust 1.80 — Map of Content

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | MOC de Rust 1.80: notas sobre ownership, borrow checker, lifetimes, traits, error handling y std library. |
| **Procedencia** | Rust 1.80 docs (docs) §std · recuperado 2026-09-27 |
| **Versión** | 1.80 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
MOC de Rust 1.80 con 8+ notas agrupadas por tema (ownership, traits, error handling, std library); incluye mapa conceptual y rutas de lectura. {src:blk_b00000000003}

{layer:l2}

## Introducción
Este MOC agrupa las notas del corpus sobre Rust 1.80, desde conceptos fundamentales (ownership, borrowing) hasta la std library y cargo. {src:blk_fedcba000100}

## Mapa conceptual
:::diagram
```mermaid
flowchart LR
    OW[rust-ownership] --> BC[rust-borrow-checker]
    OW --> LT[rust-lifetimes]
    BC --> LT
    OW --> TR[rust-traits]
    OW --> EH[rust-error-handling]
    TR --> EH
    TR --> SL[rust-std-library]
    SL --> CS[rust-cheatsheet]
# {src:blk_ccddeebf0001}
```
::: {src:blk_bbccddee0001}

## Índice

### Conceptos fundamentales {src:blk_aabbccddee02}
- [[note:rust-ownership]] — Ownership, borrowing, moves; el modelo de memoria único de Rust.
- [[note:rust-borrow-checker]] — Reglas de borrowing en tiempo de compilación.
- [[note:rust-lifetimes]] — Anotaciones de lifetime; static, 'a, 'static.
- [[note:rust-traits]] — Traits como contratos; dyn Trait vs impl Trait.
- [[note:rust-error-handling]] — `Result<T, E>`, `?`, `panic!`, errores recuperables.

### API/Std Library {src:blk_aabbccddee03}
- [[note:rust-std-library]] — `std::collections`, `std::io`, `std::fs`; tipos primitivos.

### Procedures {src:blk_aabbccddee04}
- [[note:rust-cargo]] — `cargo new`, `cargo build`, `cargo test`, `cargo publish`.

### Cheatsheets {src:blk_aabbccddee05}
- [[note:rust-cheatsheet]] — Comandos cargo, traits comunes, lifetimes.

## Prerrequisitos
- Conocer al menos un lenguaje de programación (Python, JS, C++).
- Comprender el modelo de memoria de C o C++ (recomendado).

## Rutas de lectura

### Para aprender Rust desde cero {src:blk_aabbccddee06}
1. Lee [[note:rust-ownership]] para entender el modelo de memoria. {src:blk_fedcba000200}
2. Lee [[note:rust-borrow-checker]] para entender las reglas de borrowing. {src:blk_fedcba000300}
3. Practica con [[note:rust-cheatsheet]] para comandos y patrones. {src:blk_fedcba000400}

### Para profundizar en traits y genéricos {src:blk_aabbccddee07}
1. Lee [[note:rust-traits]] para entender el sistema de tipos. {src:blk_fedcba000500}
2. Lee [[note:rust-lifetimes]] para entender las anotaciones. {src:blk_fedcba000600}

### Para manejo de errores en producción {src:blk_aabbccddee08}
1. Lee [[note:rust-error-handling]] para entender `Result` y `?`. {src:blk_fedcba000700}
2. Practica con [[note:rust-cheatsheet]] los patrones comunes. {src:blk_fedcba000800}

## Estado de cobertura

| Tema | Notas creadas | Pendientes | Planeadas |
|---|---|---|---|
| Ownership / borrowing | 3 | 0 | 0 |
| Traits / genéricos | 1 | 0 | 1 |
| Error handling | 1 | 0 | 0 |
| Std library | 1 | 0 | 0 |
| Cargo | 1 | 0 | 0 |
| Cheatsheets | 1 | 0 | 0 |

## Cobertura de la fuente

:::note
Esta nota cubre los capítulos 1-10 de The Rust Programming Language (1.80): ownership, borrowing, lifetimes, traits, error handling, std library. NO cubre: async/await (cap. 16-17), macros (cap. 19), unsafe Rust (cap. 19), ni las crates populares externas (tokio, serde).
::: {src:blk_bbccddee0009}

## Pendientes

- (ninguna por ahora)

## Próximas incorporaciones

- [[note:rust-async]] — planeada en Note Plan; cubre async/await y tokio.

## Consulta rápida

| Si buscas... | Ve a |
|---|---|
| Ownership y borrowing | [[note:rust-ownership]] |
| Reglas de borrowing | [[note:rust-borrow-checker]] |
| Anotaciones de lifetime | [[note:rust-lifetimes]] |
| Traits y genéricos | [[note:rust-traits]] |
| Manejo de errores | [[note:rust-error-handling]] |
| Comandos cargo | [[note:rust-cargo]] |
