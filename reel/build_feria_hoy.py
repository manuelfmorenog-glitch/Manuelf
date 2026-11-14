#!/usr/bin/env python3
"""Reel "¡HOY!" – Mercados Campesinos Usaquén – Baruj Shefa.

Estilo: naranja/crema, polaroids que caen, apertura circular (iris),
pantalla dividida, sello giratorio y cierre tipo cartel.

Uso: python3 build_feria_hoy.py <medios> <fuentes> <musica.wav> <final.mp4> [logos extra...]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, MUSIC, FINAL = sys.argv[1:5]
EXTRA_LOGOS = sys.argv[5:]
W, H, FPS = 1080, 1920, 30
BPM = 112
BEAT = 60 / BPM

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))
FLYER = m("3afcc1dc")
PACK, TRAY, OVEN_P = m("c80dcfa2"), m("14c3690f"), m("5efb0aea")
KITCHEN, CART_P = m("0b8446a6"), m("c47cb03b")
OVEN_V, CART_V, PROD_V, LOGO = m("501b5a86"), m("8d34adfa"), m("63b2af4a"), m("777dda90")
F_FUN = os.path.join(FONTS, "luckiest-guy-latin-400-normal.ttf")
F_RND = os.path.join(FONTS, "fredoka-latin-700-normal.ttf")
F_RND6 = os.path.join(FONTS, "fredoka-latin-600-normal.ttf")
F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")

ORA, ORA2, YEL, CRM = (247, 127, 0), (255, 166, 43), (255, 214, 10), (255, 243, 222)
BRN, PNK, GRN, WHT, INK = (74, 36, 14), (232, 23, 110), (29, 107, 58), (255, 255, 255), (40, 20, 8)

# ---------- easing ----------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back_out(x, s=2.2): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    return x if x in (0, 1) else 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1
def pulse(t): return math.exp(-((t / BEAT) % 1) * 7)
def b(n): return n * BEAT

# ---------- recursos ----------
def load(src): return ImageOps.exif_transpose(Image.open(src)).convert("RGB")
def fit(im, w, h, c=(.5, .5)): return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=c)

def vivid(im):
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.07 + 128 + np.array([9, 3, -7])
    l = a.mean(2, keepdims=True); a = l + (a - l) * 1.2
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

class Vid:
    def __init__(self, path, ss, speed, w, h, cy=.5):
        self.cy = cy
        self.a = (path, ss, speed, w, h); self.p = None; self.last = None
    def frame(self):
        path, ss, sp, w, h = self.a
        if not self.p:
            vf = (f"setpts=PTS/{sp},fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,"
                  f"crop={w}:{h}:(iw-ow)/2:(ih-oh)*{self.cy}")
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", path, "-vf", vf,
                                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        buf = self.p.stdout.read(w * h * 3)
        if len(buf) == w * h * 3: self.last = vivid(Image.frombuffer("RGB", (w, h), buf))
        return self.last
    def close(self):
        if self.p: self.p.kill()

_c = {}
def label(text, font, size, fg, bg=None, stroke=None, sw=7, pad=(34, 16), r=999, shadow=True, lh=1.0):
    k = (text, font, size, fg, bg, stroke, sw, r)
    if k in _c: return _c[k]
    f = ImageFont.truetype(font, size)
    rows = text.split("\n"); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    ws = [tmp.textlength(x, font=f) for x in rows]
    a, d_ = f.getmetrics(); L = int((a + d_) * lh)
    s = sw if stroke else 0
    tw, th = int(max(ws)) + 2 * s, L * len(rows) + 2 * s
    bw, bh = tw + 2 * pad[0], th + 2 * pad[1]
    img = Image.new("RGBA", (bw + 30, bh + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    if bg:
        rr = min(r, bh // 2)
        if shadow: d.rounded_rectangle((18, 22, 18 + bw, 22 + bh), rr, fill=(0, 0, 0, 90))
        d.rounded_rectangle((10, 10, 10 + bw, 10 + bh), rr, fill=bg)
    for i, x in enumerate(rows):
        px = 10 + pad[0] + s + (tw - 2 * s - ws[i]) / 2; py = 10 + pad[1] + s + i * L
        if shadow and not bg:
            d.text((px + 6, py + 8), x, font=f, fill=(0, 0, 0, 120), stroke_width=s, stroke_fill=(0, 0, 0, 120))
        d.text((px, py), x, font=f, fill=fg, stroke_width=s, stroke_fill=stroke)
    _c[k] = img; return img

def put(cv, img, cx, cy, sc=1., al=1., rot=0.):
    if sc < .02 or al < .02: return
    if abs(sc - 1) > 1e-3: img = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BILINEAR, expand=True)
    if al < 1:
        img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * al)))
    cv.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def enter(cv, img, t, t0, cx, cy, kind="pop", rot=0., t1=1e9):
    if t < t0 or t > t1: return
    k = (t - t0) / .38; sc, al, x, y = 1., 1., cx, cy
    if kind == "pop": sc = back_out(k, 2.6) if k < 1 else 1 + .035 * pulse(t)
    elif kind == "elastic": sc = elastic((t - t0) / .75)
    elif kind == "slam": sc = 1 + 2.2 * (1 - ease_out(k)); al = ease_out(k * 2)
    elif kind == "left": x = cx - (1 - ease_out(k)) * 1300
    elif kind == "right": x = cx + (1 - ease_out(k)) * 1300
    elif kind == "up": y = cy + (1 - back_out(k, 1.6)) * 500; al = ease_out(k * 2)
    elif kind == "drop": y = cy - (1 - back_out(k, 1.6)) * 900
    o = clamp((t - (t1 - .16)) / .16)
    if o: sc *= 1 - .5 * o; al *= 1 - o
    put(cv, img, x, y, sc, al, rot)

def rays_bg(c1, c2, n=18):
    big = Image.new("RGB", (2600, 2600), c1); d = ImageDraw.Draw(big)
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = a0 + math.pi / n
        d.polygon([(1300, 1300), (1300 + 2000 * math.cos(a0), 1300 + 2000 * math.sin(a0)),
                   (1300 + 2000 * math.cos(a1), 1300 + 2000 * math.sin(a1))], fill=c2)
    return big
RAYS_O = rays_bg(ORA, ORA2)
RAYS_C = rays_bg(CRM, (255, 230, 196))
def rays(big, t, speed=8):
    r = big.rotate(t * speed, Image.BILINEAR)
    return r.crop((760, 340, 1840, 2260)).convert("RGBA")

def polaroid(photo, cap, w=760, h=860, c=(.5, .5)):
    p = fit(vivid(photo), w, h, c)
    card = Image.new("RGBA", (w + 60, h + 210), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((14, 20, w + 54, h + 206), fill=(0, 0, 0, 120))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(card); d.rectangle((0, 0, w + 40, h + 190), fill=(255, 253, 248))
    card.paste(p, (20, 20))
    f = ImageFont.truetype(F_SC, 92)
    d.text(((w + 40 - d.textlength(cap, font=f)) / 2, h + 50), cap, font=f, fill=BRN)
    return card

# ---------- escenas (funciones t_local -> RGBA) ----------
def scene_hoy(t):
    cv = rays(RAYS_O, t, 14)
    for i, ch in enumerate("HOY"):
        img = label(ch, F_FUN, 420, YEL if i != 1 else WHT, None, BRN, sw=14)
        enter(cv, img, t, b(.25 + .6 * i), 250 + 290 * i, 820 + (i == 1) * -30, "slam", [-8, 4, 10][i])
    enter(cv, label("¡", F_FUN, 300, WHT, None, BRN, 12), t, b(0.1), 95, 830, "pop", -10)
    enter(cv, label("!", F_FUN, 300, WHT, None, BRN, 12), t, b(1.9), 1000, 830, "pop", 10)
    enter(cv, label("SÁBADO 14 DE NOVIEMBRE", F_RND, 62, WHT, PNK), t, b(2.3), 540, 1160, "right", -3)
    enter(cv, label("¡Vamos a la feria!", F_RND, 76, BRN, YEL), t, b(3.0), 540, 1300, "up", 2)
    return cv

OVEN = None
def scene_oven(t):
    global OVEN
    if OVEN is None: OVEN = Vid(OVEN_V, .3, .5, 1188, 2112)
    f = OVEN.frame(); z = 1.1 - .08 * ease_io(t / b(4)) + .03 * pulse(t)
    im = f.resize((int(W * z), int(H * z)), Image.BILINEAR)
    cv = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H)).convert("RGBA")
    enter(cv, label("¡Ya salieron", F_RND, 110, WHT, None, BRN), t, b(.4), 540, 1340, "left")
    enter(cv, label("DEL HORNO!", F_FUN, 150, YEL, None, BRN, 10), t, b(1.2), 540, 1500, "slam", -3)
    return cv

POLS = None
def scene_polaroids(t):
    global POLS
    if POLS is None:
        POLS = [polaroid(load(TRAY), "recién horneada"), polaroid(load(OVEN_P), "doradita", c=(.5, .6)),
                polaroid(load(PACK), "lista para llevar", c=(.4, .6)), polaroid(load(KITCHEN), "hecha con amor", c=(.6, .4))]
    cv = rays(RAYS_C, t, 6)
    spots = [(500, 860, -9), (590, 930, 7), (480, 990, -4), (560, 1010, 5)]
    for i, p in enumerate(POLS):
        t0 = b(2 * i)
        if t < t0: break
        k = (t - t0) / .45
        x, y, r = spots[i]
        y_ = y - (1 - back_out(k, 1.4)) * 1500
        r_ = r + (1 - ease_out(k)) * 40 * (-1) ** i
        sc = (1.15 - .15 * ease_out(k)) * .98
        put(cv, p, x, y_, sc, 1, r_)
    enter(cv, label("TORTA DE CUAJADA", F_FUN, 92, WHT, ORA, pad=(40, 18)), t, b(.5), 540, 175, "drop", -2)
    return cv

SPLIT = None
TOPIMG = None
def scene_split(t):
    global SPLIT, TOPIMG
    if SPLIT is None:
        SPLIT = Vid(PROD_V, 8.2, 1, 1080, 960, .12)
        TOPIMG = fit(vivid(load(CART_P)), 1180, 1046, (.5, .35))
    cv = Image.new("RGBA", (W, H), CRM)
    k = ease_out(t / .4)
    z = 1 + .04 * pulse(t)
    top = TOPIMG.resize((int(1180 * z), int(1046 * z)), Image.BILINEAR)
    top = top.crop(((top.width - W) // 2, (top.height - 950) // 2, (top.width - W) // 2 + W, (top.height - 950) // 2 + 950))
    cv.paste(top, (int(-W * (1 - k)), 0))
    cv.paste(SPLIT.frame(), (int(W * (1 - k)), 960))
    d = ImageDraw.Draw(cv); d.rectangle((0, 942, W, 978), fill=YEL)
    enter(cv, label("Abuela y nieta", F_RND, 92, WHT, PNK, pad=(44, 16)), t, b(.6), 540, 880, "pop", -3)
    enter(cv, label("¡TE ESPERAN!", F_FUN, 110, YEL, None, BRN, 9), t, b(1.4), 540, 1060, "slam", 3)
    return cv

CARTV = None
def badge(t):
    s = 380; img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pts = [(s / 2 + (s / 2 - 4) * (1 if i % 2 == 0 else .88) * math.cos(math.pi * i / 16),
            s / 2 + (s / 2 - 4) * (1 if i % 2 == 0 else .88) * math.sin(math.pi * i / 16)) for i in range(32)]
    d.polygon(pts, fill=PNK); d.ellipse((40, 40, s - 40, s - 40), outline=WHT, width=6)
    img = img.rotate(t * 40, Image.BICUBIC)
    put(img, label("¡VEN\nHOY!", F_FUN, 96, WHT, None, None, shadow=False, lh=.9), s / 2, s / 2 + 6)
    return img
def scene_cart(t):
    global CARTV
    if CARTV is None: CARTV = Vid(CART_V, 0, .5, 1188, 2112)
    f = CARTV.frame(); z = 1.0 + .06 * ease_io(t / b(4)) + .03 * pulse(t)
    im = f.resize((int(W * z), int(H * z)), Image.BILINEAR)
    cv = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H)).convert("RGBA")
    enter(cv, badge(t), t, b(.3), 820, 330, "elastic")
    enter(cv, label("Llévate el sabor\nde la abuela", F_RND, 92, WHT, None, BRN), t, b(1), 540, 1500, "up")
    return cv

FLY = None
def scene_flyer(t):
    global FLY
    if FLY is None: FLY = polaroid(load(FLYER), "¡hoy en Usaquén!", 760, 950, (.5, .45))
    cv = rays(RAYS_O, t, -10)
    k = (t) / .5
    put(cv, FLY, 540, 1010 - (1 - back_out(k, 1.3)) * 1600, .95 + .02 * pulse(t), 1, 4 - 14 * (1 - ease_out(k)))
    enter(cv, label("MERCADOS CAMPESINOS", F_FUN, 84, WHT, GRN, pad=(40, 18)), t, b(1), 540, 190, "drop", -2)
    return cv

def pin_icon(s=150):
    img = Image.new("RGBA", (s, int(s * 1.35)), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.ellipse((0, 0, s, s), fill=PNK)
    d.polygon([(s * .14, s * .7), (s * .86, s * .7), (s / 2, s * 1.33)], fill=PNK)
    d.ellipse((s * .3, s * .3, s * .7, s * .7), fill=WHT)
    return img

END = {}
def end_init():
    logo = Image.open(LOGO).convert("RGBA").resize((400, 400), Image.LANCZOS)
    mk = Image.new("L", (400, 400), 0); ImageDraw.Draw(mk).ellipse((5, 5, 395, 395), fill=255)
    ring = Image.new("RGBA", (440, 440), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((0, 0, 439, 439), fill=WHT)
    ring.paste(logo, (20, 20), mk); END["logo"] = ring
    fl = Image.open(FLYER)
    strip = Image.new("RGBA", (W, 310), (255, 250, 238, 255)); sd = ImageDraw.Draw(strip)
    f = ImageFont.truetype(F_RND6, 32); tx = "Con el apoyo de"
    sd.text(((W - sd.textlength(tx, font=f)) / 2, 16), tx, font=f, fill=BRN)
    logos = [fl.crop((835, 20, 1100, 150)).convert("RGBA")] + [Image.open(p).convert("RGBA") for p in EXTRA_LOGOS]
    hh = 112; logos = [l.resize((int(l.width * hh / l.height), hh), Image.LANCZOS) for l in logos]
    gap = 46; tot = sum(l.width for l in logos) + gap * (len(logos) - 1)
    if tot > W - 80:
        k = (W - 80) / tot; logos = [l.resize((int(l.width * k), int(l.height * k))) for l in logos]
        gap = int(gap * k); tot = W - 80
    x = (W - tot) // 2
    for l in logos: strip.alpha_composite(l, (x, 66 + (hh - l.height) // 2)); x += l.width + gap
    sde = fl.crop((200, 1318, 920, 1378)).convert("RGBA")
    strip.alpha_composite(sde, ((W - sde.width) // 2, 212)); END["strip"] = strip
    rng = np.random.default_rng(5)
    END["dots"] = [(rng.uniform(0, W), rng.uniform(0, H - 320), rng.uniform(10, 30), rng.uniform(0, 6.28),
                    [YEL, WHT, PNK, ORA2][rng.integers(4)]) for _ in range(40)]

def scene_end(t):
    if not END: end_init()
    cv = rays(RAYS_O, t, 5); d = ImageDraw.Draw(cv)
    for x, y, r, ph, c in END["dots"]:
        rr = r * (.6 + .4 * math.sin(t * 3 + ph))
        d.ellipse((x - rr, y - rr + 20 * math.sin(t * 2 + ph), x + rr, y + rr + 20 * math.sin(t * 2 + ph)), fill=c)
    # tarjeta crema
    k = back_out(t / .5, 1.5)
    card = Image.new("RGBA", (960, 1170), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((8, 16, 952, 1166), 60, fill=(0, 0, 0, 80))
    cd.rounded_rectangle((0, 0, 944, 1150), 60, fill=CRM)
    put(cv, card, 540, 1010 + (1 - k) * 1800, 1, 1, 0)
    put(cv, END["logo"], 540, 330, elastic(t / .8) * (1 + .03 * pulse(t)), 1, -6 * math.sin(t * 2))
    T = [(.8, label("¡HOY!", F_FUN, 170, ORA, None, BRN, 10), 600, "slam", -3),
         (1.6, label("SÁBADO 14 DE NOVIEMBRE", F_RND, 58, WHT, PNK), 760, "left", 0),
         (2.3, label("7:00 a.m. a 4:00 p.m.", F_RND, 66, BRN, YEL), 870, "right", 0),
         (3.2, label("Parque Fundacional\nde Usaquén", F_RND, 80, GRN, None, None, shadow=False), 1050, "up", 0),
         (4.0, label("Carrera 6 con Calle 119", F_RND6, 52, BRN, None, None, shadow=False), 1200, "up", 0),
         (4.8, label("Mercados Campesinos · Baruj Shefa", F_RND6, 40, WHT, ORA), 1310, "pop", 0),
         (5.5, label("@barujshefa · WhatsApp 319 653 6874", F_RND6, 38, BRN, None, None, shadow=False), 1410, "up", 0)]
    for b0, img, cy, kind, rot in T: enter(cv, img, t, b(b0), 540, cy, kind, rot)
    enter(cv, pin_icon(84), t, b(3.0), 118, 1020, "drop", -8)
    ks = ease_out((t - b(6.2)) / .5)
    if ks > 0: cv.alpha_composite(END["strip"], (0, int(H - END["strip"].height * ks)))
    return cv

SCENES = [  # (beats, función, transición de entrada)
    (4, scene_hoy, None),
    (4, scene_oven, "iris"),
    (8, scene_polaroids, "push_up"),
    (4, scene_split, "flash"),
    (4, scene_cart, "iris"),
    (4, scene_flyer, "push_left"),
    (12, scene_end, "iris"),
]
starts, acc = [], 0
for s in SCENES: starts.append(acc); acc += s[0]
DUR = b(acc); TR = .32

def iris(prev, cur, k):
    r = int(ease_io(k) * 1150); mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse((540 - r, 960 - r, 540 + r, 960 + r), fill=255)
    out = prev.copy(); out.paste(cur, (0, 0), mask)
    if 0 < r < 1150:
        ImageDraw.Draw(out).ellipse((540 - r, 960 - r, 540 + r, 960 + r), outline=YEL, width=18)
    return out

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", MUSIC, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                       "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                       "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
prev_last, cur, last = None, 0, None
N = int(DUR * FPS)
for fi in range(N):
    t = fi / FPS
    si = max(i for i, s in enumerate(starts) if b(s) <= t + 1e-6)
    if si != cur: prev_last, cur = last, si
    beats, fn, tr = SCENES[si]
    lt = t - b(starts[si])
    fr = fn(lt).convert("RGB")
    last = fr; out = fr
    k = lt / TR
    if tr and k < 1 and prev_last is not None:
        if tr == "iris": out = iris(prev_last, fr, k)
        elif tr == "push_up":
            e = ease_out(k); out = Image.new("RGB", (W, H))
            out.paste(prev_last, (0, int(-e * H))); out.paste(fr, (0, int(H - e * H)))
        elif tr == "push_left":
            e = ease_out(k); out = Image.new("RGB", (W, H))
            out.paste(prev_last, (int(-e * W), 0)); out.paste(fr, (int(W - e * W), 0))
        elif tr == "flash":
            out = Image.blend(fr, Image.new("RGB", (W, H), WHT), 1 - ease_out(k))
    ff.stdin.write(out.tobytes())
    if fi % 90 == 0: print(f"{fi}/{N}", flush=True)
ff.stdin.close(); ff.wait()
for v in (OVEN, SPLIT, CARTV):
    if v: v.close()
print(f"DUR={DUR:.2f}")
