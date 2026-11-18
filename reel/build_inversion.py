#!/usr/bin/env python3
"""Reel OPORTUNIDAD DE INVERSIÓN – Baruj Shefa (1080x1920).

Basado en "Propuesta de Inversión · Baruj Shefa · Noviembre 2026".
Estilo: presentación premium (chocolate + dorado + crema), cifras animadas,
gráficas construidas en vivo (paleta validada), material real de la marca,
CTA claro y aviso legal.

Uso: python3 build_inversion.py <medios> <fuentes> <musica.wav> <final.mp4> <carpeta_fotogramas>
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL, SNAP = sys.argv[1:6]
os.makedirs(SNAP, exist_ok=True)
W, H, FPS = 1080, 1920, 30
BEAT = 0.6

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
P = dict(spoon=m("e6bf323c"), duo=m("a4fe69f9"), tortas=m("483610ce"), almo=m("ac03ebef"), gall=m("8ae233b1"),
         cart=m("c47cb03b"), planta=m("14849d92"), llenando=m("3ed9ad98"), crudas=m("7891d98b"), lavado=m("79eefe17"))
LOGO, CLIP = m("777dda90"), m("8e192c8f")

F_PF = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_SB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
F_MD = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
for _f in ("F_SB", "F_MD"):
    if not os.path.exists(globals()[_f]): globals()[_f] = F_XB

SURF, SURF2 = (42, 20, 10), (60, 30, 15)          # superficie oscura de marca
CREAM, CREAM2 = (246, 236, 218), (200, 182, 158)   # texto principal / secundario
GOLD, GOLD_L = (194, 135, 44), (232, 196, 120)     # #C2872C (dato destacado), acento claro
BAR = (154, 83, 50)                                # #9A5332 (serie base)  – validado vs #2A140A
GREEN, WHT = (40, 130, 84), (255, 255, 255)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=1.6): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def b(n): return n * BEAT

def warm(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.06 + 128 + np.array([6, 2, -5]); l = a.mean(2, keepdims=True); a = l + (a - l) * 1.12
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
IM = {k: warm(ImageOps.exif_transpose(Image.open(p)).convert("RGB")) for k, p in P.items()}
def view(img, z, cx, cy, w=W, h=H):
    iw, ih = img.size; s = max(w / iw, h / ih) * z; vw, vh = w / s, h / s
    l = clamp(cx * iw - vw / 2, 0, iw - vw); t = clamp(cy * ih - vh / 2, 0, ih - vh)
    return img.resize((int(w), int(h)), Image.BILINEAR, box=(l, t, l + vw, t + vh))

class Vid:
    def __init__(self, ss, sp, w=W, h=H):
        self.a = (ss, sp, w, h); self.p = None; self.last = None
    def frame(self):
        ss, sp, w, h = self.a
        if not self.p:
            vf = f"setpts=PTS/{sp},fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", CLIP, "-vf", vf,
                                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        buf = self.p.stdout.read(w * h * 3)
        if len(buf) == w * h * 3: self.last = warm(Image.frombuffer("RGB", (w, h), buf))
        return self.last
V_HORNO = Vid(7.0, .7)

# ---------- texto ----------
_c = {}
def txt(text, font, size, fill, maxw=None, lh=1.15, align="left", track=0):
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
    a, d_ = f.getmetrics(); L = int((a + d_) * lh); ws = [tl(r) for r in rows]; tw = int(max(ws)) + 4
    img = Image.new("RGBA", (tw + 4, L * len(rows) + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        x = (tw - ws[i]) / 2 if align == "center" else (tw - ws[i]) if align == "right" else 0
        if track:
            for ch in r: d.text((x, i * L), ch, font=f, fill=fill); x += tmp.textlength(ch, font=f) + track
        else: d.text((x, i * L), r, font=f, fill=fill)
    _c[k] = img; return img

def show(cv, img, t, t0, x, y, anchor="l", dy=36, dur=.5):
    if t < t0: return
    k = eo((t - t0) / dur); im = img
    if k < 1: im = img.copy(); im.putalpha(img.getchannel("A").point(lambda v: int(v * k)))
    xx = x - img.width / 2 if anchor == "c" else x - img.width if anchor == "r" else x
    cv.alpha_composite(im, (int(xx), int(y + (1 - k) * dy)))

def put(cv, img, cx, cy, sc=1., al=1.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def money(v, dec=1):
    return f"${v:,.{dec}f}M".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------- fondo y estructura ----------
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W * .5) / W) ** 2 + ((yy - H * .35) / H) ** 2)
    g = np.clip(1 - r * 1.5, 0, 1)[..., None]
    a = np.array(SURF) * (1 - g) + np.array(SURF2) * g + np.random.default_rng(2).normal(0, 2.5, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
BG = make_bg()
def round_logo(size, ring=GOLD, rw=6):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 2 * rw, size - 2 * rw), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((2, 2, lg.width - 2, lg.height - 2), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (rw, rw), mk); return out
LOGO_S, LOGO_L = round_logo(96), round_logo(300)

def frame_ui(cv, t, idx, label):
    """Marco editorial: logo, índice de sección y título de sección."""
    put(cv, LOGO_S, 100, 110, 1, eo(t / .4))
    show(cv, txt("PROPUESTA DE INVERSIÓN · 2026", F_SB, 24, CREAM2, track=4), t, 0, 170, 96, dy=0)
    if idx:
        show(cv, txt(idx, F_SB, 26, GOLD_L, track=3), t, .1, 990, 96, "r", 0)
        show(cv, txt(label, F_XB, 30, GOLD_L, track=6), t, .2, 80, 230, dy=20)
        d = ImageDraw.Draw(cv); k = eo((t - .3) / .6)
        if k > 0: d.line((80, 290, 80 + 920 * k, 290), fill=(110, 70, 40), width=2)

def photo_bg(cv, key, t, dur, z0=1.12, z1=1.0, cx=.5, cy=.5, dim=150):
    im = view(IM[key], z0 + (z1 - z0) * eio(t / dur), cx, cy).convert("RGBA"); cv.alpha_composite(im)
    cv.alpha_composite(Image.new("RGBA", (W, H), SURF + (dim,)))
    g = np.zeros((H, W, 4), np.uint8); g[..., :3] = SURF; y = np.arange(H)[:, None]
    g[..., 3] = np.repeat(np.clip((y - 900) / 900, 0, 1) ** 1.1 * 235, W, 1).astype(np.uint8)
    cv.alpha_composite(Image.fromarray(g))

def rounded(img, r):
    img = img.convert("RGBA"); mk = Image.new("L", img.size, 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255); img.putalpha(mk); return img

# ---------- escenas ----------
def sc_hook(t):
    cv = BG.copy(); photo_bg(cv, "spoon", t, 6, 1.25, 1.08, .5, .45, 120)
    frame_ui(cv, t, "", "")
    show(cv, txt("60 años guardados.", F_PF, 96, CREAM, align="center"), t, .5, 540, 1180, "c", 50, .7)
    show(cv, txt("La ciudad los descubre.", F_PFI, 84, GOLD_L, align="center"), t, 1.6, 540, 1310, "c", 50, .7)
    show(cv, txt("Una oportunidad de inversión en un negocio que ya está creciendo", F_MD, 40, CREAM2, maxw=860, align="center"),
         t, 3.0, 540, 1480, "c")
    return cv

def sc_origen(t):
    cv = BG.copy(); frame_ui(cv, t, "01 / 08", "EL ORIGEN")
    ph = rounded(view(IM["duo"], 1.08 - .05 * eio(t / 6), .5, .35, 920, 1000), 40)
    k = eo((t - .2) / .7); cv.alpha_composite(ph.crop((0, int(1000 * (1 - k)), 920, 1000)), (80, 340 + int(1000 * (1 - k))))
    show(cv, txt("Una receta campesina de más de 60 años", F_PF, 62, CREAM, maxw=920), t, 1.2, 80, 1370)
    show(cv, txt("Chipaque, Cundinamarca → Bogotá, desde marzo de 2026", F_MD, 40, GOLD_L, maxw=920), t, 2.2, 80, 1585)
    show(cv, txt("Carrito · Canal digital · Ventas institucionales", F_SB, 36, CREAM2), t, 3.2, 80, 1730)
    return cv

KPI = [("$45,9M", "facturados", "Mar–Nov 2026", 45.9, "M"), ("755", "pedidos únicos", "en 9 meses", 755, ""),
       ("43%", "margen bruto", "costo directo 57%", 43, "%"), ("$61K", "ticket promedio", "por pedido", 61, "K")]
def tile(value, label, sub, w=440, h=330):
    t_ = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(t_)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=(255, 255, 255, 14), outline=(120, 80, 46), width=2)
    v = txt(value, F_BLK, 104, CREAM); t_.alpha_composite(v, (34, 40))
    t_.alpha_composite(txt(label, F_XB, 38, GOLD_L), (36, 185)); t_.alpha_composite(txt(sub, F_MD, 28, CREAM2), (36, 240))
    return t_
def sc_traccion(t):
    cv = BG.copy(); frame_ui(cv, t, "02 / 08", "TRACCIÓN REAL")
    show(cv, txt("Nueve meses de operación.", F_PF, 70, CREAM), t, .3, 80, 330)
    show(cv, txt("Los números hablan.", F_PFI, 66, GOLD_L), t, .9, 80, 430)
    for i, (val, lab, sub, num, unit) in enumerate(KPI):
        t0 = 1.6 + .5 * i
        if t < t0: continue
        k = eo((t - t0) / 1.2); x, y = 80 + (i % 2) * 480, 620 + (i // 2) * 380
        if unit == "M": shown = "$" + f"{num * k:.1f}".replace(".", ",") + "M"
        elif unit == "%": shown = f"{int(round(num * k))}%"
        elif unit == "K": shown = f"${int(round(num * k))}K"
        else: shown = f"{int(round(num * k))}"
        show(cv, tile(shown, lab, sub), t, t0, x, y, dy=40, dur=.4)
    show(cv, txt("Mejor día: 12 de noviembre · $1,56M en ventas", F_SB, 38, CREAM, maxw=920), t, 4.6, 80, 1420)
    show(cv, txt("Crecimiento financiado 100% con recursos propios", F_MD, 34, CREAM2, maxw=920), t, 5.4, 80, 1490)
    return cv

MONTHS = [("Mar", 1.77), ("Abr", 2.71), ("May", 2.96), ("Jun", 5.28), ("Jul", 7.08), ("Ago", 5.67),
          ("Sep", 6.77), ("Oct", 8.73), ("Nov*", 8.8)]
def sc_ventas(t):
    cv = BG.copy(); frame_ui(cv, t, "03 / 08", "VENTAS MENSUALES")
    show(cv, txt("Facturación por mes · millones COP", F_PF, 52, CREAM, maxw=920), t, .2, 80, 330)
    d = ImageDraw.Draw(cv)
    x0, x1, yb, ytop = 110, 1000, 1360, 560; vmax = 10
    for g in (2, 4, 6, 8, 10):  # rejilla recesiva
        y = yb - (yb - ytop) * g / vmax; d.line((x0, y, x1, y), fill=(78, 46, 26), width=1)
        cv.alpha_composite(txt(f"{g}", F_MD, 24, CREAM2), (x0 - 46, int(y - 16)))
    d.line((x0, yb, x1, yb), fill=(140, 100, 70), width=2)
    n = len(MONTHS); slot = (x1 - x0) / n; bw = slot - 22
    for i, (mo, v) in enumerate(MONTHS):
        t0 = .8 + .22 * i; k = eo((t - t0) / .6)
        cx = x0 + slot * (i + .5)
        cv.alpha_composite(txt(mo, F_SB, 26, CREAM2), (int(cx - 24), yb + 14))
        if k <= 0: continue
        h = (yb - ytop) * v / vmax * k; col = GOLD if mo == "Oct" else BAR
        if mo.startswith("Nov"):  # proyección: contorno + textura
            d.rounded_rectangle((cx - bw / 2, yb - h, cx + bw / 2, yb), 4, outline=BAR, width=3)
            for yy in range(int(yb - h) + 6, yb, 14): d.line((cx - bw / 2 + 4, yy, cx + bw / 2 - 4, yy - 8), fill=BAR, width=2)
        else:
            d.rounded_rectangle((cx - bw / 2, yb - h, cx + bw / 2, yb), 4, fill=col)
            d.rectangle((cx - bw / 2, yb - min(h, 6), cx + bw / 2, yb), fill=col)
    # etiquetas selectivas
    xo = x0 + slot * 7.5; yo = yb - (yb - ytop) * 8.73 / vmax
    show(cv, txt("Récord: $8,73M", F_XB, 34, CREAM, align="center"), t, 3.2, xo, yo - 110, "c", 20)
    show(cv, txt("180 ventas", F_MD, 26, CREAM2, align="center"), t, 3.4, xo, yo - 68, "c", 20)
    show(cv, txt("Marzo: $1,77M", F_SB, 28, CREAM2), t, 3.8, x0 - 10, yb - (yb - ytop) * 1.77 / vmax - 60, dy=20)
    show(cv, txt("×4,9 en 7 meses", F_PF, 74, GOLD_L), t, 4.6, 80, 1470)
    show(cv, txt("* Noviembre: proyección con base en 17 días ($293K/día).", F_MD, 28, CREAM2, maxw=920), t, 5.4, 80, 1580)
    return cv

def sc_portafolio(t):
    cv = BG.copy(); frame_ui(cv, t, "04 / 08", "PORTAFOLIO CERTIFICADO")
    shots = [("tortas", "Torta de Cuajada", (.5, .5)), ("almo", "Almojábanas del Campo", (.45, .6)), ("gall", "Galletas Caseritas", (.35, .5))]
    for i, (k, name, c) in enumerate(shots):
        t0 = .3 + .45 * i; kk = eo((t - t0) / .6)
        if kk <= 0: continue
        ph = rounded(view(IM[k], 1.15 - .08 * eio(t / 9), *c, 290, 420), 26)
        x = 80 + i * 315; y = 340 + int((1 - kk) * 80); ph.putalpha(ph.getchannel("A").point(lambda v: int(v * kk)))
        cv.alpha_composite(ph, (x, y)); show(cv, txt(name, F_SB, 28, CREAM, maxw=280), t, t0 + .3, x, 780, dy=10)
    # sello INVIMA
    if t > 2.2:
        k = back((t - 2.2) / .6); s = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(s)
        sd.ellipse((0, 0, 299, 299), fill=(26, 96, 62)); sd.ellipse((14, 14, 285, 285), outline=GOLD_L, width=4)
        s.alpha_composite(txt("3", F_BLK, 120, WHT, align="center"), (115, 40))
        s.alpha_composite(txt("REGISTROS", F_XB, 26, GOLD_L, align="center", track=2), (78, 180))
        s.alpha_composite(txt("INVIMA", F_BLK, 36, WHT, align="center"), (90, 214))
        put(cv, s, 220, 1060, k)
    show(cv, txt("Registros INVIMA vigentes", F_PF, 52, CREAM, maxw=560), t, 2.8, 410, 930)
    show(cv, txt("Toda la línea lista para retail, distribución y exportación.", F_MD, 34, CREAM2, maxw=560), t, 3.4, 410, 1085)
    show(cv, txt("Una barrera de entrada que tomó 3 años construir.", F_SB, 36, GOLD_L, maxw=920), t, 4.4, 80, 1300)
    show(cv, txt("+ Pandeyuca · Chocolate campesino · presentaciones de $3K a $120K", F_MD, 32, CREAM2, maxw=920), t, 5.2, 80, 1400)
    return cv

def sc_planta(t):
    cv = BG.copy(); photo_bg(cv, "planta", t, 6, 1.15, 1.02, .5, .5, 110)
    frame_ui(cv, t, "05 / 08", "CAPACIDAD Y CANALES")
    show(cv, txt("Planta de producción propia", F_PF, 66, CREAM, maxw=920), t, .4, 80, 1080)
    chans = [("Hoy", "Carrito · Digital · Institucional"), ("Siguiente", "Tienda a tienda (TAT) · Retail")]
    for i, (a, bb) in enumerate(chans):
        t0 = 1.4 + .8 * i
        row = Image.new("RGBA", (920, 110), (0, 0, 0, 0)); rd = ImageDraw.Draw(row)
        rd.rounded_rectangle((0, 0, 919, 109), 30, fill=(255, 255, 255, 18), outline=(120, 80, 46), width=2)
        row.alpha_composite(txt(a.upper(), F_XB, 26, GOLD_L, track=4), (30, 38))
        row.alpha_composite(txt(bb, F_SB, 38, CREAM), (230, 30)); show(cv, row, t, t0, 80, 1260 + 130 * i)
    show(cv, txt("Un cliente B2B reemplaza de 8 a 30 ventas individuales en recurrencia.", F_PFI, 44, GOLD_L, maxw=920),
         t, 3.4, 80, 1560)
    return cv

PHASES = [("FASE 1", "Meses 1–3", 20, "Estabilizar y fortalecer", "Capital de trabajo · ×1,5 vendedores · pauta digital"),
          ("FASE 2", "Meses 3–6", 12, "Canal TAT y retail", "15–20 puntos TAT · primer pedido retail"),
          ("FASE 3", "Meses 6–12", 8, "Primer local propio", "Vitrina y centro de distribución · 2T 2027")]
def sc_plan(t):
    cv = BG.copy(); frame_ui(cv, t, "06 / 08", "USO DEL CAPITAL")
    show(cv, txt("Plan de expansión en 3 fases · 12 meses", F_PF, 46, CREAM, maxw=940), t, .2, 80, 330)
    d = ImageDraw.Draw(cv); x = 150; y0, y1 = 520, 1450
    k = eo((t - .6) / 2.4); d.line((x, y0, x, y0 + (y1 - y0) * k), fill=GOLD, width=4)
    for i, (f, mm, amt, title, det) in enumerate(PHASES):
        t0 = .9 + 1.5 * i; y = 560 + 330 * i
        if t < t0: continue
        kk = back((t - t0) / .5); r = 34 * kk
        d.ellipse((x - r, y - r, x + r, y + r), fill=GOLD); cv.alpha_composite(txt(str(i + 1), F_BLK, 40, SURF, align="center"), (x - 13, y - 26))
        show(cv, txt(f"{f} · {mm}", F_XB, 28, GOLD_L, track=3), t, t0, 220, y - 60)
        show(cv, txt(f"${amt}M", F_BLK, 76, CREAM), t, t0 + .1, 220, y - 20)
        show(cv, txt(title, F_PF, 44, CREAM, maxw=480), t, t0 + .2, 500, y - 8)
        show(cv, txt(det, F_MD, 30, CREAM2, maxw=480), t, t0 + .3, 500, y + 60)
    show(cv, txt("Plan completo: $48M COP", F_PF, 60, GOLD_L), t, 6.0, 80, 1540)
    show(cv, txt("incluye producción, marketing y reserva operativa", F_MD, 34, CREAM2), t, 6.5, 80, 1630)
    show(cv, txt("“El capital no sostiene lo que ya funciona: abre los canales que multiplican el flujo de caja.”",
                 F_PFI, 38, CREAM, maxw=920), t, 7.4, 80, 1720)
    return cv

def offer_card(title, sub, rows, foot, accent):
    c = Image.new("RGBA", (920, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 919, 559), 36, fill=(255, 255, 255, 16), outline=accent, width=3)
    c.alpha_composite(txt(title, F_PF, 50, CREAM), (40, 32)); c.alpha_composite(txt(sub, F_MD, 30, CREAM2, maxw=840), (40, 106))
    y = 190
    for a, bb in rows:
        c.alpha_composite(txt(a, F_MD, 32, CREAM2), (40, y)); v = txt(bb, F_XB, 40, CREAM); c.alpha_composite(v, (880 - v.width, y - 4))
        d.line((40, y + 58, 880, y + 58), fill=(90, 56, 32), width=1); y += 76
    c.alpha_composite(txt(foot, F_MD, 26, GOLD_L, maxw=840), (40, 500)); return c
CARD_A = offer_card("A · Préstamo a término fijo", "Sin participación en el negocio.",
                    [("Monto", "$20M – $50M"), ("Interés", "2% mensual"), ("Plazo", "36 meses"), ("Respaldo", "Contrato notariado")],
                    "Retorno total: $24,8M – $62M según monto", GOLD_L)
CARD_B = offer_card("B · Participación en equity", "Participación real con potencial de valorización.",
                    [("Monto", "$20M – $50M"), ("Participación", "2,5% – 5%"), ("Valoración", "$800M – $1.000M"), ("Vesting", "Lineal 3 años")],
                    "+1% adicional (máx.) como colaborador activo", GOLD)
def sc_oferta(t):
    cv = BG.copy(); frame_ui(cv, t, "07 / 08", "OFERTA DE INVERSIÓN")
    show(cv, txt("Dos modalidades. Tú decides.", F_PF, 64, CREAM, maxw=920), t, .2, 80, 330)
    show(cv, CARD_A, t, 1.0, 80, 470, dy=60, dur=.6)
    show(cv, CARD_B, t, 2.6, 80, 1070, dy=60, dur=.6)
    show(cv, txt("Inversión desde $20M COP · condiciones sujetas a contrato", F_SB, 32, CREAM2, maxw=920), t, 4.6, 80, 1680)
    return cv

SCEN = [("2026", "Ritmo actual", 90, False), ("2027", "Conservador", 120, False), ("2027", "Base · con inversión", 160, True),
        ("2027", "Optimista", 220, False)]
def sc_proyeccion(t):
    cv = BG.copy(); frame_ui(cv, t, "08 / 08", "PROYECCIÓN")
    show(cv, txt("Trayectoria con capital", F_PF, 64, CREAM), t, .2, 80, 330)
    show(cv, txt("Facturación anual estimada · millones COP", F_MD, 32, CREAM2), t, .5, 80, 430)
    d = ImageDraw.Draw(cv); x0, xmax, y0 = 80, 1000, 600
    for i, (yr, lab, v, hi) in enumerate(SCEN):
        t0 = .9 + .5 * i; k = eo((t - t0) / .7); y = y0 + i * 210
        cv.alpha_composite(txt(f"{yr} · {lab}", F_SB, 32, CREAM if hi else CREAM2), (x0, y))
        if k <= 0: continue
        w = (xmax - x0 - 200) * v / 220 * k
        d.rounded_rectangle((x0, y + 56, x0 + w, y + 120), 4, fill=GOLD if hi else BAR)
        lab_v = ("$220M+" if v == 220 else f"${v}M") if k > .95 else f"${int(v * k)}M"
        cv.alpha_composite(txt(lab_v, F_XB, 44, CREAM), (int(x0 + w + 18), y + 60))
    show(cv, txt("Valoración $800M–$1.000M: múltiplo de 8–12× sobre ingresos recientes.", F_SB, 36, GOLD_L, maxw=920), t, 3.6, 80, 1460)
    show(cv, txt("El inversionista no compra el presente: compra la plataforma del canal B2B y retail de 2027.",
                 F_PFI, 38, CREAM, maxw=920), t, 4.6, 80, 1580)
    return cv

WHY = [("Tracción probada", "$45,9M facturados en 9 meses, sin capital externo."),
       ("INVIMA listo", "3 registros vigentes: barrera de entrada superada."),
       ("Temporada alta", "El capital opera desde diciembre, el mejor mes del año."),
       ("Canal TAT desatendido", "Alimentos artesanales certificados en tiendas de barrio.")]
def sc_porque(t):
    cv = BG.copy(); photo_bg(cv, "cart", t, 8.4, 1.1, 1.0, .5, .4, 175)
    frame_ui(cv, t, "", "")
    show(cv, txt("¿Por qué ahora?", F_PF, 84, CREAM), t, .2, 80, 260)
    for i, (a, bb) in enumerate(WHY):
        t0 = 1.0 + 1.0 * i; y = 470 + 280 * i
        if t < t0: continue
        k = back((t - t0) / .5); d = ImageDraw.Draw(cv); r = 30 * k
        d.ellipse((110 - r, y + 40 - r, 110 + r, y + 40 + r), fill=GOLD)
        if k > .8: d.line([(96, y + 40), (107, y + 52), (126, y + 28)], fill=SURF, width=7, joint="curve")
        show(cv, txt(a, F_XB, 46, CREAM), t, t0, 170, y + 8)
        show(cv, txt(bb, F_MD, 34, CREAM2, maxw=800), t, t0 + .15, 170, y + 78)
    return cv

def sc_cta(t):
    cv = BG.copy(); d = ImageDraw.Draw(cv)
    put(cv, LOGO_L, 540, 330, back(t / .7))
    show(cv, txt("“Esta no es una apuesta al futuro.", F_PFI, 60, CREAM, align="center"), t, .7, 540, 560, "c")
    show(cv, txt("Es entrar a un tren que ya", F_PFI, 60, CREAM, align="center"), t, 1.4, 540, 650, "c")
    show(cv, txt("está en movimiento.”", F_PFI, 60, GOLD_L, align="center"), t, 2.0, 540, 740, "c")
    if t > 3.2:
        k = back((t - 3.2) / .6); pul = 1 + .03 * math.sin(max(0, t - 4) * 5)
        btn = Image.new("RGBA", (860, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
        bd.rounded_rectangle((0, 0, 859, 149), 75, fill=GOLD); v = txt("AGENDA UNA REUNIÓN", F_BLK, 58, SURF, align="center")
        btn.alpha_composite(v, ((860 - v.width) // 2, 40)); put(cv, btn, 540, 960, k * pul)
    show(cv, txt("Compartimos estados financieros, proyecciones detalladas y una reunión de trabajo.",
                 F_MD, 34, CREAM2, maxw=880, align="center"), t, 4.0, 540, 1070, "c")
    contacts = [("Correo", "manuel@barujshefa.com"), ("WhatsApp", "+57 319 653 6874"), ("Web", "barujshefa.com"), ("Instagram", "@barujshefa")]
    for i, (a, bb) in enumerate(contacts):
        row = Image.new("RGBA", (880, 96), (0, 0, 0, 0)); rd = ImageDraw.Draw(row)
        rd.rounded_rectangle((0, 0, 879, 95), 26, fill=(255, 255, 255, 16), outline=(110, 72, 42), width=2)
        row.alpha_composite(txt(a.upper(), F_XB, 24, GOLD_L, track=3), (30, 34)); v = txt(bb, F_XB, 40, CREAM)
        row.alpha_composite(v, (850 - v.width, 22)); show(cv, row, t, 4.8 + .3 * i, 100, 1210 + 112 * i, dy=20)
    show(cv, txt("Baruj Shefa S.A.S. · NIT 901.990.427-6 · Bogotá, Colombia", F_SB, 26, CREAM2, align="center"), t, 6.4, 540, 1680, "c")
    show(cv, txt("Pieza informativa. No constituye oferta pública de valores. Toda inversión implica riesgos; "
                 "las condiciones finales se definen por contrato y tras debida diligencia.", F_MD, 22, (170, 150, 128),
                 maxw=900, align="center", lh=1.3), t, 6.8, 540, 1740, "c")
    return cv

def wipe(prev, cur, k):
    e = eio(k); x = int(W * e); out = prev.copy(); out.paste(cur.crop((0, 0, x, H)), (0, 0))
    if 0 < e < 1: ImageDraw.Draw(out).rectangle((x - 4, 0, x + 4, H), fill=GOLD)
    return out
def fade(prev, cur, k): return Image.blend(prev, cur, eio(k))

SCENES = [(6.0, sc_hook, None), (6.0, sc_origen, "fade"), (7.2, sc_traccion, "wipe"), (7.2, sc_ventas, "wipe"),
          (7.2, sc_portafolio, "wipe"), (6.0, sc_planta, "fade"), (9.6, sc_plan, "wipe"), (8.4, sc_oferta, "wipe"),
          (7.2, sc_proyeccion, "wipe"), (7.2, sc_porque, "fade"), (12.0, sc_cta, "fade")]
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
DUR = acc; TR = .5

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", MUSIC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev, cur, last = None, 0, None
N = int(DUR * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(starts) if s <= t + 1e-6)
    if si != cur: last.save(os.path.join(SNAP, f"escena_{cur + 1:02d}.png")); prev, cur = last, si
    _, fn, tr = SCENES[si]; lt = t - starts[si]
    fr = fn(lt).convert("RGB"); last = fr; out = fr
    if tr and lt < TR and prev is not None: out = wipe(prev, fr, lt / TR) if tr == "wipe" else fade(prev, fr, lt / TR)
    if fi < 8: out = Image.blend(Image.new("RGB", (W, H), SURF), out, fi / 8)
    ff.stdin.write(out.tobytes())
    if fi % 300 == 0: print(f"{fi}/{N}", flush=True)
last.save(os.path.join(SNAP, f"escena_{cur + 1:02d}.png"))
ff.stdin.close(); ff.wait()
print(f"DUR={DUR:.2f}")
