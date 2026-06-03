#!/usr/bin/env python
import argparse
import shutil
import subprocess
from pathlib import Path


def render_with_pdftoppm(pdf: Path, out_dir: Path, dpi: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"
    exe = shutil.which("pdftoppm")
    if not exe:
        raise RuntimeError("pdftoppm not found. Install Poppler or TeX Live tools, or render PDF pages manually.")
    subprocess.run([exe, "-png", "-r", str(dpi), str(pdf), str(prefix)], check=True)


def main():
    ap = argparse.ArgumentParser(description="Render PDF pages to PNG files for figure/table/algorithm cropping.")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=220, help="Render DPI. 220+ is recommended for readable PPT figures.")
    args = ap.parse_args()
    render_with_pdftoppm(args.pdf, args.out, args.dpi)
    print(f"Rendered pages to {args.out}")


if __name__ == "__main__":
    main()
