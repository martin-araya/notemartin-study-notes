"""Utilidades I/O compartidas entre scripts util/ (F38/F39).

Sin dependencias externas (Python 3.9+ stdlib puro).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(path: Path, payload: Any) -> None:
    """Escribe `payload` como JSON en `path` con escritura atómica.

    Patrón: tempfile en el mismo directorio + Path.replace. Garantiza
    que un crash a mitad no deja un JSON corrupto (invariante L-04 del
    Coverage Ledger, F15 §3).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        Path(tmp_path).replace(path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
