# PPT Production Engine

A stateless, project-agnostic PPTX production, rendering, and QA engine for GitHub-based projects.

## What this repository is

This repository is a **public execution engine**, not a project repository and not a deliverable store.

It permanently stores only reusable production machinery:

- PptxGenJS-based PPTX generation
- build-request and source-spec contracts
- package / slide-size / hash QA
- real rendering with LibreOffice Impress
- page rasterization with Poppler
- hash-bound build and render evidence
- trusted cross-repository orchestration
- synthetic public fixtures used only for engine unit tests

It must **not** permanently store caller project source, private images, private templates, private business data, project history, or final caller PPTX files.

## Primary production path

The acceptance path is now:

```text
Private project repository
  └─ build-request.json + PPT source JSON
            ↓ temporary authenticated read
Public PPT Production Engine
  ├─ PptxGenJS build
  ├─ package QA
  ├─ LibreOffice real render
  ├─ Poppler page PNGs
  └─ SHA-256 evidence binding
            ↓ authenticated writeback
Same private project repository
  ├─ final .pptx
  └─ QA / render evidence
```

The public engine does **not** upload private caller outputs as public Actions artifacts.

## Mature components, not reinvention

The engine intentionally delegates established responsibilities to mature tools:

- **PptxGenJS** — PPTX generation
- **LibreOffice Impress** — headless PPTX → PDF rendering
- **Poppler / pdftoppm** — PDF → per-page PNG rendering
- **Python stdlib** — ZIP/package inspection and SHA-256 evidence

The repository only implements the missing orchestration layer: safe request validation, temporary execution, QA binding, and private-repository writeback.

## Build request contract

A caller repository provides a small request file, for example:

```json
{
  "contract_version": "1",
  "request_id": "report-ppt-001",
  "driver": "pptxgenjs-spec-v1",
  "source": "ppt/source.json",
  "output": {
    "pptx": "ppt/exports/report.pptx",
    "evidence_dir": "ppt/qa/engine",
    "writeback_render_evidence": true
  },
  "quality": {
    "min_slides": 6,
    "require_wide": true,
    "render_dpi": 144
  }
}
```

The source and all output destinations are repository-relative. Absolute paths and `..` traversal are rejected.

## Security model

- Private caller repositories must be explicitly allowlisted in `config/allowed-repositories.json`.
- Cross-repository access uses one least-privilege engine credential stored as the repository secret `PPT_ENGINE_REPO_TOKEN`.
- The source checkout uses `persist-credentials: false`.
- Caller source is never executed with write credentials present.
- Writeback occurs in a fresh checkout after build and QA have completed.
- The writeback step refuses to publish if package QA or render QA fails, or if their PPTX hashes do not match the generated PPTX.
- Pull requests do not receive the private-repository credential.

GitHub scopes the built-in `GITHUB_TOKEN` to the current repository; checking out a different private repository therefore requires a separate scoped credential. This is infrastructure authorization, not part of each build request.

## Workflows

- `.github/workflows/private-project-build.yml` — primary production workflow; private input → public runner → private writeback.
- `.github/workflows/fixture-smoke.yml` — synthetic engine-only unit smoke; it does not count as cross-repository acceptance.

## Current integration target

The first real integration fixture lives in the **private** `riyuewuxing/PPT` repository on `rules/general-ppt-workflow`:

- `projects/_engine_bridge_smoke/build-request.json`
- `projects/_engine_bridge_smoke/ppt-source.json`

Expected writeback:

- `projects/_engine_bridge_smoke/exports/engine-generated-smoke.pptx`
- `projects/_engine_bridge_smoke/qa/engine/engine-result.json`
- package QA, render QA, PDF, and per-page PNG evidence

The integration is PASS only when those outputs are produced by the public engine and committed back to the private branch.

## Version

Current engine contract: `0.2.0`.
