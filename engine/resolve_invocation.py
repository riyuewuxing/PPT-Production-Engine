#!/usr/bin/env python3
"""Resolve a trusted build invocation without exposing caller content."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_RE = re.compile(r"^[A-Za-z0-9_./-]+$")


def die(msg: str) -> None:
    raise SystemExit(msg)


def safe_rel(value: str, label: str) -> str:
    p = Path(value)
    if not value or p.is_absolute() or ".." in p.parts:
        die(f"{label}: unsafe relative path: {value!r}")
    return p.as_posix()


def write_output(name: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        die("GITHUB_OUTPUT is not set")
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    ap.add_argument("--integration-config", default="integration/private-smoke.json")
    ap.add_argument("--allowlist", default="config/allowed-repositories.json")
    args = ap.parse_args()

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event = json.loads(Path(args.event).read_text(encoding="utf-8")) if args.event else {}

    if event_name == "repository_dispatch":
        payload = event.get("client_payload") or {}
    elif event_name == "workflow_dispatch":
        payload = event.get("inputs") or {}
    elif event_name == "push":
        payload = json.loads(Path(args.integration_config).read_text(encoding="utf-8"))
    else:
        die(f"Unsupported event: {event_name}")

    source_repo = str(payload.get("source_repo", "")).strip()
    source_ref = str(payload.get("source_ref", "main")).strip()
    request_path = safe_rel(str(payload.get("request_path", "")), "request_path")
    writeback_branch = str(payload.get("writeback_branch", source_ref)).strip()

    if not REPO_RE.fullmatch(source_repo):
        die(f"Invalid repository: {source_repo!r}")
    if not REF_RE.fullmatch(source_ref) or source_ref.startswith("-"):
        die(f"Invalid source_ref: {source_ref!r}")
    if not REF_RE.fullmatch(writeback_branch) or writeback_branch.startswith("-"):
        die(f"Invalid writeback_branch: {writeback_branch!r}")

    allow_cfg = json.loads(Path(args.allowlist).read_text(encoding="utf-8"))
    allowed = set(allow_cfg.get("repositories", []))
    if source_repo not in allowed:
        die(f"Repository is not allowlisted: {source_repo}")

    write_output("source_repo", source_repo)
    write_output("source_ref", source_ref)
    write_output("request_path", request_path)
    write_output("writeback_branch", writeback_branch)
    print(f"Resolved trusted request: repo={source_repo} ref={source_ref} request={request_path}")


if __name__ == "__main__":
    main()
