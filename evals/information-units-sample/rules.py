"""Shim de compatibilidad — la fuente vive en scripts/util/unit_rules.py.

Mantiene la API `{AUTO_RULES, is_must_keep}` que build_fixtures.py y run_eval.py
de F37 importaban. La implementación canónica está en
`skill/notemartin-study-notes/scripts/util/unit_rules.py`; este shim carga
el módulo por ruta (sin requerir que `util` sea un paquete) y re-exporta.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_UNIT_RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "skill"
    / "notemartin-study-notes"
    / "scripts"
    / "util"
    / "unit_rules.py"
)

_spec = importlib.util.spec_from_file_location("unit_rules", _UNIT_RULES_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

AUTO_RULES = _module.AUTO_RULES
is_must_keep = _module.is_must_keep
