#!/usr/bin/env python3
"""
build_assets.py — generates the animated SVG system used by the profile README.

Everything is plain SVG (SMIL + CSS). No JavaScript, no external fonts, no
network calls: GitHub's image proxy strips all of that, so the assets have to
be self-contained to survive.

    python3 tools/build_assets.py
"""

from __future__ import annotations

import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# ── palette (sampled from assets/banner.png) ──────────────────────────────────
C = {
    "bg0": "#0a0a0a",
    "bg1": "#1c1c1c",
    "panel": "#0d0d0d",
    "panel2": "#181818",
    "line": "#3d3d3d",
    "line_soft": "#242424",
    "violet": "#8f7cff",
    "purple": "#c3a8ff",
    "purple_dim": "#9d86c9",
    "text": "#d6d6d6",
    "muted": "#6e6e6e",
    "mint": "#39e0a0",
    "amber": "#e2a63c",
    "rose": "#e5534b",
}

MONO = "ui-monospace,'SFMono-Regular','JetBrains Mono','Fira Code',Consolas,'DejaVu Sans Mono',monospace"
SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,Georgia,'Times New Roman',serif"

random.seed(1312)  # stable output across runs


def cw(fs: float) -> float:
    """Advance width of one monospace glyph at font-size fs."""
    return fs * 0.6


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, fs=16, fill=None, family=MONO, anchor="start", weight=None,
        opacity=None, ls=None, fixed=True, extra=""):
    fill = fill or C["text"]
    a = [f'x="{x:g}"', f'y="{y:g}"', f'font-family="{family}"', f'font-size="{fs:g}"', f'fill="{fill}"']
    if fixed and family is MONO and s:
        a.append(f'textLength="{len(s) * cw(fs):.1f}" lengthAdjust="spacingAndGlyphs"')
    if anchor != "start":
        a.append(f'text-anchor="{anchor}"')
    if weight:
        a.append(f'font-weight="{weight}"')
    if opacity is not None:
        a.append(f'opacity="{opacity:g}"')
    if ls is not None:
        a.append(f'letter-spacing="{ls:g}"')
    if extra:
        a.append(extra)
    return f'<text {" ".join(a)}>{esc(s)}</text>'


def type_anim(width: float, chars: int, start: float, dur: float, cycle: float) -> str:
    """Character-stepped reveal, looping perfectly over `cycle` seconds."""
    kt, vals = [], []

    def add(t, v):
        t = min(max(t / cycle, 0.0), 1.0)
        if kt and t <= kt[-1]:
            t = kt[-1]
        kt.append(t)
        vals.append(round(v, 2))

    add(0, 0)
    if start > 0:
        add(start, 0)
    for i in range(1, chars + 1):
        add(start + dur * i / chars, width * i / chars)
    if kt[-1] < 1.0:
        kt.append(1.0)
        vals.append(round(width, 2))
    return (f'<animate attributeName="width" dur="{cycle:g}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{";".join(f"{t:.4f}" for t in kt)}" '
            f'values="{";".join(str(v) for v in vals)}"/>')


def fade_in(start: float, cycle: float, dur: float = 0.25, to: float = 1.0) -> str:
    k0 = max(0.0, start / cycle)
    k1 = min(1.0, (start + dur) / cycle)
    return (f'<animate attributeName="opacity" dur="{cycle:g}s" repeatCount="indefinite" '
            f'keyTimes="0;{k0:.4f};{k1:.4f};1" values="0;0;{to:g};{to:g}"/>')


def constellation(w, h, n=46, seed=7, opacity=0.9, link=150):
    """Faint node/edge field echoing the banner artwork."""
    rnd = random.Random(seed)
    pts = [(rnd.uniform(8, w - 8), rnd.uniform(8, h - 8)) for _ in range(n)]
    out = [f'<g opacity="{opacity:g}">']
    for i, (x1, y1) in enumerate(pts):
        for x2, y2 in pts[i + 1:]:
            d = math.hypot(x2 - x1, y2 - y1)
            if d < link:
                o = 0.18 * (1 - d / link)
                out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                           f'stroke="{C["violet"]}" stroke-width="0.7" opacity="{o:.3f}"/>')
    for i, (x, y) in enumerate(pts):
        r = rnd.choice([0.9, 1.1, 1.4, 1.9])
        dly = rnd.uniform(0, 6)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{C["purple"]}" '
                   f'opacity="0.5"><animate attributeName="opacity" values="0.15;0.75;0.15" '
                   f'dur="{rnd.uniform(3.5, 7):.1f}s" begin="-{dly:.1f}s" repeatCount="indefinite"/></circle>')
    out.append("</g>")
    return "".join(out)


