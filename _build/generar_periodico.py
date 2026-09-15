# -*- coding: utf-8 -*-
"""Genera LA_CUESTION_periodico.docx: portada estilo diario + 5 páginas interiores.

Todo el texto es editable en Word. La maquetación usa tablas sin bordes (rejilla del
periódico) y estilos de párrafo propios con prefijo «LC». Las fuentes de /fuentes se
aplican por nombre y se incrustan en el .docx. Cada cara (Bold, Italic...) es una familia
propia porque Word 2007 solo carga caras «Regular» incrustadas.
"""
import json, os, re, uuid, zipfile
from lxml import etree
from PIL import Image
from fontTools.ttLib import TTFont
from docx import Document
from docx.document import Document as DocCls
from docx.text.paragraph import Paragraph
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT as VA, WD_ROW_HEIGHT_RULE
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = "L:/periodico/"
FUENTES = BASE + "fuentes/"
IMG = BASE + "imagenes/"
TMP = BASE + "_build/tmp/"
BORRADOR = TMP + "borrador.docx"
SALIDA = BASE + "LA_CUESTION_periodico.docx"
CRUCI = BASE + "_build/crucigrama.json"

INK, BLUE, GREY, RULE = "1E1C22", "1F6FB2", "6E6A72", "A7A3AB"
CREAM, LBLUE, WHITE, YEL = "F4EFE4", "E3EDF6", "FFFFFF", "FFF1B8"
W, WL = 19.19, 25.54          # ancho útil vertical / horizontal (cm)
FECHA = "Martes 8 de septiembre de 2026"

# ============================================================ fuentes
DISP, DISPB, DISPI, HEAVY = "Newsreader Display", "Newsreader Display Bold", "Newsreader Display Italic", \
    "Newsreader Display ExtraBold"
TXT, TXTB, TXTI = "Newsreader Text", "Newsreader Text Bold", "Newsreader Text Italic"
OS, OSB = "Oswald", "Oswald Bold"
ARCHIVOS = {DISP: "NewsreaderDisplay-Regular.ttf", DISPB: "NewsreaderDisplay-Bold.ttf",
            DISPI: "NewsreaderDisplay-Italic.ttf", HEAVY: "NewsreaderDisplay-ExtraBold.ttf",
            TXT: "NewsreaderText-Regular.ttf", TXTB: "NewsreaderText-Bold.ttf", TXTI: "NewsreaderText-Italic.ttf",
            OS: "Oswald-Regular.ttf", OSB: "Oswald-Bold.ttf"}
_RAIZ = {DISP: (DISP, False, False), DISPB: (DISP, True, False), DISPI: (DISP, False, True),
         HEAVY: (HEAVY, False, False), TXT: (TXT, False, False), TXTB: (TXT, True, False),
         TXTI: (TXT, False, True), OS: (OS, False, False), OSB: (OS, True, False)}


def cara(family, bold=None, italic=None):
    """Familia concreta para una combinación de negrita/cursiva."""
    root, b0, i0 = _RAIZ[family]
    b = b0 if bold is None else bold
    i = i0 if italic is None else italic
    if root == HEAVY:
        return HEAVY
    if root == OS:
        return OSB if b else OS
    return root + (" Bold" if b else " Italic" if i else "")


# ============================================================ utilidades OOXML
def _order(*t): return [qn(x) for x in t]
PPR = _order('w:pStyle', 'w:keepNext', 'w:keepLines', 'w:pageBreakBefore', 'w:framePr', 'w:widowControl', 'w:numPr',
             'w:suppressLineNumbers', 'w:pBdr', 'w:shd', 'w:tabs', 'w:suppressAutoHyphens', 'w:kinsoku', 'w:wordWrap',
             'w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN', 'w:bidi', 'w:adjustRightInd',
             'w:snapToGrid', 'w:spacing', 'w:ind', 'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
             'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl', 'w:divId', 'w:cnfStyle', 'w:rPr',
             'w:sectPr', 'w:pPrChange')
RPR = _order('w:rStyle', 'w:rFonts', 'w:b', 'w:bCs', 'w:i', 'w:iCs', 'w:caps', 'w:smallCaps', 'w:strike', 'w:dstrike',
             'w:outline', 'w:shadow', 'w:emboss', 'w:imprint', 'w:noProof', 'w:snapToGrid', 'w:vanish', 'w:webHidden',
             'w:color', 'w:spacing', 'w:w', 'w:kern', 'w:position', 'w:sz', 'w:szCs', 'w:highlight', 'w:u', 'w:effect',
             'w:bdr', 'w:shd', 'w:fitText', 'w:vertAlign', 'w:rtl', 'w:cs', 'w:em', 'w:lang', 'w:eastAsianLayout')
TCPR = _order('w:cnfStyle', 'w:tcW', 'w:gridSpan', 'w:hMerge', 'w:vMerge', 'w:tcBorders', 'w:shd', 'w:noWrap', 'w:tcMar',
              'w:textDirection', 'w:tcFitText', 'w:vAlign', 'w:hideMark')
TBLPR = _order('w:tblStyle', 'w:tblpPr', 'w:tblOverlap', 'w:bidiVisual', 'w:tblStyleRowBandSize', 'w:tblStyleColBandSize',
               'w:tblW', 'w:jc', 'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout', 'w:tblCellMar',
               'w:tblLook')
SIDES = _order('w:top', 'w:left', 'w:bottom', 'w:right', 'w:insideH', 'w:insideV')
P_TAG, TBL_TAG = qn('w:p'), qn('w:tbl')


def tw(cm): return int(round(cm * 566.929))


def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn('w:' + k), str(v))
    return e


def put(parent, child, order):
    """Inserta child respetando el orden de esquema (Word 2007 es estricto)."""
    for old in parent.findall(child.tag):
        parent.remove(old)
    idx = order.index(child.tag)
    for ex in parent:
        if ex.tag in order and order.index(ex.tag) > idx:
            ex.addprevious(child)
            return child
    parent.append(child)
    return child


def rfonts(rpr, name):
    put(rpr, el('w:rFonts', ascii=name, hAnsi=name, cs=name, eastAsia=name), RPR)


def tracking(rpr, pts):
    put(rpr, el('w:spacing', val=int(pts * 20)), RPR)


# ============================================================ métricas para ajustar titulares
_MET = {}


def ancho_pt(family, text, size):
    if family not in _MET:
        f = TTFont(FUENTES + ARCHIVOS[family])
        _MET[family] = (f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm)
    cmap, hmtx, upm = _MET[family]
    return sum(hmtx[cmap.get(ord(ch), cmap[ord('n')])][0] for ch in text) * size / upm


def lineas(family, text, size, width_cm):
    limit, n, cur = width_cm / 2.54 * 72, 1, ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if ancho_pt(family, t, size) <= limit:
            cur = t
        else:
            n, cur = n + 1, word
    return n


def ajustar(text, family, width_cm, max_lines, start, minimum):
    s = start
    while s > minimum and lineas(family, text, s, width_cm) > max_lines:
        s -= 0.5
    print(f"   titular {s:>4}pt · {lineas(family, text, s, width_cm)} línea(s) · {text[:50]}")
    return s


# ============================================================ estilos
def estilo(doc, name, font, size, bold=False, italic=False, color=INK, align=None, before=0, after=0, line=None,
           caps=False, track=None, keep=False, hanging=None, outline=None, nohyphen=False):
    st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = doc.styles['Normal']
    st.quick_style = True
    f = st.font
    f.size, f.all_caps = Pt(size), caps
    f.color.rgb = RGBColor.from_string(color)
    rpr = st.element.get_or_add_rPr()
    rfonts(rpr, cara(font, bold, italic))
    if track:
        tracking(rpr, track)
    pf = st.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if line:
        pf.line_spacing, pf.line_spacing_rule = Pt(line), WD_LINE_SPACING.EXACTLY
    else:
        pf.line_spacing = 1.0
    if align is not None:
        pf.alignment = align
    if keep:
        pf.keep_with_next = True
    if hanging is not None:
        pf.left_indent, pf.first_line_indent = Cm(hanging), Cm(-hanging)
    ppr = st.element.get_or_add_pPr()
    if nohyphen:
        put(ppr, el('w:suppressAutoHyphens'), PPR)
    if outline is not None:
        put(ppr, el('w:outlineLvl', val=outline), PPR)


