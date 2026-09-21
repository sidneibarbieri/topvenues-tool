#!/usr/bin/env python3
"""Build the TopVenues landing page from release manifests.

Every number about the current release is read from the tool checkout:
the profile manifest, ``pyproject.toml`` and ``src/areas.py``. The two papers
are frozen publications, so their values are constants here and must match
``docs/PAPERS.md``; they never change with a release.

Usage: python site/build_site.py --out OUTPUT_DIR [--tool REPOSITORY_ROOT]

Brand files come from docs/brand and screenshots from docs/assets/screenshots,
so the page never carries its own copy of either. See site/README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib.util
import json
import math
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

PROFILE = "security-20-v4"
SITE_DIR = Path(__file__).resolve().parent
SITE_URL = "https://sidneibarbieri.github.io/topVenues/"
GH = "https://github.com/sidneibarbieri"
HF = "https://huggingface.co/datasets/sidneibarbieri"
DEMO = f"{HF}/topvenues/resolve/main/assets/demo/topvenues-demo-v1.5.9"

PAPER_A = {
    "id": "a",
    "title": "TopVenues: A Reproducible Corpus and Tooling Substrate for Cybersecurity Literature Reviews",
    "booktitle": "Anais do XXVI Simpósio Brasileiro de Cibersegurança (SBSeg 2026)",
    "pages": "1150–1165",
    "sol": "https://sol.sbc.org.br/index.php/sbseg/article/view/44350",
    "doi": "10.5753/sbseg.2026.29056",
    "repo": "topVenues",
    "release": "sbseg2026-camera-ready",
    "records": 9925,
    "venues": 11,
    "window": None,
    "snapshot_en": "May 2026",
    "snapshot_pt": "maio de 2026",
    "sha": "0f4dbaa97d0cf39abd2340adb3280643df090b5de9cd1a29bff39a0b53ef64cd",
    "tests": 252,
    "cmd": "git clone https://github.com/sidneibarbieri/topVenues\ncd topVenues\nbash reproduce.sh",
}
PAPER_B = {
    "id": "b",
    "title": "TopVenues: An Executable Corpus and Research Tool for Cybersecurity Literature Reviews",
    "booktitle": "Anais Estendidos do XXVI Simpósio Brasileiro de Cibersegurança (SBSeg 2026)",
    "pages": "234–241",
    "sol": "https://sol.sbc.org.br/index.php/sbseg_estendido/article/view/44470",
    "doi": "10.5753/sbseg_estendido.2026.33733",
    "repo": "topvenues-tool",
    "release": "sbseg2026-sf-submission-r1",
    "profile": "security-20",
    "records": 20305,
    "venues": 20,
    "window": "2017–2026",
    "sha": "5a35bd6e3ec6845a0fde4cc3d6aa05b1db04e511cb39e783eeaee2cea7493b08",
    "cmd": "git clone https://github.com/sidneibarbieri/topvenues-tool\ncd topvenues-tool\nbash reproduce.sh --profile security-20",
}
AUTHORS = "Sidnei Barbieri, Ágney Lopes Roth Ferraz, Lourenço Alves Pereira Júnior"
BIB_AUTHORS = (
    "Sidnei Barbieri and {\\'A}gney Lopes Roth Ferraz and "
    "Louren{\\c{c}}o Alves {Pereira J{\\'u}nior}"
)


# ---------------------------------------------------------------- formatting


def num(n: int | float, lang: str, digits: int = 0) -> str:
    s = f"{n:,.{digits}f}"
    if lang == "pt":
        s = s.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return s


def pct(part: int, whole: int, lang: str, digits: int = 1) -> str:
    return num(100 * part / whole, lang, digits) + "%"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def both(en: str, pt: str, tag: str = "span", attrs: str = "") -> str:
    """One element per language; CSS shows the active one."""
    a = f" {attrs}" if attrs else ""
    return f'<{tag} data-l="en"{a}>{en}</{tag}><{tag} data-l="pt"{a}>{pt}</{tag}>'


def code_block(text: str, label_en: str = "", label_pt: str = "") -> str:
    label = both(label_en, label_pt) if label_en else ""
    return (
        f'<div class="code"><div class="code-bar"><span class="code-label">{label}</span>'
        f'<button class="copy" type="button" data-copy>{both("Copy", "Copiar")}</button></div>'
        f"<pre><code>{esc(text)}</code></pre></div>"
    )


def png_size(path: Path) -> tuple[int, int]:
    """Width and height from the PNG header, so the page never guesses them."""
    with path.open("rb") as handle:
        header = handle.read(24)
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def size_screenshots(page: str, screens: Path) -> str:
    """Set every screenshot's width and height to the file's real dimensions."""

    def fix(match: re.Match) -> str:
        width, height = png_size(screens / match.group(1))
        return f'src="assets/screens/{match.group(1)}" width="{width}" height="{height}"'

    return re.sub(r'src="assets/screens/([\w.-]+\.png)" width="\d+" height="\d+"', fix, page)


def inline_svg(path: Path) -> str:
    """A brand master as inline SVG whose colours follow the page theme."""
    svg = path.read_text()
    svg = re.sub(r"<title>.*?</title>\s*", "", svg)
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg, count=2)
    svg = re.sub(r'\srole="img" aria-label="[^"]*"', ' aria-hidden="true" focusable="false"', svg)
    for attr in ("fill", "stroke"):
        svg = svg.replace(f'{attr}="#10233F"', f'class="bi{"s" if attr == "stroke" else ""}"')
        svg = svg.replace(f'{attr}="#2867B2"', f'class="bb{"s" if attr == "stroke" else ""}"')
    return svg.strip()


# ---------------------------------------------------------------- data


def load_release(tool: Path) -> dict:
    manifest = json.loads((tool / f"data/profiles/{PROFILE}/manifest.json").read_text())
    snap = manifest["snapshot"]
    version = tomllib.loads((tool / "pyproject.toml").read_text())["project"]["version"]
    # The tool's own venue→area mapping, loaded alone so the build needs only
    # the standard library (src/__init__.py imports the network stack).
    spec = importlib.util.spec_from_file_location("tv_areas", tool / "src/areas.py")
    areas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(areas)
    area_for = areas.area_for

    venues = []
    for e in snap["event_counts"]:
        venues.append({**e, "area": area_for(e["event"])})
    venues.sort(key=lambda v: (-v["papers"], v["event"]))
    unknown = [v["event"] for v in venues if v["area"] == "unknown"]
    if unknown:
        raise SystemExit(f"unmapped venues in {PROFILE}: {unknown}")
    core = [v for v in venues if v["area"] == "security"]
    audit = json.loads(
        (tool / "evaluation/security-20-v3/manual_abstract_audit_summary.json").read_text()
    )
    commit = (
        subprocess.run(
            ["git", "-C", str(tool), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        or "unknown"
    )
    return {
        "manifest": manifest,
        "snap": snap,
        "version": version,
        "venues": venues,
        "core_papers": sum(v["papers"] for v in core),
        "core_abstracts": sum(v["abstracts"] for v in core),
        "core_n": len(core),
        "survey": [v for v in venues if v["area"] != "security"],
        "commit": commit,
        "audit": audit,
    }


# ---------------------------------------------------------------- figure


def convergence_svg(release: dict) -> str:
    """Figure 1: every declared venue converges on one snapshot.

    Line weight follows sqrt(records) so the smallest venues stay visible;
    survey venues are dashed. Colour carries no data.
    """
    venues = release["venues"]
    n = len(venues)
    top, step = 28, 24
    height = top * 2 + step * (n - 1)
    px, py = 560, top + step * (n - 1) / 2
    mx = max(v["papers"] for v in venues)
    out = [
        f'<svg class="conv" viewBox="0 0 880 {height:.0f}" role="img" '
        f'aria-labelledby="fig1-title" xmlns="http://www.w3.org/2000/svg">',
        '<title id="fig1-title">Twenty declared venues converge on one snapshot</title>',
    ]
    for i, v in enumerate(venues):
        y = top + i * step
        w = 0.8 + 4.4 * math.sqrt(v["papers"] / mx)
        # pathLength drives the draw-in animation; it would rescale a dash
        # pattern, so dashed (survey) lines fade in instead.
        dash = ' stroke-dasharray="5 4"' if v["area"] != "security" else ' pathLength="1"'
        name = v["event"].replace(
            "IEEE Communications Surveys & Tutorials", "IEEE Comm. Surveys & Tutorials"
        )
        name = name.replace(
            "Foundations and Trends in Privacy and Security", "FnT Privacy and Security"
        )
        out.append(
            f'<g class="v" style="--i:{i}">'
            f'<text class="vn" x="232" y="{y + 4.5}" text-anchor="end">{esc(name)}</text>'
            f'<text class="vc" x="292" y="{y + 4.5}" text-anchor="end">'
            f'<tspan data-l="en">{num(v["papers"], "en")}</tspan><tspan data-l="pt">{num(v["papers"], "pt")}</tspan></text>'
            f'<path class="ln" d="M304 {y} C 430 {y}, 470 {py:.1f}, {px} {py:.1f}" '
            f'stroke-width="{w:.2f}"{dash}/></g>'
        )
    s = release["snap"]
    sha = s["gzip_sha256"]
    out += [
        f'<circle class="halo" cx="{px}" cy="{py:.1f}" r="17"/>',
        f'<circle class="pt" cx="{px}" cy="{py:.1f}" r="8.5"/>',
        f'<g class="lbl" transform="translate({px + 34} {py - 38:.1f})">',
        f'<text class="l1" y="0">{PROFILE}</text>',
        f'<text class="l2" y="26"><tspan data-l="en">{num(s["papers"], "en")} records</tspan>'
        f'<tspan data-l="pt">{num(s["papers"], "pt")} registros</tspan></text>',
        f'<text class="l3" y="48"><tspan data-l="en">{s["venues"]} venues · {s["observed_year_min"]}–{s["observed_year_max"]}</tspan>'
        f'<tspan data-l="pt">{s["venues"]} veículos · {s["observed_year_min"]}–{s["observed_year_max"]}</tspan></text>',
        f'<text class="l4" y="74">sha256 {sha[:8]}…{sha[-6:]}</text>',
        "</g></svg>",
    ]
    return "\n".join(out)


def venue_table(release: dict) -> str:
    rows = []
    for v in release["venues"]:
        area_en = "security" if v["area"] == "security" else "survey"
        area_pt = "segurança" if v["area"] == "security" else "surveys"
        rows.append(
            "<tr>"
            f'<th scope="row">{esc(v["event"])}</th>'
            f"<td>{both(area_en, area_pt)}</td>"
            f'<td class="n">{both(num(v["papers"], "en"), num(v["papers"], "pt"))}</td>'
            f'<td class="n">{both(num(v["abstracts"], "en"), num(v["abstracts"], "pt"))}</td>'
            f'<td class="n">{both(pct(v["abstracts"], v["papers"], "en"), pct(v["abstracts"], v["papers"], "pt"))}</td>'
            f'<td class="n">{v["year_min"]}–{v["year_max"]}</td>'
            "</tr>"
        )
    head = (
        "<thead><tr>"
        f'<th scope="col">{both("Venue", "Veículo")}</th>'
        f'<th scope="col">{both("Area", "Área")}</th>'
        f'<th scope="col" class="n">{both("Records", "Registros")}</th>'
        f'<th scope="col" class="n">{both("Abstracts", "Resumos")}</th>'
        f'<th scope="col" class="n">{both("Coverage", "Cobertura")}</th>'
        f'<th scope="col" class="n">{both("Years", "Anos")}</th>'
        "</tr></thead>"
    )
    return f'<div class="table-wrap"><table class="venues">{head}<tbody>{"".join(rows)}</tbody></table></div>'


def venue_list(release: dict) -> str:
    """Narrow-screen text alternative to Figure 1."""
    items = "".join(
        f"<li><span>{esc(v['event'])}"
        + (
            f' <small class="tag">{both("survey", "surveys")}</small>'
            if v["area"] != "security"
            else ""
        )
        + '</span><span class="n">'
        f"{both(num(v['papers'], 'en'), num(v['papers'], 'pt'))}</span></li>"
        for v in release["venues"]
    )
    return f'<ol class="vlist">{items}</ol>'


# ---------------------------------------------------------------- sections


def paper_card(paper: dict, kind_en: str, kind_pt: str) -> str:
    rows = [
        (
            both("Repository", "Repositório"),
            f'<a href="{GH}/{paper["repo"]}"><code>sidneibarbieri/{paper["repo"]}</code></a>',
        ),
        (
            both("Release", "Versão"),
            f'<a href="{GH}/{paper["repo"]}/releases/tag/{paper["release"]}"><code>{paper["release"]}</code></a>',
        ),
    ]
    if "profile" in paper:
        rows.append((both("Profile", "Perfil"), f"<code>{paper['profile']}</code>"))
    if paper.get("snapshot_en"):
        snap = both(
            f"{paper['snapshot_en']} · {num(paper['records'], 'en')} records · {paper['venues']} venues",
            f"{paper['snapshot_pt']} · {num(paper['records'], 'pt')} registros · {paper['venues']} veículos",
        )
    else:
        snap = both(
            f"{num(paper['records'], 'en')} records · {paper['venues']} venues · {paper['window']}",
            f"{num(paper['records'], 'pt')} registros · {paper['venues']} veículos · {paper['window']}",
        )
    rows.append((both("Snapshot", "Snapshot"), snap))
    rows.append(("SHA-256", f'<code class="hash">{paper["sha"]}</code>'))
    if "tests" in paper:
        rows.append(
            (both("Tests", "Testes"), both(f"{paper['tests']} tests", f"{paper['tests']} testes"))
        )
    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return f"""
