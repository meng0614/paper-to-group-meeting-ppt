#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i].startsWith("--")) {
      args[argv[i].slice(2)] = argv[i + 1];
      i += 1;
    }
  }
  return args;
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function contain(file, x, y, w, h) {
  const s = pngSize(file);
  const r = Math.min(w / s.w, h / s.h);
  const nw = s.w * r;
  const nh = s.h * r;
  return { x: x + (w - nw) / 2, y: y + (h - nh) / 2, w: nw, h: nh };
}

function addImage(slide, file, x, y, w, h) {
  if (!file || !fs.existsSync(file)) return false;
  slide.addImage({ path: file, ...contain(file, x, y, w, h) });
  return true;
}

const PRESETS = {
  "nature-clean": {
    bg: "FFFFFF",
    primary: "102A43",
    accent: "D62828",
    secondary: "1F77B4",
    neutral: "6B7280",
    light: "F5F7FA",
    body: "111827",
    rail: true,
    font: "Microsoft YaHei",
  },
  "conference-blue": {
    bg: "FFFFFF",
    primary: "0F172A",
    accent: "2563EB",
    secondary: "0EA5E9",
    neutral: "64748B",
    light: "EFF6FF",
    body: "111827",
    rail: true,
    font: "Microsoft YaHei",
  },
  "minimal-dark": {
    bg: "111827",
    primary: "F9FAFB",
    accent: "38BDF8",
    secondary: "A78BFA",
    neutral: "CBD5E1",
    light: "1F2937",
    body: "F3F4F6",
    rail: false,
    font: "Microsoft YaHei",
  },
  "warm-paper": {
    bg: "FFFDF7",
    primary: "1F2937",
    accent: "C2410C",
    secondary: "0F766E",
    neutral: "78716C",
    light: "F7F2E8",
    body: "292524",
    rail: true,
    font: "Microsoft YaHei",
  },
};

function bulletText(items) {
  return (items || []).map((s) => `• ${s}`).join("\n");
}

function safeText(v) {
  return String(v || "");
}

function addHeader(pptx, slide, sec, idx, style) {
  slide.background = { color: style.bg };
  if (style.rail) {
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.06, fill: { color: style.accent }, line: { color: style.accent } });
    slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.1, h: 7.5, fill: { color: style.secondary }, line: { color: style.secondary } });
  }
  slide.addText(safeText(sec.section || sec.story_phase || ""), {
    x: 0.55,
    y: 0.34,
    w: 3.2,
    h: 0.28,
    fontFace: style.font,
    fontSize: 11.5,
    bold: true,
    color: style.accent,
    margin: 0,
  });
  const title = safeText(sec.one_message || sec.title);
  slide.addText(title, {
    x: 0.55,
    y: 0.74,
    w: 11.85,
    h: title.length > 29 ? 1.08 : 0.86,
    fontFace: style.font,
    fontSize: title.length > 31 ? 22 : 26,
    bold: true,
    color: style.primary,
    fit: "shrink",
    margin: 0.01,
    breakLine: false,
  });
  slide.addText(String(idx).padStart(2, "0"), {
    x: 12.05,
    y: 6.94,
    w: 0.5,
    h: 0.2,
    fontFace: "Arial",
    fontSize: 8,
    color: style.neutral,
    margin: 0,
  });
}

function addFooter(slide, spec, style) {
  slide.addText("Source: " + path.basename(safeText(spec.source_pdf || "paper.pdf")), {
    x: 0.55,
    y: 7.13,
    w: 8.4,
    h: 0.17,
    fontFace: "Arial",
    fontSize: 7,
    color: style.neutral,
    margin: 0,
  });
}

function addCallout(pptx, slide, text, x, y, w, h, style) {
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w,
    h,
    fill: { color: style.light },
    line: { color: style.light },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w: 0.07,
    h,
    fill: { color: style.accent },
    line: { color: style.accent },
  });
  slide.addText(text, {
    x: x + 0.18,
    y: y + 0.11,
    w: w - 0.28,
    h: h - 0.15,
    fontFace: style.font,
    fontSize: 13.5,
    bold: true,
    color: style.primary,
    fit: "shrink",
    margin: 0,
  });
}

