import json, urllib.request, urllib.parse, pathlib
out = pathlib.Path("asset-candidates"); out.mkdir(exist_ok=True)
UA = {"User-Agent": "tpasini.github.io asset fetcher (personal academic site)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
# INAF logo from Wikimedia Commons
q = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action":"query","generator":"search","gsrsearch":"INAF logo Istituto Nazionale di Astrofisica","gsrnamespace":"6","gsrlimit":"8","prop":"imageinfo","iiprop":"url","format":"json"})
try:
    pages = json.loads(get(q))["query"]["pages"].values()
    for i, p in enumerate(pages):
        u = p["imageinfo"][0]["url"]; print("commons:", p["title"], u)
        ext = u.rsplit(".", 1)[-1].lower()
        (out / f"inaf_{i}.{ext}").write_bytes(get(u))
except Exception as e:
    print("commons failed", e)
# images from the old Google Site
gs = [
 "https://sites.google.com/sitesv-images-rt/AMxu72tXmuYuphf7Bu7q64KghnZzY8_1Yz2CDRyVHz2nvLP-ckv_VaIfIB6kpNHLFVDI6040Bd680-2mKWs14T_gBhdxlaTm1JfXGorFTRTUOuoM2Et7zjRDS8AQl6cwJDf75VBhgt2BbTClfDCdcjcsmO1MNRgGRv13OZZfFGbYhudsxPE4JK5PIWRUxF_x7s0=w1280",
 "https://sites.google.com/sitesv-images-rt/AMxu72suYul8lWxVryyjIRLjPG78S_WMlSg6i-iVQSNjU3Rdny_yQvoRpE9Q6jDzbu_gCouaCgtdKkl-6bPoW34NVrLj0UdLrPByPbuvJ105yuQOr64twBvMX_BqlvO8J_yQWB9YJRPZlyqvVqUYqE-hxGg33-5kasBarwHiaZmztbnPDva1GnFWbN_4AkvmV_S__VqQaILA9tLb-YWq7_JOW7EF24rBFjFBKt4DeWXDcOE=w1280",
 "https://sites.google.com/sitesv-images-rt/AMxu72t2Pav7Cs4ZPz3ozbw7GGnIMA94cpLu3EXt0wGMQz8Z2CPapDMi07eTq2W7G1RoxI4fCuYT51XkyWiz_L0jF8H9N5ffvNdTvvWV1guwYY2-MXmrO7rial0EEIIgK3TtacIvICHDnNzgKV80kkuCRYXN7Vy5ADYC5zO8PAMbtmANK8yQKslOsiinpCvG3dPOlIrUIjCl5JyJFSF9yg4ELjCi00dxqp6cI8jQIh87=w1280",
 "https://sites.google.com/sitesv-images-rt/AMxu72vxB4SAtLHH4A-cLvtoiG2voaRYiaU-VW38wQvRH0Bv-WCJj2UMCzvkcZRdhdztKpsLXvGXJPfSB9Dscr3rtW7MbreI4nszqZr89t-Fuw0t-XaIXJwxPxVX6cb5s_3E3vafs5a-VctHL6U17zG8j67Oasjhd4wM-UpQ8JpABBJeYs7K6JJ16BcPIfFHMNfGHGQ0tLxF-9G0sRDq9kPCSrI54dBUqXowElqaVB0TBxc=w1280",
 "https://sites.google.com/sitesv-images-rt/AMxu72usuak8ZSDLJ8N-gDSjHLKZkbvnWuT1ECcU6TtENXjxEp_e61DU6RMi9ZqkzFUMgQrPXUl4Ro10H2nBM_ahgWn_GTV9it4EdNUga8igSsTp4WbTPHdcZRqh6_nA0ZOlNi5lFxau9F3ZAj6Q204-ezgp5Qc8uQwb7oh4HsOITMXoUFQJlTx0ZgCM6TlOYzbqzD8yODnWQEnVosYLGvCEiEVV70kYxSFXTMZMDonKtLU=w1280",
]
for i, u in enumerate(gs):
    try:
        (out / f"oldsite_{i}.img").write_bytes(get(u)); print("oldsite", i, "ok")
    except Exception as e:
        print("oldsite", i, "failed", e)