<article class="paper" id="paper-{paper["id"]}">
  <p class="kicker">{both(kind_en, kind_pt)}</p>
  <h3>{esc(paper["title"])}</h3>
  <p class="venue">{esc(paper["booktitle"])}, {both("pp.", "p.")} {paper["pages"]}</p>
  <p class="links"><a class="arrow" href="{paper["sol"]}">{both("Read on SOL", "Ler no SOL")}</a>
     <span class="doi">DOI <code>{paper["doi"]}</code></span></p>
  <dl class="facts">{dl}</dl>
  {code_block(paper["cmd"], "Reproduce", "Reproduzir")}
</article>"""


def bibtex(key: str, paper: dict) -> str:
    booktitle = (
        paper["booktitle"]
        .replace("Simpósio", "Simp{\\'o}sio")
        .replace("Cibersegurança", "Ciberseguran{\\c{c}}a")
    )
    return (
        f"@inproceedings{{{key},\n"
        f"  author    = {{{BIB_AUTHORS}}},\n"
        f"  title     = {{{{TopVenues}}{paper['title'][len('TopVenues') :]}}},\n"
        f"  booktitle = {{{booktitle}}},\n"
        f"  pages     = {{{paper['pages'].replace('–', '--')}}},\n"
        f"  year      = {{2026}},\n"
        f"  publisher = {{Sociedade Brasileira de Computa{{\\c{{c}}}}{{\\~a}}o}},\n"
        f"  address   = {{Porto Alegre, RS, Brasil}},\n"
        f"  doi       = {{{paper['doi']}}},\n"
        f"  url       = {{{paper['sol']}}}\n"
        "}"
    )


def json_ld(release: dict) -> str:
    s = release["snap"]
    graph = [
        {
            "@type": "Dataset",
            "name": f"TopVenues cybersecurity corpus ({PROFILE})",
            "description": (
                f"{s['papers']:,} bibliographic records from {s['venues']} declared security "
                f"and survey venues, {s['observed_year_min']}–{s['observed_year_max']}, with "
                f"abstracts where available and a BibTeX entry for every record."
            ),
            "url": f"{HF}/topvenues",
            "sameAs": f"{GH}/topvenues-tool",
            "identifier": f"sha256:{s['gzip_sha256']}",
            "temporalCoverage": f"{s['observed_year_min']}/{s['observed_year_max']}",
            "creator": [{"@type": "Person", "name": a.strip()} for a in AUTHORS.split(",")],
            "isAccessibleForFree": True,
        },
        {
            "@type": "SoftwareSourceCode",
            "name": "TopVenues",
            "codeRepository": f"{GH}/topvenues-tool",
            "programmingLanguage": "Python",
            "license": "https://opensource.org/licenses/MIT",
            "softwareVersion": release["version"],
        },
    ]
    for paper in (PAPER_A, PAPER_B):
        graph.append(
            {
                "@type": "ScholarlyArticle",
                "headline": paper["title"],
                "isPartOf": paper["booktitle"],
                "url": paper["sol"],
                "identifier": f"doi:{paper['doi']}",
                "datePublished": "2026",
            }
        )
    return json.dumps(
        {"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1
    )


def build(tool: Path, out: Path) -> None:
    release = load_release(tool)
    s = release["snap"]
    ver = release["version"]
    abs_en, abs_pt = pct(s["abstracts"], s["papers"], "en"), pct(s["abstracts"], s["papers"], "pt")
    survey_names = ", ".join(v["event"] for v in release["survey"])
    esorics = next(v for v in release["venues"] if v["event"] == "ESORICS")
    built = dt.date.today().isoformat()

    replacements = {
        "{{CSS}}": (SITE_DIR / "site.css").read_text(),
        "{{JS}}": (SITE_DIR / "site.js").read_text(),
        "{{BOOT}}": (SITE_DIR / "boot.js").read_text().strip(),
        "{{JSONLD}}": json_ld(release),
        "{{WORDMARK}}": inline_svg(tool / "docs/brand/topvenues-wordmark.svg"),
        "{{MARK_INNER}}": re.sub(
            r"^<svg[^>]*>|</svg>$", "", inline_svg(tool / "docs/brand/topvenues-mark.svg")
        ),
        "{{SKIP}}": both("Skip to content", "Pular para o conteúdo"),
        "{{AUD_N}}": str(release["audit"]["labelled"]),
        "{{AUD_EN}}": pct(release["audit"]["usable"], release["audit"]["labelled"], "en"),
        "{{AUD_PT}}": pct(release["audit"]["usable"], release["audit"]["labelled"], "pt"),
        "{{AUD_CI_EN}}": "–".join(
            num(100 * x, "en", 1) + "%" for x in release["audit"]["wilson_95_ci"]
        ),
        "{{AUD_CI_PT}}": "–".join(
            num(100 * x, "pt", 1) + "%" for x in release["audit"]["wilson_95_ci"]
        ),
        "{{FIGURE}}": convergence_svg(release),
        "{{VLIST}}": venue_list(release),
        "{{VTABLE}}": venue_table(release),
        "{{PAPER_A}}": paper_card(
            PAPER_A, "Paper A · Main track, SBSeg 2026", "Artigo A · Trilha principal, SBSeg 2026"
        ),
        "{{PAPER_B}}": paper_card(
            PAPER_B,
            "Paper B · Tools track, SBSeg 2026",
            "Artigo B · Salão de Ferramentas, SBSeg 2026",
        ),
        "{{BIB_A}}": code_block(bibtex("barbieri2026topvenues", PAPER_A), "Paper A", "Artigo A"),
        "{{BIB_B}}": code_block(
            bibtex("barbieri2026topvenuestool", PAPER_B), "Paper B", "Artigo B"
        ),
        "{{RECORDS_EN}}": num(s["papers"], "en"),
        "{{RECORDS_PT}}": num(s["papers"], "pt"),
        "{{ABS_EN}}": num(s["abstracts"], "en"),
        "{{ABS_PT}}": num(s["abstracts"], "pt"),
        "{{ABSPCT_EN}}": abs_en,
        "{{ABSPCT_PT}}": abs_pt,
        "{{BIBPCT_EN}}": pct(s["bibtex"], s["papers"], "en", 0),
        "{{BIBPCT_PT}}": pct(s["bibtex"], s["papers"], "pt", 0),
        "{{VENUES}}": str(s["venues"]),
        "{{CORE_N}}": str(release["core_n"]),
        "{{SURVEY_N}}": str(len(release["survey"])),
        "{{CORE_EN}}": num(release["core_papers"], "en"),
        "{{CORE_PT}}": num(release["core_papers"], "pt"),
        "{{SURVEYS}}": esc(survey_names),
        "{{ESO_P_EN}}": num(esorics["papers"], "en"),
        "{{ESO_P_PT}}": num(esorics["papers"], "pt"),
        "{{ESO_A}}": str(esorics["abstracts"]),
        "{{Y0}}": str(s["observed_year_min"]),
        "{{Y1}}": str(s["observed_year_max"]),
        "{{SHA}}": s["gzip_sha256"],
        "{{PROFILE}}": PROFILE,
        "{{VERSION}}": ver,
        "{{BUILT_ON}}": release["manifest"]["built_on"],
        "{{QUICK_UNIX}}": code_block(
            f"git clone --depth 1 --branch v{ver} https://github.com/sidneibarbieri/topvenues-tool.git\n"
            f"cd topvenues-tool\nbash reproduce.sh --profile {PROFILE}"
        ),
        "{{QUICK_WIN}}": code_block(
            f"git clone --depth 1 --branch v{ver} https://github.com/sidneibarbieri/topvenues-tool.git\n"
            f"cd topvenues-tool\npowershell -ExecutionPolicy Bypass -File .\\reproduce.ps1 -Profile {PROFILE}"
        ),
        "{{UI_UNIX}}": code_block("source .venv/bin/activate\npython -m streamlit run web/app.py"),
        "{{UI_WIN}}": code_block(
            ".\\.venv\\Scripts\\Activate.ps1\npython -m streamlit run web/app.py"
        ),
        "{{CLI}}": code_block(
            f'python -m src.cli --profile {PROFILE} search --rank "LLM security" \\\n'
            f'  --tier-scope "Security top-4" --limit 20\n'
            f'python -m src.cli --profile {PROFILE} export --format bibtex --tech "fuzzing" \\\n'
            f'  --tier-scope "Security top-4" -o fuzzing-tier1.bib'
        ),
        "{{HFCODE}}": code_block(
            "from datasets import load_dataset\n\n"
            'corpus = load_dataset("sidneibarbieri/topvenues", split="train")\n'
            'security = corpus.filter(lambda paper: paper["area"] == "security")'
        ),
        "{{DEMO}}": DEMO,
        "{{GH}}": GH,
        "{{HF}}": HF,
        "{{SITE}}": SITE_URL,
        "{{STAMP}}": f"{PROFILE} · v{ver} · {release['commit']} · {built}",
    }
    page = (SITE_DIR / "template.html").read_text()
    for k, v in replacements.items():
        page = page.replace(k, v)
    page = size_screenshots(page, tool / "docs/assets/screenshots")
    left = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", page)))
    if left:
        raise SystemExit(f"unfilled placeholders: {left}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page)
    shutil.copytree(SITE_DIR / "assets", out / "assets", dirs_exist_ok=True)
    brand = out / "assets" / "brand"
    brand.mkdir(parents=True, exist_ok=True)
    for name in ("topvenues-mark.svg", "topvenues-social.png", "mark-32.png", "mark-180.png"):
        shutil.copy2(tool / "docs/brand" / name, brand / name)
    shutil.copytree(
        tool / "docs/assets/screenshots", out / "assets" / "screens", dirs_exist_ok=True
    )
    (out / ".nojekyll").write_text("")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{SITE_URL}</loc><lastmod>{built}</lastmod></url></urlset>\n"
    )
    print(
        f"wrote {out / 'index.html'} ({len(page) / 1024:.0f} KiB) from {PROFILE} v{ver} @ {release['commit']}"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--tool",
        type=Path,
        default=SITE_DIR.parent,
        help="repository root (default: this checkout)",
    )
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    build(a.tool.expanduser().resolve(), a.out.expanduser().resolve())
