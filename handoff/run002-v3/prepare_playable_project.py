#!/usr/bin/env python3
"""Prepare the Run002 V3 native SVG project with presenter-paced animation groups.

This script deliberately runs after the independent asset gate. It reuses the
15 reviewed SVG assets, adds only the missing dynamic-state groups needed for
slides 7/13/15, and writes a PPT Master animations.json file.

Important: asset SVGs are optimized first for high-quality deterministic PNG
review. Before sending them to PPT Master for native DrawingML generation, this
script also applies a bounded SVG compatibility normalization so strict target
conversion does not rediscover the same unsupported SVG syntax in every future
project.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "dist/run002-v3/assets/svg"
PROJECT = ROOT / "dist/run002-v3/playable-project"
OUT = PROJECT / "svg_output"
ANIM = PROJECT / "animations.json"
QA = ROOT / "dist/run002-v3/playable-qa/playable-project-prep.json"

PPT_SAFE_FONT = "Microsoft YaHei"
PAGE_BOUNDS = "0 0 1200 560"


def die(message: str) -> None:
    raise SystemExit(message)


def write(name: str, content: str) -> None:
    (OUT / name).write_text(content, encoding="utf-8")


def ensure(text: str, needle: str, label: str) -> None:
    if needle not in text:
        die(f"{label}: required token not found: {needle}")


def group_wrap(text: str, group_id: str, inner_pattern: str, label: str) -> str:
    if f'id="{group_id}"' in text:
        return text
    m = re.search(inner_pattern, text, flags=re.S)
    if not m:
        die(f"{label}: cannot locate group content for {group_id}")
    return text[:m.start()] + f'<g id="{group_id}">' + m.group(0) + '</g>' + text[m.end():]


def add_bounds_to_groups(text: str) -> tuple[str, int]:
    """Add required PPT Master bounds metadata to group tags.

    PPT Master rejects visible root-level groups that lack data-pptx-bounds. For
    this flat full-page route, using the page design zone for groups is a safe
    compatibility fallback; final geometry is still visually reviewed after
    native conversion. We add it to all unbounded groups so nested animation
    groups and future promoted groups are deterministic too.
    """
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if 'data-pptx-bounds=' in tag:
            return tag
        if tag.endswith('/>'):
            return tag[:-2] + f' data-pptx-bounds="{PAGE_BOUNDS}"/>'
        return tag[:-1] + f' data-pptx-bounds="{PAGE_BOUNDS}">'
    return re.subn(r'<g(?=[\s>/])[^>]*>', repl, text)


def normalize_for_ppt_master(text: str, *, label: str) -> tuple[str, dict[str, int]]:
    """Make reviewed SVG syntax compatible with strict PPT Master export.

    This is not a visual-quality approval. It is a bounded syntax/compatibility
    bridge from reviewed SVG/PNG assets to native PowerPoint DrawingML.
    """
    counts: dict[str, int] = {}

    def sub(pattern: str, repl: str, key: str, value: str) -> str:
        new, n = re.subn(pattern, repl, value)
        counts[key] = counts.get(key, 0) + n
        return new

    text = sub(r'\s+dominant-baseline="[^"]*"', '', 'removed_dominant_baseline', text)
    text = sub(r'font-weight="650"', 'font-weight="700"', 'font_weight_650_to_700', text)
    text = sub(r'font-weight="750"', 'font-weight="700"', 'font_weight_750_to_700', text)
    text = sub(
        r'font-family="Noto Sans CJK SC, Noto Sans, sans-serif"',
        f'font-family="{PPT_SAFE_FONT}"',
        'font_stack_to_ppt_safe',
        text,
    )
    text = sub(
        r"font-family='Noto Sans CJK SC, Noto Sans, sans-serif'",
        f'font-family="{PPT_SAFE_FONT}"',
        'font_stack_to_ppt_safe',
        text,
    )

    text = text.replace('#22354f', '#22354F')
    counts['uppercase_shadow_color'] = counts.get('uppercase_shadow_color', 0)

    if 'data-pptx-page-role=' not in text:
        text = text.replace('<svg ', '<svg data-pptx-page-role="content" ', 1)
        counts['added_root_page_role'] = 1
    else:
        text = re.sub(r'data-pptx-page-role="[^"]+"', 'data-pptx-page-role="content"', text, count=1)
        counts['added_root_page_role'] = 0

    text, group_bounds = add_bounds_to_groups(text)
    counts['added_group_bounds'] = group_bounds

    if 'dominant-baseline=' in text:
        die(f"{label}: dominant-baseline remained after normalization")
    if 'font-weight="650"' in text or 'font-weight="750"' in text:
        die(f"{label}: unsupported intermediate font weight remained after normalization")
    return text, counts


def slide07(text: str) -> str:
    ensure(text, 'id="work-path"', 'slide07')
    ensure(text, 'id="heat-path"', 'slide07')
    text = group_wrap(
        text,
        "formula-final",
        r'<g><rect x="445" y="435" width="310" height="58"[\s\S]*?</g>',
        "slide07",
    )
    return text


def slide13(text: str) -> str:
    if 'id="statement-A"' in text:
        return text
    statements = f'''
<g id="question-statements">
  <g id="statement-A"><text x="170" y="130" font-family="{PPT_SAFE_FONT}" font-size="25" font-weight="700" fill="#203047">只要物体温度升高，就一定吸收了热量。</text></g>
  <g id="statement-B"><text x="170" y="225" font-family="{PPT_SAFE_FONT}" font-size="25" font-weight="700" fill="#203047">外界对气体做功，气体内能可能增加。</text></g>
  <g id="statement-C"><text x="170" y="320" font-family="{PPT_SAFE_FONT}" font-size="25" font-weight="700" fill="#203047">热量是物体内部本来含有的一种物质。</text></g>
  <g id="statement-D"><text x="170" y="415" font-family="{PPT_SAFE_FONT}" font-size="25" font-weight="700" fill="#203047">摩擦生热说明机械能可以转化为内能。</text></g>
</g>
<g id="answer-reveal">
  <text x="1119" y="131" font-family="{PPT_SAFE_FONT}" font-size="24" font-weight="900" fill="#D64545" text-anchor="middle">错</text>
  <text x="1119" y="226" font-family="{PPT_SAFE_FONT}" font-size="24" font-weight="900" fill="#15803D" text-anchor="middle">对</text>
  <text x="1119" y="321" font-family="{PPT_SAFE_FONT}" font-size="24" font-weight="900" fill="#D64545" text-anchor="middle">错</text>
  <text x="1119" y="416" font-family="{PPT_SAFE_FONT}" font-size="24" font-weight="900" fill="#15803D" text-anchor="middle">对</text>
</g>
'''
    text = text.replace('</svg>', statements + '</svg>')
    for token in ["statement-A", "statement-B", "statement-C", "statement-D", "answer-reveal", "摩擦生热说明机械能可以转化为内能"]:
        ensure(text, token, 'slide13')
    return text


def slide15(text: str) -> str:
    ensure(text, 'id="work-path"', 'slide15')
    ensure(text, 'id="heat-path"', 'slide15')
    ensure(text, 'id="state-change"', 'slide15')
    text = group_wrap(
        text,
        "delta-u-target",
        r'<g><rect x="500" y="245" width="165" height="70"[\s\S]*?</g>\s*<text x="582" y="345"[\s\S]*?</text>',
        "slide15",
    )
    text = group_wrap(
        text,
        "observable-result",
        r'<g id="state-change">[\s\S]*?</g><g><rect x="715" y="245" width="145" height="70"[\s\S]*?</g>\s*<rect x="960" y="225"[\s\S]*?<line x1="860" y1="280" x2="955" y2="280"[^>]*/>',
        "slide15",
    )
    text = group_wrap(
        text,
        "bottom-chain",
        r'<text x="600" y="505"[\s\S]*?</text>',
        "slide15",
    )
    return text


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    QA.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    normalization_totals: dict[str, int] = {}
    for src in sorted(SRC.glob("*.svg")):
        text = src.read_text(encoding="utf-8")
        if src.name.startswith("07-"):
            text = slide07(text)
        elif src.name.startswith("13-"):
            text = slide13(text)
        elif src.name.startswith("15-"):
            text = slide15(text)
        text, counts = normalize_for_ppt_master(text, label=src.name)
        for key, value in counts.items():
            normalization_totals[key] = normalization_totals.get(key, 0) + value
        write(src.name, text)
        rows.append({"source": src.relative_to(ROOT).as_posix(), "output": (OUT/src.name).relative_to(ROOT).as_posix(), "normalization": counts})

    animations = {
        "version": 1,
        "defaults": {"transition": {"effect": "fade", "duration": 0.25}},
        "slides": {
            "07-s07-energy-ledger": {"groups": {"work-path": {"effect": "entrance_fade", "trigger": "on-click", "order": 1, "duration": 0.25}, "heat-path": {"effect": "entrance_fade", "trigger": "on-click", "order": 2, "duration": 0.25}, "formula-final": {"effect": "entrance_fade", "trigger": "on-click", "order": 3, "duration": 0.25}}},
            "13-s13-concept-check": {"groups": {"question-statements": {"effect": "entrance_fade", "trigger": "on-click", "order": 1, "duration": 0.25}, "answer-reveal": {"effect": "entrance_fade", "trigger": "on-click", "order": 2, "duration": 0.25}}},
            "15-s15-synthesis-two-channels": {"groups": {"work-path": {"effect": "entrance_fade", "trigger": "on-click", "order": 1, "duration": 0.25}, "heat-path": {"effect": "entrance_fade", "trigger": "on-click", "order": 2, "duration": 0.25}, "delta-u-target": {"effect": "entrance_fade", "trigger": "on-click", "order": 3, "duration": 0.25}, "observable-result": {"effect": "entrance_fade", "trigger": "on-click", "order": 4, "duration": 0.25}, "bottom-chain": {"effect": "entrance_fade", "trigger": "on-click", "order": 5, "duration": 0.25}}}
        }
    }
    ANIM.write_text(json.dumps(animations, ensure_ascii=False, indent=2), encoding="utf-8")
    evidence = {
        "status": "PASS",
        "project": PROJECT.relative_to(ROOT).as_posix(),
        "svg_count": len(rows),
        "animated_slides": [7, 13, 15],
        "minimum_clicks": {"7": 3, "13": 2, "15": 5},
        "animations": ANIM.relative_to(ROOT).as_posix(),
        "normalization_totals": normalization_totals,
        "rows": rows,
        "scope": "Prepares native SVG project for playable PPTX candidate; does not approve target-player playback or reuse PNG asset visual review for the converted playable output."
    }
    QA.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
