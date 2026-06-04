#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_reference_design_philosophy import extract


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Deprecated compatibility entrypoint. It no longer extracts colors or fonts; "
            "it extracts reference PPT design philosophy only."
        )
    )
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = extract(args.reference.resolve())
    data["deprecated_entrypoint"] = "extract_reference_style.py"
    data["replacement"] = "extract_reference_design_philosophy.py"
    data["warning"] = "Colors and fonts are intentionally ignored."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
