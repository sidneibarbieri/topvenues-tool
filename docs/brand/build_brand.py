"""Build the TopVenues brand masters as SVG, with text converted to outlines.

The wordmark is set in Inter and every glyph becomes a path, so the SVG renders
identically on machines that do not have the font installed. The SVG files in
this directory are the masters; the PNG files are rasterized from them.

Usage: python docs/brand/build_brand.py --font path/to/Inter-SemiBold.ttf
(Inter 4.1, SIL Open Font License: https://github.com/rsms/inter/releases)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).parent
FONT: Path  # set from --font in __main__

INK = "#10233F"
BLUE = "#2867B2"
SLATE = "#667085"
INK_DARK = "#E8EDF4"
BLUE_DARK = "#6FA3E0"


def glyph_paths(text: str, size: float, x0: float, baseline: float, tracking: float = -0.012):
    font = TTFont(FONT)
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    upm = font["head"].unitsPerEm
    hmtx = font["hmtx"]
    scale = size / upm
    x = x0
    parts = []
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        tpen = TransformPen(pen, (scale, 0, 0, -scale, x, baseline))
        gs[name].draw(tpen)
        parts.append(pen.getCommands())
        x += hmtx[name][0] * scale + tracking * size
    return parts, x


def mark(colors, size=64, sources=3):
    """Three sources converging on one point: many venues, one frozen corpus.

    Two strong arms carry the V silhouette; a lighter centre line makes the
    convergence read as more than a letter. The dot is the snapshot.
    """
    outer, inner = colors
    top, vx, vy = 11, 32, 50
    arms = (
        f'<line x1="10" y1="{top}" x2="{vx}" y2="{vy}" stroke="{outer}" stroke-width="6.4" stroke-linecap="round"/>',
        f'<line x1="54" y1="{top}" x2="{vx}" y2="{vy}" stroke="{outer}" stroke-width="6.4" stroke-linecap="round"/>',
        f'<line x1="{vx}" y1="{top + 4}" x2="{vx}" y2="{vy}" stroke="{inner}" stroke-width="3.4" stroke-linecap="round"/>',
    )
    dot = f'<circle cx="{vx}" cy="{vy}" r="5.4" fill="{inner}"/>'
    return "\n  ".join((*arms, dot))


def svg(w, h, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{title}">\n'
        f"  <title>{title}</title>\n  {body}\n</svg>\n"
    )


def lockup(ink, blue, mark_colors):
    size = 44
    baseline = 47
    top_parts, x_after_top = glyph_paths("Top", size, 78, baseline)
    ven_parts, x_end = glyph_paths("Venues", size, x_after_top, baseline)
    body = (
        f'<g transform="translate(0,0)">\n  {mark(mark_colors)}\n  </g>\n'
        + "".join(f'  <path d="{d}" fill="{ink}"/>\n' for d in top_parts)
        + "".join(f'  <path d="{d}" fill="{blue}"/>\n' for d in ven_parts)
    )
    return svg(x_end + 6, 64, body, "TopVenues")


def main():
    (OUT / "topvenues-mark.svg").write_text(svg(64, 64, mark((INK, BLUE)), "TopVenues mark"))
    (OUT / "topvenues-mark-reversed.svg").write_text(
        svg(64, 64, mark((INK_DARK, BLUE_DARK)), "TopVenues mark")
    )
    (OUT / "topvenues-mark-mono.svg").write_text(
        svg(64, 64, mark(("#000000", "#000000")), "TopVenues mark")
    )
    (OUT / "topvenues-wordmark.svg").write_text(lockup(INK, BLUE, (INK, BLUE)))
    (OUT / "topvenues-wordmark-reversed.svg").write_text(
        lockup(INK_DARK, BLUE_DARK, (INK_DARK, BLUE_DARK))
    )
    (OUT / "topvenues-wordmark-mono.svg").write_text(
        lockup("#000000", "#000000", ("#000000", "#000000"))
    )
    for f in sorted(OUT.glob("*.svg")):
        print(f"  {f.name:34} {f.stat().st_size:6} bytes")


def social_preview():
    """1280x640 card for link previews: identity plus the one-line claim."""
    size = 96
    baseline = 300
    top_parts, x_top = glyph_paths("Top", size, 250, baseline)
    ven_parts, x_end = glyph_paths("Venues", size, x_top, baseline)
    tag1, _ = glyph_paths("A versioned, reproducible corpus", 34, 250, 392, tracking=-0.005)
    tag2, _ = glyph_paths("for cybersecurity literature research", 34, 250, 440, tracking=-0.005)
    body = (
        '<rect width="1280" height="640" fill="#FFFFFF"/>\n'
        '  <rect x="0" y="600" width="1280" height="40" fill="#10233F"/>\n'
        f'  <g transform="translate(96,205) scale(2.35)">{mark((INK, BLUE))}</g>\n'
        + "".join(f'  <path d="{d}" fill="{INK}"/>\n' for d in top_parts)
        + "".join(f'  <path d="{d}" fill="{BLUE}"/>\n' for d in ven_parts)
        + "".join(f'  <path d="{d}" fill="{SLATE}"/>\n' for d in tag1 + tag2)
    )
    (OUT / "topvenues-social.svg").write_text(svg(1280, 640, body, "TopVenues"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", type=Path, required=True, help="Inter-SemiBold.ttf")
    FONT = parser.parse_args().font
    main()
    social_preview()
