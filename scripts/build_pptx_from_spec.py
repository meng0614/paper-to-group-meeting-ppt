#!/usr/bin/env python
import argparse
import html
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image

EMU_W, EMU_H = 12192000, 6858000


def esc(s):
    return html.escape(str(s), quote=True)


def fit_image(path, x, y, w, h):
    im = Image.open(path)
    iw, ih = im.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    return x + (w - nw) // 2, y + (h - nh) // 2, nw, nh


class ShapeIds:
    def __init__(self):
        self.n = 1
    def next(self):
        self.n += 1
        return self.n


def text_box(ids, x, y, w, h, text, size=20, color="222831", bold=False, fill=None):
    paras = []
    for line in str(text).split("\n"):
        paras.append(
            f'<a:p><a:r><a:rPr lang="zh-CN" sz="{int(size*100)}" b="{1 if bold else 0}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Microsoft YaHei"/>'
            f'<a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>{esc(line)}</a:t></a:r></a:p>'
        )
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
    sid = ids.next()
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill_xml}<a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(paras)}</p:txBody>
    </p:sp>"""


def bullets(ids, x, y, w, h, items, size=17, color="222831"):
    paras = []
    for b in items or []:
        paras.append(
            f'<a:p><a:pPr marL="260000" indent="-160000"><a:buChar char="•"/></a:pPr>'
            f'<a:r><a:rPr lang="zh-CN" sz="{int(size*100)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>{esc(b)}</a:t></a:r></a:p>'
        )
    sid = ids.next()
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{sid}" name="Bullets {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(paras)}</p:txBody>
    </p:sp>"""


