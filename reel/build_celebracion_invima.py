#!/usr/bin/env python3
"""Reel CELEBRACIÓN "¡Un gran paso!": registro sanitario INVIMA de Baruj Shefa (1080x1920).

Une material propio + fotos de stock libres (Wikimedia Commons) + logos de
Baruj Shefa, Mercados Campesinos, Secretaría de Desarrollo Económico / Bogotá y sello INVIMA.

Uso: python3 build_celebracion.py <medios> <fuentes> <musica.wav> <final.mp4> <carpeta_fotogramas>
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL, SNAP = sys.argv[1:6]
os.makedirs(SNAP, exist_ok=True)
W, H, FPS, BPM = 1080, 1920, 30, 120
BEAT = 60 / BPM
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "celebracion", "assets")

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
P = dict(duo=m("c5266882"), cart=m("c47cb03b"), spoon=m("0f60c5bb"), almo=m("a0cf5d80"), torta=m("6351a50d"),
         kitchen=m("0b8446a6"), oven_prod=m("7bc77db3"), oven=m("5efb0aea"), flyer1=m("d7a2769d"), flyer2=m("3afcc1dc"),
         mc_plaza=os.path.join(ASSETS, "stock_mercados_campesinos_plaza.jpg"),
         plaza=os.path.join(ASSETS, "stock_plaza_mercado_bogota.jpg"),
         canastos=os.path.join(ASSETS, "stock_canastos_plaza_restrepo.jpg"))
LOGO, OVEN_V = m("777dda90"), m("501b5a86")

F_FUN = os.path.join(FONTS, "luckiest-guy-latin-400-normal.ttf")
F_RND = os.path.join(FONTS, "fredoka-latin-700-normal.ttf")
F_RND6 = os.path.join(FONTS, "fredoka-latin-600-normal.ttf")
F_PF = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")

GRN, GRN2 = (29, 107, 58), (40, 130, 72)
ORA, PNK, YEL = (244, 123, 32), (230, 0, 126), (255, 205, 60)
CHOC, TERRA, GOLD = (74, 36, 14), (196, 86, 44), (222, 168, 66)
CRM, CRM2, WHT = (250, 241, 224), (240, 226, 200), (255, 255, 255)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=2.0): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    return x if x in (0, 1) else 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1
def pulse(t): return math.exp(-((t / BEAT) % 1) * 7)
def b(n): return n * BEAT

def warm(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.07 + 128 + np.array([7, 3, -6]); l = a.mean(2, keepdims=True); a = l + (a - l) * 1.2
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
IM = {k: warm(ImageOps.exif_transpose(Image.open(p)).convert("RGB")) for k, p in P.items()}
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
        if len(buf) == w * h * 3: self.last = warm(Image.frombuffer("RGB", (w, h), buf))
        return self.last

# ---------- texto ----------
_c = {}
def txt(text, font, size, fill, stroke=0, sfill=None, shadow=False, lh=1.05, maxw=None):
    k = (text, font, size, fill, stroke, sfill, shadow, lh, maxw)
    if k in _c: return _c[k]
    f = ImageFont.truetype(font, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    rows = []
    for para in text.split("\n"):
        if not maxw: rows.append(para); continue
        cur = ""
        for w_ in para.split():
            t2 = (cur + " " + w_).strip()
            if tmp.textlength(t2, font=f) <= maxw: cur = t2
            else: rows.append(cur); cur = w_
        rows.append(cur)
    a, d_ = f.getmetrics(); L = int((a + d_) * lh); ws = [tmp.textlength(r, font=f) for r in rows]
    pad = 30 + stroke
    img = Image.new("RGBA", (int(max(ws)) + 2 * pad, L * len(rows) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        d.text((pad + (max(ws) - ws[i]) / 2, pad + i * L), r, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); blk = Image.new("RGBA", img.size, (20, 8, 0, 255))
        blk.putalpha(img.getchannel("A")); sh.alpha_composite(blk, (4, 7)); sh = sh.filter(ImageFilter.GaussianBlur(9))
        sh = Image.alpha_composite(sh, sh); sh.alpha_composite(img); img = sh
    _c[k] = img; return img

def put(cv, img, cx, cy, sc=1., al=1., rot=0.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BICUBIC, expand=True)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def enter(cv, img, t, t0, cx, cy, kind="pop", rot=0.):
    if t < t0: return
    k = (t - t0) / .4; sc, al, x, y = 1., 1., cx, cy
    if kind == "pop": sc = back(k, 2.4) * (1 + .03 * pulse(t) * (k > 1)); al = eo(k * 3)
    elif kind == "elastic": sc = elastic((t - t0) / .8)
    elif kind == "drop": y = cy - (1 - back(k, 1.6)) * 800
    elif kind == "up": y = cy + (1 - eo(k)) * 120; al = eo(k * 1.4)
    elif kind == "left": x = cx - (1 - eo(k)) * 1200
    elif kind == "right": x = cx + (1 - eo(k)) * 1200
    elif kind == "slam": sc = 1 + 1.8 * (1 - eo(k)); al = eo(k * 2.5)
    put(cv, img, x, y, sc, al, rot)

def pill(img, bg, pad=(36, 22), r=None):
    w, h = img.width + 2 * pad[0], img.height + 2 * pad[1]; r = r or h // 2
    out = Image.new("RGBA", (w + 14, h + 18), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.rounded_rectangle((6, 12, w + 6, h + 12), r, fill=(0, 0, 0, 80)); d.rounded_rectangle((0, 0, w, h), r, fill=bg)
    out.alpha_composite(img, pad); return out

# ---------- logos ----------
def round_logo(size, ring=YEL, rw=12):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 2 * rw, size - 2 * rw), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((3, 3, lg.width - 3, lg.height - 3), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (rw, rw), mk); return out
LOGO_BIG, LOGO_MID, LOGO_SM = round_logo(520), round_logo(330), round_logo(120, WHT, 6)
def fit_h(im, h): return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
MC = Image.open(os.path.join(ASSETS, "logo_mercados_campesinos.png")).convert("RGBA")
MC_PILL = pill(fit_h(MC, 150), GRN, (40, 18), 40)
SDE = fit_h(Image.open(os.path.join(ASSETS, "logo_sde.png")).convert("RGBA"), 64)
BOG = Image.open(os.path.join(ASSETS, "logo_bogota.png")).convert("RGBA")
def rounded_img(img, r):
    img = img.convert("RGBA"); mk = Image.new("L", img.size, 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255); img.putalpha(mk); return img
BOG = rounded_img(fit_h(BOG, 120), 18)

def invima_seal(s=300):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pts = [(s / 2 + (s / 2 - 3) * (1 if i % 2 == 0 else .92) * math.cos(math.pi * i / 20),
            s / 2 + (s / 2 - 3) * (1 if i % 2 == 0 else .92) * math.sin(math.pi * i / 20)) for i in range(40)]
    d.polygon(pts, fill=(24, 90, 60)); d.ellipse((26, 26, s - 26, s - 26), outline=GOLD, width=5)
    put(img, txt("REGISTRO\nSANITARIO", F_RND6, int(s * .09), WHT, lh=.95), s / 2, s / 2 - s * .17)
    put(img, txt("INVIMA", F_PF, int(s * .2), GOLD), s / 2, s / 2 + s * .06)
    put(img, txt("COLOMBIA", F_RND6, int(s * .075), WHT), s / 2, s / 2 + s * .27)
    return img
SEAL, SEAL_SM = invima_seal(340), invima_seal(150)

# ---------- efectos ----------
rng = np.random.default_rng(9)
PAL = [YEL, ORA, PNK, WHT, (120, 200, 90), (90, 170, 230)]
def make_conf(n, burst=True):
    out = []
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); v = rng.uniform(500, 1500)
        out.append(dict(x=540, y=760, vx=math.cos(a) * v if burst else rng.uniform(-40, 40),
                        vy=math.sin(a) * v - 500 if burst else rng.uniform(250, 520),
                        x0=rng.uniform(0, W), y0=rng.uniform(-1200, -30), r=rng.uniform(0, 360),
                        vr=rng.uniform(-400, 400), c=PAL[rng.integers(len(PAL))], s=rng.uniform(12, 24),
                        shape=rng.integers(3)))
    return out
BURST, RAIN = make_conf(140), make_conf(120, False)
def confetti(cv, t, parts, burst=True):
    d = ImageDraw.Draw(cv)
    for c in parts:
        if burst:
            x = c["x"] + c["vx"] * t * math.exp(-t * .9); y = c["y"] + c["vy"] * t * math.exp(-t * .9) + 380 * t * t
        else:
            x = c["x0"] + c["vx"] * t + 30 * math.sin(t * 3 + c["r"]); y = c["y0"] + c["vy"] * t
        if not (-40 < y < H + 40): continue
        a = math.radians(c["r"] + c["vr"] * t); s = c["s"]
        if c["shape"] == 0:
            d.ellipse((x - s / 2, y - s / 2, x + s / 2, y + s / 2), fill=c["c"])
        else:
            dx, dy = math.cos(a) * s, math.sin(a) * s * .45
            d.polygon([(x - dx, y - dy), (x + dy, y - dx * .4), (x + dx, y + dy), (x - dy, y + dx * .4)], fill=c["c"])

def rays_bg(c1, c2, n=20):
    big = Image.new("RGB", (2600, 2600), c1); d = ImageDraw.Draw(big)
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = a0 + math.pi / n
        d.polygon([(1300, 1300), (1300 + 2000 * math.cos(a0), 1300 + 2000 * math.sin(a0)),
                   (1300 + 2000 * math.cos(a1), 1300 + 2000 * math.sin(a1))], fill=c2)
    return big
RAYS_T, RAYS_G = rays_bg(TERRA, (214, 104, 56)), rays_bg(GRN, GRN2)
def rays(big, t, sp=8, cy=760):
    r = big.rotate(t * sp, Image.BILINEAR); oy = 1300 - cy
    return r.crop((760, oy, 1840, oy + H)).convert("RGBA")

def waves_bg():
    bg = Image.new("RGB", (W, H), GRN); d = ImageDraw.Draw(bg)
    for y in range(-80, H + 120, 120):
        d.line([(x, y + 26 * math.sin(x / 70)) for x in range(0, W + 10, 10)], fill=GRN2, width=34)
    return bg.convert("RGBA")
WAVES = waves_bg()

def grad(top=0, bot=0, color=(20, 10, 2)):
    y = np.arange(H)[:, None].astype(float); a = np.zeros((H, 1))
    if bot: a = np.maximum(a, np.clip((y - (H - bot)) / bot, 0, 1) ** 1.1 * 240)
    if top: a = np.maximum(a, np.clip(1 - y / top, 0, 1) ** 1.1 * 220)
    g = np.zeros((H, W, 4), np.uint8); g[..., :3] = color; g[..., 3] = np.repeat(a, W, 1).astype(np.uint8)
    return Image.fromarray(g)
G_BOT, G_TOP = grad(bot=900), grad(top=700)

def polaroid(img, cap, w=640, h=700, c=(.5, .45), z=1.0):
    ph = view(img, z, *c, w=w, h=h)
    card = Image.new("RGBA", (w + 70, h + 200), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((18, 24, w + 64, h + 196), fill=(0, 0, 0, 120))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(card); d.rectangle((0, 0, w + 44, h + 180), fill=(255, 253, 248)); card.paste(ph, (22, 22))
    t = txt(cap, F_SC, 76, CHOC); card.alpha_composite(t, ((w + 44 - t.width) // 2, h + 40))
    return card

def poster(img, w=470):
    p = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS).convert("RGBA")
    out = Image.new("RGBA", (w + 40, p.height + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((14, 20, w + 34, p.height + 34), fill=(0, 0, 0, 130))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); out.alpha_composite(p, (10, 10)); return out

# ---------- escenas ----------
def sc_open(t):
    cv = rays(RAYS_T, t, 12)
    put(cv, LOGO_BIG, 540, 760, elastic(t / .9) * (1 + .03 * pulse(t)), 1, (1 - eo(t / .9)) * -120)
    if t > .5: confetti(cv, t - .5, BURST)
    enter(cv, txt("Hoy celebramos", F_SC, 120, WHT, shadow=True), t, b(1.6), 540, 1150, "up")
    enter(cv, txt("¡UN GRAN", F_FUN, 150, YEL, 9, CHOC, True), t, b(2.4), 540, 1340, "slam", -3)
    enter(cv, txt("PASO!", F_FUN, 200, WHT, 10, CHOC, True), t, b(3.2), 540, 1530, "slam", 3)
    return cv

POL1 = polaroid(IM["duo"], "abuela y nieta", c=(.5, .38))
POL2 = polaroid(IM["cart"], "nuestro primer carrito", c=(.5, .38))
def sc_story(t):
    cv = Image.new("RGBA", (W, H), CRM); d = ImageDraw.Draw(cv)
    for i in range(0, H, 60): d.line((0, i, W, i), fill=CRM2, width=2)
    k1, k2 = (t - .1) / .6, (t - b(3.5)) / .6
    if t > .1: put(cv, POL1, 420, 760 - (1 - back(k1, 1.3)) * 1500, .74, 1, -7 + (1 - eo(k1)) * 30)
    if t > b(3.5): put(cv, POL2, 720, 1180 - (1 - back(k2, 1.3)) * 1500, .56, 1, 7 - (1 - eo(k2)) * 30)
    enter(cv, txt("Todo empezó con", F_RND, 70, CHOC), t, .3, 540, 170, "up")
    enter(cv, txt("una receta de familia", F_PF, 80, TERRA), t, .8, 540, 270, "up")
    enter(cv, pill(txt("y un sueño compartido", F_RND, 60, WHT), TERRA), t, b(5), 540, 1700, "pop", -2)
    return cv

def sc_mercados(t):
    half = b(5)
    if t < half:
        cv = view(IM["mc_plaza"], 1.3 + .1 * eio(t / half), .42, .78).convert("RGBA")
    else:
        cv = view(IM["plaza"], 1.15 - .1 * eio((t - half) / half), .5, .5).convert("RGBA")
        if t - half < .4: cv = Image.blend(view(IM["mc_plaza"], 1.4, .42, .78).convert("RGBA"), cv, eio((t - half) / .4))
    cv.alpha_composite(G_BOT); cv.alpha_composite(G_TOP)
    enter(cv, txt("Hoy llevamos nuestro sabor a los", F_RND, 56, WHT, shadow=True, maxw=950), t, .3, 540, 230, "up")
    enter(cv, MC_PILL, t, b(1.5), 540, 1420, "elastic", -2)
    enter(cv, txt("de Bogotá", F_FUN, 110, YEL, 7, CHOC, True), t, b(2.6), 540, 1640, "slam", 2)
    return cv

POST1, POST2 = poster(IM["flyer1"]), poster(IM["flyer2"])
def sc_apoyo(t):
    cv = WAVES.copy()
    k1, k2 = (t - .1) / .55, (t - .5) / .55
    if t > .1: put(cv, POST1, 330 - (1 - eo(k1)) * 900, 700, .95 + .02 * pulse(t), 1, -8)
    if t > .5: put(cv, POST2, 750 + (1 - eo(k2)) * 900, 760, .95 + .02 * pulse(t), 1, 7)
    card = Image.new("RGBA", (980, 480), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((8, 14, 978, 478), 46, fill=(0, 0, 0, 90)); cd.rounded_rectangle((0, 0, 970, 466), 46, fill=CRM)
    tt = txt("Gracias al apoyo de", F_RND6, 46, CHOC); card.alpha_composite(tt, ((970 - tt.width) // 2, 20))
    card.alpha_composite(BOG, ((970 - BOG.width) // 2, 120))
    card.alpha_composite(SDE, ((970 - SDE.width) // 2, 270))
    t3 = txt("por abrirnos las puertas de sus ferias", F_RND6, 38, TERRA); card.alpha_composite(t3, ((970 - t3.width) // 2, 360))
    if t > b(2.5):
        k = (t - b(2.5)) / .5; put(cv, card, 540, 1540 + (1 - eo(k)) * 700, 1, 1)
    enter(cv, txt("¡Gracias, Bogotá!", F_FUN, 96, YEL, 7, CHOC, True), t, b(1.3), 540, 180, "pop", -2)
    return cv

def sc_calidad(t):
    cv = view(IM["kitchen"], 1.12 - .08 * eio(t / b(8)), .58, .4).convert("RGBA")
    cv.alpha_composite(Image.new("RGBA", (W, H), (30, 14, 4, 110))); cv.alpha_composite(G_BOT)
    enter(cv, txt("Hecho con amor…", F_SC, 110, WHT, shadow=True), t, .2, 540, 260, "up")
    enter(cv, txt("y con todos los estándares", F_RND, 58, WHT, shadow=True), t, .9, 540, 400, "up")
    if t > b(2.5): put(cv, SEAL, 540, 1210, elastic((t - b(2.5)) / .8) * (1 + .02 * pulse(t)), 1, 5 * math.sin(t * 1.6))
    enter(cv, pill(txt("Productos con registro sanitario INVIMA", F_RND, 44, WHT), (24, 90, 60)), t, b(4.5), 540, 1560, "up")
    return cv

MONT = [("spoon", "TRADICIÓN", ORA), ("almo", "SABOR", PNK), ("torta", "CALIDAD", GRN), ("OVEN", "¡AMOR!", TERRA)]
OVEN = {}
def sc_montaje(t):
    dur = b(3); si = min(int(t / dur), 3); lt = t - si * dur
    k, word, col = MONT[si]
    if k == "OVEN":
        if "v" not in OVEN: OVEN["v"] = Vid(OVEN_V, .3, .5)
        cv = view(OVEN["v"].frame(), 1.1 + .03 * pulse(t), .5, .5).convert("RGBA")
    else:
        z = (1.25 - .15 * eio(lt / dur)) * (1 + .03 * pulse(t))
        cv = view(IM[k], z, .5, .45 if k != "spoon" else .5).convert("RGBA")
    if lt < .12 and si > 0: cv = Image.blend(cv, Image.new("RGBA", (W, H), WHT), .7 * (1 - lt / .12))
    cv.alpha_composite(G_BOT)
    enter(cv, pill(txt(word, F_FUN, 130, WHT), col, (50, 20)), t, si * dur + .1, 540, 1560, "slam", [-4, 3, -3, 4][si])
    put(cv, LOGO_SM, 100, 110)
    return cv

def logos_strip():
    s = Image.new("RGBA", (W, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle((30, 0, W - 30, 390), 50, fill=WHT)
    t = txt("Calidad respaldada · Juntos seguimos creciendo", F_RND6, 34, CHOC); s.alpha_composite(t, ((W - t.width) // 2, 6))
    mc = pill(fit_h(MC, 92), GRN, (24, 14), 26)
    row = [SEAL_SM, mc, BOG]; gap = 34; tot = sum(r.width for r in row) + gap * 2; x = (W - tot) // 2
    for r in row: s.alpha_composite(r, (x, 175 - r.height // 2)); x += r.width + gap
    s.alpha_composite(SDE, ((W - SDE.width) // 2, 285)); return s
STRIP = logos_strip()
def sc_final(t):
    cv = rays(RAYS_G, t, 6, 560)
    confetti(cv, t, RAIN, False)
    put(cv, LOGO_MID, 540, 470, elastic(t / .9) * (1 + .03 * pulse(t)), 1, -6 * math.sin(t * 1.5))
    enter(cv, txt("¡GRACIAS", F_FUN, 130, YEL, 9, CHOC, True), t, b(1), 540, 800, "slam", -3)
    enter(cv, txt("POR SER PARTE!", F_FUN, 104, WHT, 8, CHOC, True), t, b(1.8), 540, 940, "slam", 2)
    enter(cv, txt("Esto apenas comienza…", F_SC, 96, WHT, shadow=True), t, b(3), 540, 1090, "up")
    enter(cv, pill(txt("Baruj Shefa · Ahora con registro INVIMA", F_RND, 40, CHOC), YEL), t, b(4), 540, 1230, "pop")
    if t > b(5):
        k = eo((t - b(5)) / .6); cv.alpha_composite(STRIP, (0, int(1440 + (1 - k) * 600)))
    if t > b(7):
        put(cv, txt("Fotos de mercados: Wikimedia Commons", F_RND6, 22, (230, 240, 230)), 540, 1880, 1, eo((t - b(7)) / .5))
    return cv

SEAL_BIG = invima_seal(520)
def sc_invima(t):
    cv = rays(RAYS_G, t, 10, 900)
    enter(cv, txt("Hoy ese sueño tiene un respaldo:", F_RND, 56, WHT, shadow=True, maxw=960), t, .2, 540, 230, "up")
    tr = b(1.5)
    if t > tr:
        k = (t - tr) / .9
        glow = Image.new("RGBA", (760, 760), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((60, 60, 700, 700), fill=(255, 230, 140, 150))
        put(cv, glow.filter(ImageFilter.GaussianBlur(50)), 540, 860, eo(k) * (1 + .05 * pulse(t)), 1)
        put(cv, SEAL_BIG, 540, 860, elastic(k) * (1 + .02 * pulse(t)), 1, 4 * math.sin(t * 1.4))
        confetti(cv, t - tr, BURST)
    enter(cv, txt("¡LO LOGRAMOS!", F_FUN, 140, YEL, 9, CHOC, True), t, b(3), 540, 1270, "slam", -3)
    enter(cv, pill(txt("Registro sanitario INVIMA", F_RND, 58, WHT), TERRA, (44, 18)), t, b(4.2), 540, 1450, "pop", 2)
    enter(cv, txt("para nuestros productos y nuestra planta de producción", F_RND6, 46, WHT, shadow=True, maxw=900, lh=1.15),
          t, b(5.4), 540, 1620, "up")
    return cv

PLANTA = [("oven_prod", 1.1, 1.2, .5, .5), ("kitchen", 1.18, 1.05, .58, .4)]
CHIPS = ["Planta con aval INVIMA", "Procesos de higiene y calidad", "La receta de la abuela, intacta"]
def chip(text):
    r = Image.new("RGBA", (900, 112), (0, 0, 0, 0)); d = ImageDraw.Draw(r)
    d.rounded_rectangle((6, 10, 896, 110), 50, fill=(0, 0, 0, 90)); d.rounded_rectangle((0, 0, 890, 100), 50, fill=CRM)
    d.ellipse((16, 14, 88, 86), fill=(37, 150, 90)); d.line([(34, 50), (48, 64), (72, 36)], fill=WHT, width=9, joint="curve")
    tx = txt(text, F_RND, 42, CHOC); r.alpha_composite(tx, (98, (100 - tx.height) // 2)); return r
CHIP_IM = [chip(c) for c in CHIPS]
SEAL_MD = invima_seal(210)
def sc_planta(t):
    dur = b(5); si = min(int(t / dur), 1); lt = t - si * dur
    k, z0, z1, cx, cy = PLANTA[si]; cv = view(IM[k], z0 + (z1 - z0) * eio(lt / dur), cx, cy).convert("RGBA")
    if lt < .45 and si > 0:
        pk, pz0, pz1, pcx, pcy = PLANTA[0]; cv = Image.blend(view(IM[pk], pz1, pcx, pcy).convert("RGBA"), cv, eio(lt / .45))
    cv.alpha_composite(Image.new("RGBA", (W, H), (30, 14, 4, 90))); cv.alpha_composite(G_BOT); cv.alpha_composite(G_TOP)
    enter(cv, txt("Nuestra planta", F_FUN, 104, WHT, 8, CHOC, True), t, .2, 540, 230, "slam", -2)
    enter(cv, txt("de producción", F_FUN, 104, YEL, 8, CHOC, True), t, .6, 540, 360, "slam", 2)
    for i, c in enumerate(CHIP_IM):
        enter(cv, c, t, b(2.4 + 1.6 * i), 540, 1320 + 135 * i, "left" if i % 2 == 0 else "right")
    put(cv, SEAL_MD, 540, 1110, back((t - b(1.4)) / .5) if t > b(1.4) else 0, 1, 6)
    return cv

PRODS = [("torta", "Torta de Cuajada", "INVIMA RSA-6500-2026", .55), ("almo", "Almojábanas del Campo", "INVIMA RSA-6561-2026", .45)]
def sc_productos(t):
    dur = b(5); si = min(int(t / dur), 1); lt = t - si * dur
    k, name, reg, cy = PRODS[si]
    cv = view(IM[k], (1.22 - .12 * eio(lt / dur)) * (1 + .02 * pulse(t)), .5, cy).convert("RGBA")
    if lt < .12 and si > 0: cv = Image.blend(cv, Image.new("RGBA", (W, H), WHT), .7 * (1 - lt / .12))
    cv.alpha_composite(G_BOT)
    pk = eo(lt / .5); py = int(1460 + (1 - pk) * 600)
    panel = Image.new("RGBA", (W, 460), (0, 0, 0, 0)); pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((40, 0, W - 40, 420), 50, fill=CRM)
    n = txt(name, F_PF, 74, CHOC); panel.alpha_composite(n, ((W - n.width) // 2, 30))
    rp = pill(txt(reg, F_RND, 44, WHT), (24, 90, 60), (34, 14)); panel.alpha_composite(rp, ((W - rp.width) // 2, 170))
    tg = txt("Calidad certificada en cada bocado", F_RND6, 36, TERRA); panel.alpha_composite(tg, ((W - tg.width) // 2, 300))
    cv.alpha_composite(panel, (0, py))
    put(cv, SEAL_SM, 940, 130, 1, 1, 8); put(cv, LOGO_SM, 100, 110)
    return cv

APOYO_CARD = None
def sc_crecer(t):
    global APOYO_CARD
    cv = view(IM["mc_plaza"], 1.3 + .1 * eio(t / b(10)), .42, .78).convert("RGBA")
    cv.alpha_composite(G_BOT); cv.alpha_composite(G_TOP)
    enter(cv, txt("Y seguimos creciendo en los", F_RND, 58, WHT, shadow=True), t, .2, 540, 220, "up")
    enter(cv, MC_PILL, t, b(1.2), 540, 390, "elastic", -2)
    if APOYO_CARD is None:
        card = Image.new("RGBA", (980, 440), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((8, 14, 978, 438), 46, fill=(0, 0, 0, 90)); cd.rounded_rectangle((0, 0, 970, 426), 46, fill=CRM)
        tt = txt("con el apoyo de", F_RND6, 44, CHOC); card.alpha_composite(tt, ((970 - tt.width) // 2, 16))
        card.alpha_composite(BOG, ((970 - BOG.width) // 2, 115)); card.alpha_composite(SDE, ((970 - SDE.width) // 2, 265))
        APOYO_CARD = card
    if t > b(3):
        k = eo((t - b(3)) / .55); put(cv, APOYO_CARD, 540, 1560 + (1 - k) * 700, 1, 1)
    return cv

def iris(prev, cur, k):
    r = int(eio(k) * 1150); mk = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mk).ellipse((540 - r, 960 - r, 540 + r, 960 + r), fill=255)
    out = prev.copy(); out.paste(cur, (0, 0), mk)
    if 0 < r < 1150: ImageDraw.Draw(out).ellipse((540 - r, 960 - r, 540 + r, 960 + r), outline=YEL, width=18)
    return out
def push(prev, cur, k, d=1):
    e = eio(k); out = Image.new("RGB", (W, H))
    out.paste(prev, (int(-d * e * W), 0)); out.paste(cur, (int(d * (W - e * W)), 0)); return out
def stripes(prev, cur, k):
    """Barras de colores de la feria que barren la pantalla."""
    out = prev.copy(); d = ImageDraw.Draw(out); cols = [YEL, ORA, PNK, GRN]
    for i, c in enumerate(cols):
        kk = clamp(k * 1.6 - i * .15); y = int(H * eio(kk))
        d.rectangle((i * W // 4, 0, (i + 1) * W // 4, y), fill=c)
    if k > .55:
        e = eio((k - .55) / .45); mk = Image.new("L", (W, H), 0); ImageDraw.Draw(mk).rectangle((0, 0, W, int(H * e)), fill=255)
        out.paste(cur, (0, 0), mk)
    return out

SCENES = [(8, sc_open, None), (8, sc_story, "iris"), (12, sc_invima, "stripes"), (10, sc_planta, "push"),
          (10, sc_productos, "iris"), (10, sc_crecer, "push"), (16, sc_final, "stripes")]
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
DUR = b(acc); TR = .5

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", MUSIC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev, cur, last = None, 0, None
N = int(DUR * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(starts) if b(s) <= t + 1e-6)
    if si != cur:
        last.save(os.path.join(SNAP, f"escena_{cur + 1}.png")); prev, cur = last, si
    _, fn, tr = SCENES[si]; lt = t - b(starts[si])
    fr = fn(lt).convert("RGB"); last = fr; out = fr
    if tr and lt < TR and prev is not None:
        out = iris(prev, fr, lt / TR) if tr == "iris" else push(prev, fr, lt / TR) if tr == "push" else stripes(prev, fr, lt / TR)
    if fi < 6: out = Image.blend(Image.new("RGB", (W, H), TERRA), out, fi / 6)
    ff.stdin.write(out.tobytes())
    if fi % 150 == 0: print(f"{fi}/{N}", flush=True)
last.save(os.path.join(SNAP, f"escena_{cur + 1}.png"))
ff.stdin.close(); ff.wait()
print(f"DUR={DUR:.2f}")
