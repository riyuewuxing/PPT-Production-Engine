#!/usr/bin/env python3
"""Tiny semantic-label normalization after iteration 3."""
from pathlib import Path

p = Path('dist/run002-v3/assets/svg/01-s01-hero-two-channels.svg')
raw = p.read_text(encoding='utf-8')
old = '>ΔU 改变</text>'
new = '>内能改变 ΔU</text>'
if old not in raw:
    raise SystemExit('iteration4: expected visible S1 ΔU label not found')
p.write_text(raw.replace(old, new, 1), encoding='utf-8')
print('iteration4 normalized S1 visible semantic label')
