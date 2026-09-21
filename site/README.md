# Project page

Source of <https://sidneibarbieri.github.io/topVenues/>, the front door to both
repositories, both papers and the dataset.

```bash
python site/build_site.py --out /tmp/topvenues-site
```

The build uses only the standard library. Every figure about the current
release is read from `data/profiles/security-20-v4/manifest.json`, the venue
areas from `src/areas.py`, and the abstract-audit result from
`evaluation/security-20-v3/manual_abstract_audit_summary.json`. The two papers
are frozen publications, so their values are constants in `build_site.py`; a
test checks them against `docs/PAPERS.md`. Brand files come from `docs/brand/`
and screenshots from `docs/assets/screenshots/`.

The page is bilingual (English and Brazilian Portuguese; `?lang=pt` selects
Portuguese), follows the system light or dark setting, sets no cookies, and
loads nothing from third parties until the demo video is played. Inter is
self-hosted as a Latin subset under the SIL Open Font License
(`assets/fonts/Inter-LICENSE.txt`).

## Publishing

The page is served from the `gh-pages` branch of
[`sidneibarbieri/topVenues`](https://github.com/sidneibarbieri/topVenues), so
that repository's `main` stays the frozen artifact of the main-track paper.
Build into a checkout of that branch, commit, and push:

```bash
git clone --branch gh-pages --depth 1 https://github.com/sidneibarbieri/topVenues site-pages
python site/build_site.py --out site-pages
git -C site-pages add -A && git -C site-pages commit -m "Rebuild from topvenues-tool vX.Y.Z"
git -C site-pages push
```
