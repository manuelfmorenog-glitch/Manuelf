#!/usr/bin/env python3
"""Reel campaña VENDEDORES DIGITALES Baruj Shefa (1080x1920).

6 escenas: Gancho · Oportunidad · Sin complicaciones · Desde donde estés · Respaldo · Conversión.
Sin precios, sin cifras de ganancias, INVIMA solo para tortas de cuajada, botón "REGÍSTRATE AHORA".

Uso: python3 build_vendedores.py <medios> <fuentes> <musica.wav> <final.mp4> <carpeta_portadas>
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL, COVERS = sys.argv[1:6]
os.makedirs(COVERS, exist_ok=True)
W, H, FPS, BPM = 1080, 1920, 30, 112
BEAT = 60 / BPM
URL = "www.barujshefa.com/registro-vendedor"

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
P = {k: m(v) for k, v in dict(duo="c5266882", spoon="0f60c5bb", almo_r="a0cf5d80", torta_r="6351a50d",
                               oven_prod="7bc77db3", torta_p="09ff1f5e", kitchen="0b8446a6", oven="eec84a84",
                               gall="8ae233b1", almo="eef727c6", tray="14c3690f", logo="777dda90").items()}

F_PF = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_SB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
if not os.path.exists(F_SB): F_SB = F_XB

CRM, CRM2 = (248, 239, 222), (238, 222, 196)
CHOC, CHOC2 = (52, 26, 12), (84, 44, 20)
TERRA, GOLD, GOLD2 = (196, 86, 44), (214, 160, 62), (250, 214, 130)
WHT, INK, GRN = (255, 255, 255), (40, 22, 10), (37, 150, 90)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=1.8): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    return x if x in (0, 1) else 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1
def b(n): return n * BEAT

def load(k): return ImageOps.exif_transpose(Image.open(P[k])).convert("RGB")
def warm(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.06 + 128 + np.array([6, 2, -6]); l = a.mean(2, keepdims=True); a = l + (a - l) * 1.15
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def view(img, z, cx, cy, w=W, h=H):
    iw, ih = img.size; s = max(w / iw, h / ih) * z; vw, vh = w / s, h / s
    l = clamp(cx * iw - vw / 2, 0, iw - vw); t = clamp(cy * ih - vh / 2, 0, ih - vh)
    return img.resize((w, h), Image.BILINEAR, box=(l, t, l + vw, t + vh))
IM = {k: warm(load(k)) for k in P if k != "logo"}

# ---------- texto ----------
_c = {}
def txt(text, font, size, fill, lh=1.12, align="center", maxw=None, shadow=False):
    k = (text, font, size, fill, lh, align, maxw, shadow)
    if k in _c: return _c[k]
    f = ImageFont.truetype(font, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    rows = []
    for para in text.split("\n"):
        if not maxw: rows.append(para); continue
        cur = ""
        for w_ in para.split(" "):
            t2 = (cur + " " + w_).strip()
            if tmp.textlength(t2, font=f) <= maxw: cur = t2
            else: rows.append(cur); cur = w_
        rows.append(cur)
    a, d_ = f.getmetrics(); L = int((a + d_) * lh)
    ws = [tmp.textlength(r, font=f) for r in rows]; tw = int(max(ws)) if ws else 1
    pad = 24
    img = Image.new("RGBA", (tw + 2 * pad, L * len(rows) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        x = pad + ((tw - ws[i]) / 2 if align == "center" else 0)
        d.text((x, pad + i * L), r, font=f, fill=fill)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); blk = Image.new("RGBA", img.size, (20, 8, 0, 255))
        blk.putalpha(img.getchannel("A")); sh.alpha_composite(blk); sh = sh.filter(ImageFilter.GaussianBlur(12))
        sh = Image.alpha_composite(sh, sh); sh.alpha_composite(img); img = sh
    _c[k] = img; return img

def put(cv, img, cx, cy, sc=1., al=1., rot=0., anchor="c"):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BICUBIC, expand=True)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    x = cx - img.width / 2 if anchor == "c" else cx
    cv.alpha_composite(img, (int(x), int(cy - img.height / 2)))

def enter(cv, img, t, t0, cx, cy, kind="up", anchor="c"):
    if t < t0: return
    k = (t - t0) / .55; sc, al, x, y = 1., 1., cx, cy
    if kind == "up": y = cy + (1 - eo(k)) * 90; al = eo(k * 1.3)
    elif kind == "pop": sc = back(k, 2.2); al = eo(k * 3)
    elif kind == "left": x = cx - (1 - eo(k)) * 300; al = eo(k * 1.5)
    elif kind == "fade": al = eo(k)
    put(cv, img, x, y, sc, al, 0, anchor)

def pill(text, size, fg, bg, padx=46, h=None, border=None):
    f = ImageFont.truetype(F_XB, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength(text, font=f); h = h or int(size * 2.1); w = int(tw + 2 * padx)
    img = Image.new("RGBA", (w + 16, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((6, 14, w + 6, h + 14), h // 2, fill=(0, 0, 0, 90))
    d.rounded_rectangle((0, 0, w, h), h // 2, fill=bg, outline=border, width=4 if border else 0)
    a, dd = f.getmetrics(); d.text((padx, (h - a - dd) / 2 + 2), text, font=f, fill=fg)
    return img

def round_logo(size, ring=GOLD):
    lg = Image.open(P["logo"]).convert("RGBA").resize((size - 16, size - 16), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((3, 3, lg.width - 3, lg.height - 3), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (8, 8), mk); return out
LOGO_S, LOGO_M = round_logo(120), round_logo(260)

def rounded(img, r):
    img = img.convert("RGBA"); mk = Image.new("L", img.size, 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255); img.putalpha(mk); return img

# ---------- celular con catálogo (sin precios) ----------
SW, SH = 440, 920
def catalog_screen():
    rows = [("torta_p", "Torta Personal", "Receta de la abuela"), ("almo", "Almojábanas del Campo", "Caja x6"),
            ("spoon", "Torta de Cuajada", "Suave y doradita"), ("gall", "Galletas Caseritas", "Hechas con amor"),
            ("torta_r", "Torta Mediana", "Para compartir"), ("almo_r", "Combo Familiar", "Torta + almojábanas")]
    cw, chh = 196, 330
    tall = Image.new("RGBA", (SW, 150 + ((len(rows) + 1) // 2) * (chh + 16) + 40), (250, 245, 236, 255))
    d = ImageDraw.Draw(tall)
    tall.alpha_composite(round_logo(70), (18, 22))
    d.text((100, 30), "CATÁLOGO DE", font=ImageFont.truetype(F_SB, 15), fill=(180, 130, 50))
    d.text((100, 50), "Tu nombre aquí", font=ImageFont.truetype(F_PF, 26), fill=CHOC)
    x = 16
    for i, chip in enumerate(["Todos", "Tortas", "Combos", "Productos"]):
        f = ImageFont.truetype(F_SB, 17); w = d.textlength(chip, font=f) + 28
        d.rounded_rectangle((x, 104, x + w, 138), 17, fill=CHOC if i == 0 else WHT, outline=CRM2, width=2)
        d.text((x + 14, 110), chip, font=f, fill=WHT if i == 0 else CHOC); x += w + 8
    for i, (k, name, sub) in enumerate(rows):
        cx, cy = 16 + (i % 2) * (cw + 16), 154 + (i // 2) * (chh + 16)
        card = Image.new("RGBA", (cw, chh), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, cw - 1, chh - 1), 18, fill=WHT, outline=CRM2, width=2)
        ph = rounded(view(IM[k], 1.1, .5, .5, cw - 12, 170), 14); card.alpha_composite(ph, (6, 6))
        if i < 2:
            cd.rounded_rectangle((14, 14, 112, 40), 13, fill=GOLD); cd.text((24, 17), "★ Destacado", font=ImageFont.truetype(F_SB, 14), fill=WHT)
        f1 = ImageFont.truetype(F_PF, 19); y = 186
        for ln in (name if len(name) < 17 else name.replace(" del ", "\ndel ").replace("Combo ", "Combo\n")).split("\n"):
            cd.text((12, y), ln, font=f1, fill=CHOC); y += 24
        cd.text((12, y + 2), sub, font=ImageFont.truetype(F_SB, 14), fill=(130, 100, 70))
        cd.rounded_rectangle((12, chh - 52, cw - 12, chh - 14), 19, fill=(196, 146, 56))
        cd.text((cw / 2 - 38, chh - 46), "+  Agregar", font=ImageFont.truetype(F_SB, 17), fill=WHT)
        tall.alpha_composite(card, (cx, cy))
    return tall
CATALOG = catalog_screen()

def phone(scroll=0., overlay=None):
    bw = 18; ph = Image.new("RGBA", (SW + 2 * bw, SH + 2 * bw), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle((0, 0, SW + 2 * bw - 1, SH + 2 * bw - 1), 70, fill=(22, 18, 16))
    d.rounded_rectangle((3, 3, SW + 2 * bw - 4, SH + 2 * bw - 4), 68, outline=(90, 80, 70), width=3)
    y = int(scroll * (CATALOG.height - SH + 60))
    scr = Image.new("RGBA", (SW, SH), (250, 245, 236, 255)); scr.alpha_composite(CATALOG.crop((0, y, SW, y + SH - 60)), (0, 40))
    sd = ImageDraw.Draw(scr); sd.text((34, 10), "9:41", font=ImageFont.truetype(F_SB, 18), fill=INK)
    sd.rounded_rectangle((SW - 80, 14, SW - 36, 28), 5, outline=INK, width=2); sd.rectangle((SW - 77, 17, SW - 46, 25), fill=INK)
    sd.rectangle((0, SH - 60, SW, SH), fill=WHT); sd.line((0, SH - 60, SW, SH - 60), fill=CRM2, width=2)
    sd.text((70, SH - 44), "Catálogo", font=ImageFont.truetype(F_SB, 18), fill=(196, 146, 56))
    sd.text((280, SH - 44), "Mi pedido", font=ImageFont.truetype(F_SB, 18), fill=(150, 140, 130))
    if overlay: overlay(scr)
    ph.alpha_composite(rounded(scr, 54), (bw, bw))
    d.rounded_rectangle((SW / 2 + bw - 60, bw + 10, SW / 2 + bw + 60, bw + 40), 15, fill=(10, 8, 8))
    out = Image.new("RGBA", (ph.width + 80, ph.height + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((50, 60, ph.width + 30, ph.height + 50), 70, fill=(0, 0, 0, 120))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24))); out.alpha_composite(ph, (40, 30)); return out

# ---------- fondos ----------
def cream_bg():
    bg = Image.new("RGB", (W, H), CRM); d = ImageDraw.Draw(bg); rng = np.random.default_rng(1)
    for _ in range(38):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(8, 18)
        d.polygon([(x, y - s), (x + s * .25, y - s * .25), (x + s, y), (x + s * .25, y + s * .25), (x, y + s),
                   (x - s * .25, y + s * .25), (x - s, y), (x - s * .25, y - s * .25)], fill=CRM2)
    return bg.convert("RGBA")
CREAM = cream_bg()
def grad(top=0, bot=0, color=(30, 14, 4)):
    g = np.zeros((H, W, 4), np.uint8); g[..., :3] = color; y = np.arange(H)[:, None]
    a = np.zeros((H, 1))
    if bot: a = np.maximum(a, np.clip((y - (H - bot)) / bot, 0, 1) ** 1.2 * 235)
    if top: a = np.maximum(a, np.clip(1 - y / top, 0, 1) ** 1.2 * 225)
    g[..., 3] = np.repeat(a, W, 1).astype(np.uint8); return Image.fromarray(g)
G_TOP, G_BOT, G_BOTH = grad(top=900), grad(bot=1000), grad(top=760, bot=760)

def header(cv, t):  # marca discreta
    put(cv, LOGO_S, 92, 92, 1, eo(t / .4))

# ---------- escenas ----------
def sc_hook(t):
    cv = view(IM["tray"], 1.25 - .1 * eio(t / 5), .5, .5).filter(ImageFilter.GaussianBlur(6)).convert("RGBA")
    cv.alpha_composite(Image.new("RGBA", (W, H), (40, 18, 6, 150)))
    k = (t - .2) / .9
    put(cv, phone(eio((t - 1.6) / 3) * .5), 540, 1330 + (1 - back(k, 1.2)) * 900, .92, 1, -6 * eo(k))
    cv.alpha_composite(G_TOP)
    enter(cv, txt("¿Y si tu celular", F_PF, 92, WHT, shadow=True), t, .3, 540, 250)
    enter(cv, txt("también te ayudara a", F_PF, 72, WHT, shadow=True), t, .7, 540, 360)
    enter(cv, txt("generar ingresos?", F_PF, 100, GOLD2, shadow=True), t, 1.1, 540, 470, "pop")
    enter(cv, pill("Conviértete en vendedor digital Baruj Shefa", 36, CHOC, CRM), t, 2.0, 540, 610, "up")
    header(cv, t); return cv

OPP = [("spoon", 1.15, 1.0, .5, .5), ("almo_r", 1.1, 1.22, .5, .45), ("torta_r", 1.2, 1.05, .55, .55)]
def sc_oportunidad(t):
    dur = b(3.5); si = min(int(t / dur), 2); lt = t - si * dur
    k, z0, z1, cx, cy = OPP[si]; fr = view(IM[k], z0 + (z1 - z0) * eio(lt / dur), cx, cy).convert("RGBA")
    if lt < .5 and si > 0:
        pk, pz0, pz1, pcx, pcy = OPP[si - 1]
        fr = Image.blend(view(IM[pk], pz1, pcx, pcy).convert("RGBA"), fr, eio(lt / .5))
    fr.alpha_composite(G_BOT); fr.alpha_composite(G_BOT); fr.alpha_composite(G_BOT)
    enter(fr, txt("Comparte sabores", F_PF, 104, WHT, shadow=True), t, .2, 540, 1300)
    enter(fr, txt("que enamoran.", F_PF, 104, GOLD2, shadow=True), t, .6, 540, 1420)
    enter(fr, txt("Tortas de cuajada, almojábanas y galletas caseritas. Productos tradicionales para ofrecer a tus contactos.",
                  F_SB, 42, CRM, maxw=900, lh=1.3), t, 1.2, 540, 1600)
    header(fr, t); return fr

def icon(kind, s=150, col=WHT):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img); c = s / 2
    if kind == "share":
        pts = [(c - 35, c), (c + 32, c - 32), (c + 32, c + 32)]
        d.line([pts[1], pts[0], pts[2]], fill=col, width=9)
        for x, y in pts: d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=col)
    elif kind == "order":
        d.rounded_rectangle((c - 34, c - 44, c + 34, c + 44), 10, outline=col, width=8)
        for i in range(3): d.line((c - 18, c - 18 + i * 18, c + 18, c - 18 + i * 18), fill=col, width=7)
    elif kind == "prep":
        d.ellipse((c - 30, c - 52, c + 30, c - 8), fill=col); d.ellipse((c - 46, c - 40, c - 6, c - 4), fill=col)
        d.ellipse((c + 6, c - 40, c + 46, c - 4), fill=col); d.rectangle((c - 32, c - 20, c + 32, c + 22), fill=col)
        d.rectangle((c - 34, c + 28, c + 34, c + 42), fill=col)
    elif kind == "deliver":
        d.rounded_rectangle((c - 50, c - 30, c + 14, c + 20), 6, fill=col)
        d.polygon([(c + 14, c - 14), (c + 38, c - 14), (c + 52, c + 4), (c + 52, c + 20), (c + 14, c + 20)], fill=col)
        for x in (c - 28, c + 32): d.ellipse((x - 15, c + 12, x + 15, c + 42), fill=col); d.ellipse((x - 6, c + 21, x + 6, c + 33), fill=TERRA)
    return img
STEPS = [("share", "Compartir"), ("order", "Pedido"), ("prep", "Preparación"), ("deliver", "Entrega")]
def sc_simple(t):
    cv = CREAM.copy(); d = ImageDraw.Draw(cv)
    enter(cv, txt("Sin inventarios.", F_PF, 96, CHOC), t, .1, 540, 230)
    enter(cv, txt("Sin experiencia.", F_PF, 96, TERRA), t, .5, 540, 345)
    # flujo de 4 pasos
    ys = [600, 840, 1080, 1320]
    for i, (ic, lab) in enumerate(STEPS):
        t0 = b(2 + 1.6 * i)
        if t > t0 and i > 0:
            k = eo((t - t0 + .3) / .5); d.line((300, ys[i - 1] + 85, 300, ys[i - 1] + 85 + (ys[i] - ys[i - 1] - 170) * k), fill=GOLD, width=8)
        if t < t0: continue
        k = (t - t0) / .5
        circ = Image.new("RGBA", (190, 190), (0, 0, 0, 0)); cd = ImageDraw.Draw(circ)
        cd.ellipse((6, 10, 186, 190), fill=(0, 0, 0, 50)); cd.ellipse((0, 0, 180, 180), fill=TERRA if i % 2 == 0 else CHOC2)
        circ.alpha_composite(icon(ic, 150), (15, 15))
        put(cv, circ, 300, ys[i], back(k, 2), 1)
        enter(cv, txt(f"{i + 1}. {lab}", F_BLK, 62, CHOC, align="left"), t, t0 + .15, 420, ys[i] - 10, "left", "l")
    enter(cv, txt("Tú compartes tu catálogo. Tus clientes hacen sus pedidos. Nosotros nos encargamos del resto.",
                  F_SB, 44, CHOC2, maxw=900, lh=1.3), t, b(8.6), 540, 1600)
    header(cv, t); return cv

PLACES = [("Desde casa", "home"), ("En tus tiempos libres", "clock"), ("Mientras disfrutas un café", "cup")]
def place_icon(kind, s=90):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img); c = s / 2
    if kind == "home":
        d.polygon([(c, 10), (s - 8, c), (8, c)], fill=WHT); d.rectangle((20, c - 2, s - 20, s - 12), fill=WHT); d.rectangle((c - 8, c + 12, c + 8, s - 12), fill=TERRA)
    elif kind == "clock":
        d.ellipse((8, 8, s - 8, s - 8), outline=WHT, width=8); d.line((c, c, c, 24), fill=WHT, width=7); d.line((c, c, c + 18, c + 10), fill=WHT, width=7)
    else:
        d.rounded_rectangle((12, 30, 62, 78), 10, fill=WHT); d.ellipse((52, 38, 80, 66), outline=WHT, width=7)
        for x in (24, 38, 50): d.arc((x - 6, 6, x + 6, 30), 90, 270, fill=WHT, width=4)
    return img
def sc_contigo(t):
    cv = view(IM["oven"], 1.1, .5, .5).filter(ImageFilter.GaussianBlur(10)).convert("RGBA")
    cv.alpha_composite(Image.new("RGBA", (W, H), (44, 20, 8, 175)))
    enter(cv, txt("Tu oportunidad", F_PF, 100, WHT, shadow=True), t, .1, 540, 220)
    enter(cv, txt("va contigo.", F_PF, 100, GOLD2, shadow=True), t, .5, 540, 335)
    put(cv, phone(.15 + .7 * eio(t / b(9))), 300, 1040, .78, eo((t - .4) / .6), 4)
    for i, (lab, ic) in enumerate(PLACES):
        t0 = b(1.8 + 1.4 * i)
        if t < t0: continue
        card = Image.new("RGBA", (470, 200), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 460, 190), 36, fill=(250, 241, 225, 240))
        cd.ellipse((22, 45, 122, 145), fill=TERRA); card.alpha_composite(place_icon(ic), (27, 50))
        tx = txt(lab, F_XB, 38, CHOC, maxw=300, align="left", lh=1.15); card.alpha_composite(tx, (130, (190 - tx.height) // 2))
        enter(cv, card, t, t0, 790, 720 + 230 * i, "left")
    enter(cv, txt("Comparte tu catálogo y empieza a construir tu red de clientes.", F_SB, 44, CRM, maxw=900, lh=1.3, shadow=True),
          t, b(6.5), 540, 1700)
    header(cv, t); return cv

CHECKS = ["Productos de tradición familiar", "Registro sanitario INVIMA para nuestras tortas de cuajada",
          "Catálogo digital personalizado", "Producción y entregas a cargo de Baruj Shefa", "Oportunidad de generar ingresos por ventas"]
def check_row(text):
    row = Image.new("RGBA", (940, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(row)
    d.rounded_rectangle((0, 0, 930, 110), 30, fill=(252, 246, 236, 245))
    d.ellipse((20, 22, 86, 88), fill=GRN); d.line([(36, 56), (50, 70), (72, 42)], fill=WHT, width=9, joint="curve")
    tx = txt(text, F_XB, 34, CHOC, maxw=780, align="left", lh=1.12); row.alpha_composite(tx, (100, (110 - tx.height) // 2))
    return row
ROWS = [check_row(c) for c in CHECKS]
RESP = [("oven_prod", 1.05, 1.15, .5, .45), ("kitchen", 1.15, 1.05, .55, .4)]
def sc_respaldo(t):
    dur = b(5); si = min(int(t / dur), 1); lt = t - si * dur
    k, z0, z1, cx, cy = RESP[si]; cv = view(IM[k], z0 + (z1 - z0) * eio(lt / dur), cx, cy).convert("RGBA")
    if lt < .5 and si > 0:
        pk, pz0, pz1, pcx, pcy = RESP[0]; cv = Image.blend(view(IM[pk], pz1, pcx, pcy).convert("RGBA"), cv, eio(lt / .5))
    cv.alpha_composite(Image.new("RGBA", (W, H), (36, 16, 4, 120))); cv.alpha_composite(G_BOTH)
    enter(cv, txt("Tú vendes.", F_PF, 104, WHT, shadow=True), t, .1, 540, 230)
    enter(cv, txt("Nosotros respaldamos\ncada pedido.", F_PF, 76, GOLD2, shadow=True), t, .6, 540, 400)
    for i, r in enumerate(ROWS):
        enter(cv, r, t, b(2.2 + 1.1 * i), 545, 900 + 140 * i, "left")
    header(cv, t); return cv

def sc_final(t):
    cv = CREAM.copy()
    photo = rounded(view(IM["duo"], 1.12 - .06 * eio(t / 6), .5, .42, 920, 900), 48)
    fr = Image.new("RGBA", (960, 940), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle((0, 0, 959, 939), 60, fill=GOLD)
    fr.alpha_composite(photo, (20, 20))
    put(cv, fr, 540, 640, .97 + .03 * eo(t / .8), eo(t / .5))
    put(cv, LOGO_M, 870, 230, elastic((t - .5) / .9) if t > .5 else 0, 1, 8)
    enter(cv, txt("¡TU PRÓXIMA VENTA", F_BLK, 88, CHOC), t, b(1.5), 540, 1180, "up")
    enter(cv, txt("PUEDE EMPEZAR HOY!", F_BLK, 88, TERRA), t, b(2.1), 540, 1285, "up")
    enter(cv, txt("Únete a nuestra comunidad de vendedores digitales.", F_SB, 40, CHOC2, maxw=900), t, b(2.8), 540, 1385)
    if t > b(3.6):
        k = (t - b(3.6)) / .5; pul = 1 + .04 * math.sin(max(0, t - b(4.6)) * 6)
        put(cv, pill("REGÍSTRATE AHORA", 54, WHT, TERRA, padx=70, border=GOLD2), 540, 1530, back(k, 2.4) * pul, 1)
    if t > b(4.6):
        k = eo((t - b(4.6)) / .5)
        box = Image.new("RGBA", (1000, 130), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((0, 0, 999, 129), 28, fill=CHOC)
        tx = txt(URL, F_XB, 46, GOLD2); box.alpha_composite(tx, ((1000 - tx.width) // 2, (130 - tx.height) // 2))
        put(cv, box, 540, 1700 + (1 - k) * 60, 1, k)
    return cv

def wipe(prev, cur, k):
    e = eio(k); y = int(H * (1 - e)); out = prev.copy(); out.paste(cur.crop((0, y, W, H)), (0, y))
    if 0 < e < 1: ImageDraw.Draw(out).rectangle((0, y - 14, W, y), fill=GOLD)
    return out

SCENES = [(10, sc_hook), (10.5, sc_oportunidad), (16, sc_simple), (13, sc_contigo), (10, sc_respaldo), (14, sc_final)]
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
DUR = b(acc); TR = .6

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
        prev, cur = last, si
    lt = t - b(starts[si])
    fr = SCENES[si][1](lt).convert("RGB")
    # guardar portadas: final de cada escena
    if fi + 1 < N and max(i for i, s in enumerate(starts) if b(s) <= (fi + 1) / FPS + 1e-6) != si or fi == N - 1:
        fr.save(os.path.join(COVERS, f"escena_{si + 1}.png"))
    last = fr; out = fr
    if lt < TR and prev is not None: out = wipe(prev, fr, lt / TR)
    if fi < 8: out = Image.blend(Image.new("RGB", (W, H), CRM), out, fi / 8)
    ff.stdin.write(out.tobytes())
    if fi % 150 == 0: print(f"{fi}/{N}", flush=True)
ff.stdin.close(); ff.wait()
print(f"DUR={DUR:.2f}")
