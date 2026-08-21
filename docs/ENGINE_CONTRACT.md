# PPT Production Engine Contract

## 1. Engine role

`PPT-Production-Engine` is a stateless public execution engine.

It owns only PPT production mechanics:

- PPTX generation;
- package validation;
- real rendering;
- page rasterization;
- native-object and animation QA where the selected backend supports them;
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
PPTX + package QA + render QA + state QA when applicable + PDF + page PNGs
        ↓ transient Actions artifact
AI orchestrator retrieves and reviews result
        ↓
AI orchestrator writes accepted result to the original Private repository
```

The public engine never needs a PAT, GitHub App installation token, deploy key, or other credential for the caller repository.

## 3. Handoff manifest

The current input is a repository-relative manifest staged below `handoff/`.

It contains only declarative build data accepted by the engine. Different bounded adapters may be used for mature PPT production backends, including native SVG → DrawingML conversion through a pinned PPT Master checkout and legacy PptxGenJS-backed generation where appropriate.

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

- PPT Master may convert semantic SVG into native PowerPoint DrawingML and native animation timing;
- PptxGenJS remains available for bounded legacy generation paths;
- LibreOffice Impress performs headless PPTX → PDF rendering;
- Poppler/pdftoppm produces per-page PNGs;
- librsvg/rsvg-convert may render SVG assets and authored animation-state snapshots;
- Python stdlib performs ZIP/package, XML/timing, and SHA-256 checks.

The custom layer is limited to contract validation, execution orchestration, compatibility normalization, QA evidence binding, and status reporting.

## 6. Output contract

A successful static workflow artifact contains at least:

- final `.pptx`;
- build/native-generation evidence;
- `package-qa.json`;
- `render-qa.json`;
- rendered PDF;
- per-page PNGs.

For an animated deck, the artifact additionally contains:

- the exact animation configuration;
- native animation/timing evidence;
- per-click authored state snapshots for every animated slide;
- `animation-state-qa.json` or equivalent state evidence.

Every receipt that claims to describe the same candidate must identify the exact same final PPTX SHA-256. A receipt from another PPTX generation is not admissible evidence for the current candidate.

## 7. Status discovery

Files below `status/` contain only non-sensitive metadata needed by an AI orchestrator to discover the latest evidence without asking a human to inspect the GitHub Actions UI.

A public status may include:

- workflow status and run ID;
- artifact name;
- request ID;
- build/package/render/state PASS/FAIL;
- final PPTX SHA-256;
- rendered page count;
- animated slides and rendered animation-state count;
- exact-hash-bound AI visual-review receipt;
- target-player playback state.

A status must distinguish machine/package/render success from final target-player acceptance. `PASS_PLAYABLE_PRE_TARGET_PLAYER` is therefore valid and intentionally weaker than final acceptance.

## 8. Stateless cleanup

After the AI orchestrator retrieves the completed result, temporary handoff input may be removed from the repository's current tree.

This cleanup is organizational only; it is not a secrecy mechanism and does not erase prior public Git history.

## 9. Genericity

The engine must stay domain-agnostic. It must not encode education, investment, recruiting, business, research, or topic-specific logic into its core contract.

Caller projects own content and domain logic. The engine owns only PPT production mechanics.

## 10. Layered acceptance rules

Acceptance is intentionally split into independently verifiable layers. Passing a later-looking file-generation step never retroactively approves an earlier or different representation.

1. **Source/component gate** — content, diagrams, charts, SVGs, images, formulas, and other components are checked independently before composition when practical.
2. **Composition/package gate** — the assembled PPTX must pass package, page-count, canvas, resource, and structural checks.
3. **Post-conversion render gate** — a converted/native PPTX must be rendered again. Visual approval of its source SVG/PNG assets cannot be inherited automatically after SVG → DrawingML, PDF → PPTX, template migration, geometry normalization, font substitution, or any other representation-changing conversion.
4. **Animated-state gate** — every animated slide is reviewed as a state sequence, not only as its final frame. For N presenter-paced click effects, evidence contains N+1 states: the initial state and one state after every click. The native package must independently prove the expected click-effect count/order/targets.
5. **Target-player gate** — when the deliverable depends on behavior specific to a target application such as Microsoft PowerPoint Desktop, that runtime is a separate final gate. Static rendering or OOXML inspection must not be mislabeled as target-player playback.

Machine QA and AI visual QA are separate claims. Both may be required by a caller workflow.

## 11. Exact-hash visual-review binding

AI/human visual acceptance is reusable only when it is bound to immutable evidence.

A reusable visual-review receipt must record at least the final PPTX SHA-256 and the hashes of the exact rendered pages or state snapshots that were inspected. A later workflow may reuse that review only when every required hash matches exactly.

A new build, conversion, rendering backend, font substitution, canvas transformation, animation edit, or regenerated PPTX invalidates prior visual acceptance unless the workflow proves the relevant output/evidence hashes are unchanged.

Filename equality, slide count, semantic similarity, or a matching source-asset hash alone is insufficient to transfer approval to a newly converted PPTX.

## 12. Single canonical status writer

For one production target and one public status path, exactly one automatic workflow is the canonical writer.

Superseded static/playable workflows must be retired, made manual-only, or write to different status paths. Multiple push-triggered pipelines must never race to overwrite the same status file with different generations or PPTX hashes.

The canonical workflow should run the complete ordered gate chain and publish status only from evidence produced in that same run. This prevents stale or cross-generation PASS states.

## 13. Canvas and compatibility boundary

Reviewed source assets may use an authoring canvas different from the final delivery canvas only when the conversion is explicit and isolated.

A delivery-canvas adaptation must:

- operate on a conversion copy, not silently mutate the reviewed source asset;
- declare the target canvas exactly;
- preserve semantic animation group identities where animation configuration addresses them;
- run package QA and post-conversion visual QA again;
- never treat compatibility normalization as visual approval.

SVG syntax that browsers or rasterizers accept is not automatically valid for a strict native PowerPoint converter. Converter-specific normalization therefore belongs to a bounded compatibility layer with explicit evidence.

## 14. Acceptance baseline

The executable stack has been verified on real GitHub-hosted runners for static and native-playable paths. Run002 V3 additionally validates the production rules above with:

- 15 reviewed source assets;
- exact 16:9 native PPTX package output;
- native object animations on slides 7, 13, and 15;
- 13 rendered presenter-paced animation states;
- 15 rendered final pages;
- exact-SHA-bound AI visual review;
- final Microsoft PowerPoint Desktop runtime playback intentionally still represented as a separate gate until actually executed.

Current contract version: `0.4.0`.
