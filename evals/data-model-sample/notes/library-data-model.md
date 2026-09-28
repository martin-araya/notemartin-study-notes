---
title: "Biblioteca — modelo de datos"
note-type: data-model
status: draft
summary: "Modelo de datos de biblioteca con 4 entidades (Author, Book, Borrower, Loan), 3 relaciones, integridad PK/FK/UNIQUE/CHECK y 3 queries típicas."
tags: [type/data-model, domain/library]
source: "Library Management Schema v1"
source-type: docs
source-anchor: "schema-v1"
retrieved: 2026-09-27
vendor: Open Library Foundation
product: Library
product-version: "1"
related: "[[note:library-procedure-checkout]], [[note:library-syntax-schema]]"
---

# Biblioteca — modelo de datos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Modelo de datos de biblioteca con 4 entidades (Author, Book, Borrower, Loan), 3 relaciones, integridad PK/FK/UNIQUE/CHECK y 3 queries típicas. |
| **Procedencia** | Library Management Schema v1 (docs) §schema-v1 · recuperado 2026-09-27 |
| **Versión** | 1 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
4 entidades: Author (N:M con Book), Book (con ISBN único), Borrower (1:N con Loan), Loan (1:N con Book y Borrower). Integridad: PK + 2 FK + 3 UNIQUE + CHECK en due_date > loan_date. {src:blk_d00000000050}

{layer:l2}

## Modelo
:::diagram
```mermaid
erDiagram
    AUTHOR ||--o{ BOOK : writes {src:blk_eeeeff000001}
    AUTHOR {
        bigint id PK
        varchar name UK
    }
    BOOK {
        bigint id PK
        varchar isbn UK
        varchar title
    }
    BORROWER ||--o{ LOAN : borrows {src:blk_eeeeff000002}
    BORROWER {
        bigint id PK
        varchar email UK
    }
    BOOK ||--o{ LOAN : lent_in {src:blk_eeeeff000003}
    LOAN {
        bigint id PK
        bigint book_id FK
        bigint borrower_id FK {src:blk_eeeeff000004}
        date loan_date
        date due_date
    }
# {src:blk_ccddeebf0001}
```
::: {src:blk_bbccddee0001}

## Entidades

### Author {src:blk_aabbccddee02}
Representa un autor de uno o más libros. Identificado por id; nombre único. {src:blk_d00000000051}

### Book {src:blk_aabbccddee03}
Representa un libro físico o digital. ISBN único a nivel mundial. {src:blk_d00000000052}

### Borrower {src:blk_aabbccddee04}
Persona que toma libros en préstamo. Email único. {src:blk_d00000000053}

### Loan {src:blk_aabbccddee05}
Préstamo de un Book a un Borrower con fecha de inicio y devolución. {src:blk_d00000000054}

## Campos

### Author {src:blk_aabbccddee06}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE | Nombre completo |

### Book {src:blk_aabbccddee07}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `isbn` | VARCHAR(13) | NOT NULL, UNIQUE | ISBN-13 |
| `title` | VARCHAR(255) | NOT NULL | Título del libro |

### Borrower {src:blk_aabbccddee08}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Email único |

### Loan {src:blk_aabbccddee09}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `book_id` | BIGINT | NOT NULL, FK → book(id) | Libro prestado |
| `borrower_id` | BIGINT | NOT NULL, FK → borrower(id) | Persona |
| `loan_date` | DATE | NOT NULL, DEFAULT CURRENT_DATE | Fecha del préstamo |
| `due_date` | DATE | NOT NULL | Fecha de devolución |

## Relaciones
| Origen | Cardinalidad | Destino | Descripción |
|---|---|---|---|
| Author | N:M | Book | Un autor escribe N libros; un libro tiene N autores |
| Book | 1:N | Loan | Un libro tiene N préstamos |
| Borrower | 1:N | Loan | Un borrower tiene N préstamos activos |

## Claves e índices
| Entidad | PK | Índices secundarios |
|---|---|---|
| Author | id | UNIQUE(name) |
| Book | id | UNIQUE(isbn) |
| Borrower | id | UNIQUE(email) |
| Loan | id | INDEX(book_id, borrower_id) |

## Integridad

:::warning
**PK** — Author(id), Book(id), Borrower(id), Loan(id). Auto-increment + NOT NULL. {src:blk_d00000000060}
::: {src:blk_bbccddee000a}

:::warning
**FK** — Loan.book_id → Book(id); ON DELETE RESTRICT. {src:blk_d00000000061}
::: {src:blk_bbccddee000b}

:::warning
**FK** — Loan.borrower_id → Borrower(id); ON DELETE RESTRICT. {src:blk_d00000000062}
::: {src:blk_bbccddee000c}

:::warning
**UNIQUE** — Book(isbn). Impide duplicados de ISBN. {src:blk_d00000000063}
::: {src:blk_bbccddee000d}

:::warning
**CHECK** — Loan.due_date > loan_date. Impide fechas inválidas. {src:blk_d00000000064}
::: {src:blk_bbccddee000e}

:::danger
**NOT NULL** — todos los campos críticos (FKs, fechas, identificadores). {src:blk_d00000000065}
::: {src:blk_bbccddee000f}

## Consultas típicas

:::example
**Q1:** Libros prestados actualmente.

```sql
SELECT b.title, l.loan_date, l.due_date {src:blk_eeeeff000005}
FROM loan l JOIN book b ON l.book_id = b.id {src:blk_eeeeff000006}
WHERE l.borrower_id = $1 AND l.due_date >= CURRENT_DATE; {src:blk_eeeeff000007}
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee0010}

:::example
**Q2:** Top 10 autores por nº de libros.

```sql
SELECT a.name, COUNT(*) AS n_books {src:blk_eeeeff000008}
FROM author a JOIN book_author ba ON a.id = ba.author_id {src:blk_eeeeff000009}
GROUP BY a.id ORDER BY n_books DESC LIMIT 10; {src:blk_eeeeff00000a}
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0011}

:::example
**Q3:** Préstamos vencidos.

```sql
SELECT b.email, COUNT(*) AS n_overdue {src:blk_eeeeff00000b}
FROM borrower b JOIN loan l ON b.id = l.borrower_id {src:blk_eeeeff00000c}
WHERE l.due_date < CURRENT_DATE GROUP BY b.email HAVING COUNT(*) > 0; {src:blk_eeeeff00000d}
# {src:blk_ccddeebf0004}
```
::: {src:blk_bbccddee0012}

## Evolución

:::note
**v1.0 (2024-Q1):** schema inicial con 4 entidades. **v1.1 (2024-Q3):** índice compuesto en `Loan(book_id, borrower_id)`. **v2.0 (planificado):** añadir `Reservation` entity para queue de reservas. {src:blk_d00000000070}
::: {src:blk_bbccddee0013}

## Backlinks
El modelo de biblioteca se complementa con el procedure de checkout y el DDL del schema; los enlaces muestran ambos aspectos. {src:blk_d00000000080}

- [[note:library-procedure-checkout]] — procedure de checkout que crea Loan.
- [[note:library-syntax-schema]] — DDL completo del schema.