def estilos(doc):
    rpr_def = doc.styles.element.find(qn('w:docDefaults')).find(qn('w:rPrDefault')).find(qn('w:rPr'))
    rfonts(rpr_def, TXT)
    put(rpr_def, el('w:lang', val='es-CO', eastAsia='es-CO', bidi='ar-SA'), RPR)
    normal = doc.styles['Normal']
    normal.font.size = Pt(9)
    rfonts(normal.element.get_or_add_rPr(), TXT)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    J, C = AL.JUSTIFY, AL.CENTER
    E = estilo
    E(doc, 'LC Mini', TXT, 1, line=1)
    E(doc, 'LC Imagen', TXT, 9)
    # cabecera y portada
    E(doc, 'LC Cabecera', HEAVY, 56, align=C, nohyphen=True)
    E(doc, 'LC Lema', TXT, 8.5, align=C, track=1.8, after=2)
    E(doc, 'LC Numero', HEAVY, 30, nohyphen=True)
    E(doc, 'LC Dato', OS, 7.5, line=9.5)
    E(doc, 'LC Teaser', DISP, 15, line=17.5, nohyphen=True)
    E(doc, 'LC PieFoto', TXT, 7.2, bold=True, line=8.8, before=2)
    # titulares (con nivel de esquema para el panel de navegación)
    E(doc, 'LC TitularGrande', HEAVY, 34, line=39, before=4, after=2, nohyphen=True, outline=0, keep=True)
    E(doc, 'LC Titular1', DISP, 30, bold=True, line=33, after=3, nohyphen=True, outline=0, keep=True)
    E(doc, 'LC Titular3', DISP, 18, bold=True, line=20, after=4, nohyphen=True, outline=1, keep=True)
    E(doc, 'LC Titular4', DISP, 15, bold=True, line=17, nohyphen=True, keep=True)
    E(doc, 'LC Titular4R', DISP, 15.5, line=17, after=3, nohyphen=True, outline=1, keep=True)
    E(doc, 'LC Titular5', DISP, 12.5, bold=True, line=14, nohyphen=True, keep=True)
    E(doc, 'LC Titular5R', DISP, 13, line=14.5, after=2, nohyphen=True, keep=True)
    E(doc, 'LC Antetitulo', OS, 12, bold=True, color=BLUE, caps=True, track=0.6, line=16, keep=True)
    E(doc, 'LC Sumario', TXT, 10.5, line=12.8, after=2)
    E(doc, 'LC Entradilla', TXT, 11, line=13, after=5, nohyphen=True)
    E(doc, 'LC Deck', TXT, 12, italic=True, line=14.8, after=3, nohyphen=True)
    E(doc, 'LC Firma', OS, 6.8, caps=True, track=0.4, line=9.5, keep=True)
    E(doc, 'LC Lugar', TXT, 7.6, bold=True, line=9, after=2, keep=True)
    E(doc, 'LC Etiqueta', OS, 9, color=GREY, caps=True, track=1.5, line=12.5, after=2, keep=True)
    E(doc, 'LC EtiquetaAzul', OS, 10.5, bold=True, color=BLUE, line=13, after=1, keep=True)
    # cuerpo y recuadros
    E(doc, 'LC Cuerpo', TXT, 8.8, line=10.7, after=3)
    E(doc, 'LC CuerpoG', TXT, 9.2, line=11.3, after=3.5)
    E(doc, 'LC Ladillo', OS, 9.5, bold=True, color=BLUE, caps=True, track=0.4, line=12.5, before=4, after=1.5,
      keep=True, outline=2)
    E(doc, 'LC Destacado', DISP, 14, italic=True, align=C, line=17, before=6, after=6, nohyphen=True)
    E(doc, 'LC CajaTitulo', OS, 10, bold=True, color=BLUE, caps=True, track=0.6, line=13, after=3, keep=True)
    E(doc, 'LC CajaTexto', TXT, 8.4, line=10.2, after=3)
    E(doc, 'LC Cifra', HEAVY, 15, color=BLUE, line=17, nohyphen=True)
    E(doc, 'LC Paso', OS, 13, bold=True, color=WHITE, align=C, line=15)
    E(doc, 'LC Referencia', TXT, 7.6, line=9.1, after=2.5, hanging=0.5)
    E(doc, 'LC Pista', TXT, 8.1, line=9.7, after=2.2)
    E(doc, 'LC Celda', OS, 5.5, line=6)
    E(doc, 'LC Narrador', OS, 8.3, line=10.2, before=1, after=1)
    E(doc, 'LC Dialogo', TXT, 8.6, line=10.2, after=1)
    E(doc, 'LC TablaEnc', OS, 8, bold=True, color=WHITE, line=10)
    E(doc, 'LC TablaTxt', TXT, 7.9, line=9.4)
    E(doc, 'LC Seccion', OS, 22, bold=True, caps=True, nohyphen=True)
    E(doc, 'LC Folio', OS, 8, line=11)
    E(doc, 'LC Pie', OS, 7, color=GREY, line=9)


# ============================================================ bloques de maquetación
def blocks(container):
    elm = container.element.body if isinstance(container, DocCls) else container._element
    return [c for c in elm if c.tag in (P_TAG, TBL_TAG)]


def fresh(p):
    if p.find(qn('w:r')) is not None:
        return False
    ppr = p.find(qn('w:pPr'))
    return ppr is None or ppr.find(qn('w:pStyle')) is None


def familia_estilo(p):
    st = p.style
    while st is not None:
        rpr = st.element.rPr
        rf = rpr.find(qn('w:rFonts')) if rpr is not None else None
        if rf is not None and rf.get(qn('w:ascii')) in _RAIZ:
            return rf.get(qn('w:ascii'))
        st = st.base_style
    return TXT


TOK = re.compile(r'(\*\*.+?\*\*|\*[^*\n]+?\*)')


def runs(p, text, bold=None, italic=None, color=None, size=None, font=None, caps=None, track=None):
    """Texto con marcas **negrita** y *cursiva* resueltas a la familia correspondiente."""
    base = font or familia_estilo(p)
    for part in TOK.split(text):
        if not part:
            continue
        b, i = bold, italic
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            part, b = part[2:-2], True
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            part, i = part[1:-1], True
        part = part.replace(" %", "\u00a0%")
        r = p.add_run(part)
        fam = cara(base, b, i)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        if size:
            r.font.size = Pt(size)
        if caps is not None:
            r.font.all_caps = caps
        rpr = r._r.get_or_add_rPr()
        if font or fam != base:
            rfonts(rpr, fam)
        if track:
            tracking(rpr, track)
    return p


def para(container, text="", style="LC Cuerpo", align=None, before=None, after=None, line=None, indent=None,
         keep=None, **run):
    bl = blocks(container)
    if len(bl) == 1 and bl[0].tag == P_TAG and fresh(bl[0]):
        p = Paragraph(bl[0], container)
        p.style = style
    else:
        p = container.add_paragraph(style=style)
    pf = p.paragraph_format
    if align is not None:
        pf.alignment = align
    if before is not None:
        pf.space_before = Pt(before)
    if after is not None:
        pf.space_after = Pt(after)
    if line is not None:
        pf.line_spacing, pf.line_spacing_rule = Pt(line), WD_LINE_SPACING.EXACTLY
    if indent is not None:
        pf.left_indent = pf.right_indent = Cm(indent)
    if keep:
        pf.keep_with_next = True
    if text:
        runs(p, text, **run)
    return p


def ref(p, page):
    runs(p, " —" + page, font=OSB, size=7)


def mini(p):
    p.style = 'LC Mini'


def espacio(container, pts):
    p = container.add_paragraph(style='LC Mini')
    p.paragraph_format.line_spacing, p.paragraph_format.line_spacing_rule = Pt(pts), WD_LINE_SPACING.EXACTLY
    return p


def pborder(p, **edges):
    ppr = p._p.get_or_add_pPr()
    b = ppr.find(qn('w:pBdr'))
    if b is None:
        b = put(ppr, OxmlElement('w:pBdr'), PPR)
    for side, v in edges.items():
        space = v[2] if len(v) > 2 else 1
        put(b, el('w:' + side, val='single', sz=int(v[0] * 8), space=int(space), color=v[1]), SIDES)


def pshade(p, fill):
    put(p._p.get_or_add_pPr(), el('w:shd', val='clear', color='auto', fill=fill), PPR)


