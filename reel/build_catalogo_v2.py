#!/usr/bin/env python3
"""Reel de catálogo v2 (ritmo pausado, Invima, conservación, historia y CTA).

Pensado para vendedores digitales: cierre con "Pídelos con tu asesor de confianza"
y franja inferior libre para que cada vendedor ponga su contacto.

Uso: python3 build_catalogo.py <medios> <fuentes> <musica.wav> <final.mp4>
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL = sys.argv[1:5]
W, H, FPS, BPM = 1080, 1920, 30, 116
BEAT = 60 / BPM

KITCHEN_F, CART_F, CARTV_F = "0b8446a6", "c47cb03b", "8d34adfa"
def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
LOGO, PACK, TRAY, OVEN_P = m("777dda90"), m("c80dcfa2"), m("14c3690f"), m("5efb0aea")
ALMO, GALL = m("eef727c6"), m("8ae233b1")
OVEN_V, PROD_V = m("501b5a86"), m("63b2af4a")
KITCHEN, CART_P, CART_V = m(KITCHEN_F), m(CART_F), m(CARTV_F)
F_PF = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_RND = os.path.join(FONTS, "fredoka-latin-700-normal.ttf")
F_RND6 = os.path.join(FONTS, "fredoka-latin-600-normal.ttf")
F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")

CRM, CRM2 = (247, 236, 216), (238, 220, 190)
BRN, BRN2 = (74, 36, 14), (110, 58, 28)
GOLD, TERRA, WHT = (217, 164, 65), (200, 87, 43), (255, 255, 255)

# ---------- easing ----------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=2.0): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    return x if x in (0, 1) else 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1
def pulse(t): return math.exp(-((t / BEAT) % 1) * 7)
def b(n): return n * BEAT

def load(p): return ImageOps.exif_transpose(Image.open(p)).convert("RGB")
def warm(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.06 + 128 + np.array([7, 3, -6])
    l = a.mean(2, keepdims=True); a = l + (a - l) * 1.12
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def view(img, z, cx, cy, w=W, h=H):
    """Recorte tipo cámara: zoom z sobre el centro normalizado (cx, cy)."""
    iw, ih = img.size
    s = max(w / iw, h / ih) * z
    vw, vh = w / s, h / s
    l = clamp(cx * iw - vw / 2, 0, iw - vw); t = clamp(cy * ih - vh / 2, 0, ih - vh)
    return img.resize((w, h), Image.BILINEAR, box=(l, t, l + vw, t + vh))

class Vid:
    def __init__(self, path, ss, speed, w=1188, h=2112):
        self.a = (path, ss, speed, w, h); self.p = None; self.last = None
    def frame(self):
        path, ss, sp, w, h = self.a
        if not self.p:
            vf = f"setpts=PTS/{sp},fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", path, "-vf", vf,
                                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        buf = self.p.stdout.read(w * h * 3)
        if len(buf) == w * h * 3: self.last = warm(Image.frombuffer("RGB", (w, h), buf))
        return self.last

_c = {}
def label(text, font, size, fg, bg=None, pad=(30, 14), r=999, border=None, lh=1.05, track=0):
    k = (text, font, size, fg, bg, border, track)
    if k in _c: return _c[k]
    f = ImageFont.truetype(font, size)
    rows = text.split("\n"); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    def tl(s): return tmp.textlength(s, font=f) + track * max(0, len(s) - 1)
    ws = [tl(x) for x in rows]; a, d_ = f.getmetrics(); L = int((a + d_) * lh)
    bw, bh = int(max(ws)) + 2 * pad[0], L * len(rows) + 2 * pad[1]
    img = Image.new("RGBA", (bw + 20, bh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    if bg:
        d.rounded_rectangle((14, 16, 14 + bw, 16 + bh), min(r, bh // 2), fill=(0, 0, 0, 60))
        d.rounded_rectangle((10, 10, 10 + bw, 10 + bh), min(r, bh // 2), fill=bg,
                            outline=border, width=3 if border else 0)
    for i, row in enumerate(rows):
        x = 10 + pad[0] + (max(ws) - ws[i]) / 2; y = 10 + pad[1] + i * L
        if track:
            for ch in row:
                d.text((x, y), ch, font=f, fill=fg); x += tmp.textlength(ch, font=f) + track
        else:
            d.text((x, y), row, font=f, fill=fg)
    _c[k] = img; return img

def put(cv, img, cx, cy, sc=1., al=1., rot=0.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BILINEAR, expand=True)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def enter(cv, img, t, t0, cx, cy, kind="pop", rot=0.):
    if t < t0: return
    k = (t - t0) / .4; sc, al, x, y = 1., 1., cx, cy
    if kind == "pop": sc = back(k, 2.4)
    elif kind == "elastic": sc = elastic((t - t0) / .8)
    elif kind == "up": y = cy + (1 - eo(k)) * 120; al = eo(k * 1.4)
    elif kind == "left": x = cx - (1 - eo(k)) * 1200
    elif kind == "right": x = cx + (1 - eo(k)) * 1200
    elif kind == "fade": al = eo(k)
    elif kind == "slam": sc = 1 + 1.6 * (1 - eo(k)); al = eo(k * 2)
    put(cv, img, x, y, sc, al, rot)

# ---------- recursos de marca ----------
def make_bg():
    bg = Image.new("RGB", (W, H), CRM); d = ImageDraw.Draw(bg)
    rng = np.random.default_rng(2)
    for _ in range(46):  # espigas y destellos suaves, como el logo
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if rng.random() < .5:
            s = rng.uniform(10, 22)
            d.polygon([(x, y - s), (x + s * .25, y - s * .25), (x + s, y), (x + s * .25, y + s * .25),
                       (x, y + s), (x - s * .25, y + s * .25), (x - s, y), (x - s * .25, y - s * .25)], fill=CRM2)
        else:
            a = rng.uniform(-.6, .6); L = rng.uniform(50, 90)
            for j in range(5):
                px, py = x + math.sin(a) * j * L / 5, y - math.cos(a) * j * L / 5
                d.ellipse((px - 12, py - 6, px - 2, py + 6), fill=CRM2); d.ellipse((px + 2, py - 6, px + 12, py + 6), fill=CRM2)
    return bg.convert("RGBA")
BG = make_bg()

def round_logo(size, ring=GOLD, rw=12):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 2 * rw, size - 2 * rw), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((4, 4, lg.width - 4, lg.height - 4), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (rw, rw), mk); return out
LOGO_BIG, LOGO_SM = round_logo(560), round_logo(150, WHT, 6)

def rounded(img, r=40):
    mk = Image.new("L", img.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255)
    out = img.convert("RGBA"); out.putalpha(mk); return out

def card(img, w, h, c=(.5, .5), z=1.0, cap=None):
    ph = rounded(view(img, z, *c, w=w, h=h), 34)
    out = Image.new("RGBA", (w + 40, h + (130 if cap else 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.rounded_rectangle((16, 24, w + 28, h + 32), 38, fill=(0, 0, 0, 70))
    out = Image.alpha_composite(out, out.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(out); d.rounded_rectangle((8, 8, w + 32, h + 32), 40, fill=WHT)
    out.alpha_composite(ph, (20, 20))
    if cap:
        f = ImageFont.truetype(F_PF, 40); tw = d.textlength(cap, font=f)
        d.text(((w + 40 - tw) / 2, h + 55), cap, font=f, fill=BRN)
    return out

IM = {"kitchen": warm(load(KITCHEN)), "cart": warm(load(CART_P)), "tray": warm(load(TRAY)), "pack": warm(load(PACK)), "oven": warm(load(OVEN_P)),
      "almo": warm(load(ALMO)), "gall": warm(load(GALL))}

# ---------- escenas ----------
def sc_intro(t):
    cv = BG.copy(); d = ImageDraw.Draw(cv)
    k = eo(t / .9)
    for i in range(24):  # rayos dorados detrás del logo
        a = 2 * math.pi * i / 24 + t * .25; r0, r1 = 300, 300 + 260 * k
        d.line((540 + r0 * math.cos(a), 760 + r0 * math.sin(a), 540 + r1 * math.cos(a), 760 + r1 * math.sin(a)),
               fill=GOLD if i % 2 else (230, 196, 120), width=10)
    put(cv, LOGO_BIG, 540, 760, elastic(t / .9) * (1 + .02 * pulse(t)), 1, (1 - eo(t / .9)) * -90)
    enter(cv, label("Receta de la abuela", F_SC, 120, BRN), t, b(1.5), 540, 1180, "up")
    enter(cv, label("TRADICIÓN QUE SE DISFRUTA HASTA EL FINAL", F_RND6, 34, BRN2, track=3), t, b(2.3), 540, 1300, "fade")
    enter(cv, label("Torta de cuajada · Almojábanas · Galletas", F_RND, 44, WHT, TERRA), t, b(3), 540, 1420, "pop")
    return cv

SHOT, XF = 4, .6  # tiempos por toma y fundido entre tomas

def shot_player(shots, beats=SHOT, pulse_amt=.012):
    """Reproduce tomas (imagen o video) con movimiento lento y fundido suave entre ellas."""
    vids, lastf = {}, {}
    def frame(t):
        si = min(int(t / b(beats)), len(shots) - 1); lt = t - si * b(beats)
        kind, src, z0, z1, cx, cy = shots[si]
        z = (z0 + (z1 - z0) * eio(lt / b(beats))) * (1 + pulse_amt * pulse(t))
        if kind == "vid":
            if si not in vids: vids[si] = Vid(*src)
            base = vids[si].frame()
        else:
            base = IM[src]
        fr = view(base, z, cx, cy).convert("RGBA")
        lastf[si] = fr
        if lt < XF and si > 0 and (si - 1) in lastf:
            fr = Image.blend(lastf[si - 1], fr, eio(lt / XF))
        return fr
    return frame

def product_scene(num, name, sub, tags, shots):
    """Plantilla de producto: tomas a pantalla completa + panel crema con nombre y etiquetas."""
    play = shot_player(shots)
    def f(t):
        cv = play(t)
        cv.alpha_composite(GRAD)
        # panel
        pk = eo(t / .5)
        py = int(1420 + (1 - pk) * 600)
        cv.alpha_composite(PANEL, (0, py))
        enter(cv, label(num, F_PF, 64, GOLD), t, .25, 140, py + 120, "pop")
        enter(cv, label(name, F_PF, 92 if len(name) < 16 else 78, BRN), t, .35, 560, py + 120, "left")
        enter(cv, label(sub, F_PFI, 46, BRN2), t, .7, 540, py + 225, "up")
        xs = [W / 2] if len(tags) == 1 else [W / 2 - 230, W / 2 + 230] if len(tags) == 2 else [200, 540, 880]
        for i, tg in enumerate(tags):
            enter(cv, label(tg, F_RND, 38, WHT, TERRA if i % 2 == 0 else BRN, pad=(26, 12)), t, 1.0 + .25 * i,
                  xs[i], py + 330, "pop")
        put(cv, LOGO_SM, 110, 120, 1, eo(t / .4))
        return cv
    return f

def make_grad():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = g.load()
    for y in range(1100, H):
        a = int(150 * ((y - 1100) / 820) ** 1.5)
        for x in range(W): px[x, y] = (40, 18, 4, a)
    for y in range(0, 260):
        a = int(90 * (1 - y / 260))
        for x in range(W): px[x, y] = (40, 18, 4, a)
    return g
GRAD = make_grad()
PANEL = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
ImageDraw.Draw(PANEL).rounded_rectangle((0, 0, W, 600), 56, fill=CRM)
ImageDraw.Draw(PANEL).rounded_rectangle((420, 16, 660, 24), 4, fill=GOLD)

sc_torta = product_scene("01", "Torta de Cuajada", "La receta de siempre, horneada con amor",
                         ["545 g", "9 porciones", "Doradita"],
                         [("vid", (OVEN_V, .3, .4), 1.12, 1.0, .5, .5),
                          ("img", "tray", 1.0, 1.12, .5, .45),
                          ("img", "pack", 1.3, 1.15, .45, .55)])
sc_almo = product_scene("02", "Almojábanas", "del campo, suavecitas y doradas",
                        ["Recién horneadas", "Para compartir"],
                        [("img", "almo", 1.0, 1.08, .5, .4),
                         ("img", "almo", 1.6, 1.4, .5, .22),
                         ("img", "almo", 1.35, 1.15, .5, .5)])
sc_gall = product_scene("03", "Galletas Caseritas", "ingredientes naturales y mucho amor",
                        ["Crocantes", "Ideales con café"],
                        [("img", "gall", 1.0, 1.06, .33, .5),
                         ("img", "gall", 1.25, 1.1, .66, .45),
                         ("img", "gall", 1.7, 1.5, .88, .86)])

TRIO = [card(IM["pack"], 270, 380, (.4, .6), 1.3, "Torta"), card(IM["almo"], 270, 380, (.5, .45), 1.0, "Almojábanas"),
        card(IM["gall"], 270, 380, (.3, .5), 1.3, "Galletas")]
def sc_trio(t):
    cv = BG.copy()
    enter(cv, label("Tu antojo favorito,", F_PFI, 70, BRN2), t, .1, 540, 380, "up")
    enter(cv, label("¡en un solo pedido!", F_PF, 86, BRN), t, b(1), 540, 490, "slam")
    for i, (cx, rot) in enumerate([(205, -6), (540, 0), (875, 6)]):
        if t < b(1.5 + .5 * i): continue
        k = (t - b(1.5 + .5 * i)) / .5
        y = 1000 - (1 - back(k, 1.5)) * -900 + 14 * math.sin(t * 2.4 + i)
        put(cv, TRIO[i], cx, y, .98 + .03 * pulse(t), 1, rot * eo(k))
    enter(cv, label("Hecho en casa · Receta de la abuela", F_RND, 44, WHT, TERRA), t, b(4), 540, 1440, "pop")
    return cv

def invima_seal(s=300):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pts = [(s / 2 + (s / 2 - 3) * (1 if i % 2 == 0 else .92) * math.cos(math.pi * i / 20),
            s / 2 + (s / 2 - 3) * (1 if i % 2 == 0 else .92) * math.sin(math.pi * i / 20)) for i in range(40)]
    d.polygon(pts, fill=(24, 90, 60)); d.ellipse((26, 26, s - 26, s - 26), outline=GOLD, width=5)
    put(img, label("REGISTRO\nSANITARIO", F_RND6, 28, WHT, lh=.95), s / 2, s / 2 - 50)
    put(img, label("INVIMA", F_PF, 62, GOLD), s / 2, s / 2 + 20)
    put(img, label("COLOMBIA", F_RND6, 24, WHT, track=3), s / 2, s / 2 + 82)
    return img
SEAL = invima_seal()

def thumb(im, c, z, s=170):
    ph = view(im, z, *c, w=s, h=s).convert("RGBA")
    mk = Image.new("L", (s, s), 0); ImageDraw.Draw(mk).ellipse((0, 0, s - 1, s - 1), fill=255); ph.putalpha(mk)
    out = Image.new("RGBA", (s + 16, s + 16), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, s + 15, s + 15), fill=GOLD)
    out.alpha_composite(ph, (8, 8)); return out

def info_row(img, name, reg, cons, icon):
    row = Image.new("RGBA", (960, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(row)
    d.rounded_rectangle((6, 10, 956, 226), 40, fill=(0, 0, 0, 40))
    d.rounded_rectangle((0, 0, 950, 216), 40, fill=WHT, outline=CRM2, width=3)
    row.alpha_composite(img, (20, 15))
    f1, f2, f3 = ImageFont.truetype(F_PF, 50), ImageFont.truetype(F_RND6, 32), ImageFont.truetype(F_RND, 36)
    d.text((225, 22), name, font=f1, fill=BRN)
    d.text((225, 92), reg, font=f2, fill=(24, 90, 60) if reg.startswith("INVIMA") else BRN2)
    # chip de conservación
    w = d.textlength((icon + "  " if icon else "") + cons, font=f3)
    d.rounded_rectangle((222, 140, 222 + w + 44, 198), 29, fill=TERRA if "Refrig" in cons else BRN)
    d.text((244, 146), (icon + "  " if icon else "") + cons, font=f3, fill=WHT)
    return row

ROWS = [info_row(thumb(IM["pack"], (.45, .55), 1.3), "Torta de Cuajada", "INVIMA RSA-6500-2026", "Refrigerada · 14 días", ""),
        info_row(thumb(IM["almo"], (.5, .4), 1.0), "Almojábanas", "INVIMA RSA-6561-2026", "Refrigeradas · 4 días", ""),
        info_row(thumb(IM["gall"], (.33, .5), 1.2), "Galletas Caseritas", "Hechas con ingredientes naturales", "Temp. ambiente · 7 días", "")]

def sc_quality(t):
    cv = BG.copy()
    enter(cv, label("Calidad garantizada", F_PF, 92, BRN), t, .1, 540, 230, "up")
    enter(cv, label("y conservación de cada producto", F_PFI, 52, BRN2), t, b(.8), 540, 335, "up")
    put(cv, SEAL, 540, 580, elastic((t - b(1.4)) / .8) * (1 + .015 * pulse(t)) if t > b(1.4) else 0, 1,
        4 * math.sin(t * 1.5))
    for i, r in enumerate(ROWS):
        enter(cv, r, t, b(3 + 1.5 * i), 545, 900 + 260 * i, "left" if i % 2 == 0 else "right")
    enter(cv, label("Torta y almojábanas con registro sanitario INVIMA", F_RND6, 34, BRN2), t, b(8), 540, 1690, "fade")
    put(cv, LOGO_SM, 110, 120, 1, 1)
    return cv

_g = {}
def glow_label(txt):
    if txt in _g: return _g[txt]
    lb = label(txt, F_PFI, 84, WHT, lh=1.15)
    pad = 40; out = Image.new("RGBA", (lb.width + 2 * pad, lb.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); a = lb.getchannel("A")
    blk = Image.new("RGBA", lb.size, (30, 12, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (pad + 3, pad + 5)); sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh2 = sh.copy(); sh = Image.alpha_composite(sh, sh2)
    out.alpha_composite(sh); out.alpha_composite(lb, (pad, pad)); _g[txt] = out; return out

def make_heart(s=110):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pts = [(s / 2 + s * .03 * 16 * math.sin(a) ** 3, s * .45 - s * .03 * (13 * math.cos(a) - 5 * math.cos(2 * a)
            - 2 * math.cos(3 * a) - math.cos(4 * a))) for a in np.linspace(0, 2 * math.pi, 80)]
    d.polygon(pts, fill=(235, 90, 90)); return img
HEART = make_heart()

STORY = shot_player([("img", "cart", 1.0, 1.1, .5, .45),
                     ("img", "kitchen", 1.12, 1.0, .6, .4),
                     ("vid", (PROD_V, 9.0, .6), 1.0, 1.08, .5, .3),
                     ("vid", (CART_V, 0, .4), 1.08, 1.0, .5, .5)], beats=3, pulse_amt=0)
STORY_TXT = [("Detrás de cada torta\nhay una historia…", 0), ("…la de una abuela\ny su nieta", 3),
             ("que convirtieron un sueño\nen emprendimiento", 6), ("Gracias por ser\nparte de ella 🤍", 9)]
def sc_story(t):
    fr = STORY(t)
    a = np.asarray(fr.convert("RGB")).astype(np.float32)  # tono cálido nostálgico
    l = a.mean(2, keepdims=True); a = l + (a - l) * .7 + np.array([18, 6, -14])
    cv = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    cv.alpha_composite(GRAD)
    for txt, b0 in STORY_TXT:
        t0, t1 = b(b0) + .25, b(b0 + 3) - .1
        if t0 <= t <= t1:
            al = min(eo((t - t0) / .6), eo((t1 - t) / .4))
            txt = txt.replace(" 🤍", "")
            put(cv, glow_label(txt), 540, 1300 + (1 - eo((t - t0) / .6)) * 40, 1, al)
    if t > b(9.5):
        put(cv, HEART, 540, 1480, back((t - b(9.5)) / .5), 1)
    return cv

def sc_end(t):
    cv = BG.copy(); d = ImageDraw.Draw(cv)
    for i in range(20):
        a = 2 * math.pi * i / 20 + t * .2; r0, r1 = 230, 230 + 150 * eo(t / .8)
        d.line((540 + r0 * math.cos(a), 470 + r0 * math.sin(a), 540 + r1 * math.cos(a), 470 + r1 * math.sin(a)), fill=GOLD, width=8)
    put(cv, round_logo(420), 540, 470, elastic(t / .8) * (1 + .02 * pulse(t)))
    enter(cv, label("¡Pídelas ya!", F_PF, 130, BRN), t, b(1), 540, 830, "slam")
    enter(cv, label("con tu vendedor más cercano", F_PFI, 64, BRN2), t, b(2), 540, 960, "up")
    enter(cv, label("Torta de cuajada · Almojábanas · Galletas", F_RND, 42, WHT, TERRA), t, b(3), 540, 1080, "pop")
    enter(cv, label("BARUJ SHEFA · BENDICIÓN EN ABUNDANCIA", F_RND6, 34, BRN2, track=3), t, b(3.8), 540, 1180, "fade")
    # flecha que rebota hacia la zona libre del vendedor
    if t > b(4.6):
        ay = 1330 + 22 * abs(math.sin((t - b(4.6)) * 4)); al = eo((t - b(4.6)) / .4)
        arr = Image.new("RGBA", (140, 120), (0, 0, 0, 0)); ad = ImageDraw.Draw(arr)
        ad.polygon([(20, 20), (120, 20), (70, 100)], fill=TERRA)
        put(cv, arr, 540, ay, 1, al)
    # franja inferior limpia para el contacto del vendedor (sin texto)
    d = ImageDraw.Draw(cv); d.rectangle((0, 1480, W, H), fill=WHT)
    d.rectangle((0, 1480, W, 1490), fill=GOLD)
    return cv

def wipe(prev, cur, k):
    """Barrido diagonal con banda dorada."""
    e = eio(k); x = int(-400 + e * (W + 800))
    mk = Image.new("L", (W, H), 0); ImageDraw.Draw(mk).polygon([(-400, 0), (x, 0), (x - 400, H), (-800, H)], fill=255)
    out = prev.copy(); out.paste(cur, (0, 0), mk)
    ImageDraw.Draw(out).polygon([(x, 0), (x + 60, 0), (x - 340, H), (x - 400, H)], fill=GOLD)
    return out

SCENES = [(4, sc_intro, None), (12, sc_torta, "wipe"), (12, sc_almo, "wipe"), (12, sc_gall, "wipe"),
          (6, sc_trio, "wipe"), (11, sc_quality, "wipe"), (12, sc_story, "fade"), (10, sc_end, "fade")]
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
DUR = b(acc); TR = .75

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", MUSIC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev, cur, last = None, 0, None
N = int(DUR * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(starts) if b(s) <= t + 1e-6)
    if si != cur: prev, cur = last, si
    _, fn, tr = SCENES[si]; lt = t - b(starts[si])
    fr = fn(lt).convert("RGB"); last = fr; out = fr
    if tr and lt < TR and prev is not None:
        out = wipe(prev, fr, lt / TR) if tr == "wipe" else Image.blend(prev, fr, eio(lt / TR))
    if fi < 8: out = Image.blend(Image.new("RGB", (W, H), CRM), out, fi / 8)
    ff.stdin.write(out.tobytes())
    if fi % 120 == 0: print(f"{fi}/{N}", flush=True)
ff.stdin.close(); ff.wait()
print(f"DUR={DUR:.2f}")
