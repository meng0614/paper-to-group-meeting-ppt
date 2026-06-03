#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from PIL import Image, ImageFilter


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def normalize_box(box, width: int, height: int) -> tuple[int, int, int, int]:
    if all(isinstance(v, float) and 0 <= v <= 1 for v in box):
        x1, y1, x2, y2 = [int(v * (width if i % 2 == 0 else height)) for i, v in enumerate(box)]
    else:
        x1, y1, x2, y2 = [int(v) for v in box]
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    return x1, y1, x2, y2


def trim_white_margin(im: Image.Image, threshold: int = 246, pad: int = 8) -> Image.Image:
    gray = im.convert("L")
    w, h = gray.size
    pix = gray.load()
    rows = []
    cols = []
    for y in range(h):
        if any(pix[x, y] < threshold for x in range(w)):
            rows.append(y)
    for x in range(w):
        if any(pix[x, y] < threshold for y in range(h)):
            cols.append(x)
    if not rows or not cols:
        return im
    x1 = clamp(min(cols) - pad, 0, w)
    y1 = clamp(min(rows) - pad, 0, h)
    x2 = clamp(max(cols) + pad + 1, 0, w)
    y2 = clamp(max(rows) + pad + 1, 0, h)
    if x2 <= x1 or y2 <= y1:
        return im
    return im.crop((x1, y1, x2, y2))