def corner_brackets(x, y, w, h, size=18, color=None, sw=1.4, opacity=0.55):
    color = color or C["violet"]
    p = (f'<path d="M{x} {y + size}V{y}H{x + size} M{x + w - size} {y}H{x + w}V{y + size} '
         f'M{x + w} {y + h - size}V{y + h}H{x + w - size} M{x + size} {y + h}H{x}V{y + h - size}" '
         f'fill="none" stroke="{color}" stroke-width="{sw}" opacity="{opacity}"/>')
    return p


def hud_rings(cx, cy, r, count=3):
    out = ['<g opacity="0.35">']
    for i in range(count):
        rr = r - i * 26
        dash = [f"{2 + i * 3} {10 + i * 6}", "34 12", "6 9 22 9"][i % 3]
        dur = 26 + i * 11
        d = "" if i % 2 == 0 else "-"
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{C["violet"]}" '
            f'stroke-width="1" stroke-dasharray="{dash}" opacity="{0.9 - i * 0.2:.2f}">'
            f'<animateTransform attributeName="transform" type="rotate" '
            f'from="0 {cx} {cy}" to="{d}360 {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></circle>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - count * 26 - 4}" fill="none" '
               f'stroke="{C["purple"]}" stroke-width="0.8" opacity="0.5"/>')
    out.append("</g>")
    return "".join(out)


def head(w, h, title, extra_defs="", extra_style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t"><title id="t">{esc(title)}</title>'
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{C["bg0"]}"/><stop offset="0.55" stop-color="{C["bg1"]}"/>'
        f'<stop offset="1" stop-color="{C["bg0"]}"/></linearGradient>'
        f'<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75">'
        f'<stop offset="0.5" stop-color="{C["bg0"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#000000" stop-opacity="0.5"/></radialGradient>'
        f'<pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<path d="M26 0H0V26" fill="none" stroke="{C["line_soft"]}" stroke-width="1"/></pattern>'
        f'<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
        f'<feGaussianBlur stdDeviation="4" result="b"/><feMerge>'
        f'<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<filter id="soft" x="-60%" y="-60%" width="220%" height="220%">'
        f'<feGaussianBlur stdDeviation="9"/></filter>'
        f'{extra_defs}</defs>'
        f'<style>text{{white-space:pre}}'
        f'@keyframes blink{{0%,45%{{opacity:1}}46%,100%{{opacity:0}}}}'
        f'@keyframes flick{{0%,100%{{opacity:.12}}50%{{opacity:.9}}}}'
        f'@keyframes breathe{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}'
        f'{extra_style}</style>'
        f'<rect width="{w}" height="{h}" fill="url(#bg)"/>'
        f'<rect width="{w}" height="{h}" fill="url(#grid)" opacity="0.55"/>'
    )


def tail(w, h, radius=14):
    return (f'<rect width="{w}" height="{h}" fill="url(#vig)"/>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{radius}" fill="none" '
            f'stroke="{C["line"]}" stroke-width="1"/></svg>')


def write(name: str, body: str):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"{name:26s} {len(body) / 1024:6.1f} KB")


# ── shared: typed terminal lines with a real clip-path reveal ────────────────

def typed_line(uid, x, y, s, fs=18, fill=None, start=0.0, dur=1.0, cycle=10.0,
                weight=None, ls=None, family=MONO):
    fill = fill or C["text"]
    width = len(s) * cw(fs)
    clip_width = width + cw(fs)  # small trailing buffer so the last glyph never clips
    clip_id = f"clip-{uid}"
    rect_h = fs * 1.6
    anim = type_anim(clip_width, max(len(s), 1), start, dur, cycle)
    frag = (
        f'<clipPath id="{clip_id}"><rect x="{x - 2:g}" y="{y - fs * 1.08:g}" '
        f'height="{rect_h:g}" width="0">{anim}</rect></clipPath>'
        f'<g clip-path="url(#{clip_id})">'
        f'{txt(x, y, s, fs=fs, fill=fill, weight=weight, ls=ls, family=family)}</g>'
    )
    return frag, width


def gated_cursor(x, y, fs, reveal_at, cycle, glyph="▌", color=None):
    """Cursor that stays hidden until `reveal_at`, then blinks forever."""
    color = color or C["purple"]
    k = max(0.0, min(1.0, reveal_at / cycle))
    return (
        f'<g><animate attributeName="opacity" dur="{cycle:g}s" repeatCount="indefinite" '
        f'keyTimes="0;{k:.4f};1" values="0;0;1"/>'
        f'<text x="{x:g}" y="{y:g}" font-family="{MONO}" font-size="{fs:g}" fill="{color}">{glyph}'
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.5;0.5;1;1" '
        f'dur="0.9s" repeatCount="indefinite"/></text></g>'
    )


