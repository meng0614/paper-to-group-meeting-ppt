#!/usr/bin/env python
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageStat

EMU_W, EMU_H = 12192000, 6858000

DEFAULT_STYLE = {
    "primary_color": "111827",
    "secondary_color": "2563EB",
    "accent_color": "DC2626",
    "neutral_color": "6B7280",
    "light_color": "F8FAFC",
    "title_font": "Microsoft YaHei",
    "body_font": "Microsoft YaHei",
    "title_size": 30,
    "body_size": 18,
    "layout": "visual-first",
    "design_system": "academic-rail",
}

LAYOUTS = [
    "visual-left",
    "visual-right",
    "visual-top",
    "full-visual",
    "comparison",
    "flow",
    "result-focus",
]


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def normalize_style(spec: dict) -> dict:
    style = dict(DEFAULT_STYLE)
    style.update(spec.get("style", {}) or {})
    for key in ["primary_color", "secondary_color", "accent_color", "neutral_color", "light_color"]:
        style[key] = str(style.get(key, DEFAULT_STYLE[key])).strip().lstrip("#").upper()
    style["title_size"] = max(24, min(32, int(style.get("title_size", 30))))
    style["body_size"] = max(15, min(22, int(style.get("body_size", 18))))
    style["design_system"] = str(style.get("design_system", "academic-rail"))
    return style


def sections(spec: dict) -> list[dict]:
    return spec.get("sections") or spec.get("slides") or []


def section_name(sec: dict) -> str:
    if sec.get("section"):
        return str(sec["section"])
    kind = sec.get("kind", "content")
    return {
        "background": "Background",
        "problem": "Problem",
        "method": "Method",
        "algorithm": "Method",
        "experiment": "Experiment",
        "result": "Results",
        "closing": "Conclusion",
    }.get(kind, kind.title())


def choose_layout(sec: dict, idx: int) -> str:
    explicit = sec.get("layout")
    if explicit:
        return explicit
    visual = sec.get("visual") or {}
    phase = str(sec.get("story_phase") or sec.get("section") or "").strip().lower()
    kind = str(sec.get("kind", "content")).strip().lower()
    if visual.get("type") == "comparison":
        return "comparison"
    if visual.get("type") in {"pipeline", "flow"}:
        return "flow"
    if visual.get("type") == "result_bar" or sec.get("kind") == "result":
        return "result-focus"
    if phase in {"problem", "challenge"} and not sec.get("image"):
        return "comparison"
    if phase in {"idea"}:
        return "visual-top"
    if phase in {"takeaway", "conclusion"} or kind in {"closing", "section"}:
        return "full-visual"
    if sec.get("image"):
        try:
            im = Image.open(sec["_image_abs"])
            aspect = im.width / max(1, im.height)
            if aspect > 1.45:
                return "visual-top"
            if aspect < 0.75:
                return "visual-right"
        except Exception:
            pass
        if phase in {"result", "experiment"}:
            return "visual-top"
        if phase in {"method"}:
            return "visual-left" if idx % 2 else "visual-right"
        return "visual-left" if idx % 2 else "visual-right"
    return LAYOUTS[idx % len(LAYOUTS)]


class Ids:
    def __init__(self) -> None:
        self.value = 1

    def next(self) -> int:
        self.value += 1
        return self.value


def rect(ids: Ids, x: int, y: int, w: int, h: int, fill: str, line: str | None = None) -> str:
    sid = ids.next()
    line_xml = f'<a:ln w="10000"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line else '<a:ln><a:noFill/></a:ln>'
    return f"""
    <p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Rect {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
    <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>{line_xml}</p:spPr></p:sp>"""


def text_box(ids: Ids, x: int, y: int, w: int, h: int, text: str, size: float, color: str, font: str, bold: bool = False, fill: str | None = None) -> str:
    paras = []
    for line in str(text or "").split("\n"):
        paras.append(
            f'<a:p><a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}" b="{1 if bold else 0}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{esc(font)}"/><a:ea typeface="{esc(font)}"/></a:rPr>'
            f'<a:t>{esc(line)}</a:t></a:r></a:p>'
        )
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
    sid = ids.next()
    return f"""
    <p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
    <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr>
    <p:txBody><a:bodyPr wrap="square" anchor="t" lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/>{''.join(paras)}</p:txBody></p:sp>"""


