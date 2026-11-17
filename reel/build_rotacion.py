#!/usr/bin/env python3
"""Reel "¡Un gran paso!" – VERSIÓN 2 (rotación) con el jingle de Baruj Shefa.

Diseño editorial tipo revista: papel claro, fotos en formas (arco, círculo, marco),
capítulos numerados 01–04, sello de goma "APROBADO · REGISTRO SANITARIO INVIMA",
cortes sincronizados al jingle (~120 BPM).

Uso: python3 build_rotacion.py <medios> <fuentes> <jingle.wav> <final.mp4> <carpeta_fotogramas>
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, JINGLE, FINAL, SNAP = sys.argv[1:6]
os.makedirs(SNAP, exist_ok=True)
W, H, FPS = 1080, 1920, 30
BEAT, OFF = 60 / 120.5, 0.21
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "celebracion", "assets")
with wave.open(JINGLE) as w: TOTAL = w.getnframes() / w.getframerate()

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
P = dict(duo=m("a4fe69f9"), spoon=m("e6bf323c"), llenando=m("3ed9ad98"), crudas=m("7891d98b"),
         lavado=m("79eefe17"), planta=m("14849d92"), tortas=m("483610ce"), almo=m("ac03ebef"))
CLIP, LOGO = m("8e192c8f"), m("777dda90")

F_PF = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_PFI = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_MD = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
if not os.path.exists(F_MD): F_MD = F_XB

PAPER, PAPER2 = (251, 247, 240), (240, 232, 218)
INK, INK2 = (58, 30, 14), (120, 84, 56)
GOLD, GREEN, TERRA, WHT = (196, 146, 58), (22, 98, 64), (190, 84, 44), (255, 255, 255)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back(x, s=1.7): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    return x if x in (0, 1) else 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1
def b(n): return n * BEAT
def pulse(t): return math.exp(-(((t) / BEAT) % 1) * 7)

def warm(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.05 + 128 + np.array([6, 3, -4]); l = a.mean(2, keepdims=True); a = l + (a - l) * 1.1
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
IM = {k: warm(ImageOps.exif_transpose(Image.open(p)).convert("RGB")) for k, p in P.items()}
def view(img, z, cx, cy, w, h):
    iw, ih = img.size; s = max(w / iw, h / ih) * z; vw, vh = w / s, h / s
    l = clamp(cx * iw - vw / 2, 0, iw - vw); t = clamp(cy * ih - vh / 2, 0, ih - vh)
    return img.resize((int(w), int(h)), Image.BILINEAR, box=(l, t, l + vw, t + vh))

class Vid:
    def __init__(self, ss, speed=1.0, w=1080, h=1920):
        self.a = (ss, speed, w, h); self.p = None; self.last = None
    def frame(self):
        ss, sp, w, h = self.a
        if not self.p:
            vf = f"setpts=PTS/{sp},fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", CLIP, "-vf", vf,
                                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        buf = self.p.stdout.read(w * h * 3)
        if len(buf) == w * h * 3: self.last = warm(Image.frombuffer("RGB", (w, h), buf))
        return self.last
V = {"feria": Vid(0.4, 1.0), "horno": Vid(7.0, 1.0), "tortas": Vid(12.0, .7), "empaque": Vid(17.0, .8)}

# ---------- formas y texto ----------
def shape_mask(w, h, kind):
    mk = Image.new("L", (int(w), int(h)), 0); d = ImageDraw.Draw(mk)
    if kind == "arch": d.rectangle((0, w / 2, w, h), fill=255); d.ellipse((0, 0, w, w), fill=255)
    elif kind == "circle": d.ellipse((0, 0, w - 1, h - 1), fill=255)
    else: d.rounded_rectangle((0, 0, w - 1, h - 1), 44, fill=255)
    return mk
_mk = {}
def framed(img, kind, w, h, border=GOLD, bw=0):
    key = (kind, int(w), int(h))
    if key not in _mk: _mk[key] = shape_mask(w, h, kind)
    out = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0)); out.paste(img.convert("RGB"), (0, 0), _mk[key])
    return out

def reveal(cv, img, x, y, k, mode="up"):
    """Revela una imagen ya enmascarada con persiana."""
    if k <= 0: return
    k = eio(k); w, h = img.size
    if mode == "up":
        hh = int(h * k); cv.alpha_composite(img.crop((0, h - hh, w, h)), (int(x), int(y + h - hh)))
    elif mode == "left":
        ww = int(w * k); cv.alpha_composite(img.crop((0, 0, ww, h)), (int(x), int(y)))
    elif mode == "circle":
        r = int(math.hypot(w, h) / 2 * k); mk = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mk).ellipse((w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r), fill=255)
        a = Image.fromarray(np.minimum(np.asarray(mk), np.asarray(img.getchannel("A"))))
        im = img.copy(); im.putalpha(a); cv.alpha_composite(im, (int(x), int(y)))

_c = {}
def txt(text, font, size, fill, maxw=None, lh=1.12, align="left", track=0):
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
    a, d_ = f.getmetrics(); L = int((a + d_) * lh); ws = [tl(r) for r in rows]; tw = int(max(ws))
    img = Image.new("RGBA", (tw + 8, L * len(rows) + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        x = (tw - ws[i]) / 2 if align == "center" else 0
        if track:
            for ch in r: d.text((x, i * L), ch, font=f, fill=fill); x += tmp.textlength(ch, font=f) + track
        else: d.text((x, i * L), r, font=f, fill=fill)
    _c[k] = img; return img

def appear(cv, img, t, t0, x, y, dy=40, anchor="l"):
    if t < t0: return
    k = eo((t - t0) / .5)
    im = img if k >= 1 else img.copy()
    if k < 1: im.putalpha(img.getchannel("A").point(lambda v: int(v * k)))
    xx = x - img.width / 2 if anchor == "c" else x
    cv.alpha_composite(im, (int(xx), int(y + (1 - k) * dy)))

def put(cv, img, cx, cy, sc=1., al=1., rot=0.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BICUBIC, expand=True)
    if al < 1: img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

# papel con grano
rng = np.random.default_rng(3)
_n = rng.normal(0, 5, (H, W, 1))
PAPER_BG = Image.fromarray(np.clip(np.array(PAPER)[None, None, :] + _n, 0, 255).astype(np.uint8)).convert("RGBA")

def chapter(cv, t, num, label, y=120):
    """Encabezado editorial: número en contorno + etiqueta + línea dorada."""
    f = ImageFont.truetype(F_PF, 150)
    if t > 0:
        k = eo(t / .5)
        n = Image.new("RGBA", (360, 210), (0, 0, 0, 0)); ImageDraw.Draw(n).text((0, 0), num, font=f, fill=(0, 0, 0, 0), stroke_width=3, stroke_fill=GOLD)
        put(cv, n, 70 + 180, y + 80 - (1 - k) * 40, 1, k)
    d = ImageDraw.Draw(cv); lk = eo((t - .2) / .6)
    if lk > 0: d.line((300, y + 150, 300 + 710 * lk, y + 150), fill=GOLD, width=3)
    appear(cv, txt(label, F_XB, 34, INK, track=8), t, .35, 300, y + 95, 20)

def round_logo(size, ring=GOLD, rw=8):
    lg = Image.open(LOGO).convert("RGBA").resize((size - 2 * rw, size - 2 * rw), Image.LANCZOS)
    mk = Image.new("L", lg.size, 0); ImageDraw.Draw(mk).ellipse((3, 3, lg.width - 3, lg.height - 3), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse((0, 0, size - 1, size - 1), fill=ring)
    out.paste(lg, (rw, rw), mk); return out
LOGO_L, LOGO_S = round_logo(300), round_logo(110)

# sello de goma
def make_stamp():
    s = Image.new("RGBA", (860, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(s); c = (22, 98, 64, 255)
    d.rounded_rectangle((10, 10, 850, 510), 40, outline=c, width=14)
    d.rounded_rectangle((38, 38, 822, 482), 26, outline=c, width=5)
    for txt_, font, size, y in [("REGISTRO SANITARIO", F_XB, 46, 70), ("APROBADO", F_BLK, 124, 150), ("INVIMA", F_BLK, 96, 336)]:
        f = ImageFont.truetype(font, size); w = d.textlength(txt_, font=f); d.text(((860 - w) / 2, y), txt_, font=f, fill=c)
    d.line((120, 318, 740, 318), fill=c, width=5)
    noise = rng.random((520, 860))
    a = np.asarray(s.getchannel("A")).astype(float) * np.where(noise > .12, 1, .25) * (0.82 + .18 * rng.random((520, 860)))
    s.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(.6))); return s.rotate(-8, Image.BICUBIC, expand=True)
STAMP = make_stamp()

def fit_h(im, h): return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
MC = Image.open(os.path.join(ASSETS, "logo_mercados_campesinos.png")).convert("RGBA")
SDE = fit_h(Image.open(os.path.join(ASSETS, "logo_sde.png")).convert("RGBA"), 52)
BOG = fit_h(Image.open(os.path.join(ASSETS, "logo_bogota.png")).convert("RGBA"), 96)
def pillbg(img, bg, pad=(22, 12), r=22):
    out = Image.new("RGBA", (img.width + 2 * pad[0], img.height + 2 * pad[1]), (0, 0, 0, 0))
    ImageDraw.Draw(out).rounded_rectangle((0, 0, out.width - 1, out.height - 1), r, fill=bg); out.alpha_composite(img, pad); return out
MC_P = pillbg(fit_h(MC, 76), (29, 107, 58))
def mini_seal(s=120):
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.ellipse((0, 0, s - 1, s - 1), fill=GREEN); d.ellipse((8, 8, s - 9, s - 9), outline=GOLD, width=3)
    for t_, f_, sz, y in [("REGISTRO", F_XB, 13, 30), ("INVIMA", F_BLK, 26, 47), ("SANITARIO", F_XB, 13, 80)]:
        f = ImageFont.truetype(f_, sz); w = d.textlength(t_, font=f); d.text(((s - w) / 2, y), t_, font=f, fill=WHT if t_ != "INVIMA" else GOLD)
    return img
SEAL = mini_seal()

# ---------- escenas ----------
def sc_intro(t):
    cv = PAPER_BG.copy()
    duo = framed(view(IM["duo"], 1.15, .5, .33, 620, 620), "circle", 620, 620)
    reveal(cv, duo, 230, 300, (t - .1) / .7, "circle")
    d = ImageDraw.Draw(cv); k = eo((t - .3) / .8)
    if k > 0: d.arc((210, 280, 870, 940), -90, -90 + 360 * k, fill=GOLD, width=6)
    if t > b(1.4): put(cv, LOGO_S, 820, 880, back((t - b(1.4)) / .5), 1)
    appear(cv, txt("Tenemos una noticia", F_PF, 84, INK, align="center"), t, b(1.8), 540, 1080, 50, "c")
    appear(cv, txt("que nos llena el corazón", F_PFI, 72, TERRA, align="center"), t, b(2.6), 540, 1200, 50, "c")
    return cv

def sc_receta(t):
    cv = PAPER_BG.copy(); chapter(cv, t, "01", "LA RECETA")
    arch = framed(view(IM["duo"], 1.05 + .05 * eio(t / b(8)), .5, .35, 520, 900), "arch", 520, 900)
    reveal(cv, arch, 500, 380, (t - .2) / .8, "up")
    if t > b(2):
        circ = framed(view(V["feria"].frame(), 1.0, .5, .4, 400, 400), "circle", 400, 400)
        k = back((t - b(2)) / .5); put(cv, circ, 290, 1050, k, 1)
        ImageDraw.Draw(cv).ellipse((290 - 200 * k - 6, 1050 - 200 * k - 6, 290 + 200 * k + 6, 1050 + 200 * k + 6), outline=GOLD, width=5)
    appear(cv, txt("Todo empezó con", F_PFI, 60, INK2), t, b(3.4), 80, 1400)
    appear(cv, txt("la receta de la abuela", F_PF, 80, INK, maxw=920), t, b(4), 80, 1480)
    appear(cv, txt("y el sueño de su nieta.", F_PFI, 60, TERRA), t, b(5), 80, 1600)
    return cv

def sc_proceso(t):
    cv = PAPER_BG.copy(); chapter(cv, t, "02", "EL PROCESO")
    top = view(V["horno"].frame(), 1.0, .5, .5, 940, 640) if t < b(6) else view(IM["crudas"], 1.05 + .05 * eio((t - b(6)) / b(6)), .5, .55, 940, 640)
    reveal(cv, framed(top, "rect", 940, 640), 70, 330, (t - .2) / .6, "left")
    if b(6) <= t < b(6) + .3:  # destello de cambio
        cv.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(160 * (1 - (t - b(6)) / .3)))))
    a1 = framed(view(IM["llenando"], 1.2, .55, .35, 450, 620), "arch", 450, 620)
    a2 = framed(view(IM["lavado"], 1.25, .35, .45, 450, 620), "arch", 450, 620)
    reveal(cv, a1, 70, 1010, (t - b(2)) / .6, "up"); reveal(cv, a2, 560, 1010, (t - b(3)) / .6, "up")
    appear(cv, txt("Nuestra planta de producción:", F_PF, 60, INK, maxw=940), t, b(4.5), 70, 1680)
    appear(cv, txt("cuidado e higiene en cada paso.", F_PFI, 56, TERRA, maxw=940), t, b(5.5), 70, 1770)
    return cv

def sc_respaldo(t):
    cv = PAPER_BG.copy()
    bgp = view(IM["planta"], 1.1, .5, .55, W, H).convert("RGBA"); bgp.putalpha(38); cv.alpha_composite(bgp)
    chapter(cv, t, "03", "EL RESPALDO")
    ts = b(1.5); shake = (0, 0)
    if t > ts:
        k = (t - ts) / .18; sc = 1 + 1.6 * (1 - eo(k))
        if t - ts < .35: amp = 18 * (1 - (t - ts) / .35); shake = (int(amp * math.sin(t * 90)), int(amp * math.cos(t * 70)))
        put(cv, STAMP, 540, 780, sc * .98, eo(k * 1.5))
    appear(cv, txt("Registro sanitario INVIMA", F_PF, 74, GREEN, align="center"), t, b(3.6), 540, 1180, 40, "c")
    appear(cv, txt("para nuestros productos y nuestra planta de producción", F_MD, 42, INK, maxw=900, align="center", lh=1.25),
           t, b(4.4), 540, 1300, 40, "c")
    for i, (name, reg) in enumerate([("Torta de Cuajada", "RSA-6500-2026"), ("Almojábanas del Campo", "RSA-6561-2026")]):
        row = Image.new("RGBA", (900, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(row)
        d.rounded_rectangle((0, 0, 899, 99), 50, fill=WHT, outline=PAPER2, width=3)
        d.text((40, 26), name, font=ImageFont.truetype(F_PF, 40), fill=INK)
        f = ImageFont.truetype(F_XB, 34); w = d.textlength(reg, font=f)
        d.rounded_rectangle((870 - w - 40, 18, 880, 82), 32, fill=GREEN); d.text((870 - w - 20, 28), reg, font=f, fill=WHT)
        appear(cv, row, t, b(5.6 + .9 * i), 90, 1490 + 125 * i, 40)
    if shake != (0, 0):
        sh = Image.new("RGBA", (W, H), PAPER); sh.alpha_composite(cv, shake); cv = sh
    return cv

SABOR = [("spoon", "Suave por dentro", .5, .45), ("tortas", "Doradita por fuera", .5, .5), ("almo", "Recién horneadas", .45, .6)]
def sc_sabor(t):
    cv = PAPER_BG.copy(); chapter(cv, t, "04", "EL SABOR")
    dur = b(4); si = min(int(t / dur), 2); lt = t - si * dur
    k, word, cx, cy = SABOR[si]
    ph = framed(view(IM[k], 1.18 - .1 * eio(lt / dur), cx, cy, 940, 1250), "rect", 940, 1250)
    if si == 0: reveal(cv, ph, 70, 330, (t - .15) / .6, "up")
    else:
        pk, _, pcx, pcy = SABOR[si - 1]; prev = framed(view(IM[pk], 1.08, pcx, pcy, 940, 1250), "rect", 940, 1250)
        cv.alpha_composite(prev, (70, 330)); reveal(cv, ph, 70, 330, lt / .45, "left")
    appear(cv, txt(word, F_PFI, 92, INK, align="center"), t, si * dur + .25, 540, 1640, 40, "c")
    put(cv, LOGO_S, 960, 400, 1, 1, 8)
    return cv

def sc_final(t):
    cv = PAPER_BG.copy(); d = ImageDraw.Draw(cv)
    for i in range(26):  # destellos dorados suaves
        x = (i * 397) % W; y = (i * 733) % 1300 + 100; ph = (t * 2 + i) % 2.4
        if ph < .8:
            s = 14 * math.sin(math.pi * ph / .8)
            d.polygon([(x, y - s), (x + s * .25, y - s * .25), (x + s, y), (x + s * .25, y + s * .25), (x, y + s),
                       (x - s * .25, y + s * .25), (x - s, y), (x - s * .25, y - s * .25)], fill=GOLD)
    duo = framed(view(IM["duo"], 1.15, .5, .33, 520, 520), "circle", 520, 520)
    reveal(cv, duo, 280, 200, (t - .05) / .7, "circle")
    k = eo((t - .2) / .8)
    if k > 0: d.arc((262, 182, 818, 738), 90, 90 + 360 * k, fill=GOLD, width=6)
    if t > b(1): put(cv, LOGO_L, 800, 660, elastic((t - b(1)) / .8) * .62, 1, 8)
    appear(cv, txt("¡Gracias por celebrar", F_PF, 82, INK, align="center"), t, b(1.6), 540, 830, 50, "c")
    appear(cv, txt("este paso con nosotros!", F_PF, 82, INK, align="center"), t, b(2.2), 540, 930, 50, "c")
    appear(cv, txt("Esto apenas comienza.", F_PFI, 66, TERRA, align="center"), t, b(3.2), 540, 1060, 40, "c")
    # bloque de aliados
    if t > b(4.5):
        kk = eo((t - b(4.5)) / .6); y0 = int(1260 + (1 - kk) * 120)
        blk = Image.new("RGBA", (W - 120, 470), (0, 0, 0, 0)); bd = ImageDraw.Draw(blk)
        bd.rounded_rectangle((0, 0, W - 121, 469), 40, fill=WHT, outline=PAPER2, width=3)
        lab = txt("CALIDAD RESPALDADA", F_XB, 28, INK2, track=6); blk.alpha_composite(lab, ((W - 120 - lab.width) // 2, 30))
        bd.line((140, 84, W - 260, 84), fill=GOLD, width=2)
        row = [SEAL, MC_P, BOG]; gap = 40; tot = sum(r.width for r in row) + gap * 2; x = (W - 120 - tot) // 2
        for r in row: blk.alpha_composite(r, (x, 200 - r.height // 2)); x += r.width + gap
        blk.alpha_composite(SDE, ((W - 120 - SDE.width) // 2, 300))
        tg = txt("Baruj Shefa · Receta de la abuela", F_PFI, 40, TERRA); blk.alpha_composite(tg, ((W - 120 - tg.width) // 2, 385))
        blk.putalpha(blk.getchannel("A").point(lambda v: int(v * kk))); cv.alpha_composite(blk, (60, y0))
    return cv

def blinds(prev, cur, k, n=8):
    """Persianas horizontales."""
    out = prev.copy(); hh = H // n
    for i in range(n):
        kk = eio(clamp(k * 1.5 - i * .06)); y = i * hh; h = int(hh * kk)
        if h > 0: out.paste(cur.crop((0, y, W, y + h)), (0, y))
    return out
def slide_up(prev, cur, k):
    e = eio(k); out = Image.new("RGB", (W, H), PAPER)
    out.paste(prev, (0, int(-e * H * .3))); y = int(H * (1 - e)); out.paste(cur.crop((0, 0, W, H - y)), (0, y))
    if 0 < e < 1: ImageDraw.Draw(out).rectangle((0, y - 6, W, y), fill=GOLD)
    return out

SCENES = [(OFF + b(4), sc_intro, None), (b(8), sc_receta, "blinds"), (b(12), sc_proceso, "slide"),
          (b(10), sc_respaldo, "blinds"), (b(12), sc_sabor, "slide")]
SCENES.append((TOTAL - sum(s[0] for s in SCENES), sc_final, "blinds"))
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
TR = .45

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", JINGLE, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev, cur, last = None, 0, None
N = int(TOTAL * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(starts) if s <= t + 1e-6)
    if si != cur: last.save(os.path.join(SNAP, f"escena_{cur + 1}.png")); prev, cur = last, si
    _, fn, tr = SCENES[si]; lt = t - starts[si]
    fr = fn(lt).convert("RGB"); last = fr; out = fr
    if tr and lt < TR and prev is not None: out = blinds(prev, fr, lt / TR) if tr == "blinds" else slide_up(prev, fr, lt / TR)
    if fi < 6: out = Image.blend(Image.new("RGB", (W, H), PAPER), out, fi / 6)
    ff.stdin.write(out.tobytes())
    if fi % 150 == 0: print(f"{fi}/{N}", flush=True)
last.save(os.path.join(SNAP, f"escena_{cur + 1}.png"))
ff.stdin.close(); ff.wait()
print(f"DUR={TOTAL:.2f}")
