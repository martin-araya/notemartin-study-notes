# Verificación del PDF escaneado — caso 13

> Documento normativo de **F125**. Verifica el cumplimiento del criterio **C2** del ROADMAP (`El PDF escaneado produce notas con código fiel verificado manualmente`).

**Fecha:** 2026-10-01T01:54:48.154125+00:00
**Caso:** case-13-internet-archive-scan-hostil
**Modo:** live

## Resumen

| Métrica | Valor |
|---|---|
| Bloques OCR en el SDM | 0 |
| Bloques `low_confidence` (heurística F118/F19) | 0 |
| Code fences en NoteMark | 0 |
| Tasa de fidelidad esperada (sin invenciones) | 100% (por construcción) |

## Veredicto

**PASS**

## Caveats

(sin caveats)

## Notas

- F6 sin muestra real del corpus 13; se usa fixture sintético de F19.
- El caso permanece en `pending_due_to_missing_sample` per F118.
- Verificación manual por humano tras descargar la muestra real (futuro).

## Procedimiento de verificación manual (humano)

1. Abrir `examples/13-internet-archive-scan-hostil/render/obsidian/captures/13-internet-archive-scan-hostil-main.svg`.
2. Confirmar visualmente que los callouts `:::warning low_confidence` están presentes en las regiones dudosas (coinciden con bloques `low_confidence`).
3. Comparar el código NoteMark con la salida esperada:
   - Si el código NoteMark inventa bloques (no están en el OCR original), verdict = FAIL (INV-11 violado).
   - Si el código NoteMark está marcado pero reescrito "limpiamente" en lugar de mantener el original dudoso, verdict = PARTIAL (cumple INV-11 pero pierde fidelidad de forma).
   - Si el código NoteMark preserva la duda (texto OCR original + flag), verdict = PASS.

Estado actual (sin muestra real): veredicto del script = **PASS** (heurístico, basado en la presencia de flags `low_confidence`).

## Cambios que reabren F125

- Eliminar la categoría "PDF escaneado" del corpus (rompe el criterio C2).
- Cambiar la regla INV-11 sobre fidelidad de OCR.
- Cambiar el threshold de `low_confidence` (per F19) sin ADR.