def bullet_box(ids: Ids, x: int, y: int, w: int, h: int, items: list[str], size: float, color: str, font: str) -> str:
    paras = []
    for item in items:
        paras.append(
            f'<a:p><a:pPr marL="260000" indent="-150000"><a:buChar char="•"/></a:pPr><a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{esc(font)}"/><a:ea typeface="{esc(font)}"/></a:rPr><a:t>{esc(item)}</a:t></a:r></a:p>'
        )
    sid = ids.next()
    return f"""
    <p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Bullets {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
    <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
    <p:txBody><a:bodyPr wrap="square" anchor="t" lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/>{''.join(paras)}</p:txBody></p:sp>"""


def bullet_box(ids: Ids, x: int, y: int, w: int, h: int, items: list[str], size: float, color: str, font: str) -> str:
    paras = []
    for item in items:
        paras.append(
            f'<a:p><a:pPr marL="260000" indent="-150000"><a:buChar char="&#8226;"/></a:pPr><a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{esc(font)}"/><a:ea typeface="{esc(font)}"/></a:rPr><a:t>{esc(item)}</a:t></a:r></a:p>'
        )
    sid = ids.next()
    return f"""
    <p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Bullets {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
    <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
    <p:txBody><a:bodyPr wrap="square" anchor="t" lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/>{''.join(paras)}</p:txBody></p:sp>"""


