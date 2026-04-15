"""Load every CSV in this folder tree as a named DataFrame dict.

Usage:
    from load_all import load_all
    data = load_all()
    data["batting"]["player_hitter_2001_2020"].head()
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path


def load_all(root: str | Path = "."):
    root = Path(root)
    out: dict[str, dict[str, pd.DataFrame]] = {}
    for csv in root.rglob("*.csv"):
        if "_sources" in csv.parts:
            continue
        cat = csv.parent.name
        name = csv.stem
        out.setdefault(cat, {})[name] = pd.read_csv(csv, encoding="utf-8-sig")
    return out


if __name__ == "__main__":
    data = load_all(Path(__file__).parent)
    total = sum(len(df) for cat in data.values() for df in cat.values())
    print(f"categories: {sorted(data)}")
    print(f"files: {sum(len(c) for c in data.values())}, rows: {total}")
    for cat, files in sorted(data.items()):
        for name, df in sorted(files.items()):
            print(f"  {cat}/{name}: {df.shape}")
