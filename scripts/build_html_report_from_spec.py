#!/usr/bin/env python
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


DEFAULT_STYLE = {
    "primary_color": "111827",
    "secondary_color": "2563EB",
    "accent_color": "DC2626",
    "neutral_color": "6B7280",
    "light_color": "F8FAFC",
    "title_font": "Microsoft YaHei",
    "body_font": "Microsoft YaHei",
    "title_size": 34,
    "body_size": 18,
    "layout": "html-report",
    "design_system": "academic-rail",
}


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def normalize_style(spec: dict) -> dict:
    style = dict(DEFAULT_STYLE)
    style.update(spec.get("style", {}) or {})
    for key in ["primary_color", "secondary_color", "accent_color", "neutral_color", "light_color"]:
        style[key] = str(style.get(key, DEFAULT_STYLE[key])).strip().lstrip("#").upper()
    style["title_size"] = max(28, min(44, int(style.get("title_size", 34))))
    style["body_size"] = max(16, min(22, int(style.get("body_size", 18))))
    return style


def normalize_sections(spec: dict) -> list[dict]:
    sections = spec.get("sections") or spec.get("slides") or []
    normalized = []
    name_map = {
        "cover": "Background",
        "background": "Background",
        "problem": "Problem",
        "method": "Method",
        "algorithm": "Method",
        "experiment": "Experiment",
        "result": "Results",
        "figure": "Method",
        "closing": "Conclusion",
        "content": "Discussion",
    }
    for idx, item in enumerate(sections, 1):
        sec = dict(item)
        sec.setdefault("section", name_map.get(sec.get("kind", "content"), sec.get("kind", "Section").title()))
        sec.setdefault("id", f"section-{idx}")
        sec.setdefault("page_goal", sec.get("title", ""))
        sec.setdefault("audience_takeaway", sec.get("page_goal", sec.get("title", "")))
        sec.setdefault("one_message", sec.get("title", sec.get("page_goal", "")))
        sec.setdefault("content", "")
        sec.setdefault("bullets", [])
        normalized.append(sec)
    return normalized


def render_visual(section: dict, project: Path) -> str:
    visual = section.get("visual") or {}
    image = section.get("image")
    table = section.get("table")
    if image:
        image_path = esc(image.replace("\\", "/"))
        return f"""
        <figure class="paper-figure">
          <img src="{image_path}" alt="{esc(section.get('title', 'paper figure'))}">
          <figcaption>{esc(visual.get('caption') or section.get('content') or 'Paper visual evidence')}</figcaption>
        </figure>
        """
    if table:
        cols = table.get("columns", [])
        rows = table.get("rows", [])
        head = "".join(f"<th>{esc(c)}</th>" for c in cols)
        body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows)
        return f"""
        <div class="table-scroll"><table>
          <thead><tr>{head}</tr></thead>
          <tbody>{body}</tbody>
        </table></div>
        """
    vtype = visual.get("type", "concept")
    if vtype == "comparison":
        left = "".join(f"<li>{esc(x)}</li>" for x in visual.get("left", []))
        right = "".join(f"<li>{esc(x)}</li>" for x in visual.get("right", []))
        return f"""
        <div class="comparison visual-card">
          <div class="compare-panel">
            <h4>{esc(visual.get('left_title', 'Existing'))}</h4>
            <ul>{left}</ul>
          </div>
          <div class="vs">VS</div>
          <div class="compare-panel highlight">
            <h4>{esc(visual.get('right_title', 'This Work'))}</h4>
            <ul>{right}</ul>
          </div>
        </div>
        <p class="visual-insight">{esc(visual.get('insight', ''))}</p>
        """
    if vtype in {"pipeline", "flow"}:
        steps_html = []
        for i, step in enumerate(visual.get("steps", []), 1):
            steps_html.append(
                f"""<div class="flow-step {'hot' if step.get('highlight') else ''}">
                <span class="step-index">{i}</span>
                <h4>{esc(step.get('label', f'Step {i}'))}</h4>
                <p>{esc(step.get('detail', ''))}</p>
                </div>"""
            )
        return f"""
        <div class="flow visual-card">{''.join(steps_html)}</div>
        <p class="visual-insight">{esc(visual.get('insight', ''))}</p>
        """
    if vtype == "result_bar":
        items = visual.get("items", [])
        max_value = max([float(item.get("value", 0)) for item in items] + [1.0])
        bars = []
        for item in items:
            value = float(item.get("value", 0))
            width = max(4, min(100, value / max_value * 100))
            bars.append(
                f"""<div class="bar-row">
                  <span class="bar-label">{esc(item.get('label', ''))}</span>
                  <div class="bar-track"><div class="bar-fill {'best' if item.get('highlight') else ''}" style="width:{width:.1f}%"></div></div>
                  <span class="bar-value">{esc(item.get('value', ''))}{esc(visual.get('unit', ''))}</span>
                </div>"""
            )
        return f"""
        <div class="chart visual-card" data-chart="result-bar">{''.join(bars)}</div>
        <p class="so-what">{esc(visual.get('so_what', visual.get('insight', '')))}</p>
        """
    if section.get("pseudocode"):
        return f"<pre class='pseudocode'><code>{esc(section['pseudocode'])}</code></pre>"
    headline = visual.get("headline") or section.get("page_goal") or section.get("title", "")
    return f"""
    <div class="concept visual-card">
      <div class="concept-line"></div>
      <h3>{esc(headline)}</h3>
      <p>{esc(visual.get('insight') or section.get('content') or '')}</p>
    </div>
    """