function addBullets(slide, bullets, x, y, w, h, style, fontSize = 14.5) {
  slide.addText(bulletText((bullets || []).slice(0, 3)), {
    x,
    y,
    w,
    h,
    fontFace: style.font,
    fontSize,
    color: style.body,
    fit: "shrink",
    margin: 0.02,
    valign: "top",
    paraSpaceAfterPt: 8,
  });
}

function addStepVisual(pptx, slide, visual, x, y, w, h, style) {
  const steps = (visual.steps || []).slice(0, 4);
  const gap = 0.12;
  const bw = (w - gap * (steps.length - 1)) / Math.max(1, steps.length);
  steps.forEach((step, i) => {
    const sx = x + i * (bw + gap);
    const highlighted = i === steps.length - 1 && visual.type === "pipeline";
    slide.addShape(pptx.ShapeType.roundRect, {
      x: sx,
      y,
      w: bw,
      h,
      rectRadius: 0.04,
      fill: { color: highlighted ? style.accent : style.light },
      line: { color: highlighted ? style.accent : "D9E2EC" },
    });
    slide.addText(safeText(step.label), {
      x: sx + 0.12,
      y: y + 0.18,
      w: bw - 0.24,
      h: 0.38,
      fontFace: style.font,
      fontSize: 12.5,
      bold: true,
      color: highlighted ? "FFFFFF" : style.primary,
      fit: "shrink",
      margin: 0,
    });
    slide.addText(safeText(step.detail), {
      x: sx + 0.12,
      y: y + 0.7,
      w: bw - 0.24,
      h: h - 0.86,
      fontFace: style.font,
      fontSize: 10.8,
      color: highlighted ? "FFFFFF" : style.body,
      fit: "shrink",
      margin: 0,
    });
    if (i < steps.length - 1) {
      slide.addText("→", { x: sx + bw - 0.03, y: y + h / 2 - 0.16, w: 0.2, h: 0.22, fontFace: "Arial", fontSize: 16, bold: true, color: style.accent, margin: 0 });
    }
  });
}

function addComparison(pptx, slide, visual, x, y, w, h, style) {
  const gap = 0.22;
  const cw = (w - gap) / 2;
  [
    ["left", x, visual.left_title || "Existing"],
    ["right", x + cw + gap, visual.right_title || "This Work"],
  ].forEach(([side, sx, title]) => {
    slide.addShape(pptx.ShapeType.roundRect, {
      x: sx,
      y,
      w: cw,
      h,
      rectRadius: 0.04,
      fill: { color: style.light },
      line: { color: "D9E2EC" },
    });
    slide.addText(safeText(title), { x: sx + 0.18, y: y + 0.18, w: cw - 0.36, h: 0.38, fontFace: style.font, fontSize: 13, bold: true, color: side === "right" ? style.accent : style.primary, fit: "shrink", margin: 0 });
    addBullets(slide, visual[side] || [], sx + 0.24, y + 0.72, cw - 0.45, h - 0.85, style, 11.5);
  });
}

function addTakeawayVisual(pptx, slide, visual, x, y, w, h, style) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.04, fill: { color: style.light }, line: { color: style.light } });
  slide.addText(safeText(visual.headline || ""), { x: x + 0.35, y: y + 0.32, w: w - 0.7, h: 0.9, fontFace: style.font, fontSize: 21, bold: true, color: style.primary, fit: "shrink", margin: 0 });
  slide.addText(safeText(visual.insight || ""), { x: x + 0.35, y: y + 1.45, w: w - 0.7, h: h - 1.75, fontFace: style.font, fontSize: 15, color: style.body, fit: "shrink", margin: 0 });
}

function addVisual(pptx, slide, sec, imagePath, x, y, w, h, style) {
  const visual = sec.visual || {};
  if (imagePath && fs.existsSync(imagePath)) {
    addImage(slide, imagePath, x, y, w, h);
    return;
  }
  if (["pipeline", "flow"].includes(visual.type)) {
    addStepVisual(pptx, slide, visual, x, y, w, h, style);
  } else if (["comparison", "claim_evidence"].includes(visual.type)) {
    addComparison(pptx, slide, visual, x, y, w, h, style);
  } else {
    addTakeawayVisual(pptx, slide, visual, x, y, w, h, style);
  }
}

