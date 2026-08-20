#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import PptxGenJS from "pptxgenjs";

const ROOT = process.cwd();

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === "--manifest") out.manifest = args[++i];
  }
  if (!out.manifest) throw new Error("Usage: node engine/build_pptx.mjs --manifest <path>");
  return out;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function resolveInsideRoot(relPath, label) {
  if (!relPath || typeof relPath !== "string") throw new Error(`${label}: expected path string`);
  if (path.isAbsolute(relPath)) throw new Error(`${label}: absolute paths are not allowed: ${relPath}`);
  const resolved = path.resolve(ROOT, relPath);
  const relative = path.relative(ROOT, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`${label}: path escapes repository root: ${relPath}`);
  }
  return resolved;
}

function ensureDir(fileOrDir, isFile = true) {
  const dir = isFile ? path.dirname(fileOrDir) : fileOrDir;
  fs.mkdirSync(dir, { recursive: true });
}

function addTitleSlide(pptx, spec) {
  const slide = pptx.addSlide();
  slide.background = { color: "F7F9FC" };
  slide.addText(spec.title, { x: 0.65, y: 1.35, w: 11.0, h: 0.75, fontFace: "Aptos Display", fontSize: 38, bold: true, color: "102033", margin: 0.02 });
  slide.addText(spec.subtitle, { x: 0.7, y: 2.25, w: 10.5, h: 0.5, fontFace: "Aptos", fontSize: 20, color: "465A69", margin: 0.02 });
  slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 3.35, w: 5.0, h: 0.08, fill: { color: "2B6CB0" }, line: { color: "2B6CB0" } });
  slide.addText("fixture smoke deck", { x: 0.7, y: 5.9, w: 3.2, h: 0.28, fontSize: 12, color: "7A8793", margin: 0.02 });
}

function addSectionSlide(pptx, spec) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addText(spec.eyebrow || "Section", { x: 0.7, y: 0.75, w: 3.0, h: 0.25, fontSize: 12, bold: true, color: "2B6CB0", margin: 0.02 });
  slide.addText(spec.title, { x: 0.7, y: 1.25, w: 10.7, h: 0.65, fontSize: 32, bold: true, color: "17212B", margin: 0.02 });
  slide.addText(spec.body, { x: 0.75, y: 2.35, w: 9.6, h: 1.1, fontSize: 21, color: "3A4A57", breakLine: false, fit: "shrink", margin: 0.05 });
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 4.25, w: 4.4, h: 0.7, rectRadius: 0.08, fill: { color: "EAF3FF" }, line: { color: "C6DDF7" } });
  slide.addText("public fixture only", { x: 1.05, y: 4.48, w: 3.7, h: 0.25, fontSize: 15, bold: true, color: "2B5A88", margin: 0.02 });
}

function addBulletsSlide(pptx, spec) {
  const slide = pptx.addSlide();
  slide.background = { color: "FAFBFC" };
  slide.addText(spec.title, { x: 0.7, y: 0.7, w: 10.6, h: 0.5, fontSize: 30, bold: true, color: "17212B", margin: 0.02 });
  const lines = spec.bullets.map((b) => ({ text: b, options: { bullet: { type: "bullet" }, hanging: 4 } }));
  slide.addText(lines, { x: 1.0, y: 1.55, w: 9.7, h: 3.8, fontSize: 18, color: "273642", breakLine: false, fit: "shrink", margin: 0.06, paraSpaceAfterPt: 10 });
}

function addTwoColumnSlide(pptx, spec) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addText(spec.title, { x: 0.7, y: 0.65, w: 10.8, h: 0.5, fontSize: 30, bold: true, color: "17212B", margin: 0.02 });
  const columns = [
    { x: 0.8, title: spec.left_title, items: spec.left_items, color: "EAF3FF", accent: "2B6CB0" },
    { x: 6.25, title: spec.right_title, items: spec.right_items, color: "EEFDF6", accent: "15803D" },
  ];
  for (const col of columns) {
    slide.addShape(pptx.ShapeType.roundRect, { x: col.x, y: 1.45, w: 5.0, h: 4.6, rectRadius: 0.08, fill: { color: col.color }, line: { color: "D9E2EC" } });
    slide.addText(col.title, { x: col.x + 0.35, y: 1.85, w: 4.25, h: 0.35, fontSize: 21, bold: true, color: col.accent, margin: 0.02 });
    const lines = col.items.map((b) => ({ text: b, options: { bullet: { type: "bullet" } } }));
    slide.addText(lines, { x: col.x + 0.45, y: 2.55, w: 4.15, h: 2.7, fontSize: 16, color: "273642", fit: "shrink", margin: 0.05, paraSpaceAfterPt: 7 });
  }
}

