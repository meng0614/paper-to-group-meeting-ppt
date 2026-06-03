#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


def normalize_color(value: str) -> str:
    return value.strip().lstrip("#").upper()


def extract_style(reference_pptx: Path) -> dict:
    colors: Counter[str] = Counter()
    fonts: Counter[str] = Counter()
    with ZipFile(reference_pptx) as zf:
        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            text = zf.read(name).decode("utf-8", "ignore")
            colors.update(normalize_color(c) for c in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', text))
            fonts.update(f for f in re.findall(r'typeface="([^"]+)"', text) if f.strip())

    ignored = {"FFFFFF", "000000", "F2F2F2", "F8F8F8"}
    ranked = [c for c, _ in colors.most_common() if c not in ignored]
    primary = ranked[0] if ranked else "0E2557"
    secondary = ranked[1] if len(ranked) > 1 else "4B649F"
    accent = next((c for c in ranked if c.startswith("FF") or c in {"DC2626", "C00000", "FF0000"}), "FF0000")
    font = fonts.most_common(1)[0][0] if fonts else "Microsoft YaHei"
    if any(token in font.lower() for token in ["theme", "+mn", "+mj"]):
        font = "Microsoft YaHei"

    return {
        "primary_color": primary,
        "secondary_color": secondary,
        "accent_color": accent,
        "neutral_color": "6B7280",
        "light_color": "F4F7FB",
        "title_font": font,
        "body_font": font,
        "title_size": 30,
        "body_size": 19,
        "layout": "reference-inspired",
        "animation": "disable",
        "reference_pptx": str(reference_pptx),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a reusable style block from a reference PPTX.")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    style = extract_style(args.reference.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