def edge_touches_content(im: Image.Image, threshold: int = 246, margin: int = 8, ratio: float = 0.015) -> dict[str, bool]:
    gray = im.convert("L")
    w, h = gray.size
    pix = gray.load()

    def dark_count(xs, ys) -> int:
        count = 0
        for y in ys:
            for x in xs:
                if pix[x, y] < threshold:
                    count += 1
        return count

    m = max(4, min(margin, w // 8, h // 8))
    left_area = max(1, m * h)
    right_area = max(1, m * h)
    top_area = max(1, w * m)
    bottom_area = max(1, w * m)
    return {
        "left": dark_count(range(0, m), range(h)) / left_area > ratio,
        "right": dark_count(range(max(0, w - m), w), range(h)) / right_area > ratio,
        "top": dark_count(range(w), range(0, m)) / top_area > ratio,
        "bottom": dark_count(range(w), range(max(0, h - m), h)) / bottom_area > ratio,
    }


def auto_expand_box(im: Image.Image, box: tuple[int, int, int, int], step: int, max_rounds: int) -> tuple[int, int, int, int]:
    page_w, page_h = im.size
    x1, y1, x2, y2 = box
    for _ in range(max_rounds):
        cropped = im.crop((x1, y1, x2, y2))
        touches = edge_touches_content(cropped)
        if not any(touches.values()):
            break
        old = (x1, y1, x2, y2)
        if touches["left"]:
            x1 = clamp(x1 - step, 0, page_w)
        if touches["right"]:
            x2 = clamp(x2 + step, 0, page_w)
        if touches["top"]:
            y1 = clamp(y1 - step, 0, page_h)
        if touches["bottom"]:
            y2 = clamp(y2 + step, 0, page_h)
        if (x1, y1, x2, y2) == old:
            break
    return x1, y1, x2, y2


def component_expand_box(
    im: Image.Image,
    seed_box: tuple[int, int, int, int],
    search_pad: int = 260,
    threshold: int = 246,
    dilate_size: int = 13,
    dilate_rounds: int = 2,
    output_pad: int = 10,
) -> tuple[int, int, int, int]:
    page_w, page_h = im.size
    sx1, sy1, sx2, sy2 = seed_box
    wx1 = clamp(sx1 - search_pad, 0, page_w)
    wy1 = clamp(sy1 - search_pad, 0, page_h)
    wx2 = clamp(sx2 + search_pad, 0, page_w)
    wy2 = clamp(sy2 + search_pad, 0, page_h)
    region = im.crop((wx1, wy1, wx2, wy2)).convert("L")
    mask = region.point(lambda p: 255 if p < threshold else 0)
    for _ in range(max(0, dilate_rounds)):
        mask = mask.filter(ImageFilter.MaxFilter(max(3, dilate_size | 1)))

    w, h = mask.size
    pix = mask.load()
    visited = bytearray(w * h)
    seed_local = (
        clamp(sx1 - wx1, 0, w - 1),
        clamp(sy1 - wy1, 0, h - 1),
        clamp(sx2 - wx1, 0, w),
        clamp(sy2 - wy1, 0, h),
    )
    union = None

    def overlaps_seed(bbox: tuple[int, int, int, int]) -> bool:
        x1, y1, x2, y2 = bbox
        a1, b1, a2, b2 = seed_local
        return x1 < a2 and x2 > a1 and y1 < b2 and y2 > b1

    for start_y in range(h):
        for start_x in range(w):
            idx = start_y * w + start_x
            if visited[idx] or pix[start_x, start_y] == 0:
                visited[idx] = 1
                continue
            stack = [(start_x, start_y)]
            visited[idx] = 1
            min_x = max_x = start_x
            min_y = max_y = start_y
            count = 0
            while stack:
                x, y = stack.pop()
                count += 1
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if nx < 0 or ny < 0 or nx >= w or ny >= h:
                        continue
                    nidx = ny * w + nx
                    if visited[nidx]:
                        continue
                    visited[nidx] = 1
                    if pix[nx, ny] != 0:
                        stack.append((nx, ny))
            bbox = (min_x, min_y, max_x + 1, max_y + 1)
            if count > 12 and overlaps_seed(bbox):
                if union is None:
                    union = bbox
                else:
                    union = (
                        min(union[0], bbox[0]),
                        min(union[1], bbox[1]),
                        max(union[2], bbox[2]),
                        max(union[3], bbox[3]),
                    )

    if union is None:
        return seed_box
    x1, y1, x2, y2 = union
    return (
        clamp(wx1 + x1 - output_pad, 0, page_w),
        clamp(wy1 + y1 - output_pad, 0, page_h),
        clamp(wx1 + x2 + output_pad, 0, page_w),
        clamp(wy1 + y2 + output_pad, 0, page_h),
    )


def upscale_if_needed(im: Image.Image, min_width: int, min_height: int) -> Image.Image:
    w, h = im.size
    scale = max(min_width / max(1, w), min_height / max(1, h), 1.0)
    if scale <= 1.01:
        return im
    return im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)


def crop_region(page_path: Path, box, out_path: Path, padding: int, trim: bool, min_width: int, min_height: int, auto_expand: bool, expand_step: int, max_expand_rounds: int, component_expand: bool, search_pad: int) -> None:
    im = Image.open(page_path).convert("RGB")
    w, h = im.size
    x1, y1, x2, y2 = normalize_box(box, w, h)
    if component_expand:
        x1, y1, x2, y2 = component_expand_box(im, (x1, y1, x2, y2), search_pad=search_pad)
    x1 = clamp(x1 - padding, 0, w)
    y1 = clamp(y1 - padding, 0, h)
    x2 = clamp(x2 + padding, 0, w)
    y2 = clamp(y2 + padding, 0, h)
    if auto_expand:
        x1, y1, x2, y2 = auto_expand_box(im, (x1, y1, x2, y2), expand_step, max_expand_rounds)
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid crop box {box} for {page_path}")
    cropped = im.crop((x1, y1, x2, y2))
    if trim:
        cropped = trim_white_margin(cropped)
    cropped = upscale_if_needed(cropped, min_width, min_height)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(out_path, "PNG")


def main():
    ap = argparse.ArgumentParser(description="Crop figures/tables/algorithms from rendered PDF page images.")
    ap.add_argument("--pages", type=Path, required=True, help="Directory containing page-01.png etc.")
    ap.add_argument("--spec", type=Path, required=True, help="JSON list of crop objects.")
    ap.add_argument("--out", type=Path, required=True, help="Output figures directory.")
    ap.add_argument("--padding", type=int, default=18, help="Pixels to expand every crop box before saving.")
    ap.add_argument("--auto-expand", action="store_true", help="Expand crop edges automatically when content touches the crop boundary.")
    ap.add_argument("--component-expand", action="store_true", help="Crop the connected visual component intersecting the seed box; helps recover complete paper figures while excluding page headers/text.")
    ap.add_argument("--search-pad", type=int, default=280, help="Search padding for component expansion.")
    ap.add_argument("--expand-step", type=int, default=60, help="Pixels added per auto-expand round on touched edges.")
    ap.add_argument("--max-expand-rounds", type=int, default=8, help="Maximum edge-expansion rounds.")
    ap.add_argument("--trim", action="store_true", help="Trim large white margins after cropping.")
    ap.add_argument("--min-width", type=int, default=900, help="Upscale small crops to at least this width.")
    ap.add_argument("--min-height", type=int, default=420, help="Upscale small crops to at least this height.")
    args = ap.parse_args()

    crops = json.loads(args.spec.read_text(encoding="utf-8"))
    for item in crops:
        page = int(item["page"])
        page_path = args.pages / f"page-{page:02d}.png"
        out_path = args.out / item["file"]
        padding = int(item.get("padding", args.padding))
        crop_region(
            page_path,
            item["box"],
            out_path,
            padding,
            args.trim or bool(item.get("trim")),
            args.min_width,
            args.min_height,
            args.auto_expand or bool(item.get("auto_expand")),
            int(item.get("expand_step", args.expand_step)),
            int(item.get("max_expand_rounds", args.max_expand_rounds)),
            args.component_expand or bool(item.get("component_expand")),
            int(item.get("search_pad", args.search_pad)),
        )
        print(out_path)


if __name__ == "__main__":
    main()
