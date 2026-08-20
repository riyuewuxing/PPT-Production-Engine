# Mature project survey

The engine intentionally reuses existing mature layers instead of rebuilding the full PowerPoint stack.

## Adopted in v0.1

### PptxGenJS

Decision: use as the first PPTX writer.

Why:

- mature Node.js PPTX generation library;
- supports text, shapes, tables, charts, images, SVG, master slides, and browser/Node usage;
- emits standards-compatible OOXML PPTX;
- fits GitHub Actions and temporary runner workflows.

Engine boundary:

- The engine wraps PptxGenJS behind a manifest contract.
- Caller projects do not depend on PptxGenJS directly unless they choose to.

### LibreOffice Impress

Decision: use as the first real rendering backend.

Why:

- available on GitHub-hosted Ubuntu runners;
- supports headless PPTX-to-PDF conversion;
- practical for page-level smoke rendering.

Engine boundary:

- LibreOffice render PASS is not the same as Microsoft PowerPoint compatibility PASS.
- It is sufficient as the default actual-render gate for CI smoke and page evidence.

### Poppler utilities

Decision: use `pdftoppm` and optionally `pdfinfo` after LibreOffice exports PDF.

Why:

- deterministic page image extraction;
- easy SHA-256 binding per rendered page;
- available in Ubuntu package repositories.

## Evaluated but not adopted as the v0.1 core

### PPT skill / agent-skill repositories

These projects are useful references for story-first authoring and production workflows, but this engine is intentionally narrower: it does not author content and does not store project-specific plans.

### Browser/editor-heavy AI PPT projects

Projects with JSON editors, online rendering, or commercial PPT parsing are useful architectural references, but v0.1 avoids a long-running service or UI. The engine should stay a GitHub Actions production binary.

### PPT Master-style SVG-to-PPTX pipelines

Useful for future high-fidelity native reconstruction. Not adopted as the v0.1 core because the first milestone is a minimal stateless runner that builds and renders a public fixture reliably.

## Current engine principle

Do the boring production work first:

```text
manifest -> PPTX -> package QA -> real render -> hash-bound evidence
```

Then add richer input formats and private-project bridges only after the fixture smoke test is stable.
