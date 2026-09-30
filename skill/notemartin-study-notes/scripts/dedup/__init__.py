"""Dedup scripts (F108) — detector + apply orchestrator sobre F50 transform.py.

Detector identifica pares de notas candidatas a merge/specialize/split
usando matching canónico + alias + similitud textual. Apply orquesta
F50 transform.py y actualiza manifest.json::link_debt[].
"""