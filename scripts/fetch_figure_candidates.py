#!/usr/bin/env python3
"""One-off helper: download the arXiv sources of first-author papers and
convert their figures to PNG previews in figure-candidates/, so figures for
the website can be picked. Runs in GitHub Actions (fetch-figures.yml)."""
import io
import json
import re
import shutil
import subprocess
import tarfile
import gzip
import time
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figure-candidates"
IMG_EXT = {".png", ".jpg", ".jpeg", ".pdf", ".eps", ".ps"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tpasini.github.io figure fetcher"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def to_png(src: Path, dst: Path):
    ext = src.suffix.lower()
    try:
        if ext == ".pdf":
            subprocess.run(["pdftoppm", "-r", "170", "-png", "-singlefile", "-f", "1", "-l", "1",
                            str(src), str(dst.with_suffix(""))], check=True, timeout=120)
        elif ext in {".eps", ".ps"}:
            subprocess.run(["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dEPSCrop", "-sDEVICE=png16m",
                            "-r170", f"-sOutputFile={dst}", str(src)], check=True, timeout=120,
                           capture_output=True)
        else:
            Image.open(src).convert("RGB").save(dst)
        im = Image.open(dst).convert("RGB")
        im.thumbnail((1800, 1800))
        im.save(dst, optimize=True)
        return True
    except Exception as e:  # noqa: BLE001
        print("  skip", src.name, e)
        dst.unlink(missing_ok=True)
        return False


def sheet(folder: Path):
    files = sorted(folder.glob("*.png"))
    if not files:
        return
    cell, cols = 340, 4
    rows = (len(files) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, rows * (cell + 24)), "white")
    d = ImageDraw.Draw(canvas)
    for k, f in enumerate(files):
        im = Image.open(f)
        im.thumbnail((cell - 10, cell - 10))
        x, y = (k % cols) * cell, (k // cols) * (cell + 24)
        canvas.paste(im, (x + 5, y + 5))
        d.text((x + 5, y + cell - 2), f"{k:02d} {f.name[:44]}", fill="black")
    canvas.save(folder.parent / f"{folder.name}_sheet.jpg", quality=80)


def ads_ids(query):
    import os, urllib.parse
    url = "https://api.adsabs.harvard.edu/v1/search/query?" + urllib.parse.urlencode(
        {"q": query, "fl": "bibcode,title,identifier,pubdate,property,author", "rows": "20", "sort": "date desc"})
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["ADS_API_TOKEN"]})
    docs = json.load(urllib.request.urlopen(req, timeout=60))["response"]["docs"]
    found = []
    for d in docs:
        aid = next((i.split(":", 1)[1] for i in d.get("identifier", []) if i.startswith("arXiv:")), None)
        print("ADS:", d["bibcode"], d.get("pubdate"), aid, (d.get("title") or [""])[0][:120], d.get("author", [])[:3])
        if aid:
            found.append(aid)
    return found


def main():
    ids = ads_ids('author:"Pasini, T" (abs:"NGC 5903" OR title:"NGC 5903" OR full:"NGC 5903") year:2025-2026')[:3]
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    for aid in ids:
        print("arXiv", aid)
        try:
            blob = get(f"https://arxiv.org/e-print/{aid}")
        except Exception as e:  # noqa: BLE001
            print("  download failed", e)
            continue
        folder = OUT / aid.replace("/", "_")
        tmp = Path("/tmp/src") / folder.name
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        try:
            with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
                tf.extractall(tmp, filter="data")
        except tarfile.TarError:
            try:
                (tmp / "main.tex").write_bytes(gzip.decompress(blob))
            except OSError:
                (tmp / "paper.pdf").write_bytes(blob)
        folder.mkdir()
        n = 0
        for f in sorted(tmp.rglob("*")):
            if f.suffix.lower() in IMG_EXT and f.stat().st_size > 8000:
                rel = re.sub(r"[^A-Za-z0-9._-]", "_", str(f.relative_to(tmp)))
                if to_png(f, folder / (Path(rel).stem + ".png")):
                    n += 1
        print("  figures:", n)
        sheet(folder)
        time.sleep(4)


if __name__ == "__main__":
    main()
