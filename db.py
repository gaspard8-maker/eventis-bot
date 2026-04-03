"""
db.py – Stockage JSON simple pour le bot Fluyn.
Chaque serveur a son propre fichier data/<guild_id>.json
"""
import json, os, pathlib

DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)

def _path(guild_id: int) -> pathlib.Path:
    return DATA_DIR / f"{guild_id}.json"

def load(guild_id: int) -> dict:
    p = _path(guild_id)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save(guild_id: int, data: dict):
    with open(_path(guild_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get(guild_id: int, key: str, default=None):
    return load(guild_id).get(key, default)

def set_(guild_id: int, key: str, value):
    data = load(guild_id)
    data[key] = value
    save(guild_id, data)

# ── Licence globale ────────────────────────────────────────────
GLOBAL_FILE = DATA_DIR / "global.json"

def load_global() -> dict:
    if not GLOBAL_FILE.exists():
        return {}
    with open(GLOBAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_global(data: dict):
    with open(GLOBAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