function chooseLayout(sec, idx) {
  const type = (sec.visual && sec.visual.type) || "";
  if (sec.kind === "cover") return "cover";
  if (["pipeline", "flow"].includes(type) && !sec.image) return "top-diagram";
  if (["comparison", "claim_evidence"].includes(type) && !sec.image) return "top-diagram";
  if (sec.kind === "result" || sec.kind === "insight") return "visual-top";
  if (sec.kind === "takeaway" || sec.kind === "discussion") return "visual-top";
  if (sec.image) return idx % 2 === 0 ? "visual-right" : "visual-left";
  return "top-diagram";
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.spec || !args.out) {
    console.error("Usage: node build_pptxgenjs_from_spec.js --spec slide_specs.json --out project_dir");
    process.exit(2);
  }
  const spec = JSON.parse(fs.readFileSync(args.spec, "utf8"));
  const outDir = path.resolve(args.out);
  const style = PRESETS[spec.style_preset || "nature-clean"] || PRESETS["nature-clean"];
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Academic Presentation Agent";
  pptx.company = "paper-to-group-meeting-ppt";
  pptx.subject = "Research-understanding-driven presentation";
  pptx.title = spec.title || "Academic Presentation";
  pptx.lang = spec.language === "en" ? "en-US" : "zh-CN";
  pptx.theme = { headFontFace: style.font, bodyFontFace: style.font, lang: pptx.lang };

  (spec.sections || []).forEach((sec, i) => {
    const slide = pptx.addSlide();
    addHeader(pptx, slide, sec, i + 1, style);
    const layout = chooseLayout(sec, i + 1);
    const imagePath = sec.image ? path.join(outDir, sec.image) : null;
    if (layout === "cover") {
      addImage(slide, imagePath, 7.25, 1.55, 4.9, 2.65);
      addCallout(pptx, slide, safeText(sec.audience_takeaway), 0.75, 4.95, 10.95, 0.72, style);
      addBullets(slide, sec.bullets, 0.85, 2.05, 6.15, 1.9, style, 15);
    } else if (layout === "visual-top") {
      addVisual(pptx, slide, sec, imagePath, 1.15, 1.62, 10.75, 3.05, style);
      addCallout(pptx, slide, safeText(sec.audience_takeaway), 7.65, 4.95, 4.15, 0.95, style);
      addBullets(slide, sec.bullets, 0.85, 4.92, 6.45, 1.35, style, 13.2);
    } else if (layout === "visual-right") {
      addBullets(slide, sec.bullets, 0.75, 2.02, 5.35, 2.25, style, 14.2);
      addCallout(pptx, slide, safeText(sec.audience_takeaway), 0.75, 4.78, 5.32, 0.95, style);
      addVisual(pptx, slide, sec, imagePath, 6.42, 1.76, 5.42, 3.75, style);
    } else if (layout === "visual-left") {
      addVisual(pptx, slide, sec, imagePath, 0.72, 1.76, 5.45, 3.75, style);
      addBullets(slide, sec.bullets, 6.42, 2.02, 5.3, 2.25, style, 14.2);
      addCallout(pptx, slide, safeText(sec.audience_takeaway), 6.42, 4.78, 5.28, 0.95, style);
    } else {
      addVisual(pptx, slide, sec, imagePath, 0.82, 1.8, 10.95, 2.65, style);
      addCallout(pptx, slide, safeText(sec.audience_takeaway), 7.65, 4.9, 4.15, 0.98, style);
      addBullets(slide, sec.bullets, 0.85, 4.92, 6.45, 1.35, style, 13.2);
    }
    addFooter(slide, spec, style);
    if (typeof slide.addNotes === "function") slide.addNotes(safeText(sec.notes || ""));
  });

  const outFile = path.join(outDir, "final_presentation_generated.pptx");
  await pptx.writeFile({ fileName: outFile });
  fs.copyFileSync(outFile, path.join(outDir, "final_presentation.pptx"));
  console.log(outFile);
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