def scanline_sweep(w, h, cycle=6.0, band=90, color=None, opacity=0.10):
    color = color or C["purple"]
    gid = f"scan-{int(w)}x{int(h)}-{int(band)}"
    return (
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="{color}" stop-opacity="{opacity}"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<rect x="0" y="{-band}" width="{w}" height="{band}" fill="url(#{gid})">'
        f'<animate attributeName="y" values="{-band};{h};{-band}" dur="{cycle:g}s" '
        f'repeatCount="indefinite"/></rect>'
    )


_CHIP_MARKS = {"ok": "OK", "warn": "~", "dev": "WIP", "off": "--"}
_CHIP_PAD_L, _CHIP_GAP, _CHIP_PAD_R = 26, 16, 16


def status_chip_width(label, state="ok", fs=13):
    mark = _CHIP_MARKS.get(state, "OK")
    mark_fs = fs - 2
    label_w = len(label) * cw(fs)
    mark_w = len(mark) * cw(mark_fs)
    return _CHIP_PAD_L + label_w + _CHIP_GAP + mark_w + _CHIP_PAD_R


_CHIP_STATE_TONES = {"ok": C["mint"], "dev": C["purple"], "warn": C["amber"], "off": "#5a5a5a"}


def status_chip(x, y, label, state="ok", fs=13):
    col = _CHIP_STATE_TONES.get(state, "#f0f0f0")
    mark = _CHIP_MARKS.get(state, "OK")
    mark_fs = fs - 2
    label_w = len(label) * cw(fs)
    label_x = _CHIP_PAD_L
    mark_x = _CHIP_PAD_L + label_w + _CHIP_GAP
    w = status_chip_width(label, state, fs)
    dly = random.Random(hash(label) & 0xffff).uniform(0, 2)
    return (
        f'<g transform="translate({x:g},{y:g})">'
        f'<rect x="0" y="0" width="{w:.1f}" height="24" rx="12" fill="{C["panel2"]}" '
        f'stroke="{col}" stroke-opacity="0.55" stroke-width="1"/>'
        f'<circle cx="14" cy="12" r="4" fill="{col}">'
        f'<animate attributeName="opacity" values="0.4;1;0.4" dur="{2.2 + dly:.1f}s" '
        f'repeatCount="indefinite"/></circle>'
        f'{txt(label_x, 16.5, label, fs=fs, fill=C["text"])}'
        f'{txt(mark_x, 16.5, mark, fs=mark_fs, fill=col, family=MONO)}'
        f'</g>'
    )


# ── asset 1: hero terminal boot sequence ──────────────────────────────────────

def build_hero():
    w, h = 1200, 270
    cycle = 13.0
    s = head(w, h, "fogg boot sequence — animated terminal", extra_style="""
      .term-glow{filter:url(#glow)}
    """)
    s += constellation(w, h, n=34, seed=3, opacity=0.6, link=130)
    s += hud_rings(w - 96, 70, 150, count=3)
    s += scanline_sweep(w, h, cycle=7.5, band=70, opacity=0.07)

    # terminal panel
    px, py, pw, ph = 26, 22, w - 52, h - 44
    s += (f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" '
          f'fill="{C["panel"]}" fill-opacity="0.55" stroke="{C["line"]}"/>')
    s += corner_brackets(px, py, pw, ph, size=22)

    # window chrome
    s += f'<g transform="translate({px + 20},{py + 22})">'
    for i, col in enumerate([C["rose"], C["amber"], C["mint"]]):
        s += f'<circle cx="{i * 18}" cy="0" r="5" fill="{col}" opacity="0.85"/>'
    s += txt(70, 5, "fogg@github — zsh", fs=12.5, fill=C["muted"], ls=0.5)
    s += "</g>"

    lx, fs1, fs2 = px + 26, 18, 15.5
    ly = py + 62
    line_h = 30

    lines = [
        ("$ whoami", fs1, C["purple"], 0.0, 0.9),
        ("> fogg — systems / security / automation", fs2, C["text"], 1.05, 1.7),
        ("$ status --watch", fs1, C["purple"], 3.05, 0.9),
    ]
    t = 0.0
    for text_s, fs, fill, start, dur in lines:
        frag, width = typed_line(f"h{abs(hash(text_s))%99999}", lx, ly, text_s,
                                  fs=fs, fill=fill, start=start, dur=dur, cycle=cycle)
        s += frag
        t = start + dur
        ly += line_h

    s += gated_cursor(lx + len("$ status --watch") * cw(fs1) + 4, ly - line_h, fs1, t, cycle)

    chips = [("linux", "ok"), ("networking", "ok"), ("iam", "dev"), ("cloud", "warn"), ("defensive_sec", "dev")]
    cx = lx
    cy = ly + 6
    chip_start = t + 0.35
    for i, (label, state) in enumerate(chips):
        chip = status_chip(cx, cy, label, state)
        reveal = chip_start + i * 0.22
        s += f'<g>{fade_in(reveal, cycle, dur=0.3)}{chip}</g>'
        cx += status_chip_width(label, state) + 12

    foot_start = chip_start + len(chips) * 0.22 + 0.6
    foot = "$ echo \"learning → building → breaking → understanding\""
    frag, _ = typed_line(f"hfoot", lx, ly + 62, foot, fs=13.5, fill=C["muted"],
                          start=foot_start, dur=1.5, cycle=cycle)
    s += frag
    s += gated_cursor(lx + len(foot) * cw(13.5) + 3, ly + 62, 13.5, foot_start + 1.5, cycle)

    s += tail(w, h)
    return s