def render_section(section: dict, project: Path) -> str:
    bullets = "".join(f"<li>{esc(b)}</li>" for b in section.get("bullets", []))
    body = section.get("body") or section.get("content") or ""
    formula = section.get("formula")
    pseudocode = section.get("pseudocode")
    long_text = section.get("details") or section.get("long_text")
    return f"""
    <section class="report-section" id="{esc(section.get('id'))}" data-section="{esc(section.get('section'))}">
      <div class="section-kicker">{esc(section.get('section'))}</div>
      <h2>{esc(section.get('title'))}</h2>
      <div class="section-grid">
        <div class="visual-zone">
          {render_visual(section, project)}
        </div>
        <div class="text-zone">
          <div class="goal-box"><b>5-second takeaway</b><p>{esc(section.get('audience_takeaway') or section.get('page_goal'))}</p></div>
          <p class="content-text">{esc(body)}</p>
          <ul class="key-list">{bullets}</ul>
          {f'<div class="formula">\\({esc(formula)}\\)</div>' if formula else ''}
          {f'<pre class="pseudocode"><code>{esc(pseudocode)}</code></pre>' if pseudocode and not (section.get("visual") or {}).get("type") == "concept" else ''}
          {f'<details><summary>More details</summary><div class="details-body">{esc(long_text)}</div></details>' if long_text else ''}
        </div>
      </div>
    </section>
    """


def stylesheet(style: dict) -> str:
    return f"""
    :root {{
      --primary: #{style['primary_color']};
      --secondary: #{style['secondary_color']};
      --accent: #{style['accent_color']};
      --neutral: #{style['neutral_color']};
      --light: #{style['light_color']};
      --title-font: "{style['title_font']}", "Microsoft YaHei", Arial, sans-serif;
      --body-font: "{style['body_font']}", "Microsoft YaHei", Arial, sans-serif;
      --title-size: {style['title_size']}px;
      --body-size: {style['body_size']}px;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--light); color: #1f2937; font-family: var(--body-font); font-size: var(--body-size); line-height: 1.6; }}
    header.hero {{ min-height: 54vh; background: var(--primary); color: white; padding: 64px 8vw 48px; border-top: 12px solid var(--accent); display: grid; align-content: center; gap: 18px; }}
    header.hero h1 {{ font-family: var(--title-font); font-size: clamp(34px, 4vw, 58px); max-width: 1100px; margin: 0; line-height: 1.16; }}
    header.hero p {{ max-width: 900px; color: #dbe7ff; font-size: 20px; }}
    nav.toc {{ position: sticky; top: 0; z-index: 5; background: rgba(255,255,255,.96); border-bottom: 1px solid #d7deea; padding: 12px 8vw; display: flex; gap: 14px; flex-wrap: wrap; }}
    nav.toc a {{ color: var(--primary); text-decoration: none; font-weight: 700; padding: 6px 10px; border-left: 4px solid var(--accent); }}
    main {{ padding: 34px 7vw 80px; }}
    .report-section {{ background: white; margin: 0 auto 38px; max-width: 1280px; min-height: 620px; padding: 38px; border-left: 10px solid var(--secondary); box-shadow: 0 12px 32px rgba(14,37,87,.12); overflow: hidden; }}
    .section-kicker {{ color: var(--accent); font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }}
    h2 {{ font-family: var(--title-font); font-size: var(--title-size); color: var(--primary); margin: 6px 0 26px; line-height: 1.22; }}
    .section-grid {{ display: grid; grid-template-columns: minmax(560px, 1.55fr) minmax(280px, .45fr); gap: 34px; align-items: start; }}
    .visual-zone {{ min-height: 390px; display: grid; align-content: center; }}
    .text-zone {{ min-width: 0; }}
    .goal-box {{ background: #f5f7fb; border-left: 6px solid var(--accent); padding: 14px 16px; margin-bottom: 18px; }}
    .goal-box p {{ margin: 6px 0 0; }}
    .content-text {{ font-size: 17px; }}
    .key-list {{ padding-left: 22px; }}
    .key-list li {{ margin: 8px 0; }}
    .visual-card {{ background: #f8fafc; border: 1px solid #d7deea; padding: 26px; min-height: 390px; }}
    .comparison {{ display: grid; grid-template-columns: 1fr auto 1fr; gap: 18px; align-items: stretch; }}
    .compare-panel {{ background: white; border-top: 6px solid var(--secondary); padding: 18px; }}
    .compare-panel.highlight {{ border-top-color: var(--accent); }}
    .compare-panel h4, .flow-step h4 {{ color: var(--primary); margin: 0 0 10px; font-size: 20px; }}
    .vs {{ align-self: center; background: var(--accent); color: white; font-weight: 900; padding: 12px 14px; }}
    .flow {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; }}
    .flow-step {{ background: white; border-top: 6px solid var(--secondary); padding: 18px; position: relative; min-height: 160px; }}
    .flow-step.hot {{ border-top-color: var(--accent); }}
    .step-index {{ position: absolute; right: 14px; top: 10px; color: #cbd5e1; font-size: 28px; font-weight: 900; }}
    .concept h3 {{ font-size: 28px; color: var(--primary); }}
    .concept-line {{ height: 8px; width: 120px; background: var(--accent); margin-bottom: 24px; }}
    .paper-figure img {{ max-width: 100%; max-height: 520px; object-fit: contain; display: block; margin: 0 auto; border: 1px solid #d7deea; }}
    .paper-figure figcaption {{ margin-top: 10px; color: var(--neutral); font-size: 14px; }}
    .bar-row {{ display: grid; grid-template-columns: 170px 1fr 92px; align-items: center; gap: 12px; margin: 18px 0; }}
    .bar-track {{ height: 24px; background: #e8eef7; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: var(--secondary); transition: width .9s ease; }}
    .bar-fill.best {{ background: var(--accent); }}
    .bar-label, .bar-value {{ font-weight: 800; }}
    .so-what, .visual-insight {{ background: var(--primary); color: white; padding: 14px 18px; margin-top: 18px; font-weight: 800; }}
    .formula {{ overflow-x: auto; padding: 12px; background: #f8fafc; border: 1px solid #d7deea; }}
    .pseudocode {{ max-height: 360px; overflow: auto; background: #0f172a; color: #e2e8f0; padding: 16px; font-size: 14px; }}
    .table-scroll {{ max-height: 420px; overflow: auto; border: 1px solid #d7deea; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th {{ background: var(--primary); color: white; }}
    th, td {{ border: 1px solid #d7deea; padding: 10px; text-align: left; }}
    details {{ margin-top: 14px; border: 1px solid #d7deea; padding: 12px; background: #fbfdff; }}
    summary {{ cursor: pointer; font-weight: 800; color: var(--primary); }}
    @media (max-width: 900px) {{ .section-grid {{ grid-template-columns: 1fr; }} header.hero {{ padding: 44px 6vw; }} main {{ padding: 24px 4vw; }} .report-section {{ padding: 24px; }} }}
    """


