#!/usr/bin/env python3
"""Construye el reel emocional de Baruj Shefa (1080x1920, 9:16).

Uso: python3 build_reel.py <carpeta_medios> <carpeta_fuentes> <carpeta_salida>
"""
import os, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFilter, ImageFont

MEDIA, FONTS, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
W, H, FPS = 1080, 1920, 30
XF = 0.6  # duración de cada fundido entre escenas

def m(prefix):
    return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(prefix))

CART, OVEN = m("8d34adfa"), m("501b5a86")
DUO, PROD, LOGO = m("2adf6372"), m("63b2af4a"), m("777dda90")
F_IT = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_BD = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")
CREAM, GOLD = (255, 246, 228), (240, 196, 120)

# (tipo, fuente, inicio, duración, velocidad, texto)
SCENES = [
    ("logo", LOGO, 0, 4.2, 1, "Hay historias que se hornean\ncon amor…"),
    ("land", CART, 0, 6.2, 0.5, "El Dios de la vida dispuso\nque tú y yo\nestuviésemos juntas…"),
    ("vert", DUO, 0.2, 4.6, 1, "…para acompañarnos\ny estar la una\npara la otra."),
    ("land", OVEN, 0, 6.2, 0.5, "Hoy, a través de este sueño,\npodemos decir:"),
    ("vert", PROD, 0, 3.0, 1, "somos\nemprendedoras."),
    ("vert", PROD, 3.0, 5.0, 1, "Llevando el sabor de la tradición\na muchos hogares."),
    ("vert", DUO, 11.0, 3.8, 1, "Quiero que sigas estudiando\ny creciendo…"),
    ("vert", DUO, 15.0, 4.7, 1, "…como una hermosa mujer\nque honra a Dios."),
    ("vert", PROD, 8.2, 2.7, 1, "Que desarrolles tus talentos…"),
    ("vert", DUO, 7.0, 3.6, 1, "…y los ofrezcas al mundo\ncomo servicio."),
    ("vert", DUO, 12.0, 2.6, 1, "Que la Torta de Cuajada\nsea reconocida…"),
    ("logo", LOGO, 0, 6.5, 1, "END"),
]

def font(p, s):
    return ImageFont.truetype(p, s)