# ── asset 2: system pulse — layered signal / network monitor ─────────────────

def build_pulse():
    w, h = 1200, 220
    cycle = 9.0
    s = head(w, h, "fogg system pulse — layered telemetry")
    s += constellation(w, h, n=26, seed=11, opacity=0.35, link=110)
    s += scanline_sweep(w, h, cycle=8, band=60, opacity=0.06)

    px, py, pw, ph = 24, 20, w - 48, h - 40
    s += (f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" '
          f'fill="{C["panel"]}" fill-opacity="0.5" stroke="{C["line"]}"/>')
    s += corner_brackets(px, py, pw, ph, size=20)

    s += txt(px + 20, py + 28, "TELEMETRY // live", fs=12, fill=C["muted"], ls=1.5)
    s += (f'<circle cx="{px + pw - 24}" cy="{py + 23}" r="4" fill="{C["mint"]}">'
          f'<animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    s += txt(px + pw - 34, py + 28, "STREAMING", fs=11, fill=C["mint"], anchor="end", ls=1)

    # three signal traces at different heights, phases, colors
    traces = [
        (C["violet"], py + 70, 22, "10 16", 0.0),
        (C["purple"], py + 100, 14, "3 9 16 9", 1.2),
        (C["mint"], py + 128, 9, "2 6", 2.4),
    ]
    rnd = random.Random(4)
    for col, base_y, amp, dash, phase in traces:
        pts = []
        n = 26
        for i in range(n + 1):
            x = px + 24 + (pw - 48) * i / n
            yy = base_y + math.sin(i * 0.9 + phase) * amp * 0.5 + rnd.uniform(-4, 4)
            pts.append((x, yy))
        d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts[1:])
        s += (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.8" '
              f'stroke-dasharray="{dash}" opacity="0.85">'
              f'<animate attributeName="stroke-dashoffset" from="0" to="-140" '
              f'dur="{4 + phase:.1f}s" repeatCount="indefinite"/></path>')

    # scrolling hex / status readout along the bottom
    hexstr = " ".join(f"{rnd.randint(0,255):02X}" for _ in range(40))
    s += (f'<clipPath id="hexclip"><rect x="{px+18}" y="{py+ph-40}" width="{pw-36}" height="18"/></clipPath>'
          f'<g clip-path="url(#hexclip)" opacity="0.4">'
          f'<text x="{px+18}" y="{py+ph-26}" font-family="{MONO}" font-size="11.5" fill="{C["purple_dim"]}">{esc(hexstr)}'
          f'<animate attributeName="x" from="{px+18}" to="{px+18-620}" dur="26s" repeatCount="indefinite"/></text>'
          f'</g>')

    labels = [("SYSTEMS", 0.10), ("SECURITY", 0.34), ("AUTOMATION", 0.60), ("BUILD/TEST/REPEAT", 0.83)]
    for i, (label, frac) in enumerate(labels):
        lx = px + 20 + (pw - 40) * frac
        dly = i * 0.4
        s += (f'<g>{fade_in(dly, cycle, dur=0.4)}'
              f'{txt(lx, py + ph - 12, label, fs=12, fill=C["text"], ls=1.2, weight=600)}</g>')

    s += tail(w, h)
    return s


# ── asset 3: section divider — reusable scan-bar ──────────────────────────────