def picture(container, path, width_cm, align=AL.CENTER, before=0, after=0):
    p = para(container, style='LC Imagen', align=align, before=before, after=after)
    p.add_run().add_picture(path, width=Cm(width_cm))
    return p


def table(container, widths, rows=1, pad=(0, 0, 0, 0), center=False):
    if isinstance(container, DocCls):
        bl = blocks(container)
        if bl and bl[-1].tag == TBL_TAG:
            mini(container.add_paragraph())
        t = container.add_table(rows, len(widths))
    else:
        t = container.add_table(rows, len(widths))
        tc = container._element
        first = tc.find(P_TAG)
        if first is not None and first.getnext() is t._tbl and fresh(first):
            tc.remove(first)
        mini(container.paragraphs[-1])          # Word exige un párrafo tras la tabla
    tblPr = t._tbl.tblPr
    put(tblPr, el('w:tblW', w=tw(sum(widths)), type='dxa'), TBLPR)
    if center:
        put(tblPr, el('w:jc', val='center'), TBLPR)
    else:
        put(tblPr, el('w:tblInd', w=0, type='dxa'), TBLPR)
    put(tblPr, el('w:tblLayout', type='fixed'), TBLPR)
    mar = OxmlElement('w:tblCellMar')
    for side, v in zip(('top', 'left', 'bottom', 'right'), pad):
        mar.append(el('w:' + side, w=tw(v), type='dxa'))
    put(tblPr, mar, TBLPR)
    for gc, wdt in zip(t._tbl.tblGrid.findall(qn('w:gridCol')), widths):
        gc.set(qn('w:w'), str(tw(wdt)))
    for row in t.rows:
        for c, wdt in zip(row.cells, widths):
            c.width = Cm(wdt)
    return t


def cborders(cell, **edges):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn('w:tcBorders'))
    if b is None:
        b = put(tcPr, OxmlElement('w:tcBorders'), TCPR)
    for side, v in edges.items():
        e = el('w:' + side, val='nil') if v is None else \
            el('w:' + side, val='single', sz=int(v[0] * 8), space=0, color=v[1])
        put(b, e, SIDES)


def box(cell, weight=0.75, color=INK):
    cborders(cell, top=(weight, color), left=(weight, color), bottom=(weight, color), right=(weight, color))


def shade(cell, fill):
    put(cell._tc.get_or_add_tcPr(), el('w:shd', val='clear', color='auto', fill=fill), TCPR)


