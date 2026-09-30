# Catálogo de scripts — `scripts/CHECKLIST.md`

> Spec compacta de la **Fase 117** del roadmap. Define la forma canónica
> de la fila `| Dependencias |` en `scripts/README.md` (4 niveles:
> req/rec/opt/bin), la columna nueva `| Si falta |`, y la CLI del
> verificador `scripts/check_deps.py`.
>
> **Cuándo cargar:** al añadir un script nuevo al catálogo; al
> ejecutar `scripts/check_deps.py` para diagnosticar el entorno;
> en F118 evals.

---

## §1 · Forma canónica de la fila `| Dependencias |`

Cada entrada H3 de `scripts/README.md` debe incluir una fila `| Dependencias |`
con tokens separados por `;`. Cada token sigue el formato:

```
<nivel>:<paquete-o-binario>
```

donde `<nivel>` ∈ {`req`, `rec`, `opt`, `bin`}.

Ejemplo:
```
| Dependencias | req:python3.9; req:PyYAML; rec:pypdf; opt:easyocr; bin:tesseract |
```

El parser (`check_deps.py`) tolera la forma libre antigua (texto sin
prefijo de nivel) tratándola como `req` por default; emite un warning
informativo y recomienda migrar a la forma canónica.

---

## §2 · Los 4 niveles

| Nivel | Significado | Si falta |
|---|---|---|
| `req:<pkg>` | obligatorio; el script aborta sin él | exit 1 del checker + recomendación de instalar |
| `rec:<pkg>` | recomendado; el script degrada | exit 2 + warning listando qué se degrada |
| `opt:<pkg>` | opcional; mejora UX (calidad, velocidad) | exit 0 + info |
| `bin:<bin>` | binario externo (PATH lookup con `shutil.which`) | depende del script; el checker lo busca en PATH |

---

## §3 · Forma de la columna `| Si falta |`

Cada entrada H3 puede (debe) incluir una nueva columna:

```
| Si falta | <descripción del comportamiento sin la dep> |
```

Forma corta (≤ 100 chars). Si requiere más espacio, link al spec de la fase:

```
| Si falta | OCR sin auto-invert (F97 §A 5.4 — ver [F97](references/02-source-model/ocr.md) para workaround manual) |
```

---

## §4 · Ejemplo completo de entrada canónica

```
### `validate/density_check.py` — F76

Verificador de densidad y jerarquía. Lee una nota NoteMark (`.md`), parsea
bloques por sección H2/H3, y mide las 8 reglas canónicas R1-R8 de
`references/07-visual/density.md`. ...

| Aspecto | Detalle |
|---|---|
| Propósito | Hacer ejecutable la tabla cerrada de densidad R1-R8. |
| Entrada | `--note <path>` / `--notes <dir>` / `--strict` / `--allow-violations <csv>` |
| Salida | JSON estructurado (`--json`) o texto humano |
| Códigos | 0 / 1 / 2 |
| Dependencias | req:python3.9 |
| Si falta | (sin fallback — el script aborta) |
| Wirings | F76 ROADMAP §1483-1485; F46 R8; F51 L1, F75 §5.2 |
```

---

## §5 · Cómo añadir un script nuevo al catálogo (3 pasos)

1. **Crear el script** bajo la subcarpeta adecuada (`ingest/`, `validate/`,
   `audit/`, etc.) con shebang `#!/usr/bin/env python3` y docstring
   con: nombre, descripción, fase, modo de uso.

2. **Añadir entrada H3** en `scripts/README.md` con la tabla de 8 filas
   canónicas (Propósito / Entrada / Salida / Códigos / Dependencias /
   Si falta / Wirings) + bloque "Dependencias mínimas y declaradas
   en `requirements.txt` plano" si la tabla de §0 lo referencia.

3. **Actualizar** `scripts/pkg/deps.yaml` con el nivel (req/rec/opt) de
   cada nueva dependencia externa. Si no la añades, el checker la
   reporta como "missing (rec)" en la columna `rec:`.

---

## §6 · CLI del `scripts/check_deps.py`

```
check_deps.py [--strict] [--json] [--filter NAME]
               [--bin-search-path PATH]
               [--catalog PATH] [--manifest PATH]

# Defaults:
#   --catalog = scripts/README.md
#   --manifest = scripts/pkg/deps.yaml
#   Recorre pkg/deps.yaml para deps globales (python/git/curl/unzip).
#   Recorre scripts/**/*.py e identifica el nivel de cada dep (parser
#     regex sobre | Dependencias | rows + AST-lite sobre imports).
#   Cruza con módulos disponibles en el sys.path actual + shutil.which.
#   Emite reporte.
```

Salida (texto):
```
check_deps.py — Verificador de dependencias
============================================
PAQUETES PYTHON:
  ✓ python3.9+     OK
  ✓ PyYAML         OK (1.5.1)
  ✗ pypdf          MISSING (req)    — usado por ingest_check.py
  ⚠ easyocr        MISSING (rec)    — usado por ocr.py (degraded: tesseract only)
  ℹ Pillow         MISSING (opt)    — mejora recorte de imágenes
BINARIOS EXTERNOS:
  ✓ tesseract      OK (/usr/local/bin/tesseract)
  ✗ pdfium         MISSING (bin:req) — usado por render_pdf.py

Summary: 1 missing (required), 1 missing (recommended), 1 missing (optional)
```

Exit codes:
- `0` — todo OK.
- `2` — sólo `rec`/`opt` faltan.
- `1` — ≥ 1 `req` falta.
- `3` — uso/schema.

---

## §7 · Wirings

- **F113** `references/10-quality/validators.md` §4 — `check_deps.py` es un
  **verificador de entorno**, no un validador. Su shape JSON no se
  requiere; emite texto humano.
- **F117** este spec — `scripts/CHECKLIST.md`.
- **F118** evals — corre `check_deps.py` para diagnosticar el entorno
  antes de correr la suite.

---

## §8 · Cambios permitidos + auto-verificación

```bash
# 1. Spec dentro de presupuesto.
wc -l scripts/CHECKLIST.md                                    # ≤ 200

# 2. Checker funcional.
python3 scripts/check_deps.py                                  # 0/2 (entorno sano)

# 3. Catálogo completo.
git ls-files | grep '^skill/notemartin-study-notes/scripts/.*\.py$' | wc -l   # ~72
grep -c '^### ' scripts/README.md                             # 71+
```

Reabren F117:
- Cambiar los 4 niveles o el exit code mapping.
- Eliminar la columna `| Si falta |`.
- Cambiar el formato canónico de token.