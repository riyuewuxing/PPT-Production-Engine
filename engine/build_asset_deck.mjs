#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import PptxGenJS from 'pptxgenjs';

const ROOT = process.cwd();
const W = 13.333;
const H = 7.5;

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '--manifest') out.manifest = args[++i];
  }
  if (!out.manifest) throw new Error('Usage: node engine/build_asset_deck.mjs --manifest <path>');
  return out;
}
function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function sha256(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function resolveInsideRoot(rel, label) {
  if (!rel || typeof rel !== 'string') throw new Error(`${label}: expected path string`);
  if (path.isAbsolute(rel)) throw new Error(`${label}: absolute paths are forbidden: ${rel}`);
  const resolved = path.resolve(ROOT, rel);
  const relative = path.relative(ROOT, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label}: path escapes repository root: ${rel}`);
  return resolved;
}
function ensureDir(fileOrDir, isFile = true) { fs.mkdirSync(isFile ? path.dirname(fileOrDir) : fileOrDir, { recursive: true }); }
function pngSize(file) {
  const b = fs.readFileSync(file);
  if (b.length < 24 || b.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error(`Only PNG assets are supported: ${file}`);
  return { width: b.readUInt32BE(16), height: b.readUInt32BE(20) };
}
function containRect(file, box) {
  const size = pngSize(file);
  const scale = Math.min(box.w / size.width, box.h / size.height);
  const w = size.width * scale;
  const h = size.height * scale;
  return { x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h };
}
function addFooter(slide, spec, idx, total) {
  if (spec.footer === false) return;
  slide.addText(String(idx).padStart(2, '0'), { x: 12.56, y: 7.12, w: 0.34, h: 0.14, fontSize: 6.5, bold: true, color: '8A96A3', margin: 0 });
  if (spec.phase) slide.addText(spec.phase, { x: 0.48, y: 7.05, w: 3.8, h: 0.2, fontSize: 8, color: '8A96A3', margin: 0 });
}
function addFullAssetSlide(pptx, spec, idx, total) {
  const slide = pptx.addSlide();
  slide.background = { color: spec.background || 'FFF8EF' };
  const imagePath = resolveInsideRoot(spec.image, `slides[${idx}].image`);
  if (!fs.existsSync(imagePath)) throw new Error(`image does not exist: ${spec.image}`);
  const box = spec.box || { x: 0.22, y: 0.43, w: 12.9, h: 6.02 };
  const fitted = containRect(imagePath, box);
  slide.addImage({ path: imagePath, ...fitted });
  addFooter(slide, spec, idx, total);
}
async function main() {
  const args = parseArgs();
  const manifestPath = resolveInsideRoot(args.manifest, 'manifest');
  const manifest = readJson(manifestPath);
  const outputPptx = resolveInsideRoot(manifest.output.pptx, 'output.pptx');
  const qaDir = resolveInsideRoot(manifest.output.qa_dir, 'output.qa_dir');
  ensureDir(outputPptx, true); ensureDir(qaDir, false);
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';
  pptx.author = manifest.deck.author || 'PPT Production Engine';
  pptx.company = manifest.deck.company || 'riyuewuxing';
  pptx.subject = manifest.deck.subject || manifest.deck.title || 'PPT';
  pptx.title = manifest.deck.title || 'PPT';
  pptx.lang = manifest.deck.language || 'zh-CN';
  pptx.theme = manifest.deck.theme || { headFontFace: 'Noto Sans CJK SC', bodyFontFace: 'Noto Sans CJK SC', lang: 'zh-CN' };
  const slides = manifest.slides || [];
  if (!slides.length) throw new Error('manifest.slides must not be empty');
  slides.forEach((spec, i) => {
    if (spec.type !== 'full_asset') throw new Error(`Unsupported asset deck slide type: ${spec.type}`);
    addFullAssetSlide(pptx, spec, i + 1, slides.length);
  });
  await pptx.writeFile({ fileName: outputPptx });
  const evidence = {
    status: 'PASS',
    engine_version: manifest.engine_version,
    request_id: manifest.request_id,
    manifest: path.relative(ROOT, manifestPath).replaceAll('\\', '/'),
    pptx: path.relative(ROOT, outputPptx).replaceAll('\\', '/'),
    pptx_sha256: sha256(outputPptx),
    slide_count_declared: slides.length,
    stage: 'STATIC_ASSET_DECK_PRE_DYNAMIC',
    generator: 'pptxgenjs full-asset compositor',
    generated_at: new Date().toISOString(),
  };
  fs.writeFileSync(path.join(qaDir, 'asset-deck-build-result.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify(evidence, null, 2));
}
main().catch((err) => { console.error(err); process.exit(1); });