def cmargins(cell, top=None, left=None, bottom=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for side, v in (('top', top), ('left', left), ('bottom', bottom), ('right', right)):
        if v is not None:
            m.append(el('w:' + side, w=tw(v), type='dxa'))
    put(tcPr, m, TCPR)


def row_exact(row, cm):
    row.height, row.height_rule = Cm(cm), WD_ROW_HEIGHT_RULE.EXACTLY


def campo(p, instr, **fmt):
    def fld(kind):
        p.add_run()._r.append(el('w:fldChar', fldCharType=kind))
    fld('begin')
    it = OxmlElement('w:instrText')
    it.set(qn('xml:space'), 'preserve')
    it.text = f' {instr} '
    p.add_run()._r.append(it)
    fld('separate')
    runs(p, '1', **fmt)
    fld('end')


# ============================================================ secciones, encabezados, cintillos
def seccion(doc, landscape=False, first=False):
    if not first:
        doc.add_section(WD_SECTION.NEW_PAGE)
        mini(Paragraph(doc.element.body.findall(P_TAG)[-1], doc))   # párrafo que guarda el salto
    s = doc.sections[-1]
    s.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    s.page_width, s.page_height = (Cm(27.94), Cm(21.59)) if landscape else (Cm(21.59), Cm(27.94))
    s.left_margin = s.right_margin = Cm(1.2)
    s.top_margin, s.bottom_margin = Cm(1.7), Cm(1.3)
    s.header_distance, s.footer_distance = Cm(0.7), Cm(0.55)
    return s


def encabezado(section, width):
    h = section.header
    h.is_linked_to_previous = False
    p = para(h, style='LC Folio')
    p.paragraph_format.tab_stops.add_tab_stop(Cm(width / 2), WD_TAB_ALIGNMENT.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(width), WD_TAB_ALIGNMENT.RIGHT)
    runs(p, "LA CUESTIÓN", font=HEAVY, size=10)
    runs(p, "   " + FECHA, color=GREY)
    runs(p, "\tPeriódico de análisis social", color=GREY)
    runs(p, "\t")
    campo(p, "PAGE", font=OSB, size=10)
    pborder(p, bottom=(0.75, INK, 3))
    f = section.footer
    f.is_linked_to_previous = False
    q = para(f, "LA CUESTIÓN · Actividad 1 · Problemas sociales contemporáneos · Docente: Allison Paola Escobar",
             style='LC Pie', align=AL.CENTER)
    pborder(q, top=(0.5, RULE, 3))


def cintillo(doc, seccion_txt, detalle, der1, der2, width):
    t = table(doc, [width * 0.64, width * 0.36], pad=(0, 0, 0.06, 0))
    c0, c1 = t.rows[0].cells
    for c in (c0, c1):
        c.vertical_alignment = VA.BOTTOM
        cborders(c, bottom=(2.25, INK))
    p = para(c0, seccion_txt, style='LC Seccion')
    runs(p, "   " + detalle, font=DISPI, size=14, caps=False, color=GREY)
    para(c1, der1, style='LC Dato', align=AL.RIGHT, color=BLUE, bold=True)
    para(c1, der2, style='LC Dato', align=AL.RIGHT)


def columnas(container, n, width, gap=0.45, rows=1):
    """Rejilla de n columnas de texto (el margen interno de las celdas hace de medianil)."""
    t = table(container, [width / n] * n, rows=rows)
    for row in t.rows:
        for i, c in enumerate(row.cells):
            cmargins(c, left=0 if i == 0 else gap / 2, right=0 if i == n - 1 else gap / 2)
    return t


def cajas(container, width, n=3, gap=0.3, fill=CREAM, top=BLUE):
    each = (width - gap * (n - 1)) / n
    ws = []
    for i in range(n):
        ws += [each] + ([gap] if i < n - 1 else [])
    t = table(container, ws, pad=(0.16, 0.25, 0.14, 0.25))
    cells = [t.rows[0].cells[i * 2] for i in range(n)]
    for c in cells:
        shade(c, fill)
        cborders(c, top=(3, top))
    return cells


# ============================================================ PÁGINA 1 · PORTADA
def portada(doc):
    s = seccion(doc, first=True)
    s.top_margin, s.bottom_margin = Cm(0.9), Cm(0.8)
    # --- cabecera
    t = table(doc, [3.6, 11.99, 3.6], pad=(0, 0, 0.12, 0))
    c0, c1, c2 = t.rows[0].cells
    c0.vertical_alignment = c2.vertical_alignment = VA.BOTTOM
    c1.vertical_alignment = VA.CENTER
    p = para(c0, "0", style='LC Numero')
    runs(p, "1", color=BLUE)
    para(c0, "Fundado en 2026\nAño I\nNúmero 1", style='LC Dato')
    para(c1, "LA CUESTIÓN", style='LC Cabecera', size=ajustar("LA CUESTIÓN", HEAVY, 11.6, 1, 62, 30))
    para(c1, "EL PERIÓDICO DE ANÁLISIS SOCIAL", style='LC Lema')
    para(c2, "Edición Colombia\nEjemplar académico", style='LC Dato', align=AL.RIGHT)
    para(c2, "Martes", style='LC Dato', align=AL.RIGHT, color=BLUE, bold=True)
    para(c2, "8 de septiembre de 2026", style='LC Dato', align=AL.RIGHT, bold=True)
    # --- franja de avance
    t = table(doc, [3.3, 2.1, 13.79], pad=(0.08, 0, 0.08, 0))
    for c in t.rows[0].cells:
        cborders(c, top=(0.75, INK), bottom=(0.75, INK))
        c.vertical_alignment = VA.CENTER
    a, b, c = t.rows[0].cells
    para(a, "Pasatiempos", style='LC Titular4', size=14)
    picture(b, IMG + "icono_crucigrama.png", 1.9)
    ref(para(c, "El crucigrama que pone a prueba tu lente sociológico", style='LC Teaser'), "P4")
    # --- nota de apertura + columna derecha
    t = table(doc, [13.55, 5.64], pad=(0.2, 0, 0, 0))
    L, R = t.rows[0].cells
    cmargins(L, right=0.3)
    cmargins(R, left=0.3)
    cborders(R, left=(0.5, RULE))
    foto = TMP + "portada_recorte.png"
    Image.open(IMG + "portada_principal.png").crop((0, 150, 1600, 930)).save(foto)
    picture(L, foto, 13.25, align=AL.LEFT)
    p = para(L, "Anochecer en un corredor urbano del Valle de Aburrá: bajo el viaducto duerme un habitante de "
                "calle y en el semáforo un niño vende dulces. ", style='LC PieFoto')
    runs(p, "ILUSTRACIÓN: LA CUESTIÓN", font=OS, size=6, color=GREY)
    para(L, "Problemas sociales y problemas de programas", style='LC Antetitulo', before=6)
    tit = "La pobreza baja, pero los programas siguen sin llegar"
    sz = ajustar(tit, DISPB, 13.2, 2, 34, 24)
    para(L, tit, style='LC Titular1', size=sz, line=sz * 1.1)
    para(L, "• La pobreza monetaria cayó al 28,0 % en 2025, según el DANE • El paso del Sisbén al RUI pone en "
            "riesgo las transferencias de cerca del 49 % de los hogares de Renta Ciudadana", style='LC Sumario')
    body = columnas(L, 3, 13.25, gap=0.35, rows=2)
    body.cell(0, 0).merge(body.cell(1, 0))
    sub = body.cell(1, 1).merge(body.cell(1, 2))
    k0, k1, k2 = body.cell(0, 0), body.cell(0, 1), body.cell(0, 2)
    para(k0, "Mesa de redacción", style='LC Firma', before=3)
    para(k0, "Bogotá / Medellín", style='LC Lugar')
    para(k0, "La pobreza monetaria bajó al 28,0 % en 2025, frente al 31,8 % de 2024, según el DANE. Pero en "
             "agosto los hogares de Renta Ciudadana supieron que su giro se aplazaba.")
    para(k1, "La razón es el paso del Sisbén al Registro Universal de Ingresos (RUI), reglamentado por el Decreto "
             "662 de 2026. Prosperidad Social advirtió que aplicarlo sin transición podría afectar a cerca del "
             "49 % de los hogares.", before=3)
    ref(para(k2, "No hay contradicción. Suárez (1989) lo explicó: una cosa es el problema social —la carencia— y "
                 "otra el problema del programa que intenta resolverla.", before=3), "P3")
    p = para(sub, "«No todo problema social se convierte en una cuestión socialmente problematizada», advertía "
                  "Suárez", style='LC Titular5', before=2)
    pborder(p, top=(0.5, INK, 4))
    cmargins(sub, left=0.175)
    # columna derecha
    para(R, "Por qué hay que leer las crisis con teoría social", style='LC Titular3')
    para(R, "Nuestro editorial: a quién le hablamos, cómo escribimos y para qué", style='LC Entradilla')
    para(R, "Editorial", style='LC Firma')
    para(R, "Mesa de redacción", style='LC Lugar')
    ref(para(R, "Las cifras dicen cuánto; la teoría explica por qué. Sin marco conceptual, la pobreza o la violencia "
                "se reducen a titulares que indignan un día y se olvidan al siguiente."), "P2")
    p = para(R, "‘Calle Cero’: el programa que vino, tomó la foto y se fue", style='LC Titular3', before=7)
    pborder(p, top=(0.5, INK, 7))
    para(R, "Nuestra tira cómica sigue a don Ramiro y a Lucía, trabajadora social, por la ruta de una cuestión "
            "socialmente problematizada", style='LC Entradilla')
    para(R, "Humor gráfico", style='LC Firma')
    para(R, "Mesa de redacción", style='LC Lugar')
    ref(para(R, "Un hombre duerme bajo un puente durante años sin que nadie lo vea. Llega una cámara, luego un "
                "programa con una meta imposible y, tres meses después, un letrero de «cerrado»."), "P5")
    # --- franja inferior
    t = table(doc, [9.0, 4.1, 6.09], pad=(0.18, 0, 0, 0))
    a, b, c = t.rows[0].cells
    for x in (a, b, c):
        cborders(x, top=(1.0, INK))
    cborders(b, left=(0.5, RULE))
    cborders(c, left=(0.5, RULE))
    cmargins(a, right=0.3)
    cmargins(b, left=0.3, right=0.3)
    cmargins(c, left=0.3)
    para(a, "Crónicas de ciudad", style='LC Etiqueta')
    n = table(a, [5.0, 3.7])
    n0, n1 = n.rows[0].cells
    cmargins(n0, right=0.25)
    para(n0, "La niñez que trabaja en la plaza de mercado", style='LC Titular4R', size=14, line=15.5)
    picture(n1, IMG + "miniatura_ninez.png", 3.6, align=AL.RIGHT)
    ref(para(a, "Bourdieu y Passeron y el trabajo infantil que se hereda como destino. Columna 5, 29 de "
                "septiembre", before=2), "P6")
    para(b, "Fronteras invisibles en los barrios", style='LC Titular4R', size=14, line=15.5)
    ref(para(b, "Shaw y McKay ante el desplazamiento intraurbano por combos. Columna 4, 22 de septiembre"), "P6")
    para(c, "Próxima edición", style='LC EtiquetaAzul')
    para(c, "Habitantes de calle y enfoque de capacidades", style='LC Titular4R', size=14, line=15.5)
    ref(para(c, "Sen y Nussbaum en los corredores urbanos. Columna 3, 15 de septiembre"), "P6")
    p = para(c, "Cronograma del curso y fuentes", style='LC Titular5R', before=4)
    pborder(p, top=(0.5, RULE, 4))
    ref(p, "P6")


# ============================================================ PÁGINA 2 · EDITORIAL GENERAL
def editorial(doc):
    s = seccion(doc)
    encabezado(s, W)
    cintillo(doc, "Opinión", "Editorial general", "COLUMNA 1", "Sesión 1 · 8 de septiembre de 2026", W)
    tit = "Sin teoría, la crisis es solo ruido"
    sz = ajustar(tit, HEAVY, W, 1, 42, 28)
    para(doc, tit, style='LC TitularGrande', size=sz, line=sz * 1.15, before=3)
    para(doc, "Presentamos LA CUESTIÓN, un periódico que lee los problemas sociales de Colombia con las "
              "herramientas de la teoría sociológica y la mirada del Trabajo Social Crítico.", style='LC Deck')
    para(doc, "Editorial · Mesa de redacción", style='LC Firma', after=5)
    t = table(doc, [11.9, 7.29])
    L, R = t.rows[0].cells
    cmargins(L, right=0.35)
    picture(L, IMG + "editorial_lente.png", 10.9, align=AL.LEFT)
    p = para(L, "El lente sociológico: lo que a simple vista es paisaje gris, bajo la teoría aparece como problema "
                "con causas, actores y responsables. ", style='LC PieFoto')
    runs(p, "ILUSTRACIÓN: LA CUESTIÓN", font=OS, size=6, color=GREY)
    shade(R, CREAM)
    cborders(R, top=(3, BLUE))
    cmargins(R, top=0.2, left=0.3, right=0.3, bottom=0.15)
    para(R, "Mesa de redacción", style='LC CajaTitulo')
    for cargo in ("Dirección editorial", "Edición y corrección de estilo", "Investigación y verificación de fuentes",
                  "Diseño, ilustración y tira cómica"):
        para(R, f"**{cargo}**\n[Nombre y apellido del integrante]", style='LC CajaTexto')
    p = para(R, "**Curso:** Problemas sociales contemporáneos\n**Docente:** Allison Paola Escobar\n"
                "**Modalidad:** trabajo grupal", style='LC CajaTexto', before=3)
    pborder(p, top=(0.5, RULE, 4))
    cols = columnas(doc, 3, W, gap=0.5)
    k0, k1, k2 = cols.rows[0].cells
    para(k0, "Por qué este periódico", style='LC Ladillo', before=8)
    para(k0, "Colombia no carece de noticias sobre sus problemas sociales. Cada semana se informa sobre personas "
             "que viven en la calle, barrios donde un combo decide quién entra y quién sale, o niños que venden "
             "dulces en los semáforos. Lo que escasea es la explicación. La prensa sensacionalista narra el drama; "
             "la política pública tradicional lo convierte en metas y cifras. Ambas suelen quedarse en la "
             "superficie.", style='LC CuerpoG')
    para(k0, "LA CUESTIÓN nace para ocupar ese espacio. Tomamos el nombre de una idea de Oszlak y O’Donnell que "
             "Francisco M. Suárez (1989) retoma: una *cuestión socialmente problematizada* es un asunto que ciertos "
             "actores logran poner en la agenda porque creen que «puede y debe hacerse algo al respecto».",
         style='LC CuerpoG')
    para(k1, "Por qué la teoría es indispensable", style='LC Ladillo', before=8)
    para(k1, "La teoría no es un adorno académico: es la herramienta que permite pasar del síntoma a la causa. Sin "
             "ella, la pobreza parece un asunto de individuos que no se esfuerzan, la violencia barrial un tema "
             "exclusivo de policía y el trabajo infantil una decisión de familias irresponsables.", style='LC CuerpoG')
    para(k1, "Las teorías del curso rompen ese sentido común. Las capacidades de Sen y Nussbaum preguntan qué "
             "libertades reales tiene una persona; la desorganización social de Shaw y McKay muestra cómo el "
             "debilitamiento de los lazos comunitarios facilita el control territorial, y la reproducción social de "
             "Bourdieu y Passeron revela cómo las instituciones convierten la desigualdad heredada en destino.",
         style='LC CuerpoG')
    para(k2, "Cómo leer cada columna", style='LC Ladillo', before=8)
    para(k2, "Cada columna sigue la misma ruta: un titular de impacto; un subtítulo que ubica el fenómeno y la "
             "teoría; una caja de glosario con tres conceptos clave; la crónica del problema en Colombia, con "
             "fuentes verificables; el lente sociológico, que explica sus causas profundas; el punto ciego de los "
             "análisis tradicionales, y una conclusión con una recomendación de intervención desde el Trabajo "
             "Social Crítico.", style='LC CuerpoG')
    p = para(k2, "«Las cifras dicen cuánto. La teoría explica por qué. El Trabajo Social pregunta qué hacer y con "
                 "quién.»", style='LC Destacado')
    pborder(p, top=(1.5, BLUE, 5), bottom=(1.5, BLUE, 5))
    espacio(doc, 8)
    textos = [("Público objetivo", "Estudiantes y profesionales de Trabajo Social y ciencias sociales, servidores "
               "públicos que diseñan o ejecutan programas sociales, organizaciones comunitarias y lectores que "
               "quieren entender los problemas del país más allá del titular."),
              ("Estilo de redacción", "Periodístico-académico: titulares llamativos pero analíticos, lenguaje claro "
               "y sin sensacionalismo, datos de fuentes oficiales y académicas verificables, y citación en normas "
               "APA (7.ª edición). Opinamos con argumentos, no con adjetivos."),
              ("Objetivo del periódico", "Analizar problemas sociales contemporáneos de Colombia desde matrices "
               "teóricas de la sociología, identificar lo que ignoran la prensa sensacionalista y la política "
               "pública tradicional, y proponer intervenciones críticas, éticas y viables desde el Trabajo Social.")]
    for cell, (h, txt) in zip(cajas(doc, W), textos):
        para(cell, h, style='LC CajaTitulo')
        para(cell, txt, style='LC CajaTexto', after=0)


# ============================================================ PÁGINA 3 · COLUMNA 2 (SUÁREZ)
def columna_suarez(doc):
    seccion(doc)  # hereda encabezado de la página 2
    cintillo(doc, "Análisis", "Columna 2 · Teórico-metodológica", "LECTURA BASE",
             "Francisco M. Suárez · CIDES, 1989", W)
    para(doc, "Políticas públicas · Diagnóstico de coyuntura", style='LC Antetitulo', before=6)
    tit = "El programa también es el problema"
    sz = ajustar(tit, HEAVY, W, 1, 38, 24)
    para(doc, tit, style='LC TitularGrande', size=sz, line=sz * 1.15, before=0)
    para(doc, "La pobreza monetaria cayó al 28,0 % en 2025, pero el paso del Sisbén al Registro Universal de "
              "Ingresos amenaza a casi la mitad de los hogares de Renta Ciudadana. Francisco M. Suárez permite "
              "separar el problema social del problema del programa que pretende resolverlo.",
         style='LC Deck', line=14.2)
    para(doc, "Mesa de redacción · Bogotá", style='LC Firma', after=3)
    t = table(doc, [12.7, 6.49])
    L, R = t.rows[0].cells
    cmargins(L, right=0.35)
    cmargins(R, left=0.35)
    cborders(R, left=(0.5, RULE))
    cols = columnas(L, 2, 12.35, gap=0.45)
    a, b = cols.rows[0].cells
    para(a, "La crónica del problema", style='LC Ladillo', before=0)
    para(a, "En junio de 2026 el DANE publicó una buena noticia: la pobreza monetaria pasó de 31,8 % en 2024 a "
            "28,0 % en 2025 (DANE, 2026). Según esa medición, cerca de 1,8 millones de personas dejaron de ser "
            "pobres por ingresos en un solo año.")
    para(a, "Dos meses después, la noticia fue otra. Prosperidad Social aplazó para septiembre el cuarto ciclo de "
            "pagos de Renta Ciudadana y Devolución del IVA, previsto para el 21 de agosto, mientras revisaba el "
            "paso del Sisbén al RUI, reglamentado por el Decreto 662 de 2026. La entidad advirtió que aplicar las "
            "nuevas reglas sin transición podría afectar a cerca del 49 % de los hogares de un programa que llega "
            "a unos 700.000 hogares (El Tiempo, 2026).")
    para(a, "El problema no es nuevo. El CONPES 3877 reconoció que los errores de inclusión del Sisbén III pasaron "
            "de 46,8 % en 2010 a 49,9 % en 2015 frente a la pobreza monetaria (DNP, 2016): el instrumento que "
            "debía identificar a los pobres había perdido capacidad para hacerlo.")
    para(a, "El lente sociológico", style='LC Ladillo')
    para(a, "Suárez (1989) define el problema social como una condición que afecta a un número significativo de "
            "personas, que se considera indeseable y que se cree corregible mediante la acción colectiva: una "
            "discrepancia entre un *estándar de deseabilidad* y una realidad observada.")
    para(b, "Su aporte decisivo es aplicar la misma lógica a los programas, cuyo funcionamiento real también "
            "puede alejarse de lo que deberían lograr. Esa distinción ordena el caso colombiano. La pobreza es el "
            "problema social; la focalización que "
            "excluye o incluye mal, la rigidez para adaptarse a un nuevo registro y la discontinuidad de los giros "
            "son problemas del programa. Suárez los nombra: cobertura insuficiente en extensión y en profundidad, "
            "rigidez ante los cambios del contexto, superposición de programas y vulnerabilidad institucional. Por "
            "eso la pobreza puede bajar en la encuesta mientras la protección de los hogares más frágiles se "
            "debilita.")
    p = para(b, "«No todo problema social se convierte en una cuestión socialmente problematizada»",
             style='LC Destacado', before=4, after=4, size=12.5, line=15)
    pborder(p, top=(1.5, BLUE, 4), bottom=(1.5, BLUE, 4))
    para(b, "El punto ciego", style='LC Ladillo')
    para(b, "La prensa sensacionalista cuenta el aplazamiento como un escándalo de «colados» o de pagos perdidos; "
            "la política pública tradicional lo trata como un ajuste técnico de bases de datos. Ambas miradas "
            "ignoran lo que Suárez advierte: un problema solo se vuelve *cuestión* cuando alguien logra ponerlo en "
            "la agenda, y los hogares en pobreza extrema rara vez tienen voz para hacerlo. Los errores de exclusión "
            "no hacen ruido: quien nunca entra a un programa no aparece en ninguna noticia.")
    # barra lateral: glosario, infografía, datos
    g = table(R, [6.14], pad=(0.16, 0.25, 0.1, 0.25))
    gc = g.rows[0].cells[0]
    shade(gc, CREAM)
    cborders(gc, top=(3, BLUE))
    para(gc, "Glosario teórico", style='LC CajaTitulo', after=2)
    for term, dfn in (("Problema social.", "Condición indeseable que afecta a un número significativo de personas "
                       "y que se cree corregible mediante la acción colectiva."),
                      ("Cuestión socialmente problematizada.", "Asunto que actores estratégicamente situados logran "
                       "poner en la agenda pública (Oszlak y O’Donnell, en Suárez, 1989)."),
                      ("Problema de programa.", "Distancia entre lo que un programa debería lograr y su "
                       "funcionamiento real: cobertura, rigidez, superposición o vulnerabilidad.")):
        para(gc, f"**{term}** {dfn}", style='LC CajaTexto', after=2.5)
    para(R, "Del problema a la política", style='LC CajaTitulo', before=6, after=2)
    pasos = [("1", "**Redefinición:** lo aislado se ve como un problema compartido."),
             ("2", "**Focalización** del descontento en aspectos salientes."),
             ("3", "**Atención pública**, sobre todo a través de los medios."),
             ("4", "**Grupos de presión** y movimientos sociales."),
             ("»", "**Cuestión:** debate sobre la política y sus programas.")]
    st = table(R, [0.7, 5.44], rows=len(pasos), pad=(0.04, 0.1, 0.04, 0.12))
    for i, (num, txt) in enumerate(pasos):
        x, y = st.rows[i].cells
        shade(x, BLUE if i < 4 else INK)
        shade(y, LBLUE if i < 4 else CREAM)
        for cc in (x, y):
            cc.vertical_alignment = VA.CENTER
            cborders(cc, bottom=(2.25, WHITE))
        para(x, num, style='LC Paso')
        para(y, txt, style='LC CajaTexto', after=0)
    para(R, "Datos clave", style='LC CajaTitulo', before=6, after=1)
    dt = table(R, [1.95, 4.19], rows=3, pad=(0.05, 0, 0.05, 0.1))
    for i, (cifra, txt) in enumerate((("28,0 %", "pobreza monetaria, 2025 (DANE, 2026)"),
                                      ("49 %", "hogares de Renta Ciudadana en riesgo (El Tiempo, 2026)"),
                                      ("49,9 %", "error de inclusión del Sisbén III, 2015 (DNP, 2016)"))):
        x, y = dt.rows[i].cells
        for cc in (x, y):
            cc.vertical_alignment = VA.CENTER
            cborders(cc, bottom=(0.5, RULE))
        para(x, cifra, style='LC Cifra')
        para(y, txt, style='LC CajaTexto', after=0)
    # conclusión
    c = table(doc, [W], pad=(0.18, 0.35, 0.16, 0.35)).rows[0].cells[0]
    shade(c, LBLUE)
    cborders(c, left=(4.5, BLUE))
    para(c, "Conclusión · Recomendación desde el Trabajo Social Crítico", style='LC CajaTitulo')
    para(c, "Recomendamos que la transición al RUI no se ejecute como un simple cruce de bases de datos, sino como "
            "un proceso participativo con tres componentes: **(1)** un periodo de transición que garantice la "
            "continuidad de los hogares en pobreza extrema mientras se verifica su situación en territorio; "
            "**(2)** mesas de revisión comunitaria y rutas de reclamación accesibles, acompañadas por "
            "trabajadoras y trabajadores sociales, para reducir los errores de exclusión, y **(3)** un seguimiento "
            "que mida por qué salen los hogares del registro y qué les ocurre después. "
            "Desde el Trabajo Social Crítico, el propósito no es depurar listas sino garantizar derechos: los "
            "hogares son sujetos con voz, no datos por validar.",
         style='LC CuerpoG', after=0)
    para(doc, "**Fuentes:** DANE (2026); DNP (2016); El Tiempo (2026); Suárez (1989). Referencias completas en la "
              "página 6.", style='LC Referencia', before=4, after=0)


# ============================================================ PÁGINA 4 · CRUCIGRAMA (horizontal)
PISTAS = {
    "HABITUS": "Para Bourdieu, sistema de disposiciones incorporadas que hace vivir la desigualdad como algo «natural».",
    "MASIVOS": "Así califica Suárez a los programas sociales de gran escala que analiza.",
    "NUSSBAUM": "Filósofa estadounidense que propuso una lista de capacidades humanas centrales.",
    "COBERTURA": "Problema de los programas que no llegan, en extensión ni en profundidad, a quienes más lo necesitan.",
    "CUESTION": "Problema social que logra entrar en la agenda pública, según Oszlak y O’Donnell.",
    "VULNERABILIDAD": "Tipo de problema social ligado a riesgos del ciclo vital, cambios tecnológicos o catástrofes.",
    "SEN": "Economista indio, Nobel de Economía en 1998, creador del enfoque de capacidades.",
    "POBREZA": "Condición que, según el DANE, afectó al 28,0 % de la población colombiana en 2025.",
    "CIDES": "Sigla del Centro Interamericano para el Desarrollo Social, que publicó el texto de Suárez.",
    "DESVIACION": "Problemas sociales ligados a la transgresión de normas vigentes, como la violencia urbana.",
    "OSZLAK": "Politólogo argentino que, con Guillermo O’Donnell, habló de «cuestiones socialmente problematizadas».",
    "ANOMIA": "Término de Durkheim para el debilitamiento de las normas que regulan la conducta social.",
    "BOURDIEU": "Sociólogo francés que escribió con Passeron *La reproducción* (1970).",
    "SUAREZ": "Autor de «Problemas sociales y problemas de programas sociales masivos»: Francisco M. ___.",
    "PROGRAMA": "Según Suárez, las políticas se plasman en un conjunto de ellos y estos, a su vez, en proyectos.",
    "CARENCIALIDAD": "Tipo de problema social referido a necesidades básicas insatisfechas: alimentación, vivienda, salud.",
    "BUROCRATIZACION": "Proceso que, junto con la dependencia de la población, vuelve permanentes a los programas.",
    "OBSOLESCENCIA": "Falta de actualización de las tecnologías y estructuras de un programa frente al estado del arte.",
    "PARTICIPACION": "Problemas de exclusión, pseudoparticipación o aislamiento en la tipología de Suárez.",
    "ESTANDAR": "La situación problemática es la distancia entre la realidad observada y un ___ de deseabilidad.",
    "IDENTIDAD": "Problemas asociados al desarraigo, las relocalizaciones o la aculturación forzosa.",
    "COMBOS": "Estructuras armadas barriales que ejercen control territorial en ciudades como Medellín.",
    "SHAW": "Clifford R. ___, coautor con Henry D. McKay de la teoría de la desorganización social.",
}


def crucigrama(doc):
    s = seccion(doc, landscape=True)
    encabezado(s, WL)
    data = json.load(open(CRUCI, encoding="utf8"))
    H, Wg, grid = data["H"], data["W"], data["grid"]
    total = len(data["across"]) + len(data["down"])
    cintillo(doc, "Pasatiempos", "El crucigrama de la cuestión social", f"{total} CONCEPTOS",
             "Lectura de Suárez y teorías del curso", WL)
    para(doc, "Pon a prueba tu lente sociológico con conceptos de Suárez y de las teorías de las próximas ediciones. "
              "Escribe sin tildes, una letra por casilla.", style='LC Deck', before=4, after=5, size=11, line=13.5)
    t = table(doc, [12.9, 0.6, 12.04])
    L, _, R = t.rows[0].cells
    cell = 0.66
    g = table(L, [cell] * Wg, rows=H, pad=(0, 0.03, 0, 0.02))
    for r in range(H):
        row = g.rows[r]
        row_exact(row, cell)
        cells = row.cells
        for c in range(Wg):
            ce = cells[c]
            if grid[r][c] is None:
                shade(ce, CREAM)
            else:
                shade(ce, WHITE)
                box(ce, 0.75, INK)
                num = data["nums"].get(f"{r},{c}")
                if num:
                    para(ce, str(num), style='LC Celda')
    para(L, "Las casillas numeradas marcan el inicio de cada palabra. Entre paréntesis, el número de letras.",
         style='LC Pie', before=3)
    k = table(R, [5.72, 0.6, 5.72])
    h, _, v = k.rows[0].cells
    for col, titulo, items in ((h, "Horizontales", data["across"]), (v, "Verticales", data["down"])):
        p = para(col, titulo, style='LC CajaTitulo')
        pborder(p, bottom=(1.5, BLUE, 2))
        for num, word in items:
            para(col, f"**{num}.** {PISTAS[word]} ({len(word)})", style='LC Pista')
    sab = table(L, [12.9], pad=(0.12, 0.3, 0.1, 0.3)).rows[0].cells[0]
    shade(sab, CREAM)
    cborders(sab, top=(3, BLUE))
    para(sab, "¿Sabías que...?", style='LC CajaTitulo', after=1)
    para(sab, "El DANE mide la pobreza con la clasificación que propuso Amartya Sen en 1981: la medición directa "
              "evalúa privaciones; la indirecta, la capacidad de adquirir bienes y servicios (DANE, 2026).",
         style='LC CajaTexto', after=0)
    sol_h = " · ".join(f"{n} {w}" for n, w in data["across"])
    sol_v = " · ".join(f"{n} {w}" for n, w in data["down"])
    para(doc, f"**SOLUCIÓN** (no la mires antes de terminar)  Horizontales: {sol_h}.  Verticales: {sol_v}.",
         style='LC Pie', before=5, size=6.5, line=8)


# ============================================================ PÁGINA 5 · TIRA CÓMICA
VINETAS = [
    ([("n", "1 · Corredor de la avenida del río, 6:00 a. m. Hace cuatro años don Ramiro duerme bajo este puente. "
             "Nadie lo ve.")], "tira_vineta1.png"),
    ([("d", "**REPORTERA:** ¡Última hora! ¡Crisis en el corredor! ¿Quién tiene la culpa?"),
      ("d", "**DON RAMIRO:** ¿Crisis? Yo llevo aquí cuatro años...")], "tira_vineta2.png"),
    ([("n", "3 · Esa tarde, en rueda de prensa..."),
      ("d", "**EL DOCTOR CIFRA:** ¡Lanzamos Calle Cero! Meta: cero habitantes de calle en 30 días.")], "tira_vineta3.png"),
    ([("d", "**LUCÍA, TRABAJADORA SOCIAL:** Salió en el noticiero y ya hay programa: ahora es una «cuestión "
             "socialmente problematizada». ¿Alguien le preguntó a don Ramiro?")], "tira_vineta4.png"),
    ([("n", "5 · Tres meses después..."),
      ("d", "**DON RAMIRO:** Vinieron, me tomaron una foto y se fueron. Dicen que se acabó la plata.")], "tira_vineta5.png"),
    ([("d", "**LUCÍA:** El problema no era solo la calle: era un programa sin cobertura real, rígido y sin "
             "presupuesto estable. Empecemos por escucharlo."),
      ("d", "**DON RAMIRO:** Por fin alguien pregunta.")], "tira_vineta6.png"),
]


def tira(doc):
    s = seccion(doc)
    encabezado(s, W)
    cintillo(doc, "Humor gráfico", "Tira cómica", "GUION Y DIBUJO", "Mesa de redacción de LA CUESTIÓN", W)
    para(doc, "Calle Cero", style='LC TitularGrande', size=28, line=32, before=2, after=0)
    para(doc, "Un problema social se vuelve noticia, luego programa y otra vez olvido.", style='LC Deck', after=5)
    pw, gap = 7.7, 0.45
    t = table(doc, [pw, gap, pw], rows=5, center=True)
    for i in (1, 3):
        row_exact(t.rows[i], 0.28)
    for idx, (lines, img) in enumerate(VINETAS):
        ce = t.cell(idx // 2 * 2, idx % 2 * 2)
        box(ce, 2.25, INK)
        cmargins(ce, top=0, left=0, right=0, bottom=0)
        for j, (kind, text) in enumerate(lines):
            if kind == "d" and j == 0:
                text = f"{idx + 1} · " + text
            p = para(ce, text, style='LC Narrador' if kind == "n" else 'LC Dialogo', indent=0.15,
                     before=3 if j == 0 else 0)
            if kind == "n":
                pshade(p, YEL)
        picture(ce, IMG + img, pw - 0.1, before=2)
    espacio(doc, 5)
    claves = [("Viñetas 1 y 2 · De problema a cuestión", "Una condición de años solo se vuelve «cuestión» cuando "
               "captura la atención pública a través de los medios (Suárez, 1989)."),
              ("Viñetas 3 y 4 · La meta como espectáculo", "Un programa hecho bajo presión mediática promete "
               "resultados sin diagnóstico ni participación."),
              ("Viñetas 5 y 6 · Problemas del programa", "Cobertura insuficiente, rigidez y financiamiento "
               "discontinuo: la vulnerabilidad del programa se suma a la de quien vive en la calle.")]
    for cell, (h, txt) in zip(cajas(doc, W), claves):
        para(cell, h, style='LC CajaTitulo', size=9)
        para(cell, txt, style='LC CajaTexto', after=0)


# ============================================================ PÁGINA 6 · AGENDA Y FUENTES
REFERENCIAS = [
    "Bourdieu, P., y Passeron, J.-C. (1970). *La reproduction: Éléments pour une théorie du système "
    "d’enseignement*. Les Éditions de Minuit.",
    "Departamento Administrativo Nacional de Estadística [DANE]. (2026, 12 de junio). *Pobreza monetaria en "
    "Colombia. Año 2025* [Boletín técnico]. https://www.dane.gov.co/files/operaciones/PM/bol-PM-2025.pdf",
    "Departamento Nacional de Planeación [DNP]. (2016). *Documento CONPES 3877: Declaración de importancia "
    "estratégica del Sistema de Identificación de Potenciales Beneficiarios (Sisbén IV)*. "
    "https://colaboracion.dnp.gov.co/CDT/Conpes/Económicos/3877.pdf",
    "El Tiempo. (2026, 28 de agosto). Reprograman pagos de Renta Ciudadana y Devolución del IVA en septiembre de "
    "2026 por revisión técnica del RUI. *El Tiempo*. https://www.eltiempo.com/economia/finanzas-personales/"
    "reprograman-pagos-de-renta-ciudadana-y-devolucion-del-iva-en-septiembre-de-2026-por-revision-tecnica-del-"
    "rui-razones-fechas-y-todo-lo-que-debe-saber-3581738",
    "Nussbaum, M. C. (2012). *Crear capacidades: Propuesta para el desarrollo humano*. Paidós.",
    "Sen, A. (2000). *Desarrollo y libertad*. Planeta.",
    "Shaw, C. R., y McKay, H. D. (1942). *Juvenile delinquency and urban areas*. University of Chicago Press.",
    "Suárez, F. M. (1989). *Problemas sociales y problemas de programas sociales masivos*. Centro Interamericano "
    "para el Desarrollo Social (CIDES); CEPAL. https://repositorio.cepal.org/handle/11362/33446",
]


def agenda(doc):
    seccion(doc)  # hereda encabezado de la página 5
    cintillo(doc, "Agenda", "Próximas ediciones y fuentes", "CONTRAPORTADA", "Cronograma académico 2026", W)
    para(doc, "Lo que viene en LA CUESTIÓN", style='LC TitularGrande', size=28, line=33, before=6, after=6)
    cards = [("miniatura_calle.png", "15 de septiembre · Columna 3", "Habitantes de calle concentrados en corredores "
              "urbanos", "Teoría del Desarrollo Humano · Amartya Sen y Martha Nussbaum",
              "El enfoque de capacidades desplaza la pregunta del ingreso a lo que las personas pueden efectivamente "
              "ser y hacer.", "¿Qué capacidades niega la vida en los corredores urbanos y quién debe garantizarlas?"),
             ("miniatura_combos.png", "22 de septiembre · Columna 4", "Desplazamiento intraurbano por control "
              "territorial de combos", "Teoría de la Desorganización Social · Clifford R. Shaw y Henry D. McKay",
              "Shaw y McKay mostraron que la delincuencia se concentra en territorios con lazos comunitarios "
              "debilitados, más allá de quiénes los habiten.",
              "¿Qué condiciones del barrio, y no solo de las personas, permiten que un combo decida quién se va?"),
             ("miniatura_ninez.png", "29 de septiembre · Columna 5", "Niñez trabajando en las plazas de mercado y "
              "semáforos", "Teoría de la Reproducción Social · Pierre Bourdieu y Jean-Claude Passeron",
              "Para Bourdieu y Passeron, la escuela tiende a reproducir las desigualdades de capital cultural y a "
              "legitimarlas como mérito individual.",
              "¿Cómo se hereda el trabajo infantil y qué papel juega la escuela en romper ese ciclo?")]
    gap = 0.4
    each = (W - 2 * gap) / 3
    t = table(doc, [each, gap, each, gap, each])
    for i, (img, kicker, title, theory, teaser, question) in enumerate(cards):
        c = t.rows[0].cells[i * 2]
        picture(c, IMG + img, each, align=AL.LEFT)
        para(c, kicker, style='LC EtiquetaAzul', before=4, size=9)
        para(c, title, style='LC Titular5', after=2, size=13, line=14.5)
        para(c, theory, style='LC Firma', after=3)
        para(c, teaser, style='LC Cuerpo', align=AL.LEFT)
        para(c, f"**Pregunta guía:** {question}", style='LC Cuerpo', align=AL.LEFT, after=0)
    t = table(doc, [11.8, 0.4, 6.99])
    L, _, R = t.rows[0].cells
    p = para(L, "Cronograma académico", style='LC CajaTitulo', before=6)
    pborder(p, bottom=(1.5, BLUE, 2))
    filas = [("Sesión", "Fecha", "Columna y problema social", "Teoría y autores"),
             ("1", "8/9/2026", "Columna 1: editorial general. Columna 2: análisis teórico-metodológico",
              "Lectura base: Francisco M. Suárez (CIDES)"),
             ("2", "15/9/2026", "Columna 3: habitantes de calle en corredores urbanos", "Desarrollo Humano: Sen y Nussbaum"),
             ("3", "22/9/2026", "Columna 4: desplazamiento intraurbano por combos", "Desorganización Social: Shaw y McKay"),
             ("4", "29/9/2026", "Columna 5: niñez trabajando en plazas y semáforos", "Reproducción Social: Bourdieu y Passeron"),
             ("5", "6/10/2026", "Sustentación", "—")]
    ct = table(L, [1.25, 1.75, 4.8, 4.0], rows=len(filas), pad=(0.05, 0.08, 0.05, 0.08))
    for i, fila in enumerate(filas):
        for j, txt in enumerate(fila):
            ce = ct.cell(i, j)
            ce.vertical_alignment = VA.CENTER
            if i == 0:
                shade(ce, BLUE)
                para(ce, txt, style='LC TablaEnc')
            else:
                if i % 2 == 0:
                    shade(ce, CREAM)
                cborders(ce, bottom=(0.5, RULE))
                para(ce, txt, style='LC TablaTxt', bold=True if j < 2 else None)
    R.vertical_alignment = VA.BOTTOM
    cc = table(R, [6.99], pad=(0.2, 0.3, 0.15, 0.3)).rows[0].cells[0]
    shade(cc, CREAM)
    cborders(cc, top=(3, BLUE))
    para(cc, "Cartas a la redacción", style='LC CajaTitulo')
    para(cc, "¿Conoces un programa social que llegó tarde, llegó mal o nunca llegó? Escríbenos: la próxima "
             "cuestión puede salir de tu barrio.", style='LC CajaTexto')
    para(cc, "**Correo:** [correo del grupo]", style='LC CajaTexto')
    p = para(cc, "**Cómo citar:** Mesa de redacción. (2026, 8 de septiembre). *LA CUESTIÓN*, (1). Curso Problemas "
                 "sociales contemporáneos.", style='LC CajaTexto', before=3, after=0)
    pborder(p, top=(0.5, RULE, 4))
    p = para(doc, "Referencias", style='LC CajaTitulo', before=6)
    pborder(p, bottom=(1.5, BLUE, 2))
    rc = columnas(doc, 2, W, gap=0.45)
    half = 3   # las tres primeras son las más largas
    for i, rtxt in enumerate(REFERENCIAS):
        para(rc.rows[0].cells[0 if i < half else 1], rtxt, style='LC Referencia')
    para(doc, "Todas las ilustraciones y la tira cómica de esta edición son originales de la mesa de redacción. "
              "Tipografías libres (SIL Open Font License): Newsreader y Oswald.",
         style='LC Pie', before=6, align=AL.CENTER)


# ============================================================ incrustación de fuentes
NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"


def ofuscar(data, guid):
    """ECMA-376 §17.8.1: XOR de los primeros 32 bytes con la clave GUID invertida."""
    key = bytes.fromhex(guid.strip("{}").replace("-", ""))[::-1]
    b = bytearray(data)
    for i in range(32):
        b[i] ^= key[i % 16]
    return bytes(b)


def incrustar_fuentes(src, dst):
    with zipfile.ZipFile(src) as z:
        order = z.namelist()
        files = {n: z.read(n) for n in order}
    wq = lambda t: f"{{{NS_W}}}{t}"
    ft = etree.fromstring(files["word/fontTable.xml"])
    rels_name = "word/_rels/fontTable.xml.rels"
    rels = etree.fromstring(files[rels_name]) if rels_name in files else \
        etree.Element(f"{{{NS_PR}}}Relationships", nsmap={None: NS_PR})
    for n, (family, archivo) in enumerate(ARCHIVOS.items(), 1):
        for old in ft.findall(wq("font")):
            if old.get(wq("name")) == family:
                ft.remove(old)
        f = etree.SubElement(ft, wq("font"))
        f.set(wq("name"), family)
        for tag, val in (("charset", "00"), ("family", "swiss" if family.startswith(OS) else "roman"),
                         ("pitch", "variable")):
            etree.SubElement(f, wq(tag)).set(wq("val"), val)
        guid = "{" + str(uuid.uuid4()).upper() + "}"
        part = f"fonts/font{n}.odttf"
        files["word/" + part] = ofuscar(open(FUENTES + archivo, "rb").read(), guid)
        order.append("word/" + part)
        r = etree.SubElement(rels, f"{{{NS_PR}}}Relationship")
        r.set("Id", f"rIdFuente{n}")
        r.set("Type", NS_R + "/font")
        r.set("Target", part)
        e = etree.SubElement(f, wq("embedRegular"))
        e.set(f"{{{NS_R}}}id", f"rIdFuente{n}")
        e.set(wq("fontKey"), guid)
    files["word/fontTable.xml"] = etree.tostring(ft, xml_declaration=True, encoding="UTF-8", standalone=True)
    if rels_name not in files:
        order.append(rels_name)
    files[rels_name] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
    ct = etree.fromstring(files["[Content_Types].xml"])
    if not any(d.get("Extension") == "odttf" for d in ct.findall(f"{{{NS_CT}}}Default")):
        d = etree.Element(f"{{{NS_CT}}}Default")
        d.set("Extension", "odttf")
        d.set("ContentType", "application/vnd.openxmlformats-officedocument.obfuscatedFont")
        ct.insert(0, d)
    files["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)
    st = etree.fromstring(files["word/settings.xml"])
    if st.find(wq("embedTrueTypeFonts")) is None:
        antes = {"writeProtection", "view", "zoom", "removePersonalInformation", "removeDateAndTime",
                 "doNotDisplayPageBoundaries", "displayBackgroundShape", "printPostScriptOverText",
                 "printFractionalCharacterWidth", "printFormsData"}
        idx = 0
        for i, ch in enumerate(st):
            if etree.QName(ch).localname in antes:
                idx = i + 1
        st.insert(idx, etree.Element(wq("embedTrueTypeFonts")))
    dts = st.find(wq("defaultTabStop"))
    if dts is not None and st.find(wq("autoHyphenation")) is None:
        dts.addnext(etree.Element(wq("autoHyphenation")))       # separación silábica en columnas estrechas
    files["word/settings.xml"] = etree.tostring(st, xml_declaration=True, encoding="UTF-8", standalone=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ["[Content_Types].xml"] + [x for x in order if x != "[Content_Types].xml"]:
            z.writestr(name, files[name])
    print(f"   {len(ARCHIVOS)} fuentes incrustadas")


# ============================================================ principal
def main():
    os.makedirs(TMP, exist_ok=True)
    doc = Document()
    estilos(doc)
    cp = doc.core_properties
    cp.title, cp.subject = "LA CUESTIÓN · Periódico de análisis social", "Actividad 1 · Problemas sociales contemporáneos"
    cp.author, cp.language, cp.keywords = "Mesa de redacción", "es-CO", "problemas sociales; Suárez; Trabajo Social"
    print("Portada");            portada(doc)
    print("Editorial general");  editorial(doc)
    print("Columna 2 · Suárez"); columna_suarez(doc)
    print("Crucigrama");         crucigrama(doc)
    print("Tira cómica");        tira(doc)
    print("Agenda y fuentes");   agenda(doc)
    doc.save(BORRADOR)
    incrustar_fuentes(BORRADOR, SALIDA)
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
