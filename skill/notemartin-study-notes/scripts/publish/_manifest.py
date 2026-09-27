"""_manifest.py — Gestión del manifiesto de publicación (F62).

Almacena el mapping `note_id × destination → {remote_id, remote_hash, ir_sha256,
last_published_at, edited_by_hand}` en `<out-dir>/.publish/manifest.json`.

API:
  - Manifest: load/save/get/upsert/mark_edited/list_all.
  - PublishEntry: dataclass.

Stdlib puro (dataclasses, json, hashlib, shutil).
"""

import hashlib
import importlib.util as _importlib_util
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime as _dt, timezone as _tz
from pathlib import Path
from typing import Any, Dict, List, Optional


# Comparte atomic_write_json con F38+.
_IO_PATH = (
    Path(__file__).resolve().parent.parent / "util" / "_io.py"
)
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json


SCHEMA_VERSION = "1.0.0"


@dataclass
class PublishEntry:
    note_id: str
    destination: str
    remote_id: str = ""
    remote_hash: str = ""
    ir_sha256: str = ""
    last_published_at: str = ""
    edited_by_hand: bool = False
    user_content: str = ""


@dataclass
class Manifest:
    schema_version: str = SCHEMA_VERSION
    generated_at: str = field(default_factory=lambda: _now_utc_iso())
    destinations: Dict[str, Dict[str, PublishEntry]] = field(default_factory=dict)

    @classmethod
    def load(cls, out_dir: Path) -> "Manifest":
        path = out_dir / ".publish" / "manifest.json"
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Manifest corrupto en {path}: {e}")
        manifest = cls(schema_version=data.get("schema_version", SCHEMA_VERSION),
                      generated_at=data.get("generated_at", _now_utc_iso()),
                      destinations={})
        for dest, entries in data.get("destinations", {}).items():
            manifest.destinations[dest] = {}
            for note_id, edata in entries.items():
                manifest.destinations[dest][note_id] = PublishEntry(
                    note_id=note_id,
                    destination=dest,
                    remote_id=edata.get("remote_id", ""),
                    remote_hash=edata.get("remote_hash", ""),
                    ir_sha256=edata.get("ir_sha256", ""),
                    last_published_at=edata.get("last_published_at", ""),
                    edited_by_hand=bool(edata.get("edited_by_hand", False)),
                    user_content=edata.get("user_content", ""),
                )
        return manifest

    def save(self, out_dir: Path) -> None:
        publish_dir = out_dir / ".publish"
        publish_dir.mkdir(parents=True, exist_ok=True)
        path = publish_dir / "manifest.json"
        # Backup.
        if path.exists():
            shutil.copy(path, publish_dir / "manifest.json.bak")

        data = {
            "schema_version": self.schema_version,
            "generated_at": _now_utc_iso(),
            "destinations": {
                dest: {
                    note_id: asdict(entry)
                    for note_id, entry in entries.items()
                }
                for dest, entries in self.destinations.items()
            },
        }
        _atomic_write_json(path, data)

    def get(self, note_id: str, destination: str) -> Optional[PublishEntry]:
        return self.destinations.get(destination, {}).get(note_id)

    def upsert(self, entry: PublishEntry) -> None:
        if entry.destination not in self.destinations:
            self.destinations[entry.destination] = {}
        self.destinations[entry.destination][entry.note_id] = entry

    def mark_edited(self, note_id: str, destination: str) -> None:
        entry = self.get(note_id, destination)
        if entry is not None:
            entry.edited_by_hand = True

    def list_all(self) -> List[PublishEntry]:
        out: List[PublishEntry] = []
        for entries in self.destinations.values():
            out.extend(entries.values())
        return out


def _now_utc_iso() -> str:
    return _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