def text_png(path, lines, fnt, size, color=CREAM, y_center=1560, glow=True):
    """Texto centrado con sombra suave, sobre un lienzo transparente."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = font(fnt, size)
    d = ImageDraw.Draw(img)
    rows = lines.split("\n")
    lh = int(size * 1.28)
    y0 = y_center - lh * len(rows) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for i, r in enumerate(rows):
        tw = d.textlength(r, font=f)
        x, y = (W - tw) / 2, y0 + i * lh
        sd.text((x + 3, y + 4), r, font=f, fill=(30, 12, 0, 230))
        d.text((x, y), r, font=f, fill=color)
    shadow = shadow.filter(ImageFilter.GaussianBlur(9 if glow else 4))
    Image.alpha_composite(shadow, img).save(path)

def gradient_png(path):
    """Degradado oscuro cálido abajo y arriba para que el texto se lea."""
    img = Image.new("RGBA", (W, H))
    px = img.load()
    for y in range(H):
        a = 0
        if y > 1150:
            a = int(205 * ((y - 1150) / (H - 1150)) ** 1.3)
        elif y < 260:
            a = int(110 * (1 - y / 260))
        for x in range(W):
            px[x, y] = (40, 18, 4, a)
    img.save(path)

gradient_png(f"{OUT}/grad.png")

def run(cmd):
    subprocess.run(cmd, check=True)

GRADE = "eq=saturation=1.08:contrast=1.04,colorbalance=rs=.05:gs=.01:bs=-.06:rh=.03:bh=-.03,vignette=PI/5"

def render(i, sc):
    kind, src, ss, dur, spd, txt = sc
    out = f"{OUT}/s{i:02d}.mp4"
    frames = int(dur * FPS)
    inputs, base = [], ""
    if kind == "logo":
        inputs = ["-loop", "1", "-t", str(dur), "-i", src]
        z = "1+0.0009*on" if i == 0 else "1.08-0.0006*on"
        base = (f"[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,gblur=sigma=40,eq=brightness=-0.06[bg];"
                f"[b]scale=2000:-1,zoompan=z='{z}':d={frames}:s=1000x1000:fps={FPS}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'[fg];"
                f"[bg][fg]overlay=(W-w)/2:{340 if i else 460}:shortest=1,format=yuv420p")
    else:
        inputs = ["-ss", str(ss), "-t", str(dur * spd + 0.1), "-i", src]
        if kind == "land":
            fit = "scale=-2:1920,crop=1080:1920"
        else:
            fit = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        # pequeño zoom lento para dar sensación cinematográfica
        base = (f"[0:v]setpts=PTS/{spd},fps={FPS},{fit},"
                f"scale=1188:2112,crop=1080:1920:'(iw-ow)/2+t*6':'(ih-oh)/2-t*8',{GRADE},format=yuv420p")
    filt = base + "[v0];"
    n = len(inputs) // 2 if kind == "logo" else 1
    idx = 1
    extra = ["-i", f"{OUT}/grad.png"]
    filt += f"[v0][{idx}:v]overlay[v1];"
    idx += 1
    last = "v1"
    pngs = []
    if txt == "END":
        text_png(f"{OUT}/t{i}a.png", "Baruj Shefa", F_SC, 150, GOLD, 1450)
        text_png(f"{OUT}/t{i}b.png", "…en el mundo entero.", F_IT, 64, CREAM, 220)
        text_png(f"{OUT}/t{i}c.png", "Bendición en abundancia", F_BD, 52, CREAM, 1610)
        text_png(f"{OUT}/t{i}d.png", "@barujshefa  ·  @tortadecuajada", F_IT, 42, GOLD, 1720, False)
        pngs = [(f"{OUT}/t{i}b.png", 0.2), (f"{OUT}/t{i}a.png", 1.4),
                (f"{OUT}/t{i}c.png", 2.4), (f"{OUT}/t{i}d.png", 3.2)]
    else:
        size = 80 if max(len(r) for r in txt.split("\n")) < 26 else 68
        if txt.startswith("somos"):
            text_png(f"{OUT}/t{i}.png", txt, F_BD, 104, GOLD, 1560)
        else:
            text_png(f"{OUT}/t{i}.png", txt, F_IT, size)
        pngs = [(f"{OUT}/t{i}.png", 0.45)]
    for p, t0 in pngs:
        extra += ["-loop", "1", "-t", str(dur), "-i", p]
        filt += (f"[{idx}:v]format=rgba,fade=in:st={t0}:d=0.9:alpha=1,"
                 f"fade=out:st={dur - 0.55}:d=0.45:alpha=1[p{idx}];"
                 f"[{last}][p{idx}]overlay=shortest=0[v{idx}];")
        last = f"v{idx}"
        idx += 1
    filt += f"[{last}]trim=duration={dur},setpts=PTS-STARTPTS[out]"
    run(["ffmpeg", "-v", "error", "-y", *inputs, *extra, "-filter_complex", filt,
         "-map", "[out]", "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
         "-crf", "17", "-pix_fmt", "yuv420p", out])
    return out, dur

clips = [render(i, s) for i, s in enumerate(SCENES)]

# Encadenar con fundidos suaves
inp, chain, off, last = [], "", 0.0, "0:v"
for i, (p, d) in enumerate(clips):
    inp += ["-i", p]
for i in range(1, len(clips)):
    off += clips[i - 1][1] - XF
    chain += f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}];"
    last = f"x{i}"
total = sum(d for _, d in clips) - XF * (len(clips) - 1)
chain += f"[{last}]fade=in:d=0.6,fade=out:st={total - 1.2}:d=1.2[v]"
run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", chain, "-map", "[v]",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", f"{OUT}/video.mp4"])
print(f"TOTAL={total:.2f}")
