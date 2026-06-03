#!/usr/bin/env python
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

EMU_W, EMU_H = 12192000, 6858000

DEFAULT_STYLE = {
    "primary_color": "0E2557",
    "secondary_color": "4B649F",
    "accent_color": "FF0000",
    "neutral_color": "6B7280",
    "light_color": "F4F7FB",
    "title_font": "Microsoft YaHei",
    "body_font": "Microsoft YaHei",
    "title_size": 30,
    "body_size": 19,
    "layout": "auto",
    "animation": "disable",
}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def normalize_style(spec: dict) -> dict:
    style = dict(DEFAULT_STYLE)
    style.update(spec.get("style", {}) or {})
    for key in ["primary_color", "secondary_color", "accent_color", "neutral_color", "light_color"]:
        style[key] = str(style.get(key, "")).strip().lstrip("#").upper() or DEFAULT_STYLE[key]
    style["title_size"] = max(24, min(40, int(style.get("title_size", 30))))
    style["body_size"] = max(15, min(26, int(style.get("body_size", 19))))
    return style


def fit_image(path: Path, x: int, y: int, w: int, h: int) -> tuple[int, int, int, int]:
    im = Image.open(path)
    iw, ih = im.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    return x + (w - nw) // 2, y + (h - nh) // 2, nw, nh


class ShapeIds:
    def __init__(self) -> None:
        self.n = 1

    def next(self) -> int:
        self.n += 1
        return self.n


