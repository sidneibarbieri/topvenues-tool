# TopVenues brand

TopVenues is scientific infrastructure. The identity is typographic, uses one
accent colour, and carries no decoration that does not also carry meaning.

## The mark

Two strong arms and one lighter centre line converge on a single point. Many
venues, one corpus; the point is the frozen snapshot every result is bound to.
It is a mechanism, not an illustration, and it stays the same everywhere.

| File | Use |
| --- | --- |
| `topvenues-wordmark.svg` | Primary lockup, light backgrounds |
| `topvenues-wordmark-reversed.svg` | Primary lockup, dark backgrounds |
| `topvenues-wordmark-mono.svg` | One-colour print, embossing, stamps |
| `topvenues-mark.svg` | Favicon, avatar, compact navigation |
| `topvenues-mark-reversed.svg` | Mark on dark backgrounds |
| `topvenues-mark-mono.svg` | Mark in one colour |
| `topvenues-social.png` | 1280×640 link preview |
| `mark-{16,32,48,180,512}.png` | Raster sizes of the mark |

SVG is the master. PNG is a distribution format. The wordmark glyphs are
outlines, so it renders the same without Inter installed. `build_brand.py`
regenerates every SVG master byte for byte from Inter 4.1 SemiBold:

```bash
python docs/brand/build_brand.py --font path/to/Inter-SemiBold.ttf
```

## Colour

Five tokens. Nothing else belongs to the brand.

| Token | Hex | Role |
| --- | --- | --- |
| Ink Navy | `#10233F` | Wordmark, headings, dark surfaces |
| Corpus Blue | `#2867B2` | The single accent |
| Slate | `#667085` | Secondary text |
| Mist | `#E9EEF4` | Quiet surfaces and rules |
| Paper | `#FFFFFF` | Base |

Dark surfaces are derived, not inverted:

| Token | Hex | Role |
| --- | --- | --- |
| Night | `#0B1627` | Dark background |
| Night Surface | `#122238` | Dark cards and panels |
| Text on Night | `#E8EDF4` | Primary text on dark |
| Blue on Night | `#6FA3E0` | Accent on dark |
| Slate on Night | `#9AA7B8` | Secondary text on dark |

### Contrast, measured

Every pair passes WCAG 2.1 AA for normal text (4.5:1).

| Foreground / background | Ratio |
| --- | --- |
| Ink Navy / Paper | 15.74:1 |
| Corpus Blue / Paper | 5.72:1 |
| Slate / Paper | 4.97:1 |
| Ink Navy / Mist | 13.49:1 |
| Text on Night / Night | 15.41:1 |
| Blue on Night / Night | 6.90:1 |
| Slate on Night / Night | 7.42:1 |

## Brand colour is not data colour

Corpus Blue identifies TopVenues. It never means *better*, *significant*,
*current* or *accepted* in a chart. Figures use their own accessible palette,
and no chart relies on colour alone: direct labels, markers or line style carry
the distinction as well.

### Data palette

Charts in the interface draw from these, declared once in `web/charts.py`:

| Role | Hex | Contrast on Paper |
| --- | --- | --- |
| Single series | `#44607F` | 6.51:1 |
| Second series | `#D55E00` (Okabe–Ito vermillion) | 3.87:1 |
| Third series | `#009E73` (Okabe–Ito bluish green) | 3.42:1 |
| Coverage | `#4F7D4A` | 4.81:1 |

Series colours fill marks and never set text; value labels use Slate. Series
also differ by line dash, and legends draw the dashed line itself.

## Type

Inter, set tight. SemiBold for the wordmark and headings, Regular for text,
tabular figures wherever numbers are compared. Monospace only for commands,
identifiers and hashes. The interface and the project page self-host Inter
(SIL Open Font License) as subsets: `web/static/InterVariable.woff2` covers
every character in the corpus titles and author names except two symbols Inter
does not draw; `site/assets/fonts/` carries a Latin subset for the page.

## Use

- Clear space around the lockup: at least the height of the dot.
- Minimum size: mark 16 px; wordmark 96 px wide.
- Do not recolour, rotate, outline, add shadow or glow, or place the mark on a
  busy image.
- Do not rebuild the wordmark in another typeface.
- One mark per surface. A slide or page does not need the logo repeated.
