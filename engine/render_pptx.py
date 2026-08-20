#!/usr/bin/env python3
"""Render a generated PPTX with LibreOffice and bind rendered pages to SHA-256 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path.cwd().resolve()


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd or ROOT), text=True, capture_output=True, check=False)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_inside_root(rel: str, label: str) -> Path:
    raw = Path(rel)
    if raw.is_absolute():
        raise SystemExit(f"{label}: absolute paths are forbidden: {rel}")
    resolved = (ROOT / raw).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"{label}: path escapes repository root: {rel}") from exc
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_command(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"Required command not found: {name}")
    return path


def libreoffice_version() -> str:
    proc = run([require_command("libreoffice"), "--version"])
    return (proc.stdout or proc.stderr).strip()


def render(manifest_path: Path) -> dict:
    manifest = load_json(manifest_path)
    pptx_path = resolve_inside_root(manifest["output"]["pptx"], "output.pptx")
    qa_dir = resolve_inside_root(manifest["output"]["qa_dir"], "output.qa_dir")
    render_dir = resolve_inside_root(manifest["output"]["render_dir"], "output.render_dir")
    qa_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    if not pptx_path.exists():
        raise SystemExit(f"PPTX missing: {pptx_path}")

    libreoffice = require_command("libreoffice")
    pdftoppm = require_command("pdftoppm")
    pdfinfo = shutil.which("pdfinfo")

    # Clean prior render outputs for deterministic evidence.
    for child in render_dir.iterdir():
        if child.is_file():
            child.unlink()

    proc = run([
        libreoffice,
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--convert-to",
        "pdf",
        "--outdir",
        str(render_dir),
        str(pptx_path),
    ])
    if proc.returncode != 0:
        raise SystemExit(f"LibreOffice conversion failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

    expected_pdf = render_dir / f"{pptx_path.stem}.pdf"
    pdf_files = list(render_dir.glob("*.pdf"))
    pdf_path = expected_pdf if expected_pdf.exists() else (pdf_files[0] if pdf_files else None)
    if not pdf_path or not pdf_path.exists():
        raise SystemExit("LibreOffice did not produce a PDF")

    dpi = int(manifest.get("quality", {}).get("render_dpi", 144))
    png_prefix = render_dir / "page"
    proc = run([pdftoppm, "-png", "-r", str(dpi), str(pdf_path), str(png_prefix)])
    if proc.returncode != 0:
        raise SystemExit(f"pdftoppm render failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")

    page_pngs = sorted(render_dir.glob("page-*.png"))
    declared_slides = len(manifest["slides"])
    failures = []
    if len(page_pngs) != declared_slides:
        failures.append(f"Rendered page count mismatch: rendered={len(page_pngs)} declared={declared_slides}")

    pdf_pages = None
    if pdfinfo:
        proc = run([pdfinfo, str(pdf_path)])
        if proc.returncode == 0:
            m = re.search(r"^Pages:\s+(\d+)", proc.stdout, re.MULTILINE)
            if m:
                pdf_pages = int(m.group(1))
                if pdf_pages != declared_slides:
                    failures.append(f"PDF page count mismatch: pdf={pdf_pages} declared={declared_slides}")

    pages = []
    for index, page in enumerate(page_pngs, start=1):
        pages.append({
            "page": index,
            "png": page.relative_to(ROOT).as_posix(),
            "sha256": sha256(page),
            "bytes": page.stat().st_size,
        })

    result = {
        "status": "PASS" if not failures else "FAIL",
        "engine_version": manifest.get("engine_version"),
        "request_id": manifest.get("request_id"),
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "pptx": pptx_path.relative_to(ROOT).as_posix(),
        "pptx_sha256": sha256(pptx_path),
        "pdf": pdf_path.relative_to(ROOT).as_posix(),
        "pdf_sha256": sha256(pdf_path),
        "pdf_pages": pdf_pages,
        "render_backend": "LibreOffice Impress headless",
        "render_backend_version": libreoffice_version(),
        "pdftoppm": pdftoppm,
        "dpi": dpi,
        "pages": pages,
        "failures": failures,
    }
    out = qa_dir / "render-qa.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    manifest_path = resolve_inside_root(args.manifest, "manifest")
    result = render(manifest_path)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
