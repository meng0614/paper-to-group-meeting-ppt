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
    "primary_color": "0E2557",
    "secondary_color": "4B649F",
    "accent_color": "FF0000",
    "neutral_color": "6B7280",
    "light_color": "F4F7FB",
    "title_font": "Microsoft YaHei",
    "body_font": "Microsoft YaHei",
    "title_size": 30,
    "body_size": 18,
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
    style["title_size"] = max(24, min(38, int(style.get("title_size", 30))))
    style["body_size"] = max(15, min(22, int(style.get("body_size", 18))))
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
    if visual.get("type") == "comparison":
        return "comparison"
    if visual.get("type") in {"pipeline", "flow"}:
        return "flow"
    if visual.get("type") == "result_bar" or sec.get("kind") == "result":
        return "result-focus"
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
    <p:txBody><a:bodyPr wrap="square" anchor="t"/><a:lstStyle/>{''.join(paras)}</p:txBody></p:sp>"""


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
    <p:txBody><a:bodyPr wrap="square" anchor="t"/><a:lstStyle/>{''.join(paras)}</p:txBody></p:sp>"""


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


def base_chrome(ids: Ids, sec: dict, idx: int, style: dict) -> list[str]:
    shapes = [
        rect(ids, 0, 0, EMU_W, EMU_H, "FFFFFF"),
        rect(ids, 0, 0, 130000, EMU_H, style["secondary_color"]),
        rect(ids, 0, 0, EMU_W, 90000, style["accent_color"]),
        text_box(ids, 620000, 310000, 2500000, 320000, section_name(sec).upper(), 14, style["accent_color"], style["title_font"], True),
        text_box(ids, 620000, 650000, 10900000, 760000, sec.get("title", ""), style["title_size"], style["primary_color"], style["title_font"], True),
        text_box(ids, 11200000, 6350000, 500000, 240000, f"{idx:02d}", 10, style["neutral_color"], style["body_font"], False),
    ]
    return shapes


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


def render_slide(sec: dict, idx: int, out_dir: Path, style: dict, image_rids: dict[Path, str]) -> tuple[str, str]:
    ids = Ids()
    shapes = base_chrome(ids, sec, idx, style)
    layout = choose_layout(sec, idx)
    text_items = (sec.get("bullets") or [])[:3]
    body = sec.get("body") or sec.get("content") or ""
    if len(body) > 260:
        body = body[:250].rstrip() + "..."

    if layout == "visual-top":
        visual_box = (860000, 1500000, 10400000, 3200000)
        text_box_area = (1050000, 5000000, 9600000, 880000)
    elif layout == "full-visual":
        visual_box = (860000, 1480000, 10400000, 4300000)
        text_box_area = (1050000, 5850000, 9600000, 440000)
    elif layout == "visual-right":
        visual_box = (6100000, 1520000, 5000000, 4200000)
        text_box_area = (860000, 1600000, 4700000, 3900000)
    else:
        visual_box = (860000, 1520000, 5450000, 4200000)
        text_box_area = (6800000, 1600000, 4300000, 3900000)

    if sec.get("image"):
        img_path = (out_dir / sec["image"]).resolve()
        if img_path.exists():
            x, y, w, h = fit_image(img_path, *visual_box)
            shapes.append(pic(ids, x, y, w, h, image_rids[img_path]))
            caption = (sec.get("visual") or {}).get("caption")
            if caption:
                shapes.append(text_box(ids, visual_box[0], visual_box[1] + visual_box[3] + 80000, visual_box[2], 280000, caption, 10.5, style["neutral_color"], style["body_font"]))
        else:
            shapes.extend(render_visual_shape(ids, sec, style, *visual_box))
    else:
        shapes.extend(render_visual_shape(ids, sec, style, *visual_box))

    tx, ty, tw, th = text_box_area
    shapes.append(text_box(ids, tx, ty, tw, 620000, "Page Goal\n" + str(sec.get("page_goal", "")), 15.5, "222831", style["body_font"], True, "F4F7FB"))
    shapes.append(text_box(ids, tx, ty + 800000, tw, 1150000, body, 15.5, "222831", style["body_font"]))
    if text_items:
        shapes.append(bullet_box(ids, tx + 100000, ty + 2050000, tw - 200000, 1350000, text_items, 14.5, "222831", style["body_font"]))

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
