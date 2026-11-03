import json, time, urllib.request, urllib.parse, pathlib
out = pathlib.Path("asset-candidates"); out.mkdir(exist_ok=True)
UA = {"User-Agent": "tpasini-site/1.0 (https://tpasini.github.io; personal academic site)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
names = []
try:
    q = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action":"query","list":"search","srsearch":"intitle:INAF logo","srnamespace":"6","srlimit":"15","format":"json"})
    names = [r["title"].split(":",1)[1] for r in json.loads(get(q))["query"]["search"]]
    print("search:", names)
except Exception as e:
    print("search fail", e)
names += ["INAF_logo.svg","Logo_INAF.svg","INAF-logo.svg","Logo_INAF.png","INAF_logo.png","Logo-INAF.svg"]
n = 0
for nm in names:
    if not any(k in nm.lower() for k in ("inaf",)): continue
    time.sleep(3)
    u = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(nm.replace(" ", "_"))
    try:
        data = get(u); ext = nm.rsplit(".",1)[-1].lower()
        (out / f"logo_{n}.{ext}").write_bytes(data); print("got", nm, len(data)); n += 1
        if n >= 6: break
    except Exception as e:
        print("fail", nm, e)
