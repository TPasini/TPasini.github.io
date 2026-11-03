#!/usr/bin/env python3
"""Refresh the publication list on the website from NASA ADS.

Runs weekly in GitHub Actions (see .github/workflows/update-publications.yml).
It queries the ADS API, then rewrites the parts of index.html between the
<!-- PUBS:START/END -->, <!-- FACTS:START/END --> and <!-- UPDATED:START/END -->
markers, saves data/publications.json and refreshes sitemap.xml.

Needs the ADS token in the ADS_API_TOKEN environment variable (a GitHub secret).
For a local test without network access:  python scripts/update_publications.py --from-file sample.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------- settings
ADS_QUERY = 'author:"Pasini, Thomas"'
ADS_FILTERS = ["database:astronomy"]
SURNAME_PREFIX = "Pasini, T"          # how the owner appears in ADS author lists
EXCLUDE_BIBCODES: set[str] = set()     # add bibcodes here if ADS ever attributes someone else's paper
SITE_URL = "https://tpasini.github.io/"

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
DATA = ROOT / "data" / "publications.json"
SITEMAP = ROOT / "sitemap.xml"

FIELDS = "bibcode,title,author,year,pub,citation_count,doi,identifier,doctype,property,pubdate"
JOURNAL_NAMES = {
    "Astronomy and Astrophysics": "Astronomy & Astrophysics",
    "Monthly Notices of the Royal Astronomical Society": "Monthly Notices of the Royal Astronomical Society",
}


# ---------------------------------------------------------------- ADS
def fetch_ads(token: str) -> list[dict]:
    docs, start = [], 0
    while True:
        params = [("q", ADS_QUERY), ("fl", FIELDS), ("rows", "200"), ("start", str(start)),
                  ("sort", "date desc")] + [("fq", f) for f in ADS_FILTERS]
        url = "https://api.adsabs.harvard.edu/v1/search/query?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.load(r)
        resp = payload["response"]
        docs.extend(resp["docs"])
        start += len(resp["docs"])
        if not resp["docs"] or start >= resp["numFound"]:
            return docs


# ---------------------------------------------------------------- helpers
def clean(text: str) -> str:
    """ADS titles may carry HTML entities and tags such as <SUB>; return plain text."""
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def owner_position(authors: list[str]) -> int:
    for i, a in enumerate(authors):
        if a.startswith(SURNAME_PREFIX):
            return i
    return -1


def arxiv_id(identifiers: list[str]) -> str | None:
    for ident in identifiers or []:
        m = re.match(r"^arXiv:(.+)$", ident)
        if m:
            return m.group(1)
    for ident in identifiers or []:
        if re.match(r"^\d{4}\.\d{4,5}$", ident):
            return ident
    return None


def author_line(authors: list[str], pos: int) -> str:
    me = lambda a: f'<span class="me">{esc(a)}</span>'
    shown = authors[:3]
    parts = [me(a) if i == pos else esc(a) for i, a in enumerate(shown)]
    line = "; ".join(parts)
    if len(authors) > 3:
        line += "; et al."
        if pos >= 3:
            line += f" (incl. {me(authors[pos])}, {ordinal(pos + 1)} of {len(authors)})"
    return line


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def h_index(cites: list[int]) -> int:
    cites = sorted(cites, reverse=True)
    return sum(1 for i, c in enumerate(cites, 1) if c >= i)


# ---------------------------------------------------------------- build
def process(docs: list[dict]) -> dict:
    papers = []
    for d in docs:
        if d.get("bibcode") in EXCLUDE_BIBCODES:
            continue
        authors = d.get("author") or []
        pos = owner_position(authors)
        if pos < 0:
            continue
        papers.append({
            "bibcode": d["bibcode"],
            "title": clean((d.get("title") or [""])[0]),
            "authors": authors,
            "position": pos,
            "year": d.get("year", ""),
            "pubdate": d.get("pubdate", ""),
            "journal": JOURNAL_NAMES.get(d.get("pub", ""), d.get("pub", "")),
            "citations": int(d.get("citation_count") or 0),
            "doi": (d.get("doi") or [None])[0],
            "arxiv": arxiv_id(d.get("identifier") or []),
            "refereed": "REFEREED" in (d.get("property") or []),
            "doctype": d.get("doctype", ""),
        })
    refereed = [p for p in papers if p["refereed"]]
    refereed.sort(key=lambda p: (p["pubdate"], p["bibcode"]), reverse=True)
    return {
        "updated": dt.date.today().isoformat(),
        "query": ADS_QUERY,
        "total_citations": sum(p["citations"] for p in papers),
        "h_index": h_index([p["citations"] for p in papers]),
        "n_refereed": len(refereed),
        "n_first_author": sum(1 for p in refereed if p["position"] == 0),
        "refereed": refereed,
    }


def render_pubs(data: dict) -> str:
    out = []
    for p in data["refereed"]:
        lead = p["position"] == 0
        abs_url = f"https://ui.adsabs.harvard.edu/abs/{urllib.parse.quote(p['bibcode'])}/abstract"
        tags = []
        if lead:
            tags.append('<span class="tag lead">first author</span>')
        if p["arxiv"]:
            tags.append(f'<a class="tag" href="https://arxiv.org/abs/{esc(p["arxiv"])}" target="_blank" rel="noopener">arXiv:{esc(p["arxiv"])}</a>')
        if p["doi"]:
            tags.append(f'<a class="tag" href="https://doi.org/{esc(p["doi"])}" target="_blank" rel="noopener">DOI</a>')
        if p["citations"]:
            tags.append(f'<span class="tag">{p["citations"]} citation{"s" if p["citations"] != 1 else ""}</span>')
        hidden = "" if lead else " hidden"
        out.append(
            f'        <li class="pub" data-kind="{"lead" if lead else "co"}"{hidden}><span class="yr">{esc(p["year"])}</span><div>\n'
            f'          <a class="t" href="{abs_url}" target="_blank" rel="noopener">{esc(p["title"])}</a>\n'
            f'          <div class="meta">{author_line(p["authors"], p["position"])} · {esc(p["journal"])}</div>\n'
            f'          <div class="tags">{"".join(tags)}</div></div></li>'
        )
    return "\n".join(out)


def render_facts(data: dict) -> str:
    def fact(value, label):
        return f'        <div class="fact"><b>{value}</b><span>{label}</span></div>'
    return "\n".join([
        fact(f'{data["total_citations"]:,}', "citations (NASA ADS)"),
        fact(data["h_index"], "h-index"),
        fact(data["n_refereed"], "refereed papers"),
        fact(data["n_first_author"], "as first author"),
    ])


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(\s*<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"marker {name} not found in index.html")
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}{m.group(3)}", text, count=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file", help="use a saved ADS JSON response instead of the API")
    args = ap.parse_args()

    if args.from_file:
        docs = json.loads(Path(args.from_file).read_text())["response"]["docs"]
    else:
        token = os.environ.get("ADS_API_TOKEN", "").strip()
        if not token:
            sys.exit("ADS_API_TOKEN is not set: add it as a repository secret.")
        docs = fetch_ads(token)

    data = process(docs)
    if not data["refereed"]:
        sys.exit("ADS returned no refereed papers; leaving the site unchanged.")

    page = INDEX.read_text(encoding="utf-8")
    page = replace_block(page, "PUBS", render_pubs(data))
    page = replace_block(page, "FACTS", render_facts(data))
    page = replace_block(page, "UPDATED",
                         f'      <span>Publications updated from NASA ADS on {data["updated"]}</span>')
    INDEX.write_text(page, encoding="utf-8")

    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    SITEMAP.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{SITE_URL}</loc><lastmod>{data["updated"]}</lastmod></url>\n'
        '</urlset>\n', encoding="utf-8")
    print(f'{data["n_refereed"]} refereed papers ({data["n_first_author"]} first author), '
          f'{data["total_citations"]} citations, h = {data["h_index"]}')


if __name__ == "__main__":
    main()