def build_divider():
    w, h = 1200, 34
    cycle = 6.0
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
         f'role="img" aria-labelledby="t"><title id="t">section divider</title>'
         f'<defs>'
         f'<linearGradient id="dl" x1="0" y1="0" x2="1" y2="0">'
         f'<stop offset="0" stop-color="{C["violet"]}" stop-opacity="0"/>'
         f'<stop offset="0.5" stop-color="{C["violet"]}" stop-opacity="0.55"/>'
         f'<stop offset="1" stop-color="{C["violet"]}" stop-opacity="0"/></linearGradient>'
         f'<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">'
         f'<stop offset="0" stop-color="{C["purple"]}" stop-opacity="0"/>'
         f'<stop offset="0.5" stop-color="{C["purple"]}" stop-opacity="0.9"/>'
         f'<stop offset="1" stop-color="{C["purple"]}" stop-opacity="0"/></linearGradient>'
         f'</defs>')
    cy = h / 2
    s += f'<line x1="0" y1="{cy}" x2="{w}" y2="{cy}" stroke="url(#dl)" stroke-width="1.2"/>'
    # ticks
    for i in range(0, w, 26):
        th = 5 if i % 130 else 9
        s += f'<line x1="{i}" y1="{cy-th/2}" x2="{i}" y2="{cy+th/2}" stroke="{C["line"]}" stroke-width="1"/>'
    # traveling sweep bar
    s += (f'<rect x="{-160}" y="0" width="160" height="{h}" fill="url(#sweep)" opacity="0.5">'
          f'<animate attributeName="x" values="{-160};{w};{-160}" dur="{cycle:g}s" repeatCount="indefinite"/></rect>')
    # center diamond node
    s += (f'<g transform="translate({w/2},{cy})">'
          f'<rect x="-5" y="-5" width="10" height="10" fill="{C["bg0"]}" stroke="{C["purple"]}" '
          f'stroke-width="1.4" transform="rotate(45)">'
          f'<animateTransform attributeName="transform" type="rotate" from="45" to="405" '
          f'dur="14s" repeatCount="indefinite" additive="sum"/></rect></g>')
    # end nodes
    for x in (18, w - 18):
        s += (f'<circle cx="{x}" cy="{cy}" r="2.6" fill="{C["purple"]}">'
              f'<animate attributeName="opacity" values="0.3;1;0.3" dur="3s" repeatCount="indefinite"/></circle>')
    s += "</svg>"
    return s


# ── asset 4: footer signature — heartbeat / signoff ───────────────────────────

def build_footer():
    w, h = 1200, 150
    cycle = 10.0
    s = head(w, h, "fogg signature — under construction")
    s += constellation(w, h, n=22, seed=19, opacity=0.4, link=120)
    s += hud_rings(120, 75, 100, count=2)
    s += hud_rings(w - 120, 75, 100, count=2)

    cx = w / 2
    s += (f'<g opacity="0.95" filter="url(#glow)">'
          f'{txt(cx, 56, "FOGG", fs=34, fill=C["purple"], anchor="middle", family=SERIF, ls=10, weight=700)}'
          f'</g>')
    s += (f'<g>{fade_in(0.3, cycle, dur=0.5)}'
          f'{txt(cx, 80, "always under construction", fs=13, fill=C["purple_dim"], anchor="middle", ls=2)}'
          f'</g>')

    # heartbeat monitor line across the middle-bottom
    hy = 112
    seg = f"M40 {hy} H{w*0.36:.0f} L{w*0.40:.0f} {hy-26} L{w*0.44:.0f} {hy+30} L{w*0.47:.0f} {hy-14} L{w*0.50:.0f} {hy} H{w-40:.0f}"
    s += (f'<path d="{seg}" fill="none" stroke="{C["mint"]}" stroke-width="1.8" '
          f'stroke-dasharray="6 10" opacity="0.8">'
          f'<animate attributeName="stroke-dashoffset" from="0" to="-64" dur="2.4s" repeatCount="indefinite"/></path>')
    # traveling dot along the heartbeat path
    s += (f'<circle r="3.4" fill="{C["mint"]}"><animateMotion dur="3.2s" repeatCount="indefinite" '
          f'path="{seg}"/></circle>')

    cycle_txt = "learning → building → breaking → understanding → repeat"
    frag, width = typed_line("footcycle", cx - len(cycle_txt) * cw(13) / 2, 138, cycle_txt,
                              fs=13, fill=C["muted"], start=0.6, dur=2.2, cycle=cycle)
    s += frag

    s += tail(w, h)
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    write("typing-signal.svg", build_hero())
    write("system-pulse.svg", build_pulse())
    write("section-divider.svg", build_divider())
    write("signal-footer.svg", build_footer())


if __name__ == "__main__":
    main()