def pic(ids, x, y, w, h, rid="rId2"):
    sid = ids.next()
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{sid}" name="Figure {sid}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:ln><a:solidFill><a:srgbClr val="CFD7E3"/></a:solidFill></a:ln></p:spPr>
    </p:pic>"""


def table_shapes(ids, table):
    cols = table.get("columns", [])
    rows = table.get("rows", [])
    if not cols:
        return ""
    x0, y0 = 650000, 1500000
    total_w = 10800000
    col_w = total_w // len(cols)
    row_h = 560000
    out = []
    for j, c in enumerate(cols):
        out.append(text_box(ids, x0 + j * col_w, y0, col_w, row_h, c, size=13, color="FFFFFF", bold=True, fill="12355B"))
    for i, row in enumerate(rows, 1):
        fill = "F4F6F8" if i % 2 else "FFFFFF"
        for j, c in enumerate(row):
            out.append(text_box(ids, x0 + j * col_w, y0 + i * row_h, col_w, row_h, c, size=11.5, fill=fill))
    return "".join(out)


def slide_xml(slide, idx, out_dir):
    ids = ShapeIds()
    kind = slide.get("kind", "content")
    dark = kind in {"cover", "section", "closing"}
    bg = "12355B" if dark else "FFFFFF"
    title_color = "FFFFFF" if dark else "12355B"
    body_color = "FFFFFF" if dark else "222831"
    shapes = [text_box(ids, 520000, 330000, 11100000, 560000, slide.get("title", f"Slide {idx}"), size=26 if dark else 22, color=title_color, bold=True)]
    if slide.get("subtitle"):
        shapes.append(text_box(ids, 620000, 930000, 10000000, 420000, slide["subtitle"], size=15, color="DDEAF3" if dark else "6B7280"))
    image = slide.get("image")
    table = slide.get("table")
    if image:
        img_path = (out_dir / image).resolve()
        im = Image.open(img_path)
        aspect = im.size[0] / im.size[1]
        if kind in {"result"} or aspect > 1.55:
            x, y, w, h = fit_image(img_path, 750000, 1100000, 10700000, 3900000)
            shapes.append(pic(ids, x, y, w, h))
            shapes.append(bullets(ids, 900000, 5150000, 10000000, 850000, slide.get("bullets", []), size=14.5, color=body_color))
        elif kind in {"algorithm"} or aspect < 0.85:
            shapes.append(bullets(ids, 650000, 1300000, 5000000, 4200000, slide.get("bullets", []), size=16, color=body_color))
            x, y, w, h = fit_image(img_path, 6600000, 1000000, 4400000, 5550000)
            shapes.append(pic(ids, x, y, w, h))
        else:
            shapes.append(bullets(ids, 650000, 1300000, 4300000, 4200000, slide.get("bullets", []), size=16, color=body_color))
            x, y, w, h = fit_image(img_path, 5550000, 1000000, 6100000, 5400000)
            shapes.append(pic(ids, x, y, w, h))
    elif table:
        shapes.append(table_shapes(ids, table))
    else:
        shapes.append(bullets(ids, 900000, 1450000, 10100000, 4200000, slide.get("bullets", []), size=19 if not dark else 18, color=body_color))
    shapes.append(text_box(ids, 720000, 6350000, 6000000, 240000, f"Slide {idx}", size=9.5, color="DDEAF3" if dark else "6B7280"))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="{bg}"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(shapes)}
    </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def build(spec, out_dir):
    slides = spec["slides"]
    pptx = out_dir / "final_presentation.pptx"
    image_paths = []
    for s in slides:
        if s.get("image"):
            p = (out_dir / s["image"]).resolve()
            if p not in image_paths:
                image_paths.append(p)
    media = {p: f"image{i+1}.png" for i, p in enumerate(image_paths)}
    slide_ids = "\n".join(f'<p:sldId id="{256+i}" r:id="rId{i+1}"/>' for i in range(len(slides)))
    rels = "\n".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>' for i in range(len(slides)))
    rels += '\n<Relationship Id="rId101" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    overrides = "\n".join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(len(slides)))

    with ZipFile(pptx, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>{overrides}</Types>""")
        z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>""")
        z.writestr("ppt/presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId101"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>""")
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>""")
        z.writestr("ppt/theme/theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Academic"><a:themeElements><a:clrScheme name="Academic"><a:dk1><a:srgbClr val="222831"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="12355B"/></a:dk2><a:lt2><a:srgbClr val="F4F6F8"/></a:lt2><a:accent1><a:srgbClr val="1C7C8C"/></a:accent1><a:accent2><a:srgbClr val="12355B"/></a:accent2><a:accent3><a:srgbClr val="6B7280"/></a:accent3><a:accent4><a:srgbClr val="CFD7E3"/></a:accent4><a:accent5><a:srgbClr val="DDEAF3"/></a:accent5><a:accent6><a:srgbClr val="9CA3AF"/></a:accent6><a:hlink><a:srgbClr val="1C7C8C"/></a:hlink><a:folHlink><a:srgbClr val="12355B"/></a:folHlink></a:clrScheme><a:fontScheme name="Microsoft YaHei"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme><a:fmtScheme name="simple"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle/></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>""")
        z.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""")
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""")
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")
        for p, name in media.items():
            z.write(p, f"ppt/media/{name}")
        for i, slide in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(slide, i, out_dir))
            sr = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
            if slide.get("image"):
                sr.append(f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{media[(out_dir / slide["image"]).resolve()]}"/>')
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(sr)}</Relationships>""")
    return pptx


def write_html_and_notes(spec, out_dir):
    html_parts = ["<!doctype html><html><head><meta charset='utf-8'><title>Paper PPT</title><style>body{font-family:Arial,'Microsoft YaHei',sans-serif;background:#f4f6f8;margin:28px}.slide{background:white;margin:0 0 20px;padding:24px;border:1px solid #d4dae3;border-radius:8px}img{max-width:55%;border:1px solid #cfd7e3}.dark{background:#12355B;color:white}.note{color:#58606b;border-top:1px solid #ddd;margin-top:12px;padding-top:8px}.dark .note{color:#dfe9f3}</style></head><body>"]
    notes = ["# Speaker Notes\n\n"]
    for i, s in enumerate(spec["slides"], 1):
        dark = s.get("kind") in {"cover", "section", "closing"}
        html_parts.append(f"<section class='slide {'dark' if dark else ''}'><h2>{i}. {esc(s.get('title',''))}</h2>")
        if s.get("image"):
            html_parts.append(f"<img src='{esc(s['image'])}'>")
        html_parts.append("<ul>" + "".join(f"<li>{esc(b)}</li>" for b in s.get("bullets", [])) + "</ul>")
        html_parts.append(f"<div class='note'>{esc(s.get('notes',''))}</div></section>")
        notes.append(f"## Slide {i}: {s.get('title','')}\n\n{s.get('notes','')}\n\n")
    html_parts.append("</body></html>")
    (out_dir / "final_presentation.html").write_text("\n".join(html_parts), encoding="utf-8")
    (out_dir / "speaker_notes.md").write_text("".join(notes), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Build PPTX/HTML/speaker notes from slide_specs.json.")
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out_dir = args.out.resolve()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    pptx = build(spec, out_dir)
    write_html_and_notes(spec, out_dir)
    print(pptx)


if __name__ == "__main__":
    main()
