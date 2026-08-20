# PPT Production Engine Contract

## Engine role

This repository is a stateless production engine. It must not become a project repository.

The engine may contain:

- reusable build code;
- rendering and QA scripts;
- input/output schemas;
- public fixtures;
- CI workflows;
- third-party notices for engine dependencies.

The engine must not permanently store:

- caller project source code;
- private slide content;
- private images, templates, data, or fonts;
- caller deliverables;
- caller render evidence;
- caller repository credentials.

## Current fixture contract

The first engine interface is a local manifest:

```json
{
  "engine_version": "0.1.0",
  "request_id": "public-fixture-basic-001",
  "deck": {
    "title": "...",
    "layout": "LAYOUT_WIDE"
  },
  "output": {
    "pptx": "dist/.../deck.pptx",
    "qa_dir": "dist/.../qa",
    "render_dir": "dist/.../rendered"
  },
  "quality": {
    "min_slides": 6,
    "require_wide": true,
    "render_dpi": 144
  },
  "slides": []
}
```

Paths must be repository-relative and must not escape the workspace.

## Output evidence

The fixture workflow writes:

- `build-result.json`
- `package-qa.json`
- `render-qa.json`
- generated `.pptx`
- LibreOffice-exported `.pdf`
- rendered page `.png` files

Each QA JSON binds evidence to the generated PPTX SHA-256.

## Future private-project bridge

Future bridge workflows should follow this model:

1. Public engine workflow is the workflow owner and runner owner.
2. A scoped credential grants access only to the intended caller repository.
3. The engine checks out a caller build package into temporary workspace storage.
4. The engine builds, renders, and validates locally in the temporary runner.
5. The engine writes the final PPTX and QA evidence back to the caller repository.
6. The public engine repository does not upload private caller artifacts as public artifacts.

Never use a broad personal token. Prefer a GitHub App or fine-grained PAT with only the target repository permissions required for a specific bridge.

## Non-goals

- This engine is not a template marketplace.
- This engine is not a long-term artifact store.
- This engine is not a content authoring assistant.
- This engine is not responsible for domain-specific lesson, finance, business, or research logic.

Caller repositories own domain logic. The engine owns production mechanics.
