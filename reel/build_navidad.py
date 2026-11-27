#!/usr/bin/env python3
"""Reel NAVIDAD COLOMBIANA – Combo Novena Baruj Shefa (1080x1920).

Noche de luces: guirnalda de bombillos que se enciende, velitas, destellos dorados,
calendario de novena (16–24 dic) que se ilumina noche a noche, "desempaque" del combo
con etiquetas que señalan cada producto y CTA de pedido.

Uso: python3 build_navidad.py <medios> <fuentes> <musica.wav> <final.mp4> <carpeta_fotogramas>
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL, SNAP = sys.argv[1:6]
os.makedirs(SNAP, exist_ok=True)
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 128
HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.join(HERE, "inversion", "assets"); NAV = os.path.join(HERE, "navidad", "assets")

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
P = dict(combo=os.path.join(NAV, "combo_novena.jpg"), duo=m("a4fe69f9"), spoon=m("e6bf323c"),
         horno=os.path.join(INV, "horno_dorado.jpg"), torta=os.path.join(INV, "torta_premium.jpg"),
         almo=os.path.join(INV, "almo_premium.jpg"), carrito=os.path.join(INV, "carrito_vendedores.jpg"),
         tortas=m("483610ce"))
LOGO = os.path.join(INV, "logo_hd.png")

F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")
F_PF = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"

NIGHT, NIGHT2 = (34, 8, 10), (70, 14, 20)
RED, RED2, GOLD, GOLD_L = (178, 24, 38), (130, 14, 26), (232, 182, 82), (255, 226, 150)
GREEN, CREAM, WHT = (22, 92, 58), (252, 240, 220), (255, 255, 255)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=1.8): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    return x if x in (0, 1) else 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1
def pulse(t): return math.exp(-((t / BEAT) % 1) * 7)

def warm(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.06 + 128 + np.array([8, 2, -6]); l = a.mean(2, keepdims=True); a = l + (a - l) * 1.15
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
IM = {k: warm(ImageOps.exif_transpose(Image.open(p)).convert("RGB")) for k, p in P.items()}
def view(img, z, cx, cy, w=W, h=H):
    iw, ih = img.size; s = max(w / iw, h / ih) * z; vw, vh = w / s, h / s
    l = clamp(cx * iw - vw / 2, 0, iw - vw); t = clamp(cy * ih - vh / 2, 0, ih - vh)
    return img.resize((int(w), int(h)), Image.BILINEAR, box=(l, t, l + vw, t + vh))

_c = {}
def txt(text, font, size, fill, maxw=None, lh=1.1, align="center", shadow=True):
    k = (text, font, size, fill, maxw, lh, align, shadow)
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
    a, d_ = f.getmetrics(); L = int((a + d_) * lh); ws = [tmp.textlength(r, font=f) for r in rows]; pad = 30
    img = Image.new("RGBA", (int(max(ws)) + 2 * pad, L * len(rows) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        x = pad + ((max(ws) - ws[i]) / 2 if align == "center" else 0); d.text((x, pad + i * L), r, font=f, fill=fill)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); blk = Image.new("RGBA", img.size, (15, 2, 4, 255))
        blk.putalpha(img.getchannel("A")); sh.alpha_composite(blk, (3, 6)); sh = sh.filter(ImageFilter.GaussianBlur(10))
        sh = Image.alpha_composite(sh, sh); sh.alpha_composite(img); img = sh
    _c[k] = img; return img

def put(cv, img, cx, cy, sc=1., al=1., rot=0.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BICUBIC, expand=True)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def enter(cv, img, t, t0, cx, cy, kind="up", rot=0.):
    if t < t0: return
    k = (t - t0) / .45; sc, al, x, y = 1., 1., cx, cy
    if kind == "up": y = cy + (1 - eo(k)) * 80; al = eo(k * 1.4)
    elif kind == "pop": sc = back(k, 2.2); al = eo(k * 3)
    elif kind == "elastic": sc = elastic((t - t0) / .8)
    elif kind == "fade": al = eo(k)
    elif kind == "left": x = cx - (1 - eo(k)) * 1200
    elif kind == "right": x = cx + (1 - eo(k)) * 1200
    put(cv, img, x, y, sc, al, rot)

# ---------- ambiente navideño ----------
def make_night():
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * .4) / H) ** 2)
    g = np.clip(1 - r * 1.4, 0, 1)[..., None]
    a = np.array(NIGHT) * (1 - g) + np.array(NIGHT2) * g
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")
NIGHT_BG = make_night()
rng = np.random.default_rng(4)
BOKEH = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), r=rng.uniform(25, 80), c=[GOLD, RED, (90, 200, 120), GOLD_L][rng.integers(4)],
              ph=rng.uniform(0, 6.3), sp=rng.uniform(8, 25)) for _ in range(34)]
def bokeh(cv, t, strength=1.):
    lay = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for b in BOKEH:
        y = (b["y"] - t * b["sp"]) % H; a = int((60 + 50 * math.sin(t * 1.5 + b["ph"])) * strength)
        r = b["r"] / 2; d.ellipse((b["x"] / 2 - r, y / 2 - r, b["x"] / 2 + r, y / 2 + r), fill=b["c"] + (a,))
    cv.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR))

BULB_C = [RED, GOLD, (60, 170, 100), (90, 150, 230), (240, 120, 40)]
def garland(cv, t, y0=70, sag=70, n=13, t_on=0.0, speed=.08):
    """Guirnalda de bombillos colombiana que se enciende uno a uno y titila."""
    d = ImageDraw.Draw(cv); pts = [(x, y0 + sag * math.sin(math.pi * x / W)) for x in range(-20, W + 40, 20)]
    d.line(pts, fill=(40, 30, 24), width=5)
    glow = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for i in range(n):
        x = (i + .5) * W / n; y = y0 + sag * math.sin(math.pi * x / W) + 26
        on = t > t_on + i * speed; c = BULB_C[i % 5]
        tw = .65 + .35 * math.sin(t * 6 + i * 1.7)
        if on: gd.ellipse((x - 34, y - 34 - y0 + 150, x + 34, y + 34 - y0 + 150), fill=c + (int(110 * tw),))
        d.rectangle((x - 7, y - 26, x + 7, y - 14), fill=(70, 60, 50))
        d.ellipse((x - 13, y - 16, x + 13, y + 18), fill=c if on else (70, 50, 46))
        if on: d.ellipse((x - 5, y - 8, x + 2, y), fill=(255, 255, 255))
    cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)), (0, y0 - 150))

def candle(t, ph=0., s=1.):
    c = Image.new("RGBA", (120, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((38, 120, 82, 300), 8, fill=CREAM); d.line((60, 120, 60, 104), fill=(60, 40, 30), width=3)
    fl = 1 + .12 * math.sin(t * 13 + ph) + .06 * math.sin(t * 29 + ph)
    gl = Image.new("RGBA", (120, 200), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse((10, 20, 110, 140), fill=(255, 190, 80, 120))
    c.alpha_composite(gl.filter(ImageFilter.GaussianBlur(16)), (0, 0))
    d.ellipse((60 - 13, 104 - 42 * fl, 60 + 13, 108), fill=(255, 200, 70)); d.ellipse((60 - 6, 104 - 24 * fl, 60 + 6, 106), fill=(255, 250, 220))
    return c

SPARK = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
ImageDraw.Draw(SPARK).polygon([(30, 0), (35, 25), (60, 30), (35, 35), (30, 60), (25, 35), (0, 30), (25, 25)], fill=GOLD_L)
SPARKS = [dict(x=rng.uniform(60, W - 60), y=rng.uniform(250, 1700), t0=rng.uniform(0, 2), s=rng.uniform(.4, 1.1)) for _ in range(18)]
def sparkles(cv, t):
    for s in SPARKS:
        lt = (t - s["t0"]) % 1.8
        if lt < .7: k = math.sin(math.pi * lt / .7); put(cv, SPARK, s["x"], s["y"], s["s"] * k, k, lt * 90)

def round_logo(size, ring=GOLD, rw=8):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 2 * rw, size - 2 * rw), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((3, 3, lg.width - 3, lg.height - 3), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (rw, rw), mk); return out
LOGO_S, LOGO_M = round_logo(120), round_logo(250)

def ornament_photo(key, size, c=(.5, .5), z=1.0):
    """Foto dentro de una bola de Navidad (círculo con aro dorado y gancho)."""
    ph = view(IM[key], z, *c, size, size).convert("RGBA")
    mk = Image.new("L", (size, size), 0); ImageDraw.Draw(mk).ellipse((0, 0, size - 1, size - 1), fill=255); ph.putalpha(mk)
    out = Image.new("RGBA", (size + 40, size + 110), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.line((size / 2 + 20, 0, size / 2 + 20, 60), fill=GOLD, width=4)
    d.rounded_rectangle((size / 2 - 22, 52, size / 2 + 62, 92), 10, fill=GOLD)
    d.ellipse((0, 70, size + 39, size + 109), fill=GOLD); out.alpha_composite(ph, (20, 90))
    return out

def grad(top=0, bot=0):
    y = np.arange(H)[:, None].astype(float); a = np.zeros((H, 1))
    if bot: a = np.maximum(a, np.clip((y - (H - bot)) / bot, 0, 1) ** 1.1 * 240)
    if top: a = np.maximum(a, np.clip(1 - y / top, 0, 1) ** 1.1 * 230)
    g = np.zeros((H, W, 4), np.uint8); g[..., :3] = NIGHT; g[..., 3] = np.repeat(a, W, 1).astype(np.uint8); return Image.fromarray(g)
G_BOT, G_TOP = grad(bot=950), grad(top=650)

# ---------- escenas ----------
def sc1(t):  # 0–4.7  la noche se enciende
    cv = NIGHT_BG.copy(); bokeh(cv, t, eo(t / 1.5)); garland(cv, t, 80, 70, 13, .2, .1)
    for i, x in enumerate([200, 380, 700, 880]):
        if t > .6 + .25 * i: put(cv, candle(t, i * 1.3), x, 1640, .9 if i in (1, 2) else .75, eo((t - .6 - .25 * i) / .4))
    enter(cv, txt("Llegó la", F_PFI, 90, CREAM), t, 1.3, 540, 650, "up")
    enter(cv, txt("Navidad", F_SC, 260, GOLD_L), t, 1.8, 540, 840, "elastic")
    enter(cv, txt("A LA COLOMBIANA", F_BLK, 74, WHT), t, 2.8, 540, 1060, "pop")
    enter(cv, txt("novenas · villancicos · reunión", F_PFI, 50, CREAM), t, 3.5, 540, 1170, "fade")
    sparkles(cv, t); return cv

ORN = [("duo", (.5, .33), 1.1), ("horno", (.5, .62), 1.0), ("tortas", (.5, .5), 1.2)]
def sc2(t):  # 4.7–10.3  la tradición
    cv = NIGHT_BG.copy(); bokeh(cv, t + 5, .8); garland(cv, t + 5, 80, 70)
    pos = [(300, 640, -6), (780, 720, 7), (540, 1150, -3)]
    for i, (k, c, z) in enumerate(ORN):
        t0 = .2 + .45 * i
        if t < t0: continue
        kk = (t - t0) / .7; x, y, r = pos[i]; sw = 4 * math.sin(t * 2 + i)
        put(cv, ornament_photo(k, 400 if i < 2 else 460, c, z), x, y - (1 - back(kk, 1.3)) * 1200, 1, 1, r + sw)
    enter(cv, txt("En cada novena hay una mesa llena…", F_PFI, 56, CREAM, maxw=950), t, 1.8, 540, 1540, "up")
    enter(cv, txt("y el sabor de la abuela", F_SC, 110, GOLD_L), t, 2.9, 540, 1680, "up")
    sparkles(cv, t); return cv

# Combo: posiciones en la foto original 1254x1254
CALL = [("Torta de cuajada", (370, 735), (250, 1520), RED),
        ("Almojábanas", (930, 470), (850, 760), GREEN),
        ("Salsa de mora", (760, 830), (520, 1640), RED2),
        ("Melao artesanal", (1015, 810), (840, 1520), (150, 90, 30))]
def sc3(t):  # 10.3–18.8  desempaque del combo
    cv = NIGHT_BG.copy(); bokeh(cv, t + 10, .6)
    size = 960; ox, oy = 60, 560; sc = size / 1254
    k = (t - .2) / .9
    if t > .2:
        ph = view(IM["combo"], 1.0 + .04 * eio(t / 8.5), .5, .5, size, size).convert("RGBA")
        mk = Image.new("L", (size, size), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, size - 1, size - 1), 50, fill=255); ph.putalpha(mk)
        fr = Image.new("RGBA", (size + 24, size + 24), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle((0, 0, size + 23, size + 23), 60, fill=GOLD)
        fr.alpha_composite(ph, (12, 12))
        put(cv, fr, ox + size / 2, oy + size / 2, .5 + .5 * back(k, 1.4), eo(k * 2), (1 - eo(k)) * -12)
    enter(cv, txt("NUEVO", F_BLK, 48, GOLD_L), t, .4, 540, 200, "fade")
    enter(cv, txt("Combo Novena", F_SC, 180, CREAM), t, .7, 540, 330, "elastic")
    enter(cv, txt("el sabor de la abuela, listo para compartir", F_PFI, 46, GOLD_L), t, 1.4, 540, 470, "up")
    d = ImageDraw.Draw(cv)
    for i, (name, (px, py), (lx, ly), col) in enumerate(CALL):
        t0 = 2.6 + 1.1 * i
        if t < t0: continue
        kk = eo((t - t0) / .5); sx, sy = ox + 12 + px * sc, oy + 12 + py * sc
        r = 18 + 6 * math.sin(t * 6); d.ellipse((sx - r, sy - r, sx + r, sy + r), outline=WHT, width=5); d.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), fill=WHT)
        ex, ey = sx + (lx - sx) * kk, sy + (ly - sy) * kk; d.line((sx, sy, ex, ey), fill=WHT, width=4)
        lab = Image.new("RGBA", (10, 10)); f = ImageFont.truetype(F_XB, 38); tw = ImageDraw.Draw(lab).textlength(name, font=f)
        lab = Image.new("RGBA", (int(tw) + 60, 84), (0, 0, 0, 0)); ld = ImageDraw.Draw(lab)
        ld.rounded_rectangle((0, 0, lab.width - 1, 83), 42, fill=col, outline=GOLD_L, width=3); ld.text((30, 18), name, font=f, fill=WHT)
        if kk > .5: put(cv, lab, clamp(lx, lab.width / 2 + 20, W - lab.width / 2 - 20), ly, back((t - t0 - .25) / .4), 1)
    sparkles(cv, t); return cv

USES = [("Tu novena en casa", "torta", (.5, .5), 1.15), ("La novena de la oficina", "almo", (.5, .45), 1.1),
        ("Regalos para tu equipo y clientes", "combo", (.4, .5), 1.25), ("Reuniones de fin de año", "spoon", (.5, .45), 1.15)]
def sc4(t):  # 18.8–25.2  para qué ocasiones
    dur = 1.6; i = min(int(t / dur), 3); lt = t - i * dur
    label, k, c, z = USES[i]
    cv = view(IM[k], z - .08 * eio(lt / dur), *c).convert("RGBA")
    if lt < .25 and i > 0:
        pl, pk, pc, pz = USES[i - 1]
        cv = Image.blend(view(IM[pk], pz - .08, *pc).convert("RGBA"), cv, eio(lt / .25))
    cv.alpha_composite(G_BOT); cv.alpha_composite(G_TOP); garland(cv, t + 20, 80, 70)
    enter(cv, txt("Perfecto para…", F_PFI, 66, CREAM), t, .1, 540, 300, "fade")
    pill = Image.new("RGBA", (980, 170), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle((0, 0, 979, 169), 85, fill=RED, outline=GOLD_L, width=4)
    v = txt(label, F_BLK, 54 if len(label) < 26 else 44, WHT, shadow=False); pill.alpha_composite(v, ((980 - v.width) // 2, (170 - v.height) // 2))
    put(cv, pill, 540, 1520, back(lt / .4), 1, [-2, 2, -2, 2][i])
    dots = ImageDraw.Draw(cv)
    for j in range(4): dots.ellipse((480 + j * 40 - 9, 1680 - 9, 480 + j * 40 + 9, 1680 + 9), fill=GOLD_L if j == i else (120, 80, 70))
    put(cv, LOGO_S, 110, 210, 1, 1); return cv

def day_card(n, lit):
    c = Image.new("RGBA", (270, 250), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 269, 249), 30, fill=RED if lit else (80, 22, 26), outline=GOLD_L if lit else (130, 60, 50), width=4)
    v = txt(str(n), F_BLK, 104, WHT if lit else (170, 120, 110), shadow=False); c.alpha_composite(v, ((270 - v.width) // 2, 20))
    v2 = txt("DIC", F_XB, 32, GOLD_L if lit else (150, 100, 90), shadow=False); c.alpha_composite(v2, ((270 - v2.width) // 2, 158))
    return c
def sc5(t):  # 25.2–31.6  9 noches
    cv = NIGHT_BG.copy(); bokeh(cv, t + 25, .8); garland(cv, t + 25, 80, 70)
    enter(cv, txt("9 noches de novena", F_PF, 78, CREAM), t, .1, 540, 270, "up")
    enter(cv, txt("16 al 24 de diciembre", F_SC, 104, GOLD_L), t, .5, 540, 400, "up")
    for i in range(9):
        n = 16 + i; x = 200 + (i % 3) * 340; y = 650 + (i // 3) * 290
        t0 = 1.0 + .38 * i; lit = t > t0
        put(cv, day_card(n, lit), x, y, back((t - t0) / .35) if lit else 1, 1)
        if n == 24 and lit: put(cv, candle(t, 2), x + 110, y - 110, .5, 1)
    enter(cv, txt("¡Reserva tu combo con tiempo!", F_BLK, 56, WHT), t, 4.6, 540, 1560, "pop")
    enter(cv, txt("Pedidos para novenas familiares y empresariales", F_PFI, 44, CREAM, maxw=940), t, 5.1, 540, 1680, "fade")
    sparkles(cv, t); return cv

def sc6(t):  # 31.6–40.0  CTA
    cv = NIGHT_BG.copy(); bokeh(cv, t + 31, 1.); garland(cv, t + 31, 80, 70, 13, 0, .03)
    put(cv, ornament_photo("combo", 560, (.45, .5), 1.05), 540, 560 + 8 * math.sin(t * 2), elastic(t / .9), 1, 3 * math.sin(t * 1.6))
    put(cv, LOGO_M, 840, 820, back((t - .8) / .5) if t > .8 else 0, 1, 10)
    enter(cv, txt("Pide tu", F_PFI, 72, CREAM), t, 1.2, 540, 1000, "up")
    enter(cv, txt("Combo Novena", F_SC, 170, GOLD_L), t, 1.6, 540, 1130, "elastic")
    if t > 2.6:
        k = back((t - 2.6) / .5); pul = 1 + .04 * pulse(t)
        b_ = Image.new("RGBA", (900, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(b_)
        bd.rounded_rectangle((0, 0, 899, 149), 75, fill=GOLD); v = txt("¡PÍDELO YA!", F_BLK, 72, RED2, shadow=False)
        b_.alpha_composite(v, ((900 - v.width) // 2, (150 - v.height) // 2)); put(cv, b_, 540, 1320, k * pul)
    enter(cv, txt("con tu vendedor de confianza o por WhatsApp", F_PFI, 44, CREAM), t, 3.3, 540, 1450, "fade")
    enter(cv, txt("319 653 6874", F_BLK, 84, WHT), t, 3.7, 540, 1550, "pop")
    enter(cv, txt("barujshefa.com · @barujshefa", F_XB, 40, GOLD_L), t, 4.2, 540, 1660, "up")
    enter(cv, txt("¡Feliz Navidad!", F_SC, 96, CREAM), t, 5.0, 540, 1790, "up")
    sparkles(cv, t); return cv

def star_wipe(prev, cur, k):
    """Transición con estrella dorada que crece."""
    e = eio(k); r = 2600 * e; mk = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mk)
    pts = [(540 + (r if i % 2 == 0 else r * .45) * math.cos(-math.pi / 2 + math.pi * i / 5),
            960 + (r if i % 2 == 0 else r * .45) * math.sin(-math.pi / 2 + math.pi * i / 5)) for i in range(10)]
    d.polygon(pts, fill=255); out = prev.copy(); out.paste(cur, (0, 0), mk)
    if 0 < e < 1: ImageDraw.Draw(out).line(pts + [pts[0]], fill=GOLD_L, width=12)
    return out

SCENES = [(0.0, sc1), (4.7, sc2), (10.3, sc3), (18.8, sc4), (25.2, sc5), (31.6, sc6)]
DUR = 40.0
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", MUSIC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev, cur, last = None, 0, None
N = int(DUR * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(SCENES) if s[0] <= t + 1e-6)
    if si != cur: last.save(os.path.join(SNAP, f"escena_{cur + 1}.png")); prev, cur = last, si
    lt = t - SCENES[si][0]; fr = SCENES[si][1](lt).convert("RGB"); last = fr; out = fr
    if lt < .5 and prev is not None: out = star_wipe(prev, fr, lt / .5)
    if fi < 10: out = Image.blend(Image.new("RGB", (W, H), NIGHT), out, fi / 10)
    ff.stdin.write(out.tobytes())
    if fi % 300 == 0: print(f"{fi}/{N}", flush=True)
last.save(os.path.join(SNAP, f"escena_{cur + 1}.png"))
ff.stdin.close(); ff.wait()
print(f"DUR={DUR}")
