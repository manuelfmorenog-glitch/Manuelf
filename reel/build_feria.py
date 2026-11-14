#!/usr/bin/env python3
"""Reel invitación a Mercados Campesinos – Baruj Shefa (1080x1920).

Uso: python3 build_feria.py <carpeta_medios> <carpeta_fuentes> <carpeta_salida> [logo1.png logo2.png ...]
Los logos extra (p. ej. Invima, Hecho en Bogotá) se agregan a la franja de aliados del cierre.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MEDIA, FONTS, OUT = sys.argv[1:4]
EXTRA_LOGOS = sys.argv[4:]
os.makedirs(OUT, exist_ok=True)
W, H, FPS, XF = 1080, 1920, 30, 0.6

def m(p):
    return next(os.path.join(MEDIA, f) for f in os.listdir(MEDIA) if f.startswith(p))

FLYER, PACK, TRAY = m("d7a2769d"), m("c80dcfa2"), m("14c3690f")
OVEN, KITCHEN, CART = m("5efb0aea"), m("0b8446a6"), m("c47cb03b")
DUO, LOGO, CARTV = m("2adf6372"), m("777dda90"), m("8d34adfa")
F_IT = os.path.join(FONTS, "playfair-display-latin-400-italic.ttf")
F_BD = os.path.join(FONTS, "playfair-display-latin-700-normal.ttf")
F_SC = os.path.join(FONTS, "great-vibes-latin-400-normal.ttf")
CREAM, GOLD, BROWN, GREEN = (255, 246, 228), (240, 196, 120), (92, 46, 20), (24, 96, 52)

def run(cmd):
    subprocess.run(cmd, check=True)

def text_layer(lines, fnt, size, color, y_center, img=None, shadow=True):
    img = img or Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = ImageFont.truetype(fnt, size)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(lay), ImageDraw.Draw(sh)
    rows = lines.split("\n")
    lh = int(size * 1.28)
    y0 = y_center - lh * len(rows) // 2
    for i, r in enumerate(rows):
        x = (W - d.textlength(r, font=f)) / 2
        if shadow:
            sd.text((x + 3, y0 + i * lh + 4), r, font=f, fill=(30, 12, 0, 230))
        d.text((x, y0 + i * lh), r, font=f, fill=color)
    if shadow:
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(9)))
    return Image.alpha_composite(img, lay)

def gradient(path):
    img = Image.new("RGBA", (W, H))
    px = img.load()
    for y in range(H):
        a = int(210 * ((y - 1150) / (H - 1150)) ** 1.3) if y > 1150 else (int(110 * (1 - y / 260)) if y < 260 else 0)
        for x in range(W):
            px[x, y] = (40, 18, 4, a)
    img.save(path)

def fit_vertical(src, path, scale=1.12):
    """Recorta una foto a 9:16 con margen para el movimiento de cámara."""
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im = ImageOps.fit(im, (int(W * scale), int(H * scale)), Image.LANCZOS, centering=(0.5, 0.45))
    im.save(path, quality=95)

def poster_on_blur(src, path, box_w=1000, top=300):
    im = Image.open(src).convert("RGB")
    bg = ImageOps.fit(im, (W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.eval(bg, lambda v: int(v * 0.8))
    fg = im.resize((box_w, int(im.height * box_w / im.width)), Image.LANCZOS)
    bg.paste(fg, ((W - box_w) // 2, top))
    bg.save(path, quality=95)

def end_card(path):
    card = Image.new("RGBA", (W, H), (249, 226, 194, 255))
    d = ImageDraw.Draw(card)
    logo = Image.open(LOGO).convert("RGBA").resize((520, 520), Image.LANCZOS)
    card.alpha_composite(logo, ((W - 520) // 2, 120))
    card = text_layer("Te esperamos en", F_SC, 96, BROWN, 760, card, False)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((90, 850, 990, 960), 55, fill=GREEN)
    card = text_layer("Mercados Campesinos", F_BD, 66, CREAM, 902, card, False)
    card = text_layer("Domingo 15 de noviembre", F_BD, 64, BROWN, 1045, card, False)
    card = text_layer("10:00 a.m. a 5:00 p.m.", F_IT, 58, BROWN, 1130, card, False)
    card = text_layer("Centro Nacional de las Artes\nDelia Zapata", F_BD, 52, GREEN, 1255, card, False)
    card = text_layer("Calle 11 con Carrera 6 · Bogotá", F_IT, 44, BROWN, 1365, card, False)
    d = ImageDraw.Draw(card)
    d.line((340, 1430, 740, 1430), fill=GOLD, width=3)
    card = text_layer("@barujshefa  ·  WhatsApp 319 653 6874", F_IT, 38, BROWN, 1478, card, False)
    # Franja de aliados
    d = ImageDraw.Draw(card)
    d.rectangle((0, 1560, W, H), fill=(248, 243, 224, 255))
    card = text_layer("Con el apoyo de", F_IT, 34, BROWN, 1600, card, False)
    logos = [Image.open(os.path.join(OUT, "logo_bogota.png")).convert("RGBA")]
    logos += [Image.open(p).convert("RGBA") for p in EXTRA_LOGOS]
    hgt = 130
    logos = [l.resize((int(l.width * hgt / l.height), hgt), Image.LANCZOS) for l in logos]
    gap = 50
    total = sum(l.width for l in logos) + gap * (len(logos) - 1)
    if total > W - 80:  # reducir si no caben
        k = (W - 80) / total
        logos = [l.resize((int(l.width * k), int(l.height * k)), Image.LANCZOS) for l in logos]
        gap, total = int(gap * k), W - 80
    x = (W - total) // 2
    for l in logos:
        card.alpha_composite(l, (x, 1650 + (hgt - l.height) // 2))
        x += l.width + gap
    sde = Image.open(os.path.join(OUT, "logo_sde.png")).convert("RGBA")
    sde = sde.crop((180, 10, 900, 70))
    card.alpha_composite(sde, ((W - sde.width) // 2, 1815))
    card.convert("RGB").save(path, quality=95)

# --- preparar recursos ---
fl = Image.open(FLYER)
fl.crop((800, 25, 1060, 145)).save(f"{OUT}/logo_bogota.png")
fl.crop((0, 1272, 1080, 1350)).save(f"{OUT}/logo_sde.png")
gradient(f"{OUT}/grad.png")
poster_on_blur(FLYER, f"{OUT}/i_flyer.jpg", 1000, 260)
for name, src in [("pack", PACK), ("tray", TRAY), ("oven", OVEN), ("kitchen", KITCHEN), ("cart", CART)]:
    fit_vertical(src, f"{OUT}/i_{name}.jpg")
end_card(f"{OUT}/i_end.jpg")

# (tipo, fuente, inicio, duración, texto, y_texto)
SCENES = [
    ("still", f"{OUT}/i_flyer.jpg", 0, 4.0, "¡Este domingo\nnos vemos en la feria!", 1720),
    ("still", f"{OUT}/i_oven.jpg", 0, 4.0, "Desde muy temprano,\nel horno ya huele a casa…", 1560),
    ("still", f"{OUT}/i_kitchen.jpg", 0, 4.0, "Manos que llevan años\nde amor y tradición.", 1560),
    ("still", f"{OUT}/i_tray.jpg", 0, 3.8, "Recién horneadas,\ncomo las hacía la abuela.", 1560),
    ("still", f"{OUT}/i_pack.jpg", 0, 3.8, "Con todo el cuidado\nque tu familia merece.", 1560),
    ("still", f"{OUT}/i_cart.jpg", 0, 4.2, "Abuela y nieta,\njuntas en un mismo sueño.", 1560),
    ("land", CARTV, 0, 5.0, "Ven a abrazarnos\ny a probar la\nTorta de Cuajada.", 1560),
    ("end", f"{OUT}/i_end.jpg", 0, 7.0, None, 0),
]
GRADE = "eq=saturation=1.08:contrast=1.04,colorbalance=rs=.05:gs=.01:bs=-.06,vignette=PI/5"

def render(i, sc):
    kind, src, ss, dur, txt, ty = sc
    out, fr = f"{OUT}/f{i:02d}.mp4", int(dur * FPS)
    if kind == "land":
        inputs = ["-ss", str(ss), "-t", str(dur * 0.5 + .1), "-i", src]
        base = (f"[0:v]setpts=PTS/0.5,fps={FPS},scale=-2:2112,crop=1188:2112,"
                f"crop=1080:1920:'(iw-ow)/2+t*6':'(ih-oh)/2-t*8',{GRADE}")
    elif kind == "vert":
        inputs = ["-ss", str(ss), "-t", str(dur + .1), "-i", src]
        base = (f"[0:v]fps={FPS},scale=1188:2112:force_original_aspect_ratio=increase,"
                f"crop=1080:1920:'(iw-ow)/2+t*6':'(ih-oh)/2-t*8',{GRADE}")
    else:
        inputs = ["-i", src]
        zoom = "1.0+0.0006*on" if i % 2 == 0 else "1.06-0.0005*on"
        size = "1080x1920"
        base = (f"[0:v]scale=2160:-1,zoompan=z='{zoom}':d={fr}:s={size}:fps={FPS}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'")
        if kind == "still" and i > 0:
            base += f",{GRADE}"
    filt = base + ",format=yuv420p[v0];"
    extra, idx, last = [], 1, "v0"
    if kind != "end":
        extra += ["-i", f"{OUT}/grad.png"]
        filt += f"[v0][1:v]overlay[v1];"
        idx, last = 2, "v1"
        lay = text_layer(txt, F_IT, 74, CREAM, ty)
        lay.save(f"{OUT}/ft{i}.png")
        extra += ["-loop", "1", "-t", str(dur), "-i", f"{OUT}/ft{i}.png"]
        filt += (f"[{idx}:v]format=rgba,fade=in:st=0.4:d=0.8:alpha=1,"
                 f"fade=out:st={dur-0.55:.2f}:d=0.45:alpha=1[p];[{last}][p]overlay[v9];")
        last = "v9"
    filt += f"[{last}]trim=duration={dur},setpts=PTS-STARTPTS[out]"
    run(["ffmpeg", "-v", "error", "-y", *inputs, *extra, "-filter_complex", filt, "-map", "[out]",
         "-an", "-r", str(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "medium",
         "-pix_fmt", "yuv420p", out])
    return out, dur

clips = [render(i, s) for i, s in enumerate(SCENES)]
inp, chain, off, last = [], "", 0.0, "0:v"
for p, _ in clips:
    inp += ["-i", p]
for i in range(1, len(clips)):
    off += clips[i - 1][1] - XF
    chain += f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}];"
    last = f"x{i}"
total = sum(d for _, d in clips) - XF * (len(clips) - 1)
chain += f"[{last}]fade=in:d=0.5,fade=out:st={total-0.8}:d=0.8[v]"
run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", chain, "-map", "[v]",
     "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", f"{OUT}/video.mp4"])
print(f"TOTAL={total:.2f}")