def fit_image(path: Path, x: int, y: int, w: int, h: int) -> tuple[int, int, int, int]:
    im = Image.open(path)
    scale = min(w / im.width, h / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    return x + (w - nw) // 2, y + (h - nh) // 2, nw, nh


def pic(ids: Ids, x: int, y: int, w: int, h: int, rid: str) -> str:
    sid = ids.next()
    return f"""
    <p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="Editable Paper Figure {sid}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
    <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
    <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:ln w="10000"><a:solidFill><a:srgbClr val="D7DEEA"/></a:solidFill></a:ln></p:spPr></p:pic>"""


def estimate_len(text: str) -> float:
    total = 0.0
    for ch in str(text or ""):
        if "\u4e00" <= ch <= "\u9fff":
            total += 1.0
        elif ch.isspace():
            total += 0.35
        else:
            total += 0.58
    return total


def clip_by_units(text: str, limit: float, suffix: str = "...") -> str:
    value = str(text or "").strip()
    if estimate_len(value) <= limit:
        return value
    kept: list[str] = []
    total = 0.0
    suffix_units = estimate_len(suffix)
    for ch in value:
        unit = 1.0 if "\u4e00" <= ch <= "\u9fff" else (0.35 if ch.isspace() else 0.58)
        if total + unit + suffix_units > limit:
            break
        kept.append(ch)
        total += unit
    return "".join(kept).rstrip(" ,;:，；：") + suffix


def wrap_by_units(text: str, line_limit: float, max_lines: int = 2) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    lines: list[str] = []
    current: list[str] = []
    total = 0.0
    for ch in value:
        unit = 1.0 if "\u4e00" <= ch <= "\u9fff" else (0.35 if ch.isspace() else 0.58)
        if current and total + unit > line_limit and len(lines) < max_lines - 1:
            lines.append("".join(current).strip())
            current = [ch]
            total = unit
        else:
            current.append(ch)
            total += unit
    if current:
        lines.append("".join(current).strip())
    return "\n".join(lines[:max_lines])


def display_title(sec: dict) -> str:
    raw = sec.get("one_message") or sec.get("title") or sec.get("page_goal") or ""
    clipped = clip_by_units(raw, 58)
    return wrap_by_units(clipped, 34, max_lines=2)


def title_layout(sec: dict, style: dict) -> dict:
    title = display_title(sec)
    title_size = float(style["title_size"])
    length = estimate_len(title)
    if length > 36:
        title_size = max(26.0, title_size - min(4.0, (length - 36) / 10))
    lines = max(1, title.count("\n") + 1)
    title_h = max(680000, int(lines * title_size * 33000 + 160000))
    content_top = 650000 + title_h + 420000
    return {"title": title, "title_size": title_size, "title_h": title_h, "content_top": content_top}


def text_height(text: str, box_w: int, size: float, min_h: int = 260000, max_h: int = 1500000) -> int:
    # Conservative approximation in EMUs. Chinese and Latin mixed text wraps earlier in PowerPoint.
    width_factor = max(0.55, box_w / 3450000)
    capacity = max(14, int(34 * width_factor * (14.5 / max(10, size))))
    lines = 0
    for para in str(text or "").split("\n"):
        units = max(1, int(estimate_len(para)))
        lines += max(1, (units + capacity - 1) // capacity)
    return max(min_h, min(max_h, int(lines * size * 24000 + 120000)))


def background_chrome(ids: Ids, style: dict) -> list[str]:
    return [
        rect(ids, 0, 0, EMU_W, EMU_H, "FFFFFF"),
        rect(ids, 0, 0, 130000, EMU_H, style["secondary_color"]),
        rect(ids, 0, 0, EMU_W, 90000, style["accent_color"]),
    ]


def foreground_chrome(ids: Ids, sec: dict, idx: int, style: dict, title_info: dict) -> list[str]:
    return [
        text_box(ids, 620000, 310000, 2500000, 320000, section_name(sec).upper(), 14, style["accent_color"], style["title_font"], True),
        text_box(ids, 620000, 650000, 10900000, title_info["title_h"], title_info["title"], title_info["title_size"], style["primary_color"], style["title_font"], True),
        text_box(ids, 11200000, 6350000, 500000, 240000, f"{idx:02d}", 10, style["neutral_color"], style["body_font"], False),
    ]


def render_visual_shape(ids: Ids, sec: dict, style: dict, x: int, y: int, w: int, h: int) -> list[str]:
    visual = sec.get("visual") or {}
    vtype = visual.get("type", "concept")
    shapes: list[str] = []
    if vtype == "comparison":
        shapes.append(rect(ids, x, y, w, h, "F8FAFC", "D7DEEA"))
        col_w = (w - 650000) // 2
        shapes.append(rect(ids, x + 180000, y + 350000, col_w, h - 700000, "FFFFFF", "D7DEEA"))
        shapes.append(rect(ids, x + col_w + 470000, y + 350000, col_w, h - 700000, "FFFFFF", "D7DEEA"))
        shapes.append(text_box(ids, x + 360000, y + 560000, col_w - 360000, 360000, visual.get("left_title", "Existing"), 18, style["primary_color"], style["body_font"], True))
        shapes.append(text_box(ids, x + col_w + 650000, y + 560000, col_w - 360000, 360000, visual.get("right_title", "This Work"), 18, style["accent_color"], style["body_font"], True))
        shapes.append(bullet_box(ids, x + 360000, y + 1050000, col_w - 420000, h - 1550000, visual.get("left", [])[:4], 14.5, "222831", style["body_font"]))
        shapes.append(bullet_box(ids, x + col_w + 650000, y + 1050000, col_w - 420000, h - 1550000, visual.get("right", [])[:4], 14.5, "222831", style["body_font"]))
        shapes.append(text_box(ids, x + col_w + 90000, y + h // 2 - 160000, 420000, 320000, "VS", 20, "FFFFFF", style["body_font"], True, style["accent_color"]))
    elif vtype in {"pipeline", "flow"}:
        steps = visual.get("steps", [])[:5]
        n = max(1, len(steps))
        gap = 150000
        box_w = (w - gap * (n - 1)) // n
        for i, step in enumerate(steps):
            sx = x + i * (box_w + gap)
            fill = style["accent_color"] if step.get("highlight") else "F8FAFC"
            color = "FFFFFF" if step.get("highlight") else "222831"
            shapes.append(rect(ids, sx, y + 650000, box_w, h - 1300000, fill, "D7DEEA"))
            shapes.append(text_box(ids, sx + 130000, y + 850000, box_w - 260000, 380000, step.get("label", f"Step {i+1}"), 16, color, style["body_font"], True))
            shapes.append(text_box(ids, sx + 130000, y + 1320000, box_w - 260000, 900000, step.get("detail", ""), 12.5, color, style["body_font"]))
            if i < n - 1:
                shapes.append(text_box(ids, sx + box_w - 20000, y + h // 2 - 160000, 280000, 320000, "→", 22, style["accent_color"], style["body_font"], True))
        if visual.get("insight"):
            shapes.append(text_box(ids, x + 200000, y + h - 500000, w - 400000, 320000, visual["insight"], 15, "FFFFFF", style["body_font"], True, style["secondary_color"]))
    elif vtype == "result_bar":
        shapes.append(rect(ids, x, y, w, h, "F8FAFC", "D7DEEA"))
        items = visual.get("items", [])[:5]
        max_value = max([float(item.get("value", 0)) for item in items] + [1.0])
        for i, item in enumerate(items):
            row_y = y + 650000 + i * 520000
            value = float(item.get("value", 0))
            bar_w = int((w - 3100000) * value / max_value)
            fill = style["accent_color"] if item.get("highlight") else style["secondary_color"]
            shapes.append(text_box(ids, x + 280000, row_y, 1700000, 300000, item.get("label", ""), 13, "222831", style["body_font"], True))
            shapes.append(rect(ids, x + 2100000, row_y + 50000, w - 3300000, 220000, "E8EEF7"))
            shapes.append(rect(ids, x + 2100000, row_y + 50000, bar_w, 220000, fill))
            shapes.append(text_box(ids, x + 2200000 + bar_w, row_y, 900000, 300000, f"{item.get('value', '')}{visual.get('unit', '')}", 13, fill, style["body_font"], True))
        if visual.get("so_what"):
            shapes.append(text_box(ids, x + 260000, y + h - 650000, w - 520000, 400000, visual["so_what"], 16, "FFFFFF", style["body_font"], True, style["accent_color"]))
    else:
        shapes.append(rect(ids, x, y, w, h, "F8FAFC", "D7DEEA"))
        shapes.append(text_box(ids, x + 350000, y + 650000, w - 700000, 900000, visual.get("headline") or sec.get("page_goal") or sec.get("title", ""), 23, style["primary_color"], style["title_font"], True))
        shapes.append(text_box(ids, x + 350000, y + 1700000, w - 700000, 900000, visual.get("insight") or sec.get("content", ""), 16, "222831", style["body_font"]))
    return shapes


def render_visual_shape(ids: Ids, sec: dict, style: dict, x: int, y: int, w: int, h: int) -> list[str]:
    visual = sec.get("visual") or {}
    vtype = visual.get("type", "concept")
    shapes: list[str] = []
    if vtype == "comparison":
        shapes.append(rect(ids, x, y, w, h, "F8FAFC", "D7DEEA"))
        col_w = (w - 700000) // 2
        card_h = max(1600000, h - 760000)
        left_x = x + 190000
        right_x = x + col_w + 520000
        card_y = y + 380000
        shapes.append(rect(ids, left_x, card_y, col_w, card_h, "FFFFFF", "D7DEEA"))
        shapes.append(rect(ids, right_x, card_y, col_w, card_h, "FFFFFF", "D7DEEA"))
        shapes.append(text_box(ids, left_x + 180000, card_y + 220000, col_w - 360000, 430000, clip_by_units(visual.get("left_title", "Existing"), 28), 16, style["primary_color"], style["body_font"], True))
        shapes.append(text_box(ids, right_x + 180000, card_y + 220000, col_w - 360000, 430000, clip_by_units(visual.get("right_title", "This Work"), 28), 16, style["accent_color"], style["body_font"], True))
        shapes.append(bullet_box(ids, left_x + 220000, card_y + 760000, col_w - 420000, card_h - 960000, [clip_by_units(v, 45) for v in (visual.get("left", []) or [])[:3]], 13.2, "222831", style["body_font"]))
        shapes.append(bullet_box(ids, right_x + 220000, card_y + 760000, col_w - 420000, card_h - 960000, [clip_by_units(v, 45) for v in (visual.get("right", []) or [])[:3]], 13.2, "222831", style["body_font"]))
        shapes.append(text_box(ids, x + col_w + 105000, y + h // 2 - 160000, 390000, 320000, "VS", 18, "FFFFFF", style["body_font"], True, style["accent_color"]))
    elif vtype in {"pipeline", "flow"}:
        steps = (visual.get("steps", []) or [])[:4]
        n = max(1, len(steps))
        gap = 170000
        box_w = (w - gap * (n - 1)) // n
        box_y = y + 620000
        box_h = max(1400000, h - 1280000)
        for i, step in enumerate(steps):
            sx = x + i * (box_w + gap)
            fill = style["accent_color"] if step.get("highlight") else "F8FAFC"
            color = "FFFFFF" if step.get("highlight") else "222831"
            shapes.append(rect(ids, sx, box_y, box_w, box_h, fill, "D7DEEA"))
            shapes.append(text_box(ids, sx + 130000, box_y + 190000, box_w - 260000, 430000, clip_by_units(step.get("label", f"Step {i+1}"), 28), 15, color, style["body_font"], True))
            shapes.append(text_box(ids, sx + 130000, box_y + 720000, box_w - 260000, box_h - 900000, clip_by_units(step.get("detail", ""), 62), 12.2, color, style["body_font"]))
            if i < n - 1:
                shapes.append(text_box(ids, sx + box_w - 10000, y + h // 2 - 160000, 260000, 320000, "->", 18, style["accent_color"], style["body_font"], True))
        if visual.get("insight"):
            insight = clip_by_units(visual["insight"], 80)
            shapes.append(text_box(ids, x + 220000, y + h - 500000, w - 440000, 330000, insight, 14, "FFFFFF", style["body_font"], True, style["secondary_color"]))
    elif vtype == "result_bar":
        shapes.append(rect(ids, x, y, w, h, "F8FAFC", "D7DEEA"))
        items = (visual.get("items", []) or [])[:4]
        max_value = max([float(item.get("value", 0)) for item in items] + [1.0])
        row_gap = min(520000, max(390000, (h - 1350000) // max(1, len(items))))
        for i, item in enumerate(items):
            row_y = y + 580000 + i * row_gap
            value = float(item.get("value", 0))
            bar_w = int((w - 3300000) * value / max_value)
            fill = style["accent_color"] if item.get("highlight") else style["secondary_color"]
            shapes.append(text_box(ids, x + 280000, row_y, 1800000, 330000, clip_by_units(item.get("label", ""), 24), 12.5, "222831", style["body_font"], True))
            shapes.append(rect(ids, x + 2200000, row_y + 65000, w - 3500000, 200000, "E8EEF7"))
            shapes.append(rect(ids, x + 2200000, row_y + 65000, bar_w, 200000, fill))
            shapes.append(text_box(ids, x + 2250000 + bar_w, row_y, 850000, 330000, f"{item.get('value', '')}{visual.get('unit', '')}", 12.5, fill, style["body_font"], True))
        if visual.get("so_what"):
            so_what = clip_by_units(visual["so_what"], 82)
            so_h = text_height(so_what, w - 520000, 14.5, min_h=360000, max_h=620000)
            shapes.append(text_box(ids, x + 260000, y + h - so_h - 220000, w - 520000, so_h, so_what, 14.5, "FFFFFF", style["body_font"], True, style["accent_color"]))
    else:
        shapes.append(rect(ids, x, y, w, h, "F8FAFC", "D7DEEA"))
        headline = clip_by_units(visual.get("headline") or sec.get("page_goal") or sec.get("title", ""), 70)
        insight = clip_by_units(visual.get("insight") or sec.get("content", ""), 95)
        head_h = text_height(headline, w - 800000, 21, min_h=620000, max_h=1280000)
        shapes.append(text_box(ids, x + 400000, y + 520000, w - 800000, head_h, headline, 21, style["primary_color"], style["title_font"], True))
        insight_y = y + 520000 + head_h + 180000
        if insight and insight_y < y + h - 450000:
            insight_h = min(text_height(insight, w - 800000, 14.8, min_h=420000, max_h=900000), y + h - insight_y - 280000)
            if insight_h > 300000:
                shapes.append(text_box(ids, x + 400000, insight_y, w - 800000, insight_h, insight, 14.8, "222831", style["body_font"]))
    return shapes


def render_slide(sec: dict, idx: int, out_dir: Path, style: dict, image_rids: dict[Path, str]) -> tuple[str, str]:
    ids = Ids()
    title_info = title_layout(sec, style)
    shapes = background_chrome(ids, style)
    layout = choose_layout(sec, idx)
    text_items = [clip_by_units(item, 58) for item in (sec.get("bullets") or [])[:3]]
    body = sec.get("body") or sec.get("content") or ""
    body = clip_by_units(body, 125)

    top = max(1540000, int(title_info["content_top"]))
    bottom = 6220000
    available_h = max(1600000, bottom - top)
    if layout == "visual-top":
        visual_h = min(max(1800000, int(available_h * 0.58)), max(1200000, available_h - 780000), 3500000)
        visual_box = (760000, top, 10650000, visual_h)
        text_y = top + visual_h + 260000
        text_box_area = (1050000, text_y, 9600000, max(520000, bottom - text_y))
    elif layout == "full-visual":
        visual_h = min(max(1800000, available_h - 760000), 4100000)
        visual_box = (760000, top, 10650000, visual_h)
        text_y = top + visual_h + 180000
        text_box_area = (1050000, text_y, 9600000, max(420000, bottom - text_y))
    elif layout == "visual-right":
        visual_box = (4550000, top, 7050000, available_h)
        text_box_area = (720000, top + 80000, 3500000, available_h - 160000)
    else:
        visual_box = (760000, top, 7050000, available_h)
        text_box_area = (8250000, top + 80000, 3500000, available_h - 160000)

    if sec.get("image"):
        img_path = (out_dir / sec["image"]).resolve()
        if img_path.exists():
            x, y, w, h = fit_image(img_path, *visual_box)
            shapes.append(pic(ids, x, y, w, h, image_rids[img_path]))
        else:
            shapes.extend(render_visual_shape(ids, sec, style, *visual_box))
    else:
        shapes.extend(render_visual_shape(ids, sec, style, *visual_box))

    tx, ty, tw, th = text_box_area
    takeaway = clip_by_units(sec.get("audience_takeaway") or sec.get("page_goal", ""), 72)
    takeaway_text = "5-second takeaway\n" + takeaway
    takeaway_h = min(text_height(takeaway_text, tw, 14.2, min_h=520000, max_h=820000), max(420000, th))
    shapes.append(text_box(ids, tx, ty, tw, takeaway_h, takeaway_text, 14.2, "222831", style["body_font"], True, style["light_color"]))
    cursor_y = ty + takeaway_h + 170000
    remaining = ty + th - cursor_y
    if body and layout != "full-visual" and remaining > 520000:
        body_h = min(text_height(body, tw, 13.8, min_h=380000, max_h=880000), remaining)
        shapes.append(text_box(ids, tx, cursor_y, tw, body_h, body, 13.8, "222831", style["body_font"]))
        cursor_y += body_h + 160000
    remaining = ty + th - cursor_y
    if text_items and layout not in {"full-visual", "visual-top"}:
        bullet_items = text_items[:2]
        while bullet_items:
            needed_h = text_height("\n".join(bullet_items), tw - 200000, 13.6, min_h=420000, max_h=1250000)
            if needed_h <= remaining:
                shapes.append(bullet_box(ids, tx + 100000, cursor_y, tw - 200000, needed_h, bullet_items, 13.6, "222831", style["body_font"]))
                break
            bullet_items = bullet_items[:-1]

    shapes.extend(foreground_chrome(ids, sec, idx, style, title_info))

    xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{''.join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
    if sec.get("image"):
        img_path = (out_dir / sec["image"]).resolve()
        if img_path in image_rids:
            rels.append(f'<Relationship Id="{image_rids[img_path]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{img_path.name}"/>')
    rel_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""
    return xml, rel_xml


def build(spec: dict, out_dir: Path) -> Path:
    style = normalize_style(spec)
    secs = sections(spec)
    out_dir.mkdir(parents=True, exist_ok=True)
    pptx = out_dir / "final_presentation_generated.pptx"
    image_paths: list[Path] = []
    for sec in secs:
        if sec.get("image"):
            p = (out_dir / sec["image"]).resolve()
            if p.exists() and p not in image_paths:
                image_paths.append(p)
                sec["_image_abs"] = p
    image_rids = {p: f"rIdImg{i+1}" for i, p in enumerate(image_paths)}
    slide_ids = "".join(f'<p:sldId id="{256+i}" r:id="rId{i+1}"/>' for i in range(len(secs)))
    presentation_rels = "".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>' for i in range(len(secs)))
    presentation_rels += '<Relationship Id="rId101" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    overrides = "".join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(len(secs)))
    with ZipFile(pptx, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="jpg" ContentType="image/jpeg"/><Default Extension="jpeg" ContentType="image/jpeg"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>{overrides}</Types>""")
        z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>""")
        z.writestr("ppt/presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId101"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>""")
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{presentation_rels}</Relationships>""")
        z.writestr("ppt/theme/theme1.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="AcademicEditable"><a:themeElements><a:clrScheme name="AcademicEditable"><a:dk1><a:srgbClr val="222831"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="{style['primary_color']}"/></a:dk2><a:lt2><a:srgbClr val="{style['light_color']}"/></a:lt2><a:accent1><a:srgbClr val="{style['secondary_color']}"/></a:accent1><a:accent2><a:srgbClr val="{style['accent_color']}"/></a:accent2><a:accent3><a:srgbClr val="{style['neutral_color']}"/></a:accent3><a:accent4><a:srgbClr val="D7DEEA"/></a:accent4><a:accent5><a:srgbClr val="7DB1CD"/></a:accent5><a:accent6><a:srgbClr val="31489F"/></a:accent6><a:hlink><a:srgbClr val="{style['secondary_color']}"/></a:hlink><a:folHlink><a:srgbClr val="{style['primary_color']}"/></a:folHlink></a:clrScheme><a:fontScheme name="{esc(style['title_font'])}"><a:majorFont><a:latin typeface="{esc(style['title_font'])}"/><a:ea typeface="{esc(style['title_font'])}"/></a:majorFont><a:minorFont><a:latin typeface="{esc(style['body_font'])}"/><a:ea typeface="{esc(style['body_font'])}"/></a:minorFont></a:fontScheme><a:fmtScheme name="simple"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle/></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>""")
        z.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""")
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""")
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")
        for p in image_paths:
            z.write(p, f"ppt/media/{p.name}")
        for i, sec in enumerate(secs, 1):
            sx, rx = render_slide(sec, i, out_dir, style, image_rids)
            z.writestr(f"ppt/slides/slide{i}.xml", sx)
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rx)
    shutil_path = out_dir / "final_presentation.pptx"
    if shutil_path != pptx:
        shutil_path.write_bytes(pptx.read_bytes())
    return pptx


def main() -> None:
    parser = argparse.ArgumentParser(description="Build editable PowerPoint deck from the same section spec used for HTML reports.")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    print(build(spec, args.out.resolve()))


if __name__ == "__main__":
    main()
