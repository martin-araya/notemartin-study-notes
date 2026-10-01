# Instalación — `INSTALL.md`

> Documento normativo de F121. Instrucciones de instalación de la skill `notemartin-study-notes` en los 4 sistemas operativos desktop principales: macOS, Ubuntu/Debian, Fedora/RHEL y Windows. Cubre dependencias de sistema (Tesseract OCR + idioma), Python y herramientas opcionales (Playwright, cairosvg).
>
> Documentos complementarios: `references/01-ingest/ocr-engines.md` (F20, spec normativa de OCR + tabla de Tesseract por OS), `scripts/README.md` (F117, catálogo de scripts con tabla de Dependencias), `scripts/CHECKLIST.md` (F117, spec compacta del verificador `check_deps.py`).

## Índice

1. [Requisitos mínimos](#1-requisitos-mínimos) · 2. [macOS](#2-macos) · 3. [Ubuntu / Debian](#3-ubuntu--debian) · 4. [Fedora / RHEL](#4-fedora--rhel) · 5. [Windows](#5-windows) · 6. [Dependencias opcionales](#6-dependencias-opcionales) · 7. [Verificación de la instalación](#7-verificación-de-la-instalación) · 8. [Primer caso de humo](#8-primer-caso-de-humo)

## 1. Requisitos mínimos

Toda instalación requiere:

| Componente | Versión mínima | Para qué sirve |
|---|---|---|
| Python | 3.9+ | Ejecución de los scripts y del agente |
| Git | 2.20+ | Clonar el repo (este paquete) |
| curl | cualquiera | Descargar muestras del corpus (F6) |
| Tesseract OCR | 5.x | OCR multilingüe de PDFs escaneados (F20) |

Python 3.9 viene preinstalado en macOS Monterey+ y en Ubuntu 20.04+. En Windows se distribuye vía `python.org` o vía Microsoft Store.

## 2. macOS

### 2.1 · Gestor de paquetes

```bash
# Homebrew (no incluido por defecto).
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Tesseract 5 + idiomas español + inglés.
brew install tesseract tesseract-lang
```

### 2.2 · Python

```bash
# macOS Monterey+ trae Python 3.9+ preinstalado; verificar.
python3 --version

# Dependencias Python del proyecto.
python3 -m pip install --user -r scripts/requirements.txt
```

### 2.3 · Verificación

```bash
tesseract --version                              # debe decir tesseract 5.x
python3 -c "import yaml, jsonschema; print('OK')"
python3 scripts/check_deps.py                     # verificador de F117
```

## 3. Ubuntu / Debian

### 3.1 · Tesseract

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
```

> Tabla completa de paquetes Tesseract por idioma: `skill/notemartin-study-notes/references/01-ingest/ocr-engines.md` §6.

### 3.2 · Python

```bash
sudo apt install -y python3 python3-pip python3-venv
python3 -m pip install --user -r scripts/requirements.txt
```

### 3.3 · Verificación

```bash
tesseract --version
python3 -c "import yaml, jsonschema; print('OK')"
python3 scripts/check_deps.py
```

## 4. Fedora / RHEL

### 4.1 · Tesseract

```bash
sudo dnf install -y tesseract tesseract-spanish tesseract-english
```

> Nota: en Fedora el paquete de idioma se llama `tesseract-<lang>` directamente (no `tesseract-ocr-<lang>` como en Debian/Ubuntu). Si tu distro usa otra convención, consulta `references/01-ingest/ocr-engines.md` §6.

### 4.2 · Python

```bash
sudo dnf install -y python3 python3-pip
python3 -m pip install --user -r scripts/requirements.txt
```

### 4.3 · Verificación

```bash
tesseract --version
python3 -c "import yaml, jsonschema; print('OK')"
python3 scripts/check_deps.py
```

## 5. Windows

### 5.1 · Gestor de paquetes (elige uno)

**Opción A — Chocolatey** (administrador):

```powershell
choco install tesseract tesseract-languages
choco install python --version=3.11
```

**Opción B — Scoop** (usuario, sin elevación):

```powershell
scoop install tesseract
scoop install python
```

> Tesseract en Windows no incluye el paquete de idioma español por defecto con Scoop; instalar `tesseract-languages` por separado o descargar el `.traineddata` desde [github.com/tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata) y copiarlo a `C:\Program Files\Tesseract-OCR\tessdata\`.

### 5.2 · Python

Si no se instaló vía gestor:

```powershell
# Descargar Python 3.11+ desde python.org (marcar "Add to PATH").
python --version
python -m pip install --user -r scripts\requirements.txt
```

### 5.3 · Verificación (PowerShell)

```powershell
tesseract --version
python -c "import yaml, jsonschema; print('OK')"
python scripts\check_deps.py
```

## 6. Dependencias opcionales

Estas dependencias se recomiendan solo si se usan las funcionalidades avanzadas:

| Dependencia | Para qué sirve | Cómo instalar |
|---|---|---|
| Playwright | Capturas PNG reales de los ejemplos (F120 `--real-captures`) | `pip install playwright && playwright install chromium` |
| cairosvg | Alternativa más ligera a Playwright para rasterizar SVG | `pip install cairosvg` (+ Cairo system dep) |
| easyocr | OCR alternativo a Tesseract para casos extremos | `pip install easyocr` |
| paddleocr | OCR alternativo chino-optimizado | `pip install paddlepaddle paddleocr` |
| weasyprint | Render PDF desde HTML (F59) | `pip install weasyprint` (+ Pango system dep) |

Sin ninguna de estas, la skill funciona: las capturas de F120 son SVG sintéticos y los renders PDF son opcionales.

## 7. Verificación de la instalación

Tras instalar en cualquier OS, ejecuta el verificador de dependencias del proyecto:

```bash
python3 scripts/check_deps.py
```

Salida esperada (con todas las deps instaladas):

```
req: 0 missing
rec: 0 missing
opt: <n> missing (informativo)
bin: 0 missing
exit 0
```

Si exit ≠ 0, el verificador indica qué falta y cómo afecta a la skill. Ver `scripts/README.md` y `scripts/CHECKLIST.md` para detalles.

## 8. Primer caso de humo

Tras verificar deps, ejecuta el primer caso end-to-end para confirmar que todo funciona:

```bash
# Regenerar el ejemplo 01 (PostgreSQL SELECT) — no requiere agente.
python3 examples/build_examples.py --example 01-postgresql-chapter
```

Salida esperada: `PASS: 01-postgresql-chapter` + 5 capturas SVG generadas.

Para el primer caso con agente (suite de evals F118):

```bash
python3 evals/suite/runner/drive_suite.py \
  --run-id smoke-test \
  --agent-command "<comando del agente>"
```

Si todo está bien instalado, el comando exit 0 con un `report.json` con 6 casos y todas las aserciones evaluadas.

## Cambios permitidos

**No reabren F121:**
- Añadir un SO adicional (Arch, FreeBSD, etc.) como nueva sección.
- Actualizar la lista de paquetes de un SO cuando cambien las convenciones.
- Añadir una dependencia opcional a la tabla de §6.

**Reabren F121:**
- Cambiar el contenido de las 4 secciones OS sin anclaje a F20.
- Eliminar una de las 4 secciones OS.
- Cambiar las reglas de §7 o §8.

## §5.5 · Instalar el `.skill` descargado (F122)

Si en lugar de clonar el repo instalas el paquete distribuido (descargado como `notemartin-study-notes-<version>.skill`), el flujo es:

```bash
# 1. Descomprimir el ZIP en la carpeta de skills de tu agente.
unzip notemartin-study-notes-<version>.skill -d ~/.kilo/skills/notemartin-study-notes/

# 2. Verificar dependencias.
python3 ~/.kilo/skills/notemartin-study-notes/scripts/check_deps.py

# 3. Caso de humo.
python3 scripts/smoke_test.py --skill ~/.kilo/skills/notemartin-study-notes/
```

El `.skill` se distribuye vía GitHub Releases (u otro canal) por release-tag. Para construirlo desde el repo:

```bash
python3 scripts/build_skill.py --version <release-tag>
# Salida: dist/notemartin-study-notes-<release-tag>.skill (≈ 1.2 MB comprimido, ~3.7 MB uncompressed)
```

Verificabilidad: `python3 scripts/build_skill.py --check` confirma que dos builds con mismo `git_sha` producen ZIPs byte-idénticos (D3 del plan F122).
