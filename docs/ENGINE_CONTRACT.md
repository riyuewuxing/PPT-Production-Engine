# PPT Production Engine Contract

## 1. Engine role

`PPT-Production-Engine` is a stateless public execution engine.

It owns only PPT production mechanics:

- PPTX generation;
- package validation;
- real rendering;
- page rasterization;
- SHA-256-bound QA evidence;
- GitHub-hosted execution.

It does not own project meaning, project history, private repository access, or final product decisions.

## 2. AI-mediated production contract

The primary path is:

```text
Private caller repository
        ↓
AI orchestrator reads project and prepares a minimum build package
        ↓
Public-safe handoff input
        ↓
PPT Production Engine / GitHub-hosted runner
        ↓
PPTX + package QA + render QA + PDF + page PNGs
        ↓ transient Actions artifact
AI orchestrator retrieves and reviews result
        ↓
AI orchestrator writes accepted result to the original Private repository
```

The public engine never needs a PAT, GitHub App installation token, deploy key, or other credential for the caller repository.

## 3. Handoff manifest

The current input is a repository-relative manifest staged at:

`handoff/current/build-manifest.json`

It contains only declarative build data accepted by the engine. The current driver uses PptxGenJS-backed slide specifications.

All engine output paths must remain inside the public engine workspace. Absolute paths and `..` traversal are forbidden.

## 4. Privacy boundary

This repository is public. Any handoff input committed here must be treated as permanently public even after the current file is deleted, because Git history, clones, mirrors, or caches may retain it.

Therefore a public handoff must never contain:

- API keys, tokens, passwords, cookies, certificates, or other credentials;
- sensitive personal data;
- confidential business or research data;
- assets whose license forbids public exposure;
- any content the caller requires to remain secret.

Sensitive jobs require a separate private execution path and are outside this public-engine contract.

## 5. Mature execution components

The engine does not reimplement mature document machinery:

- PptxGenJS generates standards-compatible PPTX packages;
- LibreOffice Impress performs headless PPTX → PDF rendering;
- Poppler/pdftoppm produces per-page PNGs;
- Python stdlib performs ZIP/package and SHA-256 checks.

The custom layer is limited to contract validation, execution orchestration, QA evidence binding, and status reporting.

## 6. Output contract

A successful workflow artifact contains at least:

- final `.pptx`;
- `build-result.json`;
- `package-qa.json`;
- `render-qa.json`;
- rendered PDF;
- per-page PNGs.

`build-result.json`, `package-qa.json`, and `render-qa.json` must identify the same request and final PPTX SHA-256.

## 7. Status discovery

`status/ai-handoff-last.json` contains only non-sensitive metadata:

- workflow status;
- run ID;
- artifact name;
- request ID;
- build/package/render PASS/FAIL;
- final PPTX SHA-256;
- rendered page count.

This allows ChatGPT or another AI orchestrator to complete the workflow without asking a human to inspect the GitHub Actions UI.

## 8. Stateless cleanup

After the AI orchestrator retrieves the completed result, the current `handoff/` input is removed from the repository's current tree.

This cleanup is organizational only; it is not a secrecy mechanism and does not erase prior public Git history.

## 9. Genericity

The engine must stay domain-agnostic. It must not encode education, investment, recruiting, business, research, or topic-specific logic into its core contract.

Caller projects own content and domain logic. The engine owns only PPT production mechanics.

## 10. Acceptance

The executable stack is already verified on real GitHub-hosted Ubuntu runners:

- engine fixture smoke: Build PASS / Package QA PASS / Render QA PASS / 6 pages;
- AI-mediated handoff smoke: Build PASS / Package QA PASS / Render QA PASS / 6 pages.

AI-mediated smoke PPTX SHA-256:

`0d1e31589e2328b788903bcebd4d90e7f6bdee1bb8e12711b4c56ed00f728a0c`

Current contract version: `0.3.0`.
