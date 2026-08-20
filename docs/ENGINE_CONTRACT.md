# PPT Production Engine Contract

## 1. Engine role

`PPT-Production-Engine` is a stateless production service for GitHub-hosted projects.

It owns production mechanics, not project meaning.

The engine may permanently contain:

- reusable PPTX build code;
- rendering and QA scripts;
- request/source/output schemas;
- trusted orchestration workflows;
- public synthetic fixtures;
- dependency/version/third-party notices.

The engine must not permanently contain:

- caller project source code or private slide content;
- caller images, templates, business/research data, or private fonts;
- caller deliverables;
- caller render evidence;
- repository access credentials.

## 2. Primary cross-repository contract

The production path is:

```text
Private caller repository
    build-request.json
    source JSON
          ↓ temporary authenticated checkout
Public PPT Production Engine / GitHub-hosted runner
          ↓ build + package QA + real render QA
Fresh checkout of the same private caller repository
          ↓
final PPTX + hash-bound evidence committed back to caller
```

The public engine repository itself remains unchanged by caller builds.

## 3. Caller request v1

A caller request uses `contract_version = 1` and currently supports the `pptxgenjs-spec-v1` driver.

```json
{
  "contract_version": "1",
  "request_id": "example-001",
  "driver": "pptxgenjs-spec-v1",
  "source": "ppt/source.json",
  "output": {
    "pptx": "ppt/exports/example.pptx",
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

Rules:

- request/source/output paths are repository-relative;
- absolute paths and `..` traversal are rejected;
- writeback destinations must stay inside the caller repository;
- source must be declarative JSON for the current driver;
- caller code is not executed during v1 cross-repository builds.

## 4. Isolation and credential boundary

The credential boundary is mandatory:

1. Engine code is checked out first.
2. Invocation is validated against `config/allowed-repositories.json`.
3. Private caller input is checked out using `PPT_ENGINE_REPO_TOKEN` with `persist-credentials: false`.
4. The caller source is parsed as data, not executed as code.
5. Build, package QA, and render QA run without private write credentials available to caller content.
6. Only after QA succeeds is the private repository checked out again into a fresh writeback directory.
7. Generated output is copied into that fresh checkout.
8. The engine refuses writeback if package QA or render QA is FAIL or if their PPTX SHA-256 does not match the generated PPTX.
9. The fresh checkout commits and pushes the generated result to the requested private branch.

The built-in `GITHUB_TOKEN` is scoped to the public engine repository and is not sufficient for a different private repository. The cross-repository credential is therefore a one-time infrastructure prerequisite, not a per-build user action.

## 5. Evidence contract

A successful build writes back at minimum:

- final `.pptx`;
- `build-result.json`;
- `package-qa.json`;
- `render-qa.json`;
- `engine-result.json`.

When `writeback_render_evidence = true`, it also writes:

- LibreOffice-exported PDF;
- every Poppler-rendered page PNG.

`package-qa.json`, `render-qa.json`, and `engine-result.json` must bind to the same final PPTX SHA-256.

## 6. Public artifact rule

Private caller artifacts must not be uploaded as artifacts of the public engine workflow.

The only allowed long-term destination for private build outputs is the authorized private caller repository (or another explicitly private destination added in a future contract).

Synthetic engine fixtures are exempt because they contain no caller data.

## 7. Genericity

The engine must remain project-agnostic. Request/schema fields must not encode domains such as education, investment, business, recruiting, research, or a particular PPT topic.

Caller projects own:

- domain logic;
- content generation;
- project-specific templates/assets;
- storyboards;
- data sourcing;
- final product decisions.

The engine owns:

- PPTX production;
- generic package validation;
- generic rendering;
- generic evidence generation;
- generic writeback mechanics.

Additional drivers may be added later, but they must preserve the same stateless and credential-isolation rules.

## 8. Acceptance definition

A synthetic public fixture proves only that the engine executable stack works.

The engine is not accepted for production until a real integration test completes this exact path:

`Private source → Public GitHub-hosted runner → generated PPTX → real render/QA → commit back to Private repository`.

Current contract version: `0.2.0`.
