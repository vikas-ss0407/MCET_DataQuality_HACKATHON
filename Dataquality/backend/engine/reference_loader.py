from pathlib import Path
import json
import pandas as pd
from typing import Dict, Set

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


def load_json_set(filename: str) -> Set[str]:
    path = CACHE_DIR / filename
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {str(item).strip() for item in data if str(item).strip()}


def load_json_map(filename: str) -> Dict[str, str]:
    path = CACHE_DIR / filename
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {str(k).strip().lower(): str(v).strip() for k, v in data.items()}


def load_email_domains(filename: str) -> Set[str]:
    path = CACHE_DIR / filename
    if not path.exists():
        return set()
    df = pd.read_csv(path)
    return {str(x).strip().lower() for x in df[df.columns[0]].dropna() if str(x).strip()}
