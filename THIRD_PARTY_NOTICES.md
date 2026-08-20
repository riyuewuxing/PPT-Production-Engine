# Third-party notices

This engine intentionally reuses mature production components instead of rebuilding the entire PPTX and rendering stack from scratch.

## Runtime dependencies

### PptxGenJS

- Purpose: PPTX generation from JavaScript.
- Package: `pptxgenjs`
- Version used by this engine: `4.0.0`
- Upstream: https://github.com/gitbrent/PptxGenJS
- License: MIT, as published by the upstream project/package.

### LibreOffice

- Purpose: headless PPTX-to-PDF rendering in GitHub Actions.
- Installed from Ubuntu package repositories during CI.
- Upstream: https://www.libreoffice.org/
- License: LibreOffice is distributed under MPL 2.0 with additional notices for bundled components. The engine does not vendor LibreOffice binaries.

### Poppler utilities

- Purpose: `pdftoppm` and optional `pdfinfo` for PDF-to-PNG rendering and page count checks.
- Installed from Ubuntu package repositories during CI.
- Upstream: https://poppler.freedesktop.org/
- License: GPL-family licensing applies to Poppler. The engine does not vendor Poppler binaries.

### Noto CJK fonts

- Purpose: stable CJK fallback rendering in CI.
- Installed from Ubuntu package repositories during CI.
- Upstream: https://github.com/notofonts/noto-cjk
- License: SIL Open Font License 1.1.

## Vendoring policy

This repository should avoid vendoring large third-party binaries. Prefer runtime installation in CI or pinned package manager dependencies.

If a future version vendors third-party source or binary artifacts, it must add the corresponding license text and notice entries before release.
