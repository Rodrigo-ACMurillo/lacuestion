# -*- coding: utf-8 -*-
"""Ilustraciones del periódico LA CUESTIÓN (portada, tira cómica, miniaturas)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import math, random

SS = 3
FUENTES = "L:/periodico/fuentes/"
OUT = "L:/periodico/imagenes/"

INK = (30, 28, 34); PAPER = (247, 242, 232); BLUE = (31, 111, 178); RED = (196, 52, 44)
ORANGE = (236, 140, 60); YELLOW = (246, 200, 84); GREEN = (92, 150, 88); WHITE = (255, 255, 255)
SKIN = [(236, 190, 150), (196, 140, 100), (150, 100, 70)]
HAIR = {"dark": (45, 35, 32), "brown": (100, 62, 40), "grey": (170, 168, 165), "black": (25, 22, 25)}


def F(name, size):
    return ImageFont.truetype(FUENTES + name, int(size * SS))


class Art:
    def __init__(self, w, h, bg=PAPER):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w * SS, h * SS), bg + (255,))
        self.d = ImageDraw.Draw(self.img)

    def S(self, v): return int(round(v * SS))
    def P(self, pts): return [(self.S(x), self.S(y)) for x, y in pts]

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=0, r=0):
        box = [self.S(x0), self.S(y0), self.S(x1), self.S(y1)]
        if r:
            self.d.rounded_rectangle(box, radius=self.S(r), fill=fill, outline=outline, width=self.S(width))
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=self.S(width))

    def ell(self, cx, cy, rx, ry, fill=None, outline=None, width=0):
        self.d.ellipse([self.S(cx - rx), self.S(cy - ry), self.S(cx + rx), self.S(cy + ry)],
                       fill=fill, outline=outline, width=self.S(width))

    def poly(self, pts, fill=None, outline=None, width=0):
        self.d.polygon(self.P(pts), fill=fill, outline=outline, width=self.S(width) if outline else 1)

    def line(self, pts, fill, width, caps=True):
        self.d.line(self.P(pts), fill=fill, width=self.S(width), joint="curve")
        if caps:
            for x, y in (pts[0], pts[-1]):
                self.ell(x, y, width / 2, width / 2, fill)

    def sline(self, pts, fill, width, ow=3, oc=INK):
        self.line(pts, oc, width + 2 * ow)
        self.line(pts, fill, width)

    def arc(self, cx, cy, rx, ry, a0, a1, fill, width):
        self.d.arc([self.S(cx - rx), self.S(cy - ry), self.S(cx + rx), self.S(cy + ry)], a0, a1,
                   fill=fill, width=self.S(width))

    def chord(self, cx, cy, rx, ry, a0, a1, fill, outline=None, width=0):
        self.d.chord([self.S(cx - rx), self.S(cy - ry), self.S(cx + rx), self.S(cy + ry)], a0, a1,
                     fill=fill, outline=outline, width=self.S(width))

    def text(self, x, y, s, font, fill, anchor="la"):
        self.d.text((self.S(x), self.S(y)), s, font=font, fill=fill, anchor=anchor)

    def vgrad(self, x0, y0, x1, y1, c0, c1):
        for yy in range(self.S(y0), self.S(y1)):
            t = (yy - self.S(y0)) / max(1, self.S(y1) - self.S(y0))
            c = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
            self.d.line([(self.S(x0), yy), (self.S(x1), yy)], fill=c)

    def _composite(self, layer):
        self.img.alpha_composite(layer)
        self.d = ImageDraw.Draw(self.img)

    def glow(self, cx, cy, r, color, alpha=150):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([self.S(cx - r), self.S(cy - r), self.S(cx + r), self.S(cy + r)],
                                      fill=color + (alpha,))
        self._composite(layer.filter(ImageFilter.GaussianBlur(self.S(r * 0.45))))

    def translucent(self, pts, color, alpha):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).polygon(self.P(pts), fill=color + (alpha,))
        self._composite(layer.filter(ImageFilter.GaussianBlur(self.S(6))))

    def frame(self, width=7):
        self.rect(0, 0, self.w, self.h, outline=INK, width=width)

    def result(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS).convert("RGB")

    def save(self, name):
        self.result().save(OUT + name, dpi=(300, 300))
        print("  imagen:", name)


# ---------------------------------------------------------------- personajes
def person(a, x, y, h, shirt=BLUE, pants=(60, 64, 80), skin=SKIN[0], hair=("short", "dark"), face="neutral",
           look=0, larm=None, rarm=None, legs="stand", glasses=False, beard=None, tie=None, sil=None,
           shoes=INK, sit_dir=1, brows=None, hat=None):
    """Dibuja una persona; (x, y) = pies (o asiento si legs='sit'); h = estatura en px."""
    ow = max(2.0, h * 0.007)
    oc = sil or INK
    if sil:
        shirt = pants = skin = shoes = sil
    r = h * 0.09
    hip_y = y if legs == "sit" else y - h * 0.46
    sh_y = hip_y - h * 0.30
    hx, hy = x, sh_y - h * 0.02 - r * 0.95
    sw, hw = h * 0.125, h * 0.095
    lw = h * 0.078
    if legs == "stand":
        L = [(x - hw * 0.5, hip_y), (x - hw * 0.55, y - lw * 0.4)]
        R = [(x + hw * 0.5, hip_y), (x + hw * 0.55, y - lw * 0.4)]
    elif legs == "walk":
        L = [(x - hw * 0.4, hip_y), (x - h * 0.06, y - h * 0.22), (x - h * 0.14, y - lw * 0.4)]
        R = [(x + hw * 0.4, hip_y), (x + h * 0.05, y - h * 0.23), (x + h * 0.10, y - lw * 0.4)]
    else:
        d = sit_dir
        L = [(x - hw * 0.4, hip_y), (x + d * h * 0.19, hip_y + h * 0.01), (x + d * h * 0.21, hip_y + h * 0.23)]
        R = [(x + hw * 0.4, hip_y), (x + d * h * 0.23, hip_y + h * 0.01), (x + d * h * 0.26, hip_y + h * 0.23)]
    for leg in (L, R):
        a.sline(leg, pants, lw, ow, oc)
        fx, fy = leg[-1]
        dirx = sit_dir if legs == "sit" else (0.3 if leg is R else -0.3)
        a.ell(fx + dirx * lw * 0.45, fy + lw * 0.2, lw * 0.75, lw * 0.4, shoes, oc, ow)
    torso = [(x - sw, sh_y + h * 0.05), (x - sw * 0.75, sh_y), (x + sw * 0.75, sh_y), (x + sw, sh_y + h * 0.05),
             (x + hw * 1.08, hip_y + h * 0.02), (x - hw * 1.08, hip_y + h * 0.02)]
    a.poly(torso, shirt, oc, ow)
    if tie and not sil:
        a.poly([(x, sh_y + h * 0.01), (x + h * 0.018, sh_y + h * 0.04), (x + h * 0.012, sh_y + h * 0.2),
                (x, sh_y + h * 0.23), (x - h * 0.012, sh_y + h * 0.2), (x - h * 0.018, sh_y + h * 0.04)],
               tie, INK, ow * 0.6)
    aw = h * 0.062
    lsh, rsh = (x - sw * 0.82, sh_y + h * 0.035), (x + sw * 0.82, sh_y + h * 0.035)
    larm = larm or [(-0.035, 0.14), (-0.045, 0.28)]
    rarm = rarm or [(0.035, 0.14), (0.045, 0.28)]
    hands = []
    for sh, arm in ((lsh, larm), (rsh, rarm)):
        pts = [sh] + [(sh[0] + dx * h, sh[1] + dy * h) for dx, dy in arm]
        a.sline(pts, shirt, aw, ow, oc)
        a.ell(pts[-1][0], pts[-1][1], h * 0.032, h * 0.032, skin, oc, ow)
        hands.append(pts[-1])
    a.rect(hx - r * 0.3, hy + r * 0.6, hx + r * 0.3, sh_y + h * 0.01, skin)
    if hair[0] == "long" and not sil:
        a.rect(hx - r * 1.15, hy - r * 0.6, hx + r * 1.15, hy + r * 1.55, HAIR[hair[1]], oc, ow, r=r * 0.8)
    a.ell(hx, hy, r, r * 1.02, skin, oc, ow)
    hc = sil or HAIR[hair[1]]
    kind = hair[0]
    if kind in ("short", "long", "bun"):
        a.chord(hx, hy - r * 0.12, r * 1.06, r * 1.0, 180, 360, hc, oc, ow)
        a.poly([(hx - r * 1.04, hy - r * 0.12), (hx - r * 0.2, hy - r * 0.12), (hx - r * 0.9, hy + r * 0.25)], hc)
        if kind == "bun":
            a.ell(hx + r * 0.1, hy - r * 1.15, r * 0.42, r * 0.36, hc, oc, ow)
    elif kind == "bald":
        a.chord(hx - r * 0.93, hy - r * 0.05, r * 0.25, r * 0.45, 90, 270, hc)
        a.chord(hx + r * 0.93, hy - r * 0.05, r * 0.25, r * 0.45, 270, 90, hc)
    elif kind == "curly":
        for i in range(9):
            ang = math.pi + i * math.pi / 8
            a.ell(hx + math.cos(ang) * r * 0.85, hy - r * 0.1 + math.sin(ang) * r * 0.85, r * 0.33, r * 0.33, hc)
    if hat:
        a.chord(hx, hy - r * 0.2, r * 1.08, r * 1.0, 180, 360, hat, oc, ow)
        a.rect(hx - r * 1.1, hy - r * 0.32, hx + r * 1.1, hy - r * 0.12, hat, oc, ow * 0.8)
    if beard and not sil:
        a.chord(hx, hy + r * 0.12, r * 0.98, r * 0.92, 10, 170, HAIR[beard], oc, ow * 0.8)
    if not sil:
        ex, ey = r * 0.36, hy - r * 0.02
        lk = look * r * 0.14
        if face == "sleep":
            for s in (-1, 1):
                a.arc(hx + s * ex + lk, ey, r * 0.14, r * 0.08, 0, 180, INK, ow)
        else:
            for s in (-1, 1):
                a.ell(hx + s * ex + lk, ey, r * 0.095, r * 0.11, INK)
        if brows == "up":
            for s in (-1, 1):
                a.line([(hx + s * ex + lk - r * 0.14, ey - r * 0.32), (hx + s * ex + lk + r * 0.14, ey - r * 0.36)], INK, ow)
        elif brows == "worried":
            for s in (-1, 1):
                a.line([(hx + s * ex + lk - s * r * 0.16, ey - r * 0.24), (hx + s * ex + lk + s * r * 0.12, ey - r * 0.34)], INK, ow)
        elif brows == "skeptic":
            a.line([(hx - ex + lk - r * 0.14, ey - r * 0.26), (hx - ex + lk + r * 0.14, ey - r * 0.26)], INK, ow)
            a.line([(hx + ex + lk - r * 0.14, ey - r * 0.30), (hx + ex + lk + r * 0.16, ey - r * 0.42)], INK, ow)
        mx, my = hx + look * r * 0.12, hy + r * 0.42
        mouth_ink = (60, 50, 50) if beard else INK
        if face == "smile":
            a.arc(mx, my - r * 0.1, r * 0.3, r * 0.2, 20, 160, mouth_ink, ow * 1.1)
        elif face == "grin":
            a.chord(mx, my - r * 0.12, r * 0.34, r * 0.26, 0, 180, WHITE, INK, ow)
        elif face == "open":
            a.ell(mx, my, r * 0.14, r * 0.17, (120, 40, 40), INK, ow * 0.8)
        elif face == "shout":
            a.ell(mx, my, r * 0.24, r * 0.22, (120, 40, 40), INK, ow)
        elif face == "sad":
            a.arc(mx, my + r * 0.08, r * 0.24, r * 0.14, 200, 340, mouth_ink, ow * 1.1)
        elif face != "sleep":
            a.line([(mx - r * 0.18, my), (mx + r * 0.18, my)], mouth_ink, ow * 1.1)
        if glasses:
            for s in (-1, 1):
                a.ell(hx + s * ex + lk, ey, r * 0.24, r * 0.22, None, INK, ow * 0.9)
            a.line([(hx - ex + lk + r * 0.24, ey), (hx + ex + lk - r * 0.24, ey)], INK, ow * 0.8, caps=False)
    return {"lhand": hands[0], "rhand": hands[1], "head": (hx, hy), "r": r, "sh_y": sh_y, "hip_y": hip_y}


def sleeper(a, x, y, length, sil=None):
    """Persona dormida sobre cartón (x = extremo izquierdo, y = suelo)."""
    ow = 3
    oc = sil or INK
    a.poly([(x - 20, y), (x + length + 30, y), (x + length + 10, y - 16), (x - 5, y - 16)], sil or (176, 138, 92), oc, ow)
    if not sil:
        for i in range(4):
            a.line([(x + 30 + i * length / 4, y - 14), (x + 60 + i * length / 4, y - 2)], (150, 112, 70), 2, caps=False)
    r = length * 0.1
    a.poly([(x + r * 1.5, y - 16), (x + r * 1.7, y - r * 2.4), (x + length * 0.5, y - r * 2.9),
            (x + length * 0.95, y - r * 1.7), (x + length, y - 16)], sil or (122, 58, 62), oc, ow)
    if not sil:
        for px, py in ((0.35, 1.9), (0.62, 2.1)):
            a.rect(x + length * px, y - r * py, x + length * px + r * 0.9, y - r * py + r * 0.8, (170, 120, 60), INK, 2)
    a.ell(x + length + 8, y - 22, r * 0.5, r * 0.32, sil or INK, oc, ow)
    hx, hy = x + r * 0.9, y - r * 1.25
    a.ell(hx, hy, r, r, sil or SKIN[1], oc, ow)
    a.chord(hx, hy - r * 0.15, r * 1.08, r * 1.02, 170, 370, sil or (70, 110, 90), oc, ow)
    if not sil:
        a.chord(hx, hy + r * 0.15, r * 0.95, r * 0.85, 0, 180, HAIR["grey"], INK, 2)
        for s in (-1, 1):
            a.arc(hx + s * r * 0.36, hy + r * 0.05, r * 0.14, r * 0.08, 0, 180, INK, 2.5)


def cart(a, x, y, s=1.0, sil=None):
    oc = sil or INK
    for bx, by, rr, col in ((x + 20 * s, y - 95 * s, 26 * s, (60, 120, 170)), (x + 62 * s, y - 100 * s, 30 * s, (220, 220, 210)),
                            (x + 100 * s, y - 92 * s, 24 * s, (90, 90, 90)), (x + 45 * s, y - 128 * s, 22 * s, (200, 80, 60))):
        a.ell(bx, by, rr, rr, sil or col, oc, 2)
    a.poly([(x, y - 90 * s), (x + 130 * s, y - 90 * s), (x + 118 * s, y - 30 * s), (x + 14 * s, y - 30 * s)], None, oc, 4 * s)
    for i in range(1, 5):
        a.line([(x + i * 26 * s, y - 90 * s), (x + 12 * s + i * 23 * s, y - 30 * s)], oc, 2 * s, caps=False)
    a.line([(x + 130 * s, y - 90 * s), (x + 150 * s, y - 118 * s), (x + 170 * s, y - 118 * s)], oc, 5 * s)
    a.line([(x + 14 * s, y - 30 * s), (x + 2 * s, y - 14 * s), (x + 124 * s, y - 14 * s)], oc, 4 * s, caps=False)
    for wx in (x + 20 * s, x + 110 * s):
        a.ell(wx, y - 6 * s, 8 * s, 8 * s, oc)


def star(a, cx, cy, r1, r2, n, fill):
    pts = []
    for i in range(n * 2):
        rr = r1 if i % 2 == 0 else r2
        ang = i * math.pi / n - math.pi / 2
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    a.poly(pts, fill)


# ---------------------------------------------------------------- foto principal de portada
def escena_ciudad(W=1600, H=1000, seed=7):
    rnd = random.Random(seed)
    a = Art(W, H)
    a.vgrad(0, 0, W, 640, (36, 52, 98), (244, 160, 96))
    a.glow(1190, 500, 190, (255, 200, 130), 170)
    a.ell(1190, 500, 88, 88, (253, 222, 160))
    far = [(x, 430 + 55 * math.sin(x / 250) + 30 * math.sin(x / 91 + 1)) for x in range(0, W + 41, 40)]
    a.poly([(0, H)] + far + [(W, H)], (132, 92, 124))
    mtn = lambda x: 505 + 70 * math.sin(x / 330 + 2) + 28 * math.sin(x / 118)
    a.poly([(0, H)] + [(x, mtn(x)) for x in range(0, W + 21, 20)] + [(W, H)], (90, 64, 100))
    houses = []
    for _ in range(1300):
        hx = rnd.uniform(-10, W)
        top = mtn(hx) + 8
        if top > 700:
            continue
        houses.append((rnd.uniform(top, 715), hx))
    for hy, hx in sorted(houses):
        w, hh = rnd.uniform(14, 28), rnd.uniform(10, 19)
        t = (hy - 450) / 300
        base = rnd.choice([(158, 88, 84), (178, 108, 92), (132, 86, 98), (196, 138, 114), (116, 78, 94)])
        col = tuple(min(255, int(c * (0.8 + 0.25 * t))) for c in base)
        a.rect(hx, hy - hh, hx + w, hy, col)
        a.rect(hx - 1, hy - hh - 2, hx + w + 1, hy - hh + 1, tuple(max(0, c - 30) for c in col))
        if rnd.random() < 0.42:
            a.rect(hx + w * 0.35, hy - hh * 0.65, hx + w * 0.35 + 4, hy - hh * 0.65 + 5, (252, 212, 128))
    x = -10
    while x < W:
        bw = rnd.uniform(40, 110); bh = rnd.uniform(40, 150)
        a.rect(x, 760 - bh, x + bw, 780, (60, 48, 80))
        for _ in range(int(bw * bh / 900)):
            wx, wy = rnd.uniform(x + 4, x + bw - 8), rnd.uniform(760 - bh + 6, 770)
            if rnd.random() < 0.5:
                a.rect(wx, wy, wx + 4, wy + 5, (246, 196, 116))
        x += bw + rnd.uniform(-8, 6)
    # valla publicitaria con el eslogan roto
    a.rect(300, 560, 316, 700, (38, 32, 46)); a.rect(560, 560, 576, 700, (38, 32, 46))
    a.rect(230, 470, 650, 600, (38, 32, 46))
    a.rect(242, 482, 638, 588, (238, 232, 216))
    a.text(430, 492, "UN PAÍS QUE", F("Oswald-Bold.ttf", 34), BLUE, "ma")
    a.text(430, 532, "SÍ LLEGA", F("Oswald-Bold.ttf", 34), BLUE, "ma")
    a.text(252, 566, "Programa social", F("NewsreaderText-Italic.ttf", 14), (90, 90, 90))
    a.poly([(560, 588), (638, 588), (638, 520), (600, 556)], (38, 32, 46))
    a.poly([(560, 588), (600, 556), (610, 600), (585, 612)], (214, 206, 186), INK, 1.5)
    # metro sobre el viaducto
    a.rect(700, 646, 1270, 694, (212, 212, 222), INK, 2, r=10)
    a.rect(700, 676, 1270, 684, BLUE)
    for i in range(12):
        a.rect(724 + i * 45, 656, 752 + i * 45, 672, (255, 226, 150))
    a.rect(0, 692, W, 734, (40, 36, 58)); a.rect(0, 692, W, 698, (104, 92, 124))
    for px in (170, 560, 950, 1340):
        a.rect(px, 734, px + 48, 830, (46, 40, 64))
    # calle
    a.rect(0, 812, W, 906, (50, 46, 62))
    for lx in range(0, W, 120):
        a.rect(lx, 858, lx + 60, 864, (206, 178, 120))
    a.rect(0, 904, W, 916, (146, 134, 146)); a.rect(0, 916, W, H, (94, 86, 104))
    # farola
    a.translucent([(1400, 612), (1310, 916), (1560, 916)], (255, 214, 140), 70)
    a.line([(1470, 916), (1470, 600), (1400, 600)], (30, 28, 38), 10)
    a.glow(1400, 612, 70, (255, 214, 140), 200); a.ell(1400, 612, 16, 10, (255, 236, 190))
    # semáforo y carros detenidos
    a.line([(1010, 906), (1010, 640)], (30, 28, 38), 10)
    a.rect(990, 610, 1030, 710, (30, 28, 38), r=6)
    a.glow(1010, 628, 34, (255, 60, 50), 210); a.ell(1010, 628, 11, 11, (255, 90, 80))
    a.ell(1010, 660, 11, 11, (70, 60, 50)); a.ell(1010, 692, 11, 11, (70, 60, 50))
    for cx, cw in ((600, 250), (1080, 270)):
        a.rect(cx, 830, cx + cw, 890, (30, 28, 40), r=18)
        a.poly([(cx + cw * 0.2, 832), (cx + cw * 0.32, 792), (cx + cw * 0.72, 792), (cx + cw * 0.85, 832)], (30, 28, 40))
        a.poly([(cx + cw * 0.27, 830), (cx + cw * 0.35, 800), (cx + cw * 0.5, 800), (cx + cw * 0.5, 830)], (84, 90, 120))
        a.ell(cx + 50, 892, 22, 22, (15, 14, 20)); a.ell(cx + cw - 50, 892, 22, 22, (15, 14, 20))
        a.glow(cx + 6, 850, 22, (255, 50, 40), 200); a.rect(cx, 842, cx + 12, 858, (255, 80, 60))
    SIL = (24, 20, 32)
    # niño vendiendo dulces en el semáforo
    k = person(a, 960, 900, 150, sil=SIL, larm=[(-0.09, 0.08), (-0.14, 0.02)], rarm=[(0.09, 0.08), (0.14, 0.02)])
    a.rect(k["lhand"][0] - 4, k["lhand"][1] - 22, k["rhand"][0] + 4, k["lhand"][1] + 2, SIL)
    for i, col in enumerate([(230, 80, 70), (250, 200, 80), (90, 170, 230), (240, 240, 240)]):
        a.ell(k["lhand"][0] + 10 + i * 9, k["lhand"][1] - 26, 4, 4, col)
    # habitante de calle y peatones
    a.rect(236, 968, 520, 986, (120, 94, 70))
    sleeper(a, 250, 985, 250, sil=(34, 28, 42))
    cart(a, 540, 990, 0.9, sil=(30, 26, 38))
    p = person(a, 800, 995, 250, sil=SIL, legs="walk", rarm=[(0.02, 0.08), (0.02, -0.02)], larm=[(-0.05, 0.13), (-0.08, 0.26)])
    a.glow(p["rhand"][0] + 4, p["rhand"][1] - 8, 26, (170, 220, 255), 200)
    a.rect(p["rhand"][0] - 3, p["rhand"][1] - 18, p["rhand"][0] + 11, p["rhand"][1] + 2, (190, 230, 255))
    person(a, 1230, 998, 240, sil=SIL, legs="walk", larm=[(-0.06, 0.13), (-0.1, 0.24)], rarm=[(0.05, 0.13), (0.09, 0.25)])
    a.rect(1318, 970, 1350, 1000, SIL, r=4)
    return a


# ---------------------------------------------------------------- viñetas de la tira
PW, PH = 1100, 600


def pared_puente(a, day=True):
    if day:
        a.vgrad(0, 0, PW, 470, (214, 206, 192), (190, 180, 166)); junta = (172, 162, 148)
    else:
        a.vgrad(0, 0, PW, 470, (86, 96, 132), (196, 150, 128)); junta = (120, 110, 128)
    for yy in range(160, 470, 56):
        a.line([(0, yy), (PW, yy)], junta, 2, caps=False)
    a.rect(0, 0, PW, 96, (150, 146, 142)); a.rect(0, 96, PW, 112, (110, 106, 104))
    a.rect(30, 112, 110, 480, (160, 156, 150), INK, 3); a.rect(30, 112, 110, 130, (120, 116, 112))
    a.rect(0, 470, PW, PH, (138, 132, 126)); a.rect(0, 470, PW, 484, (168, 160, 152))


def vineta1():
    a = Art(PW, PH)
    pared_puente(a, day=False)
    a.text(440, 170, "¿Y NOSOTROS?", F("Oswald-Bold.ttf", 60), (58, 104, 168), "ma")
    a.text(440, 250, "la calle también es ciudad", F("NewsreaderText-Italic.ttf", 22), (60, 60, 80), "ma")
    sleeper(a, 190, 560, 360)
    cart(a, 600, 565, 1.05)
    for zx, zy, zs in ((250, 420, 22), (280, 385, 28), (318, 342, 36)):
        a.text(zx, zy, "z", F("Oswald-Bold.ttf", zs), INK)
    p = person(a, 880, 580, 360, shirt=(96, 100, 110), pants=(50, 52, 64), skin=SKIN[0], hair=("short", "brown"),
               legs="walk", look=1, rarm=[(0.06, 0.1), (0.05, -0.02)], tie=(150, 40, 40))
    a.rect(p["rhand"][0] - 6, p["rhand"][1] - 26, p["rhand"][0] + 14, p["rhand"][1] + 4, INK, r=3)
    a.glow(p["rhand"][0] + 4, p["rhand"][1] - 12, 30, (170, 220, 255), 160)
    person(a, 1020, 585, 340, shirt=(180, 90, 110), pants=(40, 40, 50), skin=SKIN[1], hair=("long", "dark"),
           legs="walk", look=1)
    a.frame()
    return a


def vineta2():
    a = Art(PW, PH)
    pared_puente(a, day=True)
    a.translucent([(640, 250), (1100, 120), (1100, 600), (760, 600)], (255, 250, 200), 120)
    rep = person(a, 250, 585, 400, shirt=RED, pants=(40, 40, 50), skin=SKIN[1], hair=("long", "brown"), face="shout",
                 look=1, rarm=[(0.07, 0.08), (0.03, -0.08)], brows="up")
    mx, my = rep["rhand"]
    a.line([(mx, my), (mx + 12, my - 40)], INK, 8)
    a.ell(mx + 14, my - 50, 16, 16, (60, 60, 60), INK, 2)
    a.rect(mx - 16, my - 30, mx + 30, my - 6, BLUE, INK, 2)
    a.text(mx + 7, my - 27, "24/7", F("Oswald-Bold.ttf", 13), WHITE, "ma")
    cam = person(a, 560, 590, 420, shirt=(70, 110, 80), pants=(80, 70, 60), skin=SKIN[2], hair=("short", "black"),
                 hat=(40, 40, 44), look=1, rarm=[(0.1, 0.0), (0.15, -0.05)], larm=[(0.02, 0.1), (0.08, 0.02)])
    hx, hy = cam["head"]
    a.rect(hx - 10, hy + 10, hx + 170, hy + 90, (54, 54, 60), INK, 3, r=8)
    a.ell(hx + 190, hy + 50, 30, 30, (30, 30, 36), INK, 3); a.ell(hx + 190, hy + 50, 14, 14, (90, 140, 200))
    a.ell(hx + 20, hy + 30, 8, 8, (240, 50, 40)); a.text(hx + 34, hy + 21, "REC", F("Oswald-Bold.ttf", 16), WHITE)
    a.poly([(820, 590), (1080, 590), (1070, 574), (830, 574)], (176, 138, 92), INK, 3)
    person(a, 930, 574, 330, shirt=(122, 58, 62), pants=(70, 74, 70), skin=SKIN[1], hair=("short", "grey"),
           beard="grey", face="open", legs="sit", sit_dir=1, look=-1, brows="worried",
           larm=[(-0.08, 0.02), (-0.03, -0.1)], rarm=[(0.05, 0.14), (0.14, 0.2)])
    for i in range(5):
        ang = math.pi - 0.9 + i * 0.3
        a.line([(925 + math.cos(ang) * 120, 330 + math.sin(ang) * 120),
                (925 + math.cos(ang) * 150, 330 + math.sin(ang) * 150)], INK, 5)
    a.frame()
    return a


def vineta3():
    a = Art(PW, PH, bg=(38, 78, 138))
    f = F("Oswald-Bold.ttf", 26)
    for row in range(7):
        for col in range(8):
            a.text(-40 + col * 170 + (row % 2) * 85, 20 + row * 70, "CALLE CERO", f, (58, 100, 160))
    person(a, 550, 700, 560, shirt=(34, 40, 64), pants=(34, 40, 64), skin=SKIN[0], hair=("bald", "grey"),
           face="grin", tie=RED, rarm=[(0.08, -0.1), (0.1, -0.24)], larm=[(-0.06, 0.12), (0.02, 0.2)])
    a.poly([(380, 440), (720, 440), (690, PH), (410, PH)], (236, 236, 240), INK, 4)
    a.rect(380, 440, 720, 470, (210, 210, 218), INK, 3)
    a.text(550, 478, "CALLE CERO", F("Oswald-Bold.ttf", 44), BLUE, "ma")
    a.text(550, 540, "Meta: 0 en 30 días", F("NewsreaderText-Bold.ttf", 22), INK, "ma")
    for mx, col in ((470, RED), (550, (60, 150, 90)), (630, (240, 180, 40))):
        a.line([(mx, 440), (mx + (550 - mx) * 0.25, 390)], INK, 6)
        a.rect(mx - 14, 410, mx + 14, 434, col, INK, 2)
        a.ell(mx + (550 - mx) * 0.25, 382, 12, 12, (70, 70, 70), INK, 2)
    for fx, fy in ((130, 380), (980, 330), (230, 250)):
        a.glow(fx, fy, 110, (255, 255, 220), 220)
        star(a, fx, fy, 60, 18, 8, (255, 255, 235))
    SIL = (18, 24, 40)
    for px, ph, side in ((90, 300, 1), (240, 260, 1), (870, 280, -1), (1020, 310, -1)):
        pp = person(a, px, PH + ph * 0.4, ph, sil=SIL, rarm=[(0.06, -0.02), (0.02, -0.12)], larm=[(-0.06, -0.02), (-0.02, -0.12)])
        hx, hy = pp["head"]
        r = pp["r"]
        # cámara delante de la cara, con flash encima y objetivo hacia el político
        a.rect(hx - r * 1.3, hy - r * 0.2, hx + r * 1.3, hy + r * 1.0, SIL, r=6)
        a.rect(hx - r * 0.5, hy - r * 0.9, hx + r * 0.5, hy - r * 0.2, SIL)
        a.ell(hx + side * r * 0.2, hy + r * 0.4, r * 0.55, r * 0.55, (70, 84, 112))
        a.ell(hx + side * r * 0.2, hy + r * 0.4, r * 0.25, r * 0.25, SIL)
    a.frame()
    return a


def vineta4():
    a = Art(PW, PH, bg=(226, 214, 190))
    for i in range(6):
        a.rect(40, 90 + i * 70, 290, 96 + i * 70, (140, 104, 70))
        for j in range(9):
            a.rect(48 + j * 26, 40 + i * 70 + 12, 68 + j * 26, 90 + i * 70,
                   [BLUE, RED, GREEN, YELLOW, (120, 90, 140)][(i + j) % 5], INK, 1.5)
    a.rect(640, 60, 1040, 300, (40, 40, 44), INK, 4, r=8)
    a.rect(656, 76, 1024, 284, (38, 78, 138))
    person(a, 840, 350, 240, shirt=(34, 40, 64), skin=SKIN[0], hair=("bald", "grey"), face="grin", tie=RED,
           rarm=[(0.08, -0.1), (0.1, -0.24)])
    a.rect(656, 240, 1024, 284, RED)
    a.text(840, 262, "ÚLTIMA HORA · CRISIS EN EL CORREDOR", F("Oswald-Bold.ttf", 21), WHITE, "mm")
    a.rect(760, 300, 920, 318, (40, 40, 44))
    luc = person(a, 470, 800, 600, shirt=BLUE, pants=(50, 50, 60), skin=SKIN[1], hair=("bun", "dark"), glasses=True,
                 face="smile", look=1, brows="skeptic", larm=[(-0.02, 0.14), (0.1, 0.12)], rarm=[(0.04, 0.14), (0.15, 0.1)])
    bx, by = luc["lhand"]
    a.poly([(bx - 20, by - 110), (bx + 120, by - 130), (bx + 130, by + 10), (bx - 10, by + 25)], (180, 60, 50), INK, 4)
    a.text(bx + 55, by - 95, "SUÁREZ", F("Oswald-Bold.ttf", 26), WHITE, "ma")
    a.text(bx + 55, by - 58, "CIDES", F("Oswald-Regular.ttf", 18), (250, 220, 200), "ma")
    a.rect(0, 510, PW, PH, (120, 84, 58), INK, 4)
    a.rect(760, 460, 820, 512, WHITE, INK, 3, r=6)
    a.arc(828, 486, 16, 16, 270, 90, INK, 4)
    for sx in (778, 800):
        a.line([(sx, 450), (sx + 8, 430), (sx, 410)], (150, 150, 150), 3)
    a.frame()
    return a


def vineta5():
    a = Art(PW, PH, bg=(204, 196, 182))
    a.rect(0, 470, PW, PH, (150, 142, 132)); a.rect(0, 470, PW, 484, (176, 168, 158))
    a.rect(520, 90, 860, 476, (120, 92, 70), INK, 5)
    a.rect(540, 110, 840, 476, (140, 110, 84), INK, 2)
    a.ell(815, 380, 10, 10, (210, 180, 90), INK, 2)
    a.rect(470, 30, 910, 86, (38, 78, 138), INK, 4)
    a.text(690, 58, "PROGRAMA CALLE CERO", F("Oswald-Bold.ttf", 32), (170, 190, 215), "mm")
    a.poly([(575, 180), (805, 170), (812, 330), (570, 338)], WHITE, INK, 3)
    a.text(690, 196, "CERRADO", F("Oswald-Bold.ttf", 52), RED, "ma")
    a.text(690, 268, "Sin presupuesto", F("NewsreaderText-Bold.ttf", 24), INK, "ma")
    a.text(690, 298, "hasta nuevo aviso", F("NewsreaderText-Italic.ttf", 20), INK, "ma")
    for tx, ty in ((575, 180), (805, 170)):
        a.rect(tx - 16, ty - 6, tx + 16, ty + 6, (230, 220, 160))
    a.poly([(930, 150), (1060, 140), (1070, 330), (940, 340)], (214, 206, 180), INK, 3)
    a.text(1000, 170, "META:", F("Oswald-Bold.ttf", 26), (150, 150, 150), "ma")
    a.text(1000, 206, "0 en 30", F("Oswald-Bold.ttf", 30), (160, 160, 160), "ma")
    a.text(1000, 246, "días", F("Oswald-Bold.ttf", 30), (160, 160, 160), "ma")
    a.poly([(1062, 250), (1072, 332), (990, 342)], (204, 196, 182))
    for i in range(6):
        a.line([(860, 90), (860 + math.cos(i * 0.3) * 90, 90 + math.sin(i * 0.3) * 90)], (90, 90, 90), 1.5, caps=False)
    for rr in (30, 55, 80):
        a.arc(860, 90, rr, rr, 0, 90, (90, 90, 90), 1.5)
    for lx, ly, col in ((600, 520, (170, 120, 50)), (740, 540, (190, 90, 40)), (900, 510, (150, 130, 60))):
        a.ell(lx, ly, 18, 8, col, INK, 1.5)
    cart(a, 20, 560, 0.9)
    person(a, 250, 520, 360, shirt=(122, 58, 62), pants=(70, 74, 70), skin=SKIN[1], hair=("short", "grey"),
           beard="grey", face="sad", legs="sit", sit_dir=1, look=1, brows="worried",
           larm=[(-0.02, 0.14), (0.08, 0.2)], rarm=[(0.05, 0.14), (0.14, 0.18)])
    a.poly([(300, 410), (380, 400), (386, 460), (306, 470)], WHITE, INK, 3)
    a.rect(312, 414, 374, 452, (140, 170, 200))
    person(a, 343, 452, 36, shirt=(122, 58, 62), skin=SKIN[1], hair=("short", "grey"))
    a.frame()
    return a


def vineta6():
    a = Art(PW, PH)
    a.vgrad(0, 0, PW, 420, (250, 214, 150), (246, 236, 214))
    rnd = random.Random(3)
    x = 0
    while x < PW:
        bw, bh = rnd.uniform(60, 130), rnd.uniform(80, 220)
        a.rect(x, 420 - bh, x + bw, 420, (226, 196, 170))
        x += bw + 8
    a.rect(0, 420, PW, PH, (150, 180, 120)); a.rect(0, 500, PW, PH, (190, 176, 150))
    a.rect(80, 150, 120, 470, (110, 80, 60), INK, 3)
    for cx, cy, rr in ((30, 190, 70), (180, 180, 80), (100, 130, 110)):
        a.ell(cx, cy, rr, rr * 0.9, GREEN, INK, 3)
    a.rect(280, 380, 880, 400, (160, 100, 60), INK, 3)
    a.rect(280, 440, 880, 462, (160, 100, 60), INK, 3)
    for lx in (320, 840):
        a.rect(lx, 460, lx + 16, 540, INK)
    luc = person(a, 440, 440, 400, shirt=BLUE, pants=(50, 50, 60), skin=SKIN[1], hair=("bun", "dark"), glasses=True,
                 face="smile", legs="sit", sit_dir=1, look=1, larm=[(0.04, 0.15), (0.14, 0.14)], rarm=[(0.06, 0.13), (0.16, 0.12)])
    nx, ny = luc["rhand"]
    a.poly([(nx - 30, ny - 50), (nx + 30, ny - 58), (nx + 36, ny + 6), (nx - 24, ny + 12)], (250, 246, 220), INK, 3)
    for i in range(4):
        a.line([(nx - 18, ny - 38 + i * 12), (nx + 22, ny - 43 + i * 12)], (120, 120, 140), 2, caps=False)
    ram = person(a, 730, 440, 390, shirt=(122, 58, 62), pants=(70, 74, 70), skin=SKIN[1], hair=("short", "grey"),
                 beard="grey", face="smile", legs="sit", sit_dir=-1, look=-1,
                 larm=[(-0.05, 0.14), (-0.15, 0.1)], rarm=[(0.02, 0.15), (-0.08, 0.17)])
    cx, cy = ram["lhand"]
    a.rect(cx - 16, cy - 30, cx + 14, cy + 6, WHITE, INK, 3, r=4)
    for sx in (cx - 6, cx + 6):
        a.line([(sx, cy - 40), (sx + 6, cy - 56), (sx, cy - 72)], (140, 140, 140), 3)
    for px, py in ((960, 560), (1010, 575)):
        a.ell(px, py, 22, 15, (140, 140, 150), INK, 2); a.ell(px + 18, py - 14, 9, 9, (140, 140, 150), INK, 2)
        a.poly([(px + 26, py - 14), (px + 36, py - 11), (px + 26, py - 8)], ORANGE)
    a.frame()
    return a


# ---------------------------------------------------------------- miniaturas
def ninez():
    a = Art(900, 600, bg=(236, 222, 196))
    a.rect(0, 0, 900, 170, (206, 180, 140))
    for i in range(10):
        a.poly([(i * 90, 150), (i * 90 + 90, 150), (i * 90 + 90, 210), (i * 90 + 45, 230), (i * 90, 210)],
               BLUE if i % 2 else WHITE, INK, 2)
    a.rect(0, 140, 900, 156, (120, 84, 58), INK, 2)
    # vendedora detrás de los guacales: solo asoma el torso
    person(a, 590, 480, 240, shirt=(250, 250, 250), pants=(60, 60, 80), skin=SKIN[2], hair=("bun", "dark"), look=-1,
           larm=[(-0.05, 0.12), (-0.02, 0.24)], rarm=[(0.05, 0.12), (0.02, 0.24)])
    rnd = random.Random(5)
    for cx0, col in ((60, ORANGE), (270, RED), (480, YELLOW), (690, GREEN)):
        a.rect(cx0, 330, cx0 + 190, 420, (170, 120, 70), INK, 3)
        for _ in range(26):
            a.ell(cx0 + rnd.uniform(18, 172), 330 - rnd.uniform(0, 34), 16, 16, col, INK, 1.5)
    a.rect(0, 420, 900, 600, (166, 150, 130))
    kid = person(a, 300, 580, 260, shirt=(230, 120, 60), pants=(70, 90, 120), skin=SKIN[1], hair=("curly", "black"),
                 face="sad", look=1, brows="worried", larm=[(-0.05, -0.08), (0.02, -0.2)], rarm=[(0.05, -0.08), (0.0, -0.2)])
    hx, hy = kid["head"]
    a.poly([(hx - 80, hy - 40), (hx + 80, hy - 40), (hx + 64, hy - 110), (hx - 64, hy - 110)], (190, 150, 90), INK, 3)
    for i in range(6):
        a.ell(hx - 50 + i * 20, hy - 116, 14, 14, [RED, ORANGE, GREEN][i % 3], INK, 1.5)
    a.frame(5)
    return a


def icono_crucigrama():
    a = Art(320, 200, bg=PAPER)
    cells = ["LA#C#", "#CUES", "S#E#T", "OBRA#"]
    s = 34
    for r, row in enumerate(cells):
        for c, ch in enumerate(row):
            x0, y0 = 40 + c * s, 30 + r * s
            if ch == "#":
                a.rect(x0, y0, x0 + s, y0 + s, INK)
            else:
                a.rect(x0, y0, x0 + s, y0 + s, WHITE, INK, 2)
                a.text(x0 + s / 2, y0 + s * 0.52, ch, F("NewsreaderText-Bold.ttf", 18), INK, "mm")
    a.poly([(230, 170), (292, 40), (306, 48), (244, 178)], YELLOW, INK, 2)
    a.poly([(230, 170), (244, 178), (232, 192)], (236, 206, 160), INK, 2)
    a.poly([(292, 40), (306, 48), (312, 34), (298, 26)], (230, 130, 150), INK, 2)
    return a


def prox_combos():
    a = Art(900, 600, bg=(246, 214, 170))
    a.poly([(0, 600), (0, 210), (300, 120), (620, 180), (900, 90), (900, 600)], (206, 150, 110))
    rnd = random.Random(11)
    for _ in range(160):
        hx, hy = rnd.uniform(0, 880), rnd.uniform(200, 430)
        w, h = rnd.uniform(34, 60), rnd.uniform(26, 44)
        a.rect(hx, hy - h, hx + w, hy, rnd.choice([(196, 110, 90), (226, 170, 130), (170, 96, 86), (236, 220, 196)]), INK, 1.5)
        a.rect(hx + w * 0.3, hy - h * 0.6, hx + w * 0.5, hy - h * 0.25, (80, 70, 70))
    a.rect(0, 420, 900, 600, (180, 170, 160))
    a.rect(520, 250, 900, 470, (230, 224, 210), INK, 3)
    a.text(690, 280, "FRONTERA", F("Oswald-Bold.ttf", 50), RED, "ma")
    a.line([(580, 440), (780, 380)], RED, 10)
    person(a, 858, 470, 190, sil=(40, 34, 46))
    p = person(a, 250, 580, 300, shirt=(100, 120, 90), pants=(60, 60, 70), skin=SKIN[1], hair=("short", "dark"),
               legs="walk", look=-1, face="sad", brows="worried",
               larm=[(-0.02, -0.1), (0.04, -0.22)], rarm=[(0.02, -0.1), (0.06, -0.22)])
    hx, hy = p["head"]
    a.rect(hx - 110, hy - 130, hx + 110, hy - 60, (210, 200, 230), INK, 3, r=20)
    a.rect(100, 500, 160, 560, (190, 150, 100), INK, 3)
    person(a, 420, 585, 230, shirt=(220, 120, 140), pants=(60, 80, 110), skin=SKIN[1], hair=("long", "dark"), legs="walk",
           look=-1, face="sad", rarm=[(0.02, 0.12), (0.08, 0.02)])
    a.rect(470, 480, 530, 530, (190, 150, 100), INK, 3)
    a.frame(5)
    return a


if __name__ == "__main__":
    ciudad = escena_ciudad()
    ciudad.save("portada_principal.png")
    # la misma escena: gris fuera de la lupa y a color dentro (el lente sociológico)
    col = ciudad.result().crop((0, 180, 1600, 980)).resize((1400, 700), Image.LANCZOS)
    gris = Image.blend(ImageOps.grayscale(col).convert("RGB"), Image.new("RGB", col.size, PAPER), 0.55)
    mask = Image.new("L", (2800, 1400), 0)
    ImageDraw.Draw(mask).ellipse([1180, 440, 2180, 1440], fill=255)
    gris.paste(col, (0, 0), mask.resize((1400, 700), Image.LANCZOS))
    lente = Art(1400, 700)
    lente.img = gris.resize((1400 * SS, 700 * SS), Image.LANCZOS).convert("RGBA")
    lente.d = ImageDraw.Draw(lente.img)
    lente.ell(840, 470, 252, 252, None, INK, 22)
    lente.ell(840, 470, 240, 240, None, (120, 120, 130), 5)
    lente.line([(1020, 650), (1120, 760)], INK, 58)
    lente.save("editorial_lente.png")
    for n, fn in enumerate((vineta1, vineta2, vineta3, vineta4, vineta5, vineta6), 1):
        fn().save(f"tira_vineta{n}.png")
    ninez().save("miniatura_ninez.png")
    prox_combos().save("miniatura_combos.png")
    icono_crucigrama().save("icono_crucigrama.png")
    Image.open(OUT + "tira_vineta1.png").crop((150, 90, 1050, 690 - 90)).save(OUT + "miniatura_calle.png")
    print("  imagen: miniatura_calle.png")
