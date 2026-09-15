# -*- coding: utf-8 -*-
"""Renderiza la vista previa PDF: fuentes usadas, número de páginas y PNG por página."""
import sys
import pymupdf
from PIL import Image

PDF = "L:/periodico/_build/tmp/vista_previa.pdf"
OUT = sys.argv[1] if len(sys.argv) > 1 else "L:/periodico/_build/tmp/"
DPI = int(sys.argv[2]) if len(sys.argv) > 2 else 110

d = pymupdf.open(PDF)
print("paginas PDF:", len(d))
fuentes = sorted({f[3].split("+")[-1] for p in d for f in p.get_fonts()})
print("fuentes en el PDF:", ", ".join(fuentes))
for i, page in enumerate(d, 1):
    print(f"  pagina {i}: {page.rect.width:.0f} x {page.rect.height:.0f} pt")
    page.get_pixmap(dpi=DPI).save(f"{OUT}pagina{i}.png")
thumbs = [Image.open(f"{OUT}pagina{i}.png") for i in range(1, len(d) + 1)]
for t in thumbs:
    t.thumbnail((520, 520))
sheet = Image.new("RGB", (sum(t.width for t in thumbs) + 10 * (len(thumbs) + 1), 540), "#888")
x = 10
for t in thumbs:
    sheet.paste(t, (x, 10))
    x += t.width + 10
sheet.save(f"{OUT}hoja_paginas.png")
print("hoja:", f"{OUT}hoja_paginas.png")
