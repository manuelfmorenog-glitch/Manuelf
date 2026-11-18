#!/usr/bin/env python3
"""Reel PITCH DE INVERSIÓN (versión negocios, 50 s) – Baruj Shefa.

Ritmo rápido, tipografía cinética grande, cifras protagonistas, sincronizado
al guion de voz en off (ver reel/inversion/GUION_VOZ_EN_OFF.md).
Si se pasa una voz (wav/m4a/mp3), se mezcla con la música bajando la música (ducking).

Uso: python3 build_pitch.py <medios> <fuentes> <musica.wav> <final.mp4> <carpeta_fotogramas> [voz]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL, SNAP = sys.argv[1:6]
VOICE = sys.argv[6] if len(sys.argv) > 6 else None
os.makedirs(SNAP, exist_ok=True)
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 116

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
P = dict(spoon=m("e6bf323c"), duo=m("a4fe69f9"), tortas=m("483610ce"), almo=m("ac03ebef"), gall=m("8ae233b1"),
         cart=m("c47cb03b"), planta=m("14849d92"), llenando=m("3ed9ad98"), crudas=m("7891d98b"), pack=m("c80dcfa2"),
         almobox=m("a0cf5d80"), almobox2=m("eef727c6"), torta_p=m("09ff1f5e"))
LOGO, OVEN_V = m("777dda90"), m("501b5a86")
AS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inversion", "assets")
for _k, _f in [("almo_p", "almo_premium.jpg"), ("torta_p2", "torta_premium.jpg"), ("carrito", "carrito_vendedores.jpg"),
               ("horno", "horno_dorado.jpg"), ("planta_op", "planta_horno.jpg")]: P[_k] = os.path.join(AS, _f)
LOGO = os.path.join(AS, "logo_hd.png")

F_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BLKI = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_SB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
if not os.path.exists(F_SB): F_SB = F_XB
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")

INK = (20, 17, 16)                      # #141110
WHT, GREY = (255, 255, 255), (168, 160, 152)
GOLD = (226, 176, 74)                   # acento de texto
BAR_HI, BAR = (194, 135, 44), (154, 83, 50)   # validados vs #141110
GREEN = (40, 140, 90)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=1.7): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def pulse(t): return math.exp(-((t / BEAT) % 1) * 8)

def grade(im, sat=1.1):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.1 + 128 + np.array([4, 1, -4]); l = a.mean(2, keepdims=True); a = l + (a - l) * sat
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
IM = {k: grade(ImageOps.exif_transpose(Image.open(p)).convert("RGB")) for k, p in P.items()}
def view(img, z, cx, cy, w=W, h=H):
    iw, ih = img.size; s = max(w / iw, h / ih) * z; vw, vh = w / s, h / s
    l = clamp(cx * iw - vw / 2, 0, iw - vw); t = clamp(cy * ih - vh / 2, 0, ih - vh)
    return img.resize((int(w), int(h)), Image.BILINEAR, box=(l, t, l + vw, t + vh))
class Vid:
    def __init__(self, path, ss, sp): self.a = (path, ss, sp); self.p = None; self.last = None
    def frame(self):
        path, ss, sp = self.a
        if not self.p:
            vf = f"setpts=PTS/{sp},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", path, "-vf", vf, "-f", "rawvideo",
                                       "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3: self.last = grade(Image.frombuffer("RGB", (W, H), buf))
        return self.last
OVEN = Vid(OVEN_V, .3, .5)

_c = {}
def txt(text, font, size, fill, maxw=None, lh=1.05, align="left", track=0):
    k = (text, font, size, fill, maxw, lh, align, track)
    if k in _c: return _c[k]
    f = ImageFont.truetype(font, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    def tl(s): return sum(tmp.textlength(ch, font=f) + track for ch in s) - track if track else tmp.textlength(s, font=f)
    rows = []
    for para in text.split("\n"):
        if not maxw: rows.append(para); continue
        cur = ""
        for w_ in para.split():
            t2 = (cur + " " + w_).strip()
            if tl(t2) <= maxw: cur = t2
            else: rows.append(cur); cur = w_
        rows.append(cur)
    a, d_ = f.getmetrics(); L = int((a + d_) * lh); ws = [tl(r) for r in rows]; tw = int(max(ws)) + 6
    img = Image.new("RGBA", (tw + 6, L * len(rows) + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        x = (tw - ws[i]) / 2 if align == "center" else 0
        if track:
            for ch in r: d.text((x, i * L), ch, font=f, fill=fill); x += tmp.textlength(ch, font=f) + track
        else: d.text((x, i * L), r, font=f, fill=fill)
    _c[k] = img; return img

def put(cv, img, cx, cy, sc=1., al=1.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def kin(cv, img, t, t0, x, y, kind="up", anchor="l", t1=None):
    """Tipografía cinética: entra con máscara (sube desde una línea) o golpe de escala."""
    if t < t0 or (t1 is not None and t > t1 + .2): return
    k = eo((t - t0) / .32); out = 1 - eo((t - t1) / .2) if t1 is not None and t > t1 else 1
    xx = x - img.width / 2 if anchor == "c" else x
    if kind == "up":
        h = img.height; dy = int((1 - k) * h)
        crop = img.crop((0, 0, img.width, h - dy)) if h - dy > 0 else None
        if crop and out > 0:
            if out < 1: crop = crop.copy(); crop.putalpha(crop.getchannel("A").point(lambda v: int(v * out)))
            cv.alpha_composite(crop, (int(xx), int(y + dy)))
    elif kind == "slam":
        put(cv, img, xx + img.width / 2, y + img.height / 2, 1 + .9 * (1 - k), eo(k * 3) * out)
    elif kind == "fade":
        put(cv, img, xx + img.width / 2, y + img.height / 2, 1, k * out)

def dark_photo(key, t, dur, z0, z1, cx=.5, cy=.5, dim=150, vid=None):
    im = vid.frame() if vid else IM[key]
    cv = view(im, (z0 + (z1 - z0) * eio(t / dur)) * (1 + .015 * pulse(t)), cx, cy).convert("RGBA")
    cv.alpha_composite(Image.new("RGBA", (W, H), INK + (dim,))); return cv

_grid = {}
def grid(cv, a=22):
    if a not in _grid:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        for x in range(0, W, 120): d.line((x, 0, x, H), fill=(255, 255, 255, a), width=1)
        for y in range(0, H, 120): d.line((0, y, W, y), fill=(255, 255, 255, a), width=1)
        _grid[a] = g
    cv.alpha_composite(_grid[a])

def round_logo(size, ring=GOLD, rw=6):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 2 * rw, size - 2 * rw), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((2, 2, lg.width - 2, lg.height - 2), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (rw, rw), mk); return out
LOGO_S, LOGO_M = round_logo(110), round_logo(260)
def brand(cv, t):
    put(cv, LOGO_S, 105, 115, 1, eo(t / .3))

def blank():
    cv = Image.new("RGBA", (W, H), INK); grid(cv); return cv

# ---------- escenas (sincronizadas con el guion) ----------
def s1(t):  # 0.0–5.6  voz 1.2–3.2 "…que ya vende" · 3.8–5.1 "y está listo para crecer"
    flashes = ["torta_p2", "almo_p", "horno", "spoon", "almo_p", "torta_p2"]
    if t < 2.4:
        cv = dark_photo(flashes[int(t / .4) % 6], t, 2.4, 1.3, 1.2, .5, .5, 110)
    else:
        cv = dark_photo("spoon", t - 2.4, 3.2, 1.25, 1.1, .5, .45, 165)
    kin(cv, txt("UN NEGOCIO", F_BLK, 120, WHT), t, 1.1, 80, 560)
    kin(cv, txt("QUE YA", F_BLK, 120, WHT), t, 1.6, 80, 700)
    kin(cv, txt("VENDE.", F_BLK, 170, GOLD), t, 2.4, 80, 830, "slam")
    kin(cv, txt("Y ESTÁ LISTO", F_BLK, 96, WHT), t, 3.8, 80, 1180)
    kin(cv, txt("PARA CRECER.", F_BLKI, 120, GOLD), t, 4.3, 80, 1300, "slam")
    if t > 4.3:  # flecha de crecimiento
        d = ImageDraw.Draw(cv); k = eo((t - 4.3) / .6)
        x0, y0, x1, y1 = 820, 1560, 1000, 1380; xe, ye = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
        d.line((x0, y0, xe, ye), fill=GOLD, width=14)
        if k > .9: d.polygon([(x1 + 12, y1 - 12), (x1 - 70, y1 - 5), (x1 + 5, y1 + 70)], fill=GOLD)
    return cv

def s2(t):  # 4.2–9.0  "Baruj Shefa: una receta campesina de más de sesenta años, convertida en marca."
    cv = blank()
    ph = view(IM["duo"], 1.12 - .06 * eio(t / 5.4), .5, .33, W, 1000).convert("RGBA")
    k = eo(t / .5); cv.alpha_composite(ph.crop((0, 0, W, int(1000 * k))), (0, 0))
    g = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(300): gd.line((0, y, W, y), fill=INK + (int(255 * y / 300),))
    cv.alpha_composite(g, (0, 700))
    put(cv, LOGO_M, 540, 1000, back((t - .4) / .5) if t > .4 else 0)
    kin(cv, txt("+60", F_BLK, 210, GOLD), t, 1.5, 80, 1200, "slam")
    kin(cv, txt("AÑOS DE RECETA", F_XB, 54, WHT), t, 1.8, 500, 1255)
    kin(cv, txt("CAMPESINA", F_XB, 54, WHT), t, 2.0, 500, 1322)
    kin(cv, txt("Convertida en marca.", F_PFI, 76, WHT), t, 3.6, 80, 1520)
    kin(cv, txt("Chipaque → Bogotá · desde marzo 2026", F_SB, 36, GREY), t, 4.2, 80, 1640, "fade")
    return cv

NUMS = [(13.37, 45.9, "M", "FACTURADOS", ""), (15.71, 755, "", "PEDIDOS", "únicos"), (18.57, 43, "%", "MARGEN BRUTO", "")]
S3_T0 = 11.0
def s3(t):  # 11.0–22.9  voz: "En solo nueve meses" 11.5 · $45,9M 13.4 · 755 15.7 · 43% 18.6 · recursos propios 21.1
    T = t + S3_T0
    if T < NUMS[0][0]:
        cv = dark_photo("horno", t, 2.4, 1.2, 1.1, .5, .6, 185); grid(cv, 14); brand(cv, t)
        kin(cv, txt("EN SOLO", F_BLK, 110, WHT), t, .4, 540, 700, "up", "c")
        kin(cv, txt("9 MESES", F_BLK, 230, GOLD), t, .8, 540, 830, "slam", "c")
        return cv
    idx = 0 if T < NUMS[1][0] else 1 if T < NUMS[2][0] else 2
    t0, val, unit, lab, sub = NUMS[idx]; lt = T - t0
    bgk = ["torta_p2", "almo_p", "carrito"][idx]
    zc = [(2.1, 1.85, .3, .3), (2.0, 1.8, .25, .15), (1.3, 1.15, .5, .45)][idx]
    cv = dark_photo(bgk, lt, 2.8, zc[0], zc[1], zc[2], zc[3], 195); grid(cv, 14); brand(cv, t)
    k = eo(lt / .9)
    if unit == "M": s = "$" + f"{val * k:.1f}".replace(".", ",") + "M"
    elif unit == "%": s = f"{int(round(val * k))}%"
    else: s = f"{int(round(val * k))}"
    put(cv, txt(s, F_BLK, 250 if idx != 0 else 230, WHT), 540, 820, 1 + .25 * (1 - eo(lt / .25)), 1)
    kin(cv, txt(lab, F_XB, 64, GOLD, track=6), t, t0 - S3_T0 + .2, 540, 990, "up", "c")
    if sub: kin(cv, txt(sub, F_PFI, 56, WHT), t, t0 - S3_T0 + .4, 540, 1080, "fade", "c")
    if T > 21.1:  # sello recursos propios
        kk = back((T - 21.1) / .4)
        st = Image.new("RGBA", (760, 120), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((0, 0, 759, 119), 60, outline=GOLD, width=5)
        v = txt("100% CON RECURSOS PROPIOS", F_XB, 40, GOLD); st.alpha_composite(v, ((760 - v.width) // 2, 34))
        put(cv, st, 540, 1400, kk)
    d = ImageDraw.Draw(cv); d.rectangle((80, 1760, 80 + 920 * clamp(t / 11.9), 1766), fill=GOLD)
    return cv

def s4(t):  # 17.0–22.2  "Tres registros INVIMA vigentes y una planta de producción lista para escalar."
    cv = dark_photo("planta_op" if t > 2.4 else "planta", t, 5.5, 1.15, 1.02, .5, .45, 175); brand(cv, t)
    if t > .7:
        k = back((t - .7) / .5); s = Image.new("RGBA", (320, 320), (0, 0, 0, 0)); sd = ImageDraw.Draw(s)
        sd.ellipse((0, 0, 319, 319), fill=(26, 98, 64)); sd.ellipse((14, 14, 305, 305), outline=GOLD, width=5)
        for tx, f, sz, y, col in [("3", F_BLK, 130, 40, WHT), ("REGISTROS", F_XB, 28, 190, GOLD), ("INVIMA", F_BLK, 40, 226, WHT)]:
            v = txt(tx, f, sz, col); s.alpha_composite(v, ((320 - v.width) // 2, y))
        put(cv, s, 540, 520, k)
    kin(cv, txt("VIGENTES", F_XB, 52, GOLD, track=8), t, 1.2, 540, 720, "up", "c")
    kin(cv, txt("PLANTA DE", F_BLK, 104, WHT), t, 2.6, 80, 1140)
    kin(cv, txt("PRODUCCIÓN", F_BLK, 104, WHT), t, 2.9, 80, 1260)
    kin(cv, txt("LISTA PARA ESCALAR.", F_BLKI, 84, GOLD), t, 3.6, 80, 1390, "slam")
    return cv

CATDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendedores", "catalogo")
CAT = [("torta_p2", "Torta Familiar"), ("almo_p", "Almojábanas x6"), ("personal", "Torta Personal"), ("gall", "Galletas Caseritas"),
       ("mediana", "Torta Mediana"), ("cmediana", "Combo Mediana"), ("generosa", "Torta La Generosa"), ("cpersonal", "Combo Personal")]
def _catimg(k):
    return IM[k] if k in IM else grade(Image.open(os.path.join(CATDIR, k + ".jpg")).convert("RGB"))
def catalog_tall(sw=440):
    cw, ch = 196, 280; tall = Image.new("RGBA", (sw, 150 + 4 * (ch + 14)), (250, 245, 236, 255)); d = ImageDraw.Draw(tall)
    tall.alpha_composite(round_logo(64), (18, 20))
    d.text((96, 26), "CATÁLOGO DIGITAL", font=ImageFont.truetype(F_SB, 15), fill=(180, 130, 50))
    d.text((96, 46), "Baruj Shefa", font=ImageFont.truetype(F_PFI, 26), fill=(60, 30, 14))
    x = 16
    for i, chip in enumerate(["Todos", "Tortas", "Combos", "Productos"]):
        f = ImageFont.truetype(F_SB, 16); w = d.textlength(chip, font=f) + 26
        d.rounded_rectangle((x, 100, x + w, 132), 16, fill=(60, 30, 14) if i == 0 else (255, 255, 255), outline=(230, 216, 196), width=2)
        d.text((x + 13, 106), chip, font=f, fill=(255, 255, 255) if i == 0 else (60, 30, 14)); x += w + 8
    for i, (k, name) in enumerate(CAT):
        cx, cy = 16 + (i % 2) * (cw + 16), 148 + (i // 2) * (ch + 14)
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, cw - 1, ch - 1), 16, fill=(255, 255, 255), outline=(230, 216, 196), width=2)
        ph = view(_catimg(k), 1.0, .5, .5, cw - 12, 160).convert("RGBA")
        mk = Image.new("L", ph.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), 12, fill=255); ph.putalpha(mk)
        card.alpha_composite(ph, (6, 6)); card.alpha_composite(txt(name, F_XB, 19, (60, 30, 14), maxw=cw - 24), (12, 176))
        cd.rounded_rectangle((12, ch - 50, cw - 12, ch - 14), 18, fill=(196, 146, 56))
        cd.text((cw / 2 - 40, ch - 44), "+  Agregar", font=ImageFont.truetype(F_SB, 17), fill=(255, 255, 255))
        tall.alpha_composite(card, (cx, cy))
    return tall
CATALOG = catalog_tall()
def phone(scroll):
    sw, sh, bw = 440, 900, 18
    ph = Image.new("RGBA", (sw + 2 * bw, sh + 2 * bw), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle((0, 0, sw + 2 * bw - 1, sh + 2 * bw - 1), 70, fill=(10, 10, 10), outline=(90, 84, 76), width=3)
    y = int(scroll * (CATALOG.height - sh + 40))
    scr = Image.new("RGBA", (sw, sh), (250, 245, 236, 255)); scr.alpha_composite(CATALOG.crop((0, y, sw, y + sh - 40)), (0, 40))
    ImageDraw.Draw(scr).text((34, 10), "9:41", font=ImageFont.truetype(F_SB, 18), fill=(30, 20, 10))
    mk = Image.new("L", (sw, sh), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, sw - 1, sh - 1), 54, fill=255); scr.putalpha(mk)
    ph.alpha_composite(scr, (bw, bw)); d.rounded_rectangle((sw / 2 + bw - 60, bw + 10, sw / 2 + bw + 60, bw + 38), 14, fill=(5, 5, 5))
    return ph
def system_card():
    c = Image.new("RGBA", (470, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 469, 299), 30, fill=(250, 245, 236), outline=GOLD, width=3)
    c.alpha_composite(txt("SISTEMA DE GESTIÓN", F_XB, 24, (150, 100, 40), track=3), (28, 24))
    for i, (lab, col) in enumerate([("Pedidos en línea", GREEN), ("Red de vendedores", BAR_HI), ("Inventario y caja", BAR)]):
        y = 80 + i * 68; d.ellipse((28, y + 8, 56, y + 36), fill=col)
        d.line([(35, y + 22), (41, y + 28), (50, y + 15)], fill=WHT, width=4)
        c.alpha_composite(txt(lab, F_XB, 32, (50, 26, 12)), (72, y))
    return c
SYS = system_card()
STEPS = [(1.0, "TIENDAS DE BARRIO"), (2.6, "RETAIL"), (4.4, "PRIMER LOCAL")]
def s5a(t):  # 28.4–34.4  voz: "El siguiente paso: tiendas de barrio, retail y nuestro primer local."
    cv = blank(); brand(cv, t)
    kin(cv, txt("EL SIGUIENTE PASO", F_XB, 52, GOLD, track=6), t, .2, 80, 260)
    k = eo((t - .1) / .6)
    put(cv, phone(eio(t / 6) * .8), 290 - (1 - k) * 600, 960, .86, 1)
    if t > 1.6: put(cv, SYS, 690, 1270, back((t - 1.6) / .5) * .82)
    for i, (t0, lab) in enumerate(STEPS):
        if t < t0: continue
        kk = eo((t - t0) / .35); chip = Image.new("RGBA", (470, 110), (0, 0, 0, 0)); cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle((0, 0, 469, 109), 55, fill=GOLD if i == len(STEPS) - 1 else (255, 255, 255, 30), outline=GOLD, width=3)
        v = txt(lab, F_BLK, 40 if len(lab) > 10 else 46, INK if i == len(STEPS) - 1 else WHT); chip.alpha_composite(v, ((470 - v.width) // 2, 30))
        put(cv, chip, 800 + (1 - kk) * 400, 470 + 150 * i, 1, kk)
    kin(cv, txt("TECNOLOGÍA PARA CRECER", F_BLK, 66, WHT), t, 2.4, 540, 1520, "slam", "c")
    kin(cv, txt("Catálogo digital + sistema de gestión, listos para escalar.", F_SB, 36, GREY, maxw=900, align="center"), t, 3.0, 540, 1620, "fade", "c")
    return cv

PLAN = [("TIENDA A TIENDA", "$20M", "Meses 1–3"), ("RETAIL", "$12M", "Meses 3–6"), ("LOCAL PROPIO", "$8M", "Meses 6–12")]
def s5b(t):  # 34.4–39.3  voz: "Un plan de doce meses, con cuarenta y ocho millones de pesos."
    cv = blank(); brand(cv, t)
    kin(cv, txt("12 MESES · $48M", F_BLK, 104, WHT), t, .4, 540, 300, "slam", "c")
    for i, (a, amt, mm) in enumerate(PLAN):
        t0 = 1.2 + .45 * i; y = 520 + 310 * i
        if t < t0: continue
        k = eo((t - t0) / .4); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle((80, y, 80 + max(60, 920 * k), y + 270), 30, fill=(255, 255, 255, 14), outline=(90, 80, 70), width=2)
        cv.alpha_composite(lay)
        if k > .6:
            cv.alpha_composite(txt(f"0{i + 1}", F_BLK, 56, GOLD), (120, y + 26))
            cv.alpha_composite(txt(a, F_BLK, 54, WHT), (120, y + 105))
            cv.alpha_composite(txt(mm, F_SB, 34, GREY), (120, y + 190))
            v = txt(amt, F_BLK, 96, GOLD); cv.alpha_composite(v, (960 - v.width, y + 85))
    kin(cv, txt("Del carrito a la góndola.", F_PFI, 64, GOLD), t, 3.0, 540, 1520, "fade", "c")
    return cv

def offer(title, lines, accent):
    c = Image.new("RGBA", (920, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 919, 299), 34, fill=(255, 255, 255, 14), outline=accent, width=4)
    c.alpha_composite(txt(title, F_BLK, 60, WHT), (44, 40))
    for i, ln in enumerate(lines): c.alpha_composite(txt(ln, F_SB, 38, GREY), (44, 140 + 56 * i))
    return c
OFF_A = offer("PRÉSTAMO", ["Interés fijo 2% mensual · 36 meses", "Contrato notariado"], GOLD)
OFF_B = offer("EQUITY", ["Participación del 2,5% al 5%", "Valoración $800M – $1.000M"], BAR_HI)
def s6(t):  # 30.0–37.0  "Invierte desde 20 millones: préstamo a tasa fija o participación en la empresa."
    cv = blank(); brand(cv, t)
    kin(cv, txt("INVIERTE DESDE", F_XB, 64, WHT, track=4), t, .1, 540, 330, "up", "c")
    kin(cv, txt("$20M", F_BLK, 300, GOLD), t, .5, 540, 410, "slam", "c")
    kin(cv, OFF_A, t, 2.0, 80, 900, "up")
    kin(cv, OFF_B, t, 3.2, 80, 1240, "up")
    kin(cv, txt("Tú eliges la modalidad.", F_PFI, 58, WHT), t, 4.6, 540, 1620, "fade", "c")
    return cv

def s7(t):  # 37.0–42.4  "La proyección: pasar de noventa a ciento sesenta millones en 2027."
    cv = blank(); brand(cv, t)
    kin(cv, txt("PROYECCIÓN · FACTURACIÓN ANUAL", F_XB, 40, GOLD, track=4), t, .1, 80, 260)
    d = ImageDraw.Draw(cv); yb = 1350; scale = 900 / 170
    for i, (lab, v, col, x) in enumerate([("2026", 90, BAR, 230), ("2027 · base", 160, BAR_HI, 640)]):
        t0 = .5 + .9 * i; k = eo((t - t0) / .8)
        cv.alpha_composite(txt(lab, F_XB, 44, WHT if i else GREY, align="center"), (x - 40 - (40 if i else 0), yb + 24))
        if k <= 0: continue
        h = v * scale * k
        d.rounded_rectangle((x - 110, yb - h, x + 110, yb), 6, fill=col); d.rectangle((x - 110, yb - min(h, 8), x + 110, yb), fill=col)
        lab_v = txt(f"${int(v * k)}M", F_BLK, 84, WHT); cv.alpha_composite(lab_v, (int(x - lab_v.width / 2), int(yb - h - 110)))
    d.line((100, yb, 980, yb), fill=(110, 100, 92), width=3)
    if t > 2.6:  # flecha de crecimiento entre barras
        k = eo((t - 2.6) / .5); x0, y0 = 360, yb - 90 * scale - 40; x1, y1 = 500, yb - 160 * scale + 40
        d.line((x0, y0, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k), fill=GOLD, width=10)
    kin(cv, txt("+78%", F_BLK, 130, GOLD), t, 3.0, 80, 360, "slam")
    kin(cv, txt("Canal TAT + retail + local", F_SB, 36, GREY), t, 3.5, 80, 1520, "fade")
    return cv

def s8(t):  # 42.4–50.0  "No es una apuesta al futuro. Es subirse a un tren en movimiento. Agenda tu reunión hoy."
    cv = dark_photo("carrito", t, 10.7, 1.12, 1.02, .5, .45, 200); brand(cv, t)
    kin(cv, txt("NO ES UNA APUESTA", F_BLK, 78, WHT), t, .1, 80, 330)
    kin(cv, txt("AL FUTURO.", F_BLK, 78, WHT), t, .4, 80, 430)
    kin(cv, txt("Es subirse a un tren", F_PFI, 72, GOLD), t, 2.0, 80, 580)
    kin(cv, txt("en movimiento.", F_PFI, 72, GOLD), t, 2.4, 80, 670)
    if t > 4.2:
        k = back((t - 4.2) / .5); pul = 1 + .03 * pulse(t)
        btn = Image.new("RGBA", (920, 170), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
        bd.rounded_rectangle((0, 0, 919, 169), 85, fill=GOLD); v = txt("CONVERSEMOS", F_BLK, 76, INK)
        btn.alpha_composite(v, ((920 - v.width) // 2, 40)); put(cv, btn, 540, 940, k * pul)
    kin(cv, txt("Estados financieros y proyecciones disponibles", F_SB, 36, WHT, align="center"), t, 4.8, 540, 1070, "fade", "c")
    rows = [("WHATSAPP", "+57 319 653 6874"), ("CORREO", "manuel@barujshefa.com"), ("WEB", "barujshefa.com")]
    for i, (a, bb) in enumerate(rows):
        r = Image.new("RGBA", (920, 110), (0, 0, 0, 0)); rd = ImageDraw.Draw(r)
        rd.rounded_rectangle((0, 0, 919, 109), 30, fill=(255, 255, 255, 18), outline=(110, 96, 80), width=2)
        r.alpha_composite(txt(a, F_XB, 26, GOLD, track=4), (34, 40)); v = txt(bb, F_BLK, 46, WHT); r.alpha_composite(v, (884 - v.width, 26))
        kin(cv, r, t, 5.4 + .3 * i, 80, 1190 + 130 * i, "up")
    kin(cv, txt("Pieza informativa. No constituye oferta pública de valores. Toda inversión implica riesgos; "
                "condiciones sujetas a contrato y debida diligencia.", F_SB, 22, GREY, maxw=900, align="center", lh=1.3),
        t, 6.6, 540, 1640, "fade", "c")
    kin(cv, txt("Baruj Shefa S.A.S. · NIT 901.990.427-6", F_SB, 24, GREY, align="center"), t, 6.6, 540, 1740, "fade", "c")
    return cv

SCENES = [(0.0, s1), (5.6, s2), (11.0, s3), (22.9, s4), (28.4, s5a), (34.4, s5b), (39.3, s6), (45.8, s7), (51.8, s8)]
DUR = 62.5

def whip(prev, cur, k):
    e = eio(k); out = Image.new("RGB", (W, H)); out.paste(prev, (0, int(-e * H))); out.paste(cur, (0, int(H - e * H)))
    return out.filter(ImageFilter.BoxBlur(int(22 * (1 - abs(2 * k - 1)))))

# audio: música + (opcional) voz con ducking
AUDIO = MUSIC
if VOICE:
    mix = os.path.join(SNAP, "mezcla.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", MUSIC, "-i", VOICE, "-filter_complex",
                    f"[1:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=80,acompressor=threshold=0.1:ratio=3,loudnorm=I=-16,apad=whole_dur={DUR}[v];"
                    "[v]asplit[v1][v2];[0:a]volume=0.9[mu];[mu][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
                    f"[duck][v2]amix=inputs=2:duration=first:weights=1 1.6:normalize=0,atrim=0:{DUR},alimiter=limit=0.95[a]", "-map", "[a]", mix], check=True)
    AUDIO = mix

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", AUDIO, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev, cur, last = None, 0, None
N = int(DUR * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(SCENES) if s[0] <= t + 1e-6)
    if si != cur: last.save(os.path.join(SNAP, f"escena_{cur + 1}.png")); prev, cur = last, si
    lt = t - SCENES[si][0]; fr = SCENES[si][1](lt).convert("RGB"); last = fr; out = fr
    if lt < .3 and prev is not None: out = whip(prev, fr, lt / .3)
    ff.stdin.write(out.tobytes())
    if fi % 300 == 0: print(f"{fi}/{N}", flush=True)
last.save(os.path.join(SNAP, f"escena_{cur + 1}.png"))
ff.stdin.close(); ff.wait()
print(f"DUR={DUR}")
