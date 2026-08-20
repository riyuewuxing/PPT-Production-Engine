# PPT Production Engine

A stateless, project-agnostic PPTX production, rendering, and QA engine for AI-orchestrated GitHub projects.

## Role

This public repository is **only a PPT execution engine**. It is not a project repository, content store, or final-deliverable store.

It permanently stores only reusable production machinery:

- PptxGenJS-based PPTX generation;
- package / slide-size / hash QA;
- LibreOffice Impress headless rendering;
- Poppler page rasterization;
- hash-bound build and render evidence;
- GitHub-hosted execution workflows;
- synthetic public fixtures for engine regression tests.

It does not need credentials for any private caller repository.

## Primary production path

```text
Private project repository
        ↓ ChatGPT reads project and prepares the minimum PPT build package
ChatGPT / AI orchestrator
        ↓ stages a public-safe handoff package
Public PPT Production Engine
        ↓ GitHub-hosted runner
PptxGenJS → PPTX → package QA → LibreOffice → PDF → Poppler PNG → hash evidence
        ↓ transient Actions artifact
ChatGPT / AI orchestrator
        ↓ retrieves, reviews, and writes the accepted result
Original private project repository
```

The engine itself never checks out or writes to the private repository.

## Mature components, not reinvention

The engine intentionally delegates mature responsibilities to established tools:

- **PptxGenJS** — PPTX generation;
- **LibreOffice Impress** — real headless PPTX → PDF rendering;
- **Poppler / pdftoppm** — PDF → per-page PNG rendering;
- **Python stdlib** — ZIP/package inspection and SHA-256 evidence.

The repository implements only the missing execution contract and evidence binding around these tools.

## AI handoff contract

The current production entry is:

`handoff/current/build-manifest.json`

A push that changes this file triggers `.github/workflows/ai-handoff-build.yml`.

The workflow produces a short-lived Actions artifact containing:

- final `.pptx`;
- package QA JSON;
- render QA JSON;
- rendered PDF;
- per-page PNGs.

`status/ai-handoff-last.json` contains only non-sensitive run metadata so an AI orchestrator can discover the run ID, artifact name, PASS/FAIL state, PPTX SHA-256, and rendered page count without asking a human to inspect the Actions UI.

## Privacy boundary

This is a **public** repository. Any build input committed here must be considered public even after the current file is deleted, because Git history may retain it and external clones/caches may already exist.

Therefore the handoff package must never contain secrets, API keys, credentials, private personal data, or assets that are not allowed to be publicly exposed.

For sensitive projects, use a different private execution path rather than placing sensitive source into this public engine.

## Verified execution

The engine has already passed two real GitHub-hosted runner checks:

1. engine fixture smoke: Build PASS / Package QA PASS / Render QA PASS / 6 rendered pages;
2. AI-mediated handoff smoke: Build PASS / Package QA PASS / Render QA PASS / 6 rendered pages.

The AI-mediated handoff PPTX SHA-256 was:

`0d1e31589e2328b788903bcebd4d90e7f6bdee1bb8e12711b4c56ed00f728a0c`

## Workflows

- `.github/workflows/ai-handoff-build.yml` — primary AI-mediated production workflow.
- `.github/workflows/fixture-smoke.yml` — engine-only regression smoke.

## Version

Current engine contract: `0.3.0`.
