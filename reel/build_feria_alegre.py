#!/usr/bin/env python3
"""Reel ENÉRGICO de invitación a Mercados Campesinos – Baruj Shefa.

Cortes al ritmo (128 BPM), textos animados con rebote, transiciones tipo
"whip" y "zoom punch", golpes de zoom en cada tiempo y cierre animado.

Uso: python3 build_feria_alegre.py <medios> <fuentes> <salida_dir> <musica.wav> <video_final.mp4> [logos extra...]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, OUT, MUSIC, FINAL = sys.argv[1:6]
EXTRA_LOGOS = sys.argv[6:]
os.makedirs(OUT, exist_ok=True)
W, H, FPS = 1080, 1920, 30
BPM = 128
BEAT = 60 / BPM
OW, OH = 1188, 2112  # fotograma fuente con margen para zoom

def m(p): return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))

FLYER, PACK, TRAY = m("d7a2769d"), m("c80dcfa2"), m("14c3690f")
OVEN_P, KITCHEN, CART_P = m("5efb0aea"), m("0b8446a6"), m("c47cb03b")
OVEN_V, CART_V, PROD_V, LOGO = m("501b5a86"), m("8d34adfa"), m("63b2af4a"), m("777dda90")

F_FUN = os.path.join(FONTS, "luckiest-guy-latin-400-normal.ttf")
F_RND = os.path.join(FONTS, "fredoka-latin-700-normal.ttf")
F_RND6 = os.path.join(FONTS, "fredoka-latin-600-normal.ttf")

YEL, ORA, GRN, PNK = (255, 210, 63), (244, 123, 32), (29, 107, 58), (230, 0, 126)
CRM, BRN, WHT = (255, 246, 228), (92, 46, 20), (255, 255, 255)

# ---------- utilidades de animación ----------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back_out(x, s=2.2):
    x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def elastic(x):
    x = clamp(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - .75) * (2 * math.pi / 3)) + 1

def beat_pulse(t):
    ph = (t / BEAT) % 1
    return math.exp(-ph * 7)

# ---------- fuentes de imagen ----------
def prep_photo(src, centering=(.5, .45)):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    return ImageOps.fit(im, (OW, OH), Image.LANCZOS, centering=centering)

def prep_poster(src):
    im = Image.open(src).convert("RGB")
    bg = ImageOps.fit(im, (OW, OH)).filter(ImageFilter.GaussianBlur(30))
    bg = Image.eval(bg, lambda v: int(v * .75))
    bw = 1080
    fg = im.resize((bw, int(im.height * bw / im.width)), Image.LANCZOS)
    bg.paste(fg, ((OW - bw) // 2, 330))
    return bg

class VideoSrc:
    def __init__(self, path, ss, speed, crop_x=.5):
        self.path, self.ss, self.speed, self.cx = path, ss, speed, crop_x
        self.p, self.last = None, None
    def frame(self):
        if self.p is None:
            vf = (f"setpts=PTS/{self.speed},fps={FPS},scale={OW}:{OH}:force_original_aspect_ratio=increase,"
                  f"crop={OW}:{OH}:(iw-ow)*{self.cx}:(ih-oh)/2")
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(self.ss), "-i", self.path,
                                       "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                      stdout=subprocess.PIPE)
        buf = self.p.stdout.read(OW * OH * 3)
        if len(buf) == OW * OH * 3:
            self.last = Image.frombuffer("RGB", (OW, OH), buf)
        return self.last
    def close(self):
        if self.p: self.p.kill()

def grade(im):
    """Look vivo y cálido."""
    a = np.asarray(im).astype(np.float32)
    a = (a - 128) * 1.08 + 128 + np.array([8, 3, -6])
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 1.22
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ---------- textos ----------
_cache = {}
def sticker(text, font, size, fg, bg=None, stroke=None, pad=(36, 18), radius=28, rot=0, shadow=True):
    key = (text, font, size, fg, bg, stroke, rot)
    if key in _cache: return _cache[key]
    f = ImageFont.truetype(font, size)
    rows = text.split("\n")
    sw = 8 if stroke else 0
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths = [tmp.textlength(r, font=f) for r in rows]
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.0)
    tw, th = int(max(widths)) + 2 * sw, lh * len(rows) + 2 * sw
    bw, bh = tw + 2 * pad[0], th + 2 * pad[1]
    img = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        if shadow:
            d.rounded_rectangle((26, 30, 26 + bw, 30 + bh), radius, fill=(0, 0, 0, 110))
        d.rounded_rectangle((20, 20, 20 + bw, 20 + bh), radius, fill=bg)
    for i, r in enumerate(rows):
        x = 20 + pad[0] + sw + (tw - 2 * sw - widths[i]) / 2
        y = 20 + pad[1] + sw + i * lh
        if shadow and not bg:
            d.text((x + 5, y + 7), r, font=f, fill=(0, 0, 0, 140), stroke_width=sw,
                   stroke_fill=(0, 0, 0, 140))
        d.text((x, y), r, font=f, fill=fg, stroke_width=sw, stroke_fill=stroke)
    if rot: img = img.rotate(rot, Image.BICUBIC, expand=True)
    _cache[key] = img
    return img

def place(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.01 or alpha <= 0.01: return
    if abs(scale - 1) > 1e-3 or rot:
        w, h = max(1, int(img.width * scale)), max(1, int(img.height * scale))
        img = img.resize((w, h), Image.BILINEAR)
        if rot: img = img.rotate(rot, Image.BILINEAR, expand=True)
    if alpha < 1:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy(); img.putalpha(a)
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

# Animaciones de entrada: pop, slide_l, slide_r, drop, rise
def anim(canvas, img, t, t0, t1, cx, cy, kind="pop", rot=0.0):
    if t < t0 or t > t1: return
    k = (t - t0) / 0.38
    out = clamp((t - (t1 - 0.18)) / 0.18)
    sc, a, x, y = 1.0, 1.0, cx, cy
    if kind == "pop":
        sc = back_out(k, 2.6) if k < 1 else 1 + .04 * beat_pulse(t)
    elif kind == "elastic":
        sc = elastic(min(1, (t - t0) / .7))
    elif kind == "slide_l":
        x = cx - (1 - ease_out(k)) * 1200
    elif kind == "slide_r":
        x = cx + (1 - ease_out(k)) * 1200
    elif kind == "drop":
        y = cy - (1 - back_out(k, 1.8)) * 900
    elif kind == "rise":
        y = cy + (1 - ease_out(k)) * 300; a = ease_out(k * 1.5)
    if out > 0:
        sc *= 1 - .6 * out; a *= 1 - out
    place(canvas, img, x, y, sc, a, rot)

# ---------- línea de tiempo ----------
def b(n): return n * BEAT

def poster_img(): return prep_poster(FLYER)

SHOTS = [  # (beats, fuente, zoom_ini, zoom_fin, transición de entrada)
    (4, ("video", OVEN_V, 0.3, .5, .5), 1.12, 1.0, "flash"),
    (4, ("img", poster_img), 1.0, 1.10, "zoom"),
    (2, ("img", lambda: prep_photo(TRAY)), 1.15, 1.0, "whip_l"),
    (2, ("img", lambda: prep_photo(OVEN_P, (.5, .6))), 1.0, 1.15, "zoom"),
    (2, ("video", PROD_V, 3.2, 1, .5), 1.05, 1.15, "whip_r"),
    (2, ("img", lambda: prep_photo(PACK, (.5, .6))), 1.15, 1.02, "zoom"),
    (4, ("img", lambda: prep_photo(KITCHEN, (.6, .4))), 1.0, 1.12, "whip_up"),
    (4, ("img", lambda: prep_photo(CART_P, (.5, .4))), 1.12, 1.0, "whip_l"),
    (4, ("video", PROD_V, 8.2, 1, .5), 1.0, 1.1, "zoom"),
    (4, ("video", CART_V, 0.0, .5, .5), 1.1, 1.0, "whip_r"),
    (14, ("end",), 1.0, 1.0, "zoom"),
]
starts, acc = [], 0
for s in SHOTS:
    starts.append(acc); acc += s[0]
TOTAL_BEATS = acc
DUR = b(TOTAL_BEATS)
END_T = b(starts[-1])

# Textos: (inicio_beat, fin_beat, sticker, cx, cy, animación, rot)
def T():
    S = []
    def add(b0, b1, img, cx, cy, kind="pop", rot=0): S.append((b(b0), b(b1), img, cx, cy, kind, rot))
    add(0.5, 4, sticker("¡ESTE", F_FUN, 150, YEL, None, BRN), 540, 760, "drop", -4)
    add(1.5, 4, sticker("DOMINGO!", F_FUN, 170, WHT, None, BRN), 540, 940, "pop", 3)
    add(2.5, 4, sticker("15 DE NOVIEMBRE", F_RND, 64, WHT, PNK, rot=-3), 540, 1130, "slide_r")
    add(4.3, 8, sticker("¡VAMOS A LA FERIA!", F_FUN, 92, YEL, GRN, rot=-3), 540, 230, "elastic")
    add(8.1, 10, sticker("¡RECIÉN\nHORNEADA!", F_FUN, 130, YEL, None, BRN), 540, 1450, "pop", -5)
    add(10.1, 12, sticker("DORADITA", F_FUN, 150, WHT, ORA, rot=4), 540, 1500, "slide_l")
    add(12.1, 14, sticker("CASERA", F_FUN, 160, YEL, None, BRN), 540, 1450, "drop", -3)
    add(14.1, 16, sticker("¡DELICIOSA!", F_FUN, 140, WHT, PNK, rot=-4), 540, 1500, "pop")
    add(16.2, 20, sticker("Receta de\nla abuela", F_RND, 110, WHT, None, BRN), 540, 1400, "rise")
    add(17.2, 20, sticker("HECHA CON AMOR", F_RND, 58, BRN, YEL, rot=3), 540, 1640, "slide_r")
    add(20.2, 24, sticker("Abuela y nieta", F_RND, 100, WHT, None, BRN), 540, 1420, "slide_l")
    add(21.2, 24, sticker("¡TE ESPERAN!", F_FUN, 120, YEL, GRN, rot=-3), 540, 1610, "pop")
    add(24.2, 28, sticker("¡VEN Y\nPRUÉBALA!", F_FUN, 150, YEL, None, BRN), 540, 1480, "elastic", -3)
    add(28.2, 32, sticker("¡Y LLÉVALA\nA CASA!", F_FUN, 130, WHT, ORA, rot=3), 540, 1480, "pop")
    return S
TEXTS = T()

# ---------- cierre animado ----------
def end_assets():
    bg = Image.new("RGB", (W, H), GRN)
    d = ImageDraw.Draw(bg)
    for y in range(-80, H + 120, 120):  # ondas como el afiche
        pts = [(x, y + 26 * math.sin(x / 70)) for x in range(0, W + 10, 10)]
        d.line(pts, fill=(36, 122, 68), width=34)
    logo = Image.open(LOGO).convert("RGBA").resize((470, 470), Image.LANCZOS)
    mask = Image.new("L", logo.size, 0)
    ImageDraw.Draw(mask).ellipse((6, 6, 464, 464), fill=255)
    ring = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, 499, 499), fill=YEL)
    ring.paste(logo, (15, 15), mask)
    fl = Image.open(FLYER)
    bogota = fl.crop((800, 25, 1060, 145)).convert("RGBA")
    sde = fl.crop((180, 1282, 900, 1342)).convert("RGBA")
    strip = Image.new("RGBA", (W, 330), (248, 243, 224, 255))
    sd = ImageDraw.Draw(strip)
    f = ImageFont.truetype(F_RND6, 34)
    t = "Con el apoyo de"
    sd.text(((W - sd.textlength(t, font=f)) / 2, 18), t, font=f, fill=BRN)
    logos = [bogota] + [Image.open(p).convert("RGBA") for p in EXTRA_LOGOS]
    hh = 120
    logos = [l.resize((int(l.width * hh / l.height), hh), Image.LANCZOS) for l in logos]
    gap = 50; tot = sum(l.width for l in logos) + gap * (len(logos) - 1)
    if tot > W - 80:
        k = (W - 80) / tot
        logos = [l.resize((int(l.width * k), int(l.height * k)), Image.LANCZOS) for l in logos]
        gap = int(gap * k); tot = W - 80
    x = (W - tot) // 2
    for l in logos:
        strip.alpha_composite(l, (x, 75 + (hh - l.height) // 2)); x += l.width + gap
    strip.alpha_composite(sde, ((W - sde.width) // 2, 225))
    return bg, ring, strip

END_BG, END_LOGO, END_STRIP = end_assets()
E_TXT = [  # (beat relativo, sticker, cy, anim, rot)
    (0.6, sticker("¡TE ESPERAMOS!", F_FUN, 116, YEL, None, BRN), 690, "elastic", -3),
    (1.6, sticker("MERCADOS CAMPESINOS", F_FUN, 76, GRN, YEL, rot=2), 830, "slide_l", 0),
    (2.6, sticker("DOMINGO 15 DE NOVIEMBRE", F_RND, 60, WHT, PNK), 960, "slide_r", 0),
    (3.4, sticker("10:00 a.m. a 5:00 p.m.", F_RND, 58, WHT, None, BRN), 1060, "pop", 0),
    (4.2, sticker("Centro Nacional de las Artes\nDelia Zapata", F_RND, 56, BRN, CRM, radius=34), 1225, "rise", 0),
    (5.0, sticker("Calle 11 con Carrera 6", F_RND6, 48, YEL, None, BRN), 1380, "pop", 0),
    (5.8, sticker("@barujshefa · 319 653 6874", F_RND6, 40, WHT, ORA), 1480, "pop", 0),
]
rng = np.random.default_rng(11)
CONF = [dict(x=rng.uniform(0, W), y=rng.uniform(-900, -50), vy=rng.uniform(320, 620),
             vx=rng.uniform(-60, 60), r=rng.uniform(0, 360), vr=rng.uniform(-300, 300),
             c=[YEL, ORA, PNK, WHT, (120, 200, 90)][rng.integers(5)], s=rng.uniform(14, 26))
        for _ in range(110)]

def draw_end(t_rel):
    zoom = 1 + .015 * beat_pulse(t_rel)
    bg = END_BG.resize((int(W * zoom), int(H * zoom)), Image.BILINEAR)
    cv = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W,
                  (bg.height - H) // 2 + H)).convert("RGBA")
    # logo con rebote y giro
    k = t_rel / .7
    sc = elastic(k) * (1 + .03 * beat_pulse(t_rel))
    place(cv, END_LOGO, 540, 330, sc * .92, 1, (1 - ease_out(k)) * -180 + 3 * math.sin(t_rel * 2))
    for b0, img, cy, kind, rot in E_TXT:
        anim(cv, img, t_rel, b(b0), 999, 540, cy, kind, rot)
    # franja de aliados
    ks = ease_out((t_rel - b(6.6)) / .5)
    if ks > 0:
        cv.alpha_composite(END_STRIP, (0, int(H - END_STRIP.height * ks)))
    # confeti
    if t_rel > b(0.6):
        d = ImageDraw.Draw(cv)
        tc = t_rel - b(0.6)
        for c in CONF:
            y = c["y"] + c["vy"] * tc
            if -40 < y < H - 300:
                x = c["x"] + c["vx"] * tc + 30 * math.sin(tc * 3 + c["r"])
                a = math.radians(c["r"] + c["vr"] * tc)
                s = c["s"]; dx, dy = math.cos(a) * s, math.sin(a) * s * .5
                d.polygon([(x - dx, y - dy), (x + dy, y - dx * .5), (x + dx, y + dy), (x - dy, y + dx * .5)],
                          fill=c["c"])
    return cv

# ---------- render ----------
def src_frame(shot_i, cache):
    s = SHOTS[shot_i][1]
    if s[0] == "img":
        if shot_i not in cache: cache[shot_i] = grade(s[1]())
        return cache[shot_i]
    if s[0] == "video":
        if shot_i not in cache: cache[shot_i] = VideoSrc(s[1], s[2], s[3], s[4])
        return grade(cache[shot_i].frame())
    return None

def framed(img, z):
    w, h = int(W * z), int(H * z)
    im = img.resize((max(w, W), max(h, H)), Image.BILINEAR)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", MUSIC,
                       "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                       "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)

cache, prev_frame = {}, None
TR = 0.24
nframes = int(DUR * FPS)
cur_shot, last_shot_frame = 0, None
for fi in range(nframes):
    t = fi / FPS
    si = max(i for i, st in enumerate(starts) if b(st) <= t + 1e-6)
    if si != cur_shot:
        prev_frame = last_shot_frame
        old = cache.get(cur_shot)
        if isinstance(old, VideoSrc): old.close()
        cur_shot = si
    beats, src, z0, z1, tr = SHOTS[si]
    t0 = b(starts[si]); dur = b(beats); lt = t - t0
    if src[0] == "end":
        frame = draw_end(lt).convert("RGB")
    else:
        img = src_frame(si, cache)
        z = z0 + (z1 - z0) * ease_in_out(lt / dur)
        z *= 1 + .035 * beat_pulse(t)  # golpe de zoom en cada tiempo
        frame = framed(img, z)
    base_frame = frame
    # transiciones
    k = lt / TR
    if k < 1 and prev_frame is not None:
        e = ease_out(k)
        if tr.startswith("whip"):
            cv = Image.new("RGB", (W, H))
            if tr == "whip_up":
                cv.paste(prev_frame, (0, int(-e * H))); cv.paste(frame, (0, int(H - e * H)))
            else:
                sgn = -1 if tr == "whip_l" else 1
                cv.paste(prev_frame, (int(sgn * e * W), 0)); cv.paste(frame, (int(sgn * (e * W - W)), 0))
            frame = cv.filter(ImageFilter.GaussianBlur(28 * (1 - abs(2 * k - 1))))
        elif tr == "zoom":
            zf = framed(frame, 1 + .5 * (1 - e))
            frame = Image.blend(zf, Image.new("RGB", (W, H), WHT), .55 * (1 - e))
        elif tr == "flash":
            frame = Image.blend(frame, Image.new("RGB", (W, H), WHT), 1 - e)
    elif si == 0 and lt < TR:
        frame = Image.blend(frame, Image.new("RGB", (W, H), WHT), 1 - ease_out(k))
    # textos
    cv = frame.convert("RGBA")
    if src[0] != "end":
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for (a0, a1, img, cx, cy, kind, rot) in TEXTS:
            anim(cv, img, t, a0, a1, cx, cy, kind, rot)
    last_shot_frame = base_frame
    ff.stdin.write(cv.convert("RGB").tobytes())
    if fi % 60 == 0: print(f"{fi}/{nframes}", flush=True)
ff.stdin.close(); ff.wait()
print(f"DUR={DUR:.2f}")
