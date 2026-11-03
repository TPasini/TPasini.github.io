import re, time, urllib.request, pathlib
out = pathlib.Path("asset-candidates"); out.mkdir(exist_ok=True)
UA = {"User-Agent": "tpasini-site/1.0 (https://tpasini.github.io; personal academic site)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
n = 0
for page in ["https://it.wikipedia.org/wiki/Istituto_nazionale_di_astrofisica", "https://en.wikipedia.org/wiki/National_Institute_for_Astrophysics"]:
    try:
        html = get(page).decode("utf-8", "ignore")
        box = html[html.find("infobox"):][:20000]
        for src in re.findall(r'src="(//upload\.wikimedia\.org/[^"]+)"', box)[:3]:
            orig = re.sub(r"/thumb(/.+?/.+?/[^/]+)/[^/]+$", r"\1", src)
            for cand in ["https:" + orig, "https:" + src]:
                try:
                    data = get(cand); ext = cand.rsplit(".", 1)[-1].split("?")[0][:4]
                    (out / f"logo_{n}.{ext}").write_bytes(data); print("got", cand); n += 1; break
                except Exception as e:
                    print("fail", cand, e)
                time.sleep(2)
    except Exception as e:
        print("page fail", page, e)
    time.sleep(3)
for u in ["https://www.media.inaf.it/wp-content/uploads/2014/01/logo_final_editable_inaf-uai_2013.png"]:
    try: (out / "media_logo.png").write_bytes(get(u)); print("got", u)
    except Exception as e: print("fail", u, e)