def rect(ids: ShapeIds, x: int, y: int, w: int, h: int, fill: str, line: str | None = None) -> str:
    sid = ids.next()
    line_xml = (
        f'<a:ln w="9000"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        if line else '<a:ln><a:noFill/></a:ln>'
    )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{sid}" name="Rect {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>{line_xml}</p:spPr>
    </p:sp>"""


def text_box(
    ids: ShapeIds,
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    size: float = 20,
    color: str = "222831",
    bold: bool = False,
    fill: str | None = None,
    font: str = "Microsoft YaHei",
) -> str:
    paras = []
    for line in str(text).split("\n"):
        paras.append(
            f'<a:p><a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}" b="{1 if bold else 0}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{esc(font)}"/><a:ea typeface="{esc(font)}"/></a:rPr>'
            f"<a:t>{esc(line)}</a:t></a:r></a:p>"
        )
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
    sid = ids.next()
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(paras)}</p:txBody>
    </p:sp>"""


def bullets(ids: ShapeIds, x: int, y: int, w: int, h: int, items: list[str], size: float, color: str, font: str) -> str:
    paras = []
    for item in items or []:
        paras.append(
            '<a:p><a:pPr marL="260000" indent="-160000"><a:buChar char="•"/></a:pPr>'
            f'<a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{esc(font)}"/><a:ea typeface="{esc(font)}"/></a:rPr><a:t>{esc(item)}</a:t></a:r></a:p>'
        )
    sid = ids.next()
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{sid}" name="Bullets {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(paras)}</p:txBody>
    </p:sp>"""


def pic(ids: ShapeIds, x: int, y: int, w: int, h: int, rid: str = "rId2") -> str:
    sid = ids.next()
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{sid}" name="Figure {sid}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:ln w="12000"><a:solidFill><a:srgbClr val="D7DEEA"/></a:solidFill></a:ln></p:spPr>
    </p:pic>"""


def visual_shapes(ids: ShapeIds, slide: dict, style: dict) -> str:
    visual = slide.get("visual") or {}
    vtype = visual.get("type", "concept")
    primary = style["primary_color"]
    secondary = style["secondary_color"]
    accent = style["accent_color"]
    neutral = style["neutral_color"]
    font = style["body_font"]
    out: list[str] = []

    if vtype == "comparison":
        out.append(rect(ids, 1050000, 1420000, 4650000, 3500000, "F8FAFC", "D7DEEA"))
        out.append(rect(ids, 6250000, 1420000, 4650000, 3500000, "F8FAFC", "D7DEEA"))
        out.append(text_box(ids, 1250000, 1600000, 4000000, 360000, visual.get("left_title", "Existing"), 19, primary, True, font=font))
        out.append(text_box(ids, 6450000, 1600000, 4000000, 360000, visual.get("right_title", "This Work"), 19, accent, True, font=font))
        out.append(bullets(ids, 1250000, 2140000, 3900000, 2100000, visual.get("left", []), 16, "222831", font))
        out.append(bullets(ids, 6450000, 2140000, 3900000, 2100000, visual.get("right", []), 16, "222831", font))
        out.append(text_box(ids, 5320000, 2860000, 800000, 340000, "VS", 24, "FFFFFF", True, accent, font))
        if visual.get("insight"):
            out.append(text_box(ids, 1450000, 5150000, 9000000, 420000, visual["insight"], 18, "FFFFFF", True, secondary, font))
    elif vtype in {"pipeline", "flow"}:
        steps = visual.get("steps", [])
        n = max(1, len(steps))
        x0, y0 = 1050000, 2060000
        box_w = min(2300000, 9300000 // n - 180000)
        gap = (9300000 - box_w * n) // max(1, n - 1) if n > 1 else 0
        for i, step in enumerate(steps):
            x = x0 + i * (box_w + gap)
            fill = accent if step.get("highlight") else secondary if i == n - 1 else "F8FAFC"
            color = "FFFFFF" if fill in {accent, secondary, primary} else "222831"
            out.append(rect(ids, x, y0, box_w, 1650000, fill, "D7DEEA"))
            out.append(text_box(ids, x + 130000, y0 + 220000, box_w - 260000, 360000, step.get("label", f"Step {i+1}"), 17, color, True, font=font))
            out.append(text_box(ids, x + 130000, y0 + 720000, box_w - 260000, 620000, step.get("detail", ""), 13.5, color, False, font=font))
            if i < n - 1:
                out.append(text_box(ids, x + box_w + 60000, y0 + 590000, 450000, 360000, "→", 28, accent, True, font=font))
        if visual.get("insight"):
            out.append(text_box(ids, 1300000, 4550000, 9000000, 520000, visual["insight"], 20, primary, True, font=font))
    elif vtype == "result_bar":
        items = visual.get("items", [])
        max_value = max([float(item.get("value", 0)) for item in items] + [1.0])
        x0, y0 = 2300000, 1600000
        for i, item in enumerate(items[:5]):
            y = y0 + i * 650000
            value = float(item.get("value", 0))
            bar_w = int(6500000 * value / max_value)
            fill = accent if item.get("highlight") else secondary
            out.append(text_box(ids, 1100000, y, 1900000, 330000, item.get("label", ""), 15, "222831", True, font=font))
            out.append(rect(ids, x0, y + 30000, 6500000, 300000, "E8EEF7", None))
            out.append(rect(ids, x0, y + 30000, bar_w, 300000, fill, None))
            out.append(text_box(ids, x0 + bar_w + 100000, y, 1200000, 330000, f"{item.get('value', '')}{visual.get('unit', '')}", 15, fill, True, font=font))
        if visual.get("so_what"):
            out.append(text_box(ids, 1500000, 5050000, 9000000, 550000, visual["so_what"], 22, "FFFFFF", True, accent, font))
    else:
        headline = visual.get("headline") or slide.get("page_goal") or slide.get("title", "")
        out.append(rect(ids, 1450000, 1680000, 9100000, 2950000, "F8FAFC", "D7DEEA"))
        out.append(text_box(ids, 1750000, 2140000, 8500000, 680000, headline, 24, primary, True, font=font))
        out.append(bullets(ids, 1900000, 3120000, 7800000, 1200000, slide.get("bullets", [])[:3], 18, "222831", font))
    return "".join(out)


def table_shapes(ids: ShapeIds, table: dict, style: dict) -> str:
    cols = table.get("columns", [])
    rows = table.get("rows", [])
    if not cols:
        return ""
    x0, y0 = 1050000, 1500000
    total_w = 9900000
    col_w = total_w // len(cols)
    row_h = 560000
    out = []
    for j, col in enumerate(cols):
        out.append(text_box(ids, x0 + j * col_w, y0, col_w, row_h, col, 13, "FFFFFF", True, style["primary_color"], style["title_font"]))
    for i, row in enumerate(rows, 1):
        fill = "F8FAFC" if i % 2 else "FFFFFF"
        for j, cell in enumerate(row):
            out.append(text_box(ids, x0 + j * col_w, y0 + i * row_h, col_w, row_h, cell, 11.5, "222831", False, fill, style["body_font"]))
    return "".join(out)


def slide_xml(slide: dict, idx: int, out_dir: Path, style: dict) -> str:
    ids = ShapeIds()
    kind = slide.get("kind", "content")
    dark = kind in {"cover", "section", "closing"}
    bg = style["primary_color"] if dark else style["light_color"]
    title_color = "FFFFFF" if dark else "FFFFFF"
    body_color = "FFFFFF" if dark else "222831"
    shapes: list[str] = []

    if dark:
        shapes.append(rect(ids, 0, 0, EMU_W, 280000, style["accent_color"]))
        shapes.append(rect(ids, 0, 5750000, EMU_W, 180000, style["secondary_color"]))
        title_x, title_y, title_w, title_h = 620000, 1180000, 10800000, 900000
    else:
        shapes.append(rect(ids, 0, 0, EMU_W, 780000, style["primary_color"]))
        shapes.append(rect(ids, 0, 780000, EMU_W, 90000, style["accent_color"]))
        shapes.append(rect(ids, 560000, 1210000, 140000, 4380000, style["secondary_color"]))
        shapes.append(rect(ids, 790000, 1180000, 11050000, 5050000, "FFFFFF", "D7DEEA"))
        title_x, title_y, title_w, title_h = 620000, 190000, 11100000, 420000

    shapes.append(text_box(ids, title_x, title_y, title_w, title_h, slide.get("title", f"Slide {idx}"), style["title_size"], title_color, True, font=style["title_font"]))
    if slide.get("subtitle"):
        shapes.append(text_box(ids, 720000, 2180000 if dark else 900000, 10000000, 420000, slide["subtitle"], max(14, style["body_size"] - 3), "DDEAF3" if dark else style["neutral_color"], font=style["body_font"]))

    image = slide.get("image")
    table = slide.get("table")
    visual = slide.get("visual")
    if image:
        img_path = (out_dir / image).resolve()
        aspect = Image.open(img_path).size[0] / Image.open(img_path).size[1]
        if kind == "result" or aspect > 1.55:
            x, y, w, h = fit_image(img_path, 1050000, 1280000, 9900000, 3550000)
            shapes.append(pic(ids, x, y, w, h))
            shapes.append(bullets(ids, 1050000, 5080000, 9600000, 850000, slide.get("bullets", []), max(14, style["body_size"] - 4), body_color, style["body_font"]))
        elif kind == "algorithm" or aspect < 0.85:
            shapes.append(bullets(ids, 1050000, 1450000, 4550000, 4200000, slide.get("bullets", []), max(15, style["body_size"] - 3), body_color, style["body_font"]))
            x, y, w, h = fit_image(img_path, 6500000, 1220000, 4700000, 5000000)
            shapes.append(pic(ids, x, y, w, h))
        else:
            shapes.append(bullets(ids, 1050000, 1450000, 4300000, 4200000, slide.get("bullets", []), max(15, style["body_size"] - 3), body_color, style["body_font"]))
            x, y, w, h = fit_image(img_path, 5550000, 1220000, 5850000, 5000000)
            shapes.append(pic(ids, x, y, w, h))
    elif visual:
        shapes.append(visual_shapes(ids, slide, style))
        if slide.get("bullets"):
            shapes.append(bullets(ids, 1050000, 5120000, 9600000, 700000, slide.get("bullets", [])[:2], max(14, style["body_size"] - 4), body_color, style["body_font"]))
    elif table:
        shapes.append(table_shapes(ids, table, style))
    else:
        y = 2760000 if dark else 1500000
        shapes.append(bullets(ids, 1050000, y, 9600000, 4200000, slide.get("bullets", []), max(17, style["body_size"] - (1 if not dark else 2)), body_color, style["body_font"]))

    shapes.append(text_box(ids, 720000, 6350000, 6000000, 240000, f"{idx:02d}", 9.5, "DDEAF3" if dark else style["neutral_color"], font=style["body_font"]))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{bg}"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(shapes)}
    </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def build(spec: dict, out_dir: Path) -> Path:
    slides = spec["slides"]
    style = normalize_style(spec)
    pptx = out_dir / "final_presentation.pptx"
    image_paths = []
    for slide in slides:
        if slide.get("image"):
            path = (out_dir / slide["image"]).resolve()
            if path not in image_paths:
                image_paths.append(path)
    media = {path: f"image{i + 1}.png" for i, path in enumerate(image_paths)}
    slide_ids = "\n".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>' for i in range(len(slides)))
    rels = "\n".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>' for i in range(len(slides)))
    rels += '\n<Relationship Id="rId101" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    overrides = "\n".join(f'<Override PartName="/ppt/slides/slide{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(len(slides)))

    with ZipFile(pptx, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="jpg" ContentType="image/jpeg"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>{overrides}</Types>""")
        z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>""")
        z.writestr("ppt/presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId101"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>""")
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>""")
        z.writestr("ppt/theme/theme1.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ReferenceAcademic"><a:themeElements><a:clrScheme name="ReferenceAcademic"><a:dk1><a:srgbClr val="222831"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="{style['primary_color']}"/></a:dk2><a:lt2><a:srgbClr val="{style['light_color']}"/></a:lt2><a:accent1><a:srgbClr val="{style['secondary_color']}"/></a:accent1><a:accent2><a:srgbClr val="{style['accent_color']}"/></a:accent2><a:accent3><a:srgbClr val="{style['neutral_color']}"/></a:accent3><a:accent4><a:srgbClr val="D7DEEA"/></a:accent4><a:accent5><a:srgbClr val="7DB1CD"/></a:accent5><a:accent6><a:srgbClr val="31489F"/></a:accent6><a:hlink><a:srgbClr val="{style['secondary_color']}"/></a:hlink><a:folHlink><a:srgbClr val="{style['primary_color']}"/></a:folHlink></a:clrScheme><a:fontScheme name="{esc(style['title_font'])}"><a:majorFont><a:latin typeface="{esc(style['title_font'])}"/><a:ea typeface="{esc(style['title_font'])}"/></a:majorFont><a:minorFont><a:latin typeface="{esc(style['body_font'])}"/><a:ea typeface="{esc(style['body_font'])}"/></a:minorFont></a:fontScheme><a:fmtScheme name="simple"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle/></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>""")
        z.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""")
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""")
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")
        for path, name in media.items():
            z.write(path, f"ppt/media/{name}")
        for i, slide in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(slide, i, out_dir, style))
            slide_rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
            if slide.get("image"):
                slide_rels.append(f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{media[(out_dir / slide["image"]).resolve()]}"/>')
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(slide_rels)}</Relationships>""")
    return pptx


def write_html_and_notes(spec: dict, out_dir: Path) -> None:
    style = normalize_style(spec)
    html_parts = [
        "<!doctype html><html><head><meta charset='utf-8'><title>Paper PPT</title>",
        f"<style>body{{font-family:'{style['body_font']}',Arial,sans-serif;background:#eef2f7;margin:28px}}.slide{{background:white;margin:0 0 22px;padding:24px;border-left:10px solid #{style['secondary_color']};box-shadow:0 2px 10px #d9dee8}}h2{{color:#{style['primary_color']}}}img{{max-width:72%;border:1px solid #cfd7e3}}.note{{color:#58606b;border-top:1px solid #ddd;margin-top:12px;padding-top:8px}}.dark{{background:#{style['primary_color']};color:white}}.dark h2{{color:white}}</style></head><body>",
    ]
    notes = ["# Speaker Notes\n\n"]
    for i, slide in enumerate(spec["slides"], 1):
        dark = slide.get("kind") in {"cover", "section", "closing"}
        html_parts.append(f"<section class='slide {'dark' if dark else ''}'><h2>{i}. {esc(slide.get('title', ''))}</h2>")
        if slide.get("page_goal"):
            html_parts.append(f"<p><b>Page Goal:</b> {esc(slide['page_goal'])}</p>")
        if slide.get("visual"):
            html_parts.append(f"<p><b>Visual:</b> {esc(slide['visual'].get('type', 'concept'))} - {esc(slide['visual'].get('insight') or slide['visual'].get('so_what') or slide['visual'].get('headline') or '')}</p>")
        if slide.get("content"):
            html_parts.append(f"<p><b>Content:</b> {esc(slide['content'])}</p>")
        if slide.get("subtitle"):
            html_parts.append(f"<p><strong>{esc(slide['subtitle'])}</strong></p>")
        if slide.get("image"):
            html_parts.append(f"<img src='{esc(slide['image'])}'>")
        html_parts.append("<ul>" + "".join(f"<li>{esc(item)}</li>" for item in slide.get("bullets", [])) + "</ul>")
        html_parts.append(f"<div class='note'>{esc(slide.get('notes', ''))}</div></section>")
        notes.append(f"## Slide {i}: {slide.get('title', '')}\n\n")
        if slide.get("page_goal"):
            notes.append(f"Page Goal: {slide['page_goal']}\n\n")
        if slide.get("visual"):
            notes.append(f"Visual: {slide['visual'].get('type', 'concept')}\n\n")
        if slide.get("content"):
            notes.append(f"Content: {slide['content']}\n\n")
        notes.append(f"{slide.get('notes', '')}\n\n")
    html_parts.append("</body></html>")
    (out_dir / "final_presentation.html").write_text("\n".join(html_parts), encoding="utf-8")
    (out_dir / "speaker_notes.md").write_text("".join(notes), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PPTX/HTML/speaker notes from slide_specs.json.")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out_dir = args.out.resolve()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    pptx = build(spec, out_dir)
    write_html_and_notes(spec, out_dir)
    print(pptx)


if __name__ == "__main__":
    main()