function addTimelineSlide(pptx, spec) {
  const slide = pptx.addSlide();
  slide.background = { color: "FAFBFC" };
  slide.addText(spec.title, { x: 0.7, y: 0.7, w: 10.8, h: 0.5, fontSize: 30, bold: true, color: "17212B", margin: 0.02 });
  const startX = 0.9;
  const gap = 2.25;
  const y = 3.05;
  for (let i = 0; i < spec.steps.length; i += 1) {
    const x = startX + i * gap;
    if (i < spec.steps.length - 1) {
      slide.addShape(pptx.ShapeType.line, { x: x + 0.62, y: y + 0.25, w: gap - 0.2, h: 0, line: { color: "9AA6B2", width: 1.25, beginArrowType: "none", endArrowType: "triangle" } });
    }
    slide.addShape(pptx.ShapeType.ellipse, { x, y: y - 0.05, w: 0.62, h: 0.62, fill: { color: "2B6CB0" }, line: { color: "2B6CB0" } });
    slide.addText(String(i + 1), { x: x + 0.18, y: y + 0.11, w: 0.26, h: 0.2, fontSize: 13, bold: true, color: "FFFFFF", margin: 0.02 });
    slide.addText(spec.steps[i], { x: x - 0.35, y: y + 0.85, w: 1.35, h: 0.55, fontSize: 14, bold: true, align: "center", color: "273642", fit: "shrink", margin: 0.02 });
  }
}

function addChecklistSlide(pptx, spec) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addText(spec.title, { x: 0.7, y: 0.65, w: 10.8, h: 0.5, fontSize: 30, bold: true, color: "17212B", margin: 0.02 });
  for (let i = 0; i < spec.items.length; i += 1) {
    const y = 1.55 + i * 0.75;
    slide.addShape(pptx.ShapeType.ellipse, { x: 0.85, y, w: 0.38, h: 0.38, fill: { color: "15803D" }, line: { color: "15803D" } });
    slide.addText("✓", { x: 0.94, y: y + 0.02, w: 0.22, h: 0.2, fontSize: 11, bold: true, color: "FFFFFF", margin: 0.02 });
    slide.addText(spec.items[i], { x: 1.45, y: y - 0.02, w: 9.5, h: 0.45, fontSize: 17, color: "273642", margin: 0.02, fit: "shrink" });
  }
}

async function main() {
  const args = parseArgs();
  const manifestPath = resolveInsideRoot(args.manifest, "manifest");
  const manifest = readJson(manifestPath);
  const outputPptx = resolveInsideRoot(manifest.output.pptx, "output.pptx");
  const qaDir = resolveInsideRoot(manifest.output.qa_dir, "output.qa_dir");
  ensureDir(outputPptx, true);
  ensureDir(qaDir, false);

  const pptx = new PptxGenJS();
  pptx.layout = manifest.deck.layout || "LAYOUT_WIDE";
  pptx.author = manifest.deck.author || "PPT Production Engine";
  pptx.company = manifest.deck.company || "riyuewuxing";
  pptx.subject = manifest.deck.subject || "PPT Production Engine fixture";
  pptx.title = manifest.deck.title || "PPT Production Engine";
  pptx.lang = manifest.deck.language || "en-US";
  pptx.theme = manifest.deck.theme || { headFontFace: "Aptos Display", bodyFontFace: "Aptos", lang: "en-US" };

  for (const slideSpec of manifest.slides) {
    if (slideSpec.type === "title") addTitleSlide(pptx, slideSpec);
    else if (slideSpec.type === "section") addSectionSlide(pptx, slideSpec);
    else if (slideSpec.type === "bullets") addBulletsSlide(pptx, slideSpec);
    else if (slideSpec.type === "two_column") addTwoColumnSlide(pptx, slideSpec);
    else if (slideSpec.type === "timeline") addTimelineSlide(pptx, slideSpec);
    else if (slideSpec.type === "checklist") addChecklistSlide(pptx, slideSpec);
    else throw new Error(`Unsupported slide type: ${slideSpec.type}`);
  }

  await pptx.writeFile({ fileName: outputPptx });
  const evidence = {
    status: "PASS",
    engine_version: manifest.engine_version,
    request_id: manifest.request_id,
    manifest: path.relative(ROOT, manifestPath).replaceAll("\\", "/"),
    pptx: path.relative(ROOT, outputPptx).replaceAll("\\", "/"),
    pptx_sha256: sha256(outputPptx),
    slide_count_declared: manifest.slides.length,
    generated_at: new Date().toISOString(),
    generator: "pptxgenjs"
  };
  fs.writeFileSync(path.join(qaDir, "build-result.json"), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
