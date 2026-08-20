# PPT Production Engine

A stateless, project-agnostic PPTX production, rendering, and QA engine for GitHub-based projects.

## Purpose

This repository is a public production engine. It does **not** store user project code, private content, slide source materials, project history, or final project deliverables.

It owns only reusable PPT production machinery:

- PPTX generation from a stable build manifest
- package and structural QA
- real rendering through LibreOffice Impress
- hash-bound evidence generation
- fixture-based smoke tests
- future private-project bridge contracts

## Current scope

The first implementation supports a public fixture build:

```text
fixture manifest -> PptxGenJS -> PPTX -> LibreOffice render -> QA manifest -> GitHub Actions artifact
```

The fixture is intentionally generic and contains no private project data.

## Why PptxGenJS and LibreOffice?

- PptxGenJS is a mature JavaScript library for generating standards-compatible PPTX files.
- LibreOffice Impress provides a practical headless renderer for CI verification.
- Python QA scripts inspect the final PPTX package and bind outputs to SHA-256 evidence.

## Repository contract

The engine is stateless:

1. It may read an input build package during a workflow run.
2. It may generate PPTX, render pages, and QA evidence in temporary workspace storage.
3. It may write results back to a caller repository when explicitly configured with scoped credentials.
4. It must not persist caller project inputs or deliverables in this public repository.

## First milestone

- [x] Public repository created
- [x] Fixture build contract defined
- [x] PPTX generator implemented
- [x] Package QA implemented
- [x] Render QA implemented
- [x] GitHub Actions smoke workflow implemented
- [ ] First GitHub Actions fixture artifact verified

