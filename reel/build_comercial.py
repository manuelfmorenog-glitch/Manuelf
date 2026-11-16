#!/usr/bin/env python3
"""Comercial Torta de Cuajada Baruj Shefa (para estados de WhatsApp / reels de vendedores).

Estilo comercial premium: fondos chocolate, tipografía gruesa dorada, barrido de luz,
vapor, destellos, sellos de autoridad (INVIMA, receta tradicional, Hecho en Bogotá)
y cierre con "¡Pídela ya con tu vendedor más cercano!" + franja libre para el vendedor.

Uso: python3 build_comercial.py <medios> <fuentes> <musica.wav> <final.mp4>
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL = sys.argv[1:5]
W, H, FPS, BPM = 1080, 1920, 30, 124
BEAT = 60 / BPM

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
LOGO, PACK, TRAY, OVEN_P, CART_P = m("777dda90"), m("c80dcfa2"), m("14c3690f"), m("5efb0aea"), m("c47cb03b")
OVEN_V = m("501b5a86")
F_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BLKI = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")

CHOC, CHOC2 = (38, 18, 8), (66, 32, 14)
GOLD, GOLD2, CRM, WHT = (236, 182, 76), (255, 222, 140), (250, 240, 222), (255, 255, 255)
TERRA, GRN = (206, 84, 38), (28, 112, 66)

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
def appetizing(im):
    """Look de comercial de comida: cálido, saturado y con contraste."""
    a = np.asarray(im).astype(np.float32) / 255
    a = a ** 0.95
    a = (a - .5) * 1.15 + .5 + np.array([.035, .012, -.03])
    l = a.mean(2, keepdims=True); a = l + (a - l) * 1.3
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def view(img, z, cx, cy, w=W, h=H):
    iw, ih = img.size; s = max(w / iw, h / ih) * z; vw, vh = w / s, h / s
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
        if len(buf) == w * h * 3: self.last = appetizing(Image.frombuffer("RGB", (w, h), buf))
        return self.last

# ---------- tipografía ----------
_c = {}
def text_img(text, font, size, fill, stroke=0, stroke_fill=None, shadow=True, lh=1.0, track=0):
    k = (text, font, size, fill, stroke, stroke_fill, shadow, track)
    if k in _c: return _c[k]
    f = ImageFont.truetype(font, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    rows = text.split("\n")
    def tl(s): return sum(tmp.textlength(ch, font=f) + track for ch in s) - track if track else tmp.textlength(s, font=f)
    ws = [tl(r) for r in rows]; a, d_ = f.getmetrics(); L = int((a + d_) * lh)
    pad = 40 + stroke
    img = Image.new("RGBA", (int(max(ws)) + 2 * pad, L * len(rows) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        x = pad + (max(ws) - ws[i]) / 2; y = pad + i * L
        if track:
            for ch in r:
                d.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
                x += tmp.textlength(ch, font=f) + track
        else:
            d.text((x, y), r, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); blk = Image.new("RGBA", img.size, (15, 6, 0, 255))
        blk.putalpha(img.getchannel("A")); sh.alpha_composite(blk, (0, 0))
        sh = sh.filter(ImageFilter.GaussianBlur(14)); sh = Image.alpha_composite(sh, sh)
        out = Image.new("RGBA", img.size, (0, 0, 0, 0)); out.alpha_composite(sh, (0, 0)); out.alpha_composite(img)
        img = out
    _c[k] = img; return img

def gold_text(text, size, font=F_BLK, track=0):
    """Texto con degradado dorado."""
    base = text_img(text, font, size, WHT, shadow=False, track=track)
    a = base.getchannel("A"); w, h = base.size
    grad = Image.new("RGBA", (w, h))
    gp = np.zeros((h, w, 4), np.uint8)
    y = np.linspace(0, 1, h)[:, None]
    for i, (c0, c1) in enumerate(zip(GOLD2, (196, 132, 40))):
        gp[..., i] = (c0 + (c1 - c0) * y).astype(np.uint8)
    gp[..., 3] = 255; grad = Image.fromarray(gp); grad.putalpha(a)
    sh = text_img(text, font, size, WHT, shadow=True, track=track)
    out = sh.copy(); out.alpha_composite(grad); return out

def sweep(img, k):
    """Barrido de luz diagonal sobre un texto (k de 0 a 1)."""
    if not 0 < k < 1: return img
    w, h = img.size; band = Image.new("L", (w, h), 0); d = ImageDraw.Draw(band)
    x = -h + k * (w + 2 * h)
    d.polygon([(x, 0), (x + 90, 0), (x + 90 - h * .5, h), (x - h * .5, h)], fill=200)
    band = band.filter(ImageFilter.GaussianBlur(10))
    mask = Image.fromarray(np.minimum(np.asarray(band), np.asarray(img.getchannel("A"))))
    out = img.copy(); out.paste(Image.new("RGBA", (w, h), (255, 250, 230, 255)), (0, 0), mask); return out

def put(cv, img, cx, cy, sc=1., al=1., rot=0.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BILINEAR, expand=True)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def enter(cv, img, t, t0, cx, cy, kind="slam", rot=0., t1=1e9):
    if t < t0 or t > t1: return
    k = (t - t0) / .35; sc, al, x, y = 1., 1., cx, cy
    if kind == "slam": sc = 1 + 1.8 * (1 - eo(k)); al = eo(k * 2.5)
    elif kind == "pop": sc = back(k, 2.4)
    elif kind == "left": x = cx - (1 - eo(k)) * 1300
    elif kind == "right": x = cx + (1 - eo(k)) * 1300
    elif kind == "up": y = cy + (1 - eo(k)) * 160; al = eo(k * 1.5)
    elif kind == "fade": al = eo(k)
    o = clamp((t - (t1 - .15)) / .15)
    if o: sc *= 1 + .4 * o; al *= 1 - o
    put(cv, img, x, y, sc, al, rot)

# ---------- efectos ----------
rng = np.random.default_rng(4)
def steam_sprite(s=420):
    img = Image.new("L", (s, s), 0); d = ImageDraw.Draw(img)
    for _ in range(7):
        x, y, r = rng.uniform(.3, .7) * s, rng.uniform(.3, .7) * s, rng.uniform(.12, .22) * s
        d.ellipse((x - r, y - r * 1.4, x + r, y + r * 1.4), fill=140)
    img = img.filter(ImageFilter.GaussianBlur(40))
    out = Image.new("RGBA", (s, s), (255, 255, 255, 0)); out.putalpha(img); return out
STEAM = [steam_sprite() for _ in range(3)]
PUFFS = [dict(x=rng.uniform(200, 880), t0=rng.uniform(0, 2.5), sp=rng.uniform(220, 360), i=i % 3,
              sc=rng.uniform(.8, 1.5)) for i in range(10)]
def draw_steam(cv, t, base_y=1250, strength=1.):
    for p in PUFFS:
        lt = (t - p["t0"]) % 2.6
        y = base_y - lt * p["sp"]; al = math.sin(math.pi * lt / 2.6) * .55 * strength
        put(cv, STEAM[p["i"]], p["x"] + 40 * math.sin(lt * 2 + p["x"]), y, p["sc"] * (1 + lt * .3), al)

SPARK = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
_d = ImageDraw.Draw(SPARK)
_d.polygon([(45, 0), (52, 38), (90, 45), (52, 52), (45, 90), (38, 52), (0, 45), (38, 38)], fill=(255, 240, 200, 255))
SPARK = SPARK.filter(ImageFilter.GaussianBlur(1.2))
SPARKS = [dict(x=rng.uniform(80, 1000), y=rng.uniform(250, 1500), t0=rng.uniform(0, 3), s=rng.uniform(.4, 1)) for _ in range(14)]
def draw_sparks(cv, t, area=None):
    for s in SPARKS:
        lt = (t - s["t0"]) % 1.6
        if lt < .6:
            k = math.sin(math.pi * lt / .6)
            put(cv, SPARK, s["x"], s["y"], s["s"] * k, k, lt * 120)

def leak(t, strength=.35):
    """Fuga de luz cálida animada."""
    img = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x = (W // 4) * (.5 + .5 * math.sin(t * .9)); y = (H // 4) * (.3 + .2 * math.cos(t * .7))
    for r, a in [(220, 40), (150, 60), (90, 80)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 170, 70, int(a * strength * 2)))
    return img.filter(ImageFilter.GaussianBlur(30)).resize((W, H), Image.BILINEAR)

def vignette():
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W * .7)) ** 2 + ((yy - H / 2) / (H * .7)) ** 2)
    a = np.clip((r - .55) * 1.6, 0, 1) * 200
    img = np.zeros((H, W, 4), np.uint8); img[..., 0], img[..., 1], img[..., 2] = 20, 8, 0; img[..., 3] = a.astype(np.uint8)
    return Image.fromarray(img)
VIG = vignette()

def check_badge(text, sub=None, color=GRN):
    f1 = ImageFont.truetype(F_XB, 60); f2 = ImageFont.truetype(F_XB, 40)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(max(tmp.textlength(text, font=f1), tmp.textlength(sub or "", font=f2))) + 200
    h = 170 if sub else 130
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 12, w + 8, h + 12), h // 2, fill=(0, 0, 0, 120))
    d.rounded_rectangle((0, 0, w, h), h // 2, fill=(250, 243, 230, 245), outline=GOLD, width=4)
    cy = h // 2; d.ellipse((22, cy - 48, 118, cy + 48), fill=color)
    d.line([(44, cy), (64, cy + 20), (98, cy - 18)], fill=WHT, width=13, joint="curve")
    d.text((145, cy - (62 if sub else 38)), text, font=f1, fill=CHOC)
    if sub: d.text((145, cy + 10), sub, font=f2, fill=(120, 70, 30))
    return img

def round_logo(size):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 20, size - 20), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((3, 3, lg.width - 3, lg.height - 3), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=GOLD)
    out.paste(lg, (10, 10), mk); return out

IM = {k: appetizing(load(p)) for k, p in [("tray", TRAY), ("pack", PACK), ("oven", OVEN_P), ("cart", CART_P)]}
LOGO_S = round_logo(130)

# ---------- escenas ----------
def shot(src, z0, z1, cx, cy, dur_beats):
    vid = {}
    def f(t):
        z = (z0 + (z1 - z0) * eio(t / b(dur_beats))) * (1 + .03 * pulse(t))
        if src == "OVEN_V":
            if "v" not in vid: vid["v"] = Vid(OVEN_V, .2, .35)
            base = vid["v"].frame()
        else:
            base = IM[src]
        cv = view(base, z, cx, cy).convert("RGBA")
        cv.alpha_composite(VIG); return cv
    return f

S_HOOK = shot("tray", 2.2, 1.7, .55, .5, 4)
def sc_hook(t):
    cv = S_HOOK(t)
    enter(cv, text_img("¿TIENES", F_BLK, 150, WHT), t, b(.3), 540, 700, "slam", -3)
    enter(cv, gold_text("ANTOJO?", 210), t, b(1.2), 540, 890, "slam", -3)
    enter(cv, text_img("de algo casero y delicioso", F_PFI, 66, CRM), t, b(2.3), 540, 1060, "up")
    return cv

S_GOLD = shot("OVEN_V", 1.25, 1.05, .5, .5, 4)
def sc_dorada(t):
    cv = S_GOLD(t); cv.alpha_composite(leak(t, .4))
    enter(cv, text_img("DORADITA", F_BLKI, 170, WHT), t, b(.2), 540, 1350, "left", -4)
    enter(cv, sweep(gold_text("POR FUERA", 130), (t - b(1.2)) / .8), t, b(1), 540, 1510, "right", -4)
    draw_sparks(cv, t)
    return cv

S_SOFT = shot("tray", 1.2, 1.4, .5, .35, 4)
def sc_suave(t):
    cv = S_SOFT(t)
    enter(cv, text_img("SUAVE", F_BLKI, 200, WHT), t, b(.2), 540, 1330, "slam", 3)
    enter(cv, gold_text("POR DENTRO", 130), t, b(1), 540, 1510, "up")
    return cv

S_STEAM = shot("oven", 1.35, 1.15, .5, .62, 4)
def sc_horno(t):
    cv = S_STEAM(t); draw_steam(cv, t, 1300, 1.0); cv.alpha_composite(leak(t + 2, .45))
    enter(cv, text_img("RECIÉN", F_BLK, 140, WHT), t, b(.2), 540, 380, "slam", -3)
    enter(cv, sweep(gold_text("HORNEADA", 170), (t - b(1.3)) / .8), t, b(.9), 540, 545, "slam", -3)
    return cv

S_PACK = shot("pack", 1.55, 1.25, .45, .6, 8)
BADGES = [check_badge("Registro INVIMA", "RSA-6500-2026"), check_badge("Receta tradicional", "de la abuela", TERRA),
          check_badge("Hecho en Bogotá", None, (180, 120, 30)), check_badge("545 g · 9 porciones", None, (120, 70, 30))]
def sc_autoridad(t):
    cv = S_PACK(t)
    dim = Image.new("RGBA", (W, H), (20, 8, 0, int(110 * eo(t / .6)))); cv.alpha_composite(dim)
    enter(cv, text_img("CALIDAD QUE", F_BLK, 104, WHT), t, b(.2), 540, 300, "up")
    enter(cv, gold_text("SE NOTA", 150), t, b(.8), 540, 430, "slam", -2)
    for i, bd in enumerate(BADGES):
        enter(cv, bd, t, b(1.8 + 1.2 * i), 540, 780 + 215 * i, "right" if i % 2 == 0 else "left")
    return cv

S_CART = shot("cart", 1.15, 1.0, .5, .42, 4)
def sc_bogota(t):
    cv = S_CART(t)
    enter(cv, text_img("BOGOTÁ YA LA", F_BLK, 100, WHT), t, b(.2), 540, 1380, "left")
    enter(cv, gold_text("ESTÁ PROBANDO", 108), t, b(.9), 540, 1520, "right")
    enter(cv, text_img("Presentes en los Mercados Campesinos", F_XB, 40, CRM), t, b(1.8), 540, 1660, "up")
    return cv

# Cierre héroe
def end_bg():
    bg = Image.new("RGB", (W, H), CHOC); a = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - 760) / H) ** 2)
    glow = np.clip(1 - r * 1.6, 0, 1)[..., None]
    a = a * (1 - glow) + np.array(CHOC2) * glow * 1.6
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
END_BG = end_bg()
def hero_card():
    w, h = 640, 640
    ph = view(IM["tray"], 1.6, .5, .38, w, h).convert("RGBA")
    mk = Image.new("L", (w, h), 0); ImageDraw.Draw(mk).ellipse((0, 0, w - 1, h - 1), fill=255); ph.putalpha(mk)
    out = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.ellipse((0, 0, w + 59, h + 59), fill=GOLD); out.alpha_composite(ph, (30, 30))
    glow = Image.new("RGBA", (w + 260, h + 260), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((60, 60, w + 200, h + 200), fill=(255, 180, 70, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(60)); glow.alpha_composite(out, (100, 100)); return glow
HERO = hero_card()
CTA = None
def cta_pill():
    f = ImageFont.truetype(F_BLK, 92); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tx = "¡PÍDELA YA!"; w = int(tmp.textlength(tx, font=f)) + 120; h = 150
    img = Image.new("RGBA", (w + 20, h + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((6, 16, w + 6, h + 16), 75, fill=(0, 0, 0, 140))
    d.rounded_rectangle((0, 0, w, h), 75, fill=TERRA, outline=GOLD2, width=5)
    d.text((60, 22), tx, font=f, fill=WHT); return img
CTA = cta_pill()

def sc_end(t):
    cv = END_BG.copy(); d = ImageDraw.Draw(cv)
    for i in range(28):  # rayos dorados girando
        a = 2 * math.pi * i / 28 + t * .3; r0, r1 = 360, 360 + 360 * eo(t / .8)
        d.line((540 + r0 * math.cos(a), 640 + r0 * math.sin(a), 540 + r1 * math.cos(a), 640 + r1 * math.sin(a)),
               fill=(120, 74, 26), width=10)
    put(cv, HERO, 540, 640 + 10 * math.sin(t * 2), elastic(t / .9) * (1 + .02 * pulse(t)))
    draw_steam(cv, t, 520, .6)
    put(cv, LOGO_S, 820, 330, back((t - b(1)) / .4) if t > b(1) else 0, 1, 8)
    enter(cv, text_img("TORTA DE", F_BLK, 96, WHT), t, b(1.4), 540, 1080, "up")
    enter(cv, sweep(gold_text("CUAJADA", 190), ((t - b(2.4)) % 3) / .9), t, b(1.9), 540, 1215, "slam")
    enter(cv, text_img("Baruj Shefa · Receta de la abuela", F_PFI, 50, CRM), t, b(2.8), 540, 1350, "fade")
    if t > b(3.6):
        k = (t - b(3.6)) / .4
        put(cv, CTA, 540, 1490, back(k, 2.6) * (1 + .05 * pulse(t)), 1)
    enter(cv, text_img("con tu vendedor más cercano", F_XB, 46, GOLD2), t, b(4.4), 540, 1610, "up")
    draw_sparks(cv, t)
    # franja inferior libre para el contacto del vendedor
    ks = eo((t - b(5)) / .5)
    if ks > 0:
        d = ImageDraw.Draw(cv); y0 = int(H - 220 * ks)
        d.rectangle((0, y0, W, H), fill=CRM); d.rectangle((0, y0, W, y0 + 8), fill=GOLD)
    return cv

def punch(prev, cur, k):
    """Transición zoom-blur con destello."""
    e = eo(k)
    if k < .5:
        z = 1 + .35 * (k / .5) ** 2
        im = prev.resize((int(W * z), int(H * z)), Image.BILINEAR)
        im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
        im = im.filter(ImageFilter.GaussianBlur(18 * k / .5))
    else:
        z = 1.35 - .35 * eo((k - .5) / .5)
        im = cur.resize((int(W * z), int(H * z)), Image.BILINEAR)
        im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
        im = im.filter(ImageFilter.GaussianBlur(18 * (1 - (k - .5) / .5)))
    fl = 1 - abs(k - .5) * 2
    return Image.blend(im, Image.new("RGB", (W, H), (255, 236, 200)), .45 * fl)

def whip(prev, cur, k, sgn=1):
    e = eio(k); out = Image.new("RGB", (W, H))
    out.paste(prev, (int(-sgn * e * W), 0)); out.paste(cur, (int(sgn * (W - e * W)), 0))
    return out.filter(ImageFilter.BoxBlur(int(30 * (1 - abs(2 * k - 1)))))

SCENES = [(4, sc_hook, None), (4, sc_dorada, "punch"), (4, sc_suave, "whip"), (4, sc_horno, "punch"),
          (8, sc_autoridad, "whip"), (4, sc_bogota, "punch"), (12, sc_end, "punch")]
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
DUR = b(acc); TR = .36

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
        out = punch(prev, fr, lt / TR) if tr == "punch" else whip(prev, fr, lt / TR, 1 if si % 2 else -1)
    if fi < 6: out = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), out, fi / 6)
    ff.stdin.write(out.tobytes())
    if fi % 120 == 0: print(f"{fi}/{N}", flush=True)
ff.stdin.close(); ff.wait()
print(f"DUR={DUR:.2f}")