def build(spec: dict, out_dir: Path) -> Path:
    style = normalize_style(spec)
    sections = normalize_sections(spec)
    title = spec.get("title", "Academic Presentation Report")
    subtitle = spec.get("subtitle", "")
    toc = "".join(f"<a href='#{esc(sec['id'])}'>{esc(sec.get('section'))}</a>" for sec in sections)
    body = "\n".join(render_section(sec, out_dir) for sec in sections)
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <script>
    window.MathJax = {{ tex: {{ inlineMath: [['\\\\(', '\\\\)'], ['$', '$']] }} }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  <style>{stylesheet(style)}</style>
</head>
<body>
  <header class="hero">
    <div class="section-kicker">Academic HTML Report</div>
    <h1>{esc(title)}</h1>
    <p>{esc(subtitle)}</p>
  </header>
  <nav class="toc">{toc}</nav>
  <main>{body}</main>
  <script>
    document.querySelectorAll('.bar-fill').forEach(el => {{
      const width = el.style.width;
      el.style.width = '0%';
      requestAnimationFrame(() => setTimeout(() => el.style.width = width, 200));
    }});
  </script>
</body>
</html>"""
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "final_presentation_generated.html"
    out.write_text(html_text, encoding="utf-8")
    (out_dir / "final_presentation.html").write_text(html_text, encoding="utf-8")
    notes = ["# HTML Report Notes\n\n"]
    for i, sec in enumerate(sections, 1):
        notes.append(f"## Section {i}: {sec.get('title', '')}\n\n")
        notes.append(f"- Page Goal: {sec.get('page_goal', '')}\n")
        notes.append(f"- Visual: {(sec.get('visual') or {}).get('type', 'image/table/concept')}\n")
        notes.append(f"- Content: {sec.get('content', '')}\n\n")
        notes.append(f"{sec.get('notes', '')}\n\n")
    (out_dir / "speaker_notes.md").write_text("".join(notes), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Visual-first academic HTML report from slide/section spec.")
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    print(build(spec, args.out.resolve()))


if __name__ == "__main__":
    main()
