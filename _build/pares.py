# -*- coding: utf-8 -*-
"""Arma imágenes de pares de páginas (tmp/<prefijo>_parN.png) a partir de los PNG de revisar_pdf.py."""
import glob, sys
from PIL import Image

TMP = "L:/periodico/_build/tmp/"
prefijo = sys.argv[1] if len(sys.argv) > 1 else "v"
n = len(glob.glob(TMP + "pagina*.png"))
for old in glob.glob(TMP + f"{prefijo}_par*.png"):
    pass
for a in range(1, n + 1, 2):
    ims = [Image.open(TMP + f"pagina{i}.png") for i in (a, a + 1) if i <= n]
    for im in ims:
        im.thumbnail((780, 780))
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 10 * (len(ims) + 1), max(i.height for i in ims) + 20), "#777")
    x = 10
    for im in ims:
        sheet.paste(im, (x, 10))
        x += im.width + 10
    sheet.save(TMP + f"{prefijo}_par{a}.png")
print("pares:", [(a, a + 1) for a in range(1, n + 1, 2)])
