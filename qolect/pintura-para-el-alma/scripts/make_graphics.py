"""Genera carruseles (1080x1350) e historias (1080x1920) de Pintura para el Alma.

Uso: python3 qolect/pintura-para-el-alma/scripts/make_graphics.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FOTOS = ROOT / "raw" / "fotos"
OUT = ROOT / "contenido"
BRAND = ROOT.parent / "brand"
LOGO = Image.open(BRAND / "logo-qolect.png").convert("RGBA")
SERIF = str(BRAND / "fonts" / "CormorantGaramond-Variable.ttf")
SANS = "/usr/share/fonts/opentype/inter/Inter-{}.otf"

NAVY = (15, 23, 42)
PETROL = (27, 58, 75)
TEAL = (46, 196, 182)
GOLD = (245, 197, 66)
WHITE = (255, 255, 255)
MUTED = (203, 213, 225)


def serif(size, weight="SemiBold"):
    f = ImageFont.truetype(SERIF, size)
    f.set_variation_by_name(weight)
    return f


def sans(size, weight="Regular"):
    return ImageFont.truetype(SANS.format(weight), size)


def cover(img, w, h, fy=0.5):
    """Recorta la imagen para llenar w x h; fy = punto focal vertical (0 arriba, 1 abajo)."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = int((img.height - h) * fy)
    return img.crop((x, y, x + w, y + h))


def gradient(w, h, start, color=NAVY, max_alpha=235):
    """Degradado vertical transparente -> color desde 'start' (px) hasta abajo."""
    g = Image.new("RGBA", (w, h), color + (0,))
    px = g.load()
    for y in range(start, h):
        a = int(max_alpha * min(1, ((y - start) / max(1, h - start)) ** 0.8 * 1.15))
        for x in range(w):
            px[x, y] = color + (a,)
    return g


def wrap(draw, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=font, features=feats(font)) <= maxw:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def feats(font):
    return ["lnum"] if str(getattr(font, "path", "")).endswith("Variable.ttf") else None


def text_block(draw, x, y, text, font, fill, maxw, spacing=1.15):
    for line in wrap(draw, text, font, maxw):
        draw.text((x, y), line, font=font, fill=fill, features=feats(font))
        y += int(font.size * spacing)
    return y


def block_height(draw, text, font, maxw, spacing=1.15):
    return len(wrap(draw, text, font, maxw)) * int(font.size * spacing)


def paste_logo(canvas, x, y, width):
    lg = LOGO.resize((width, round(LOGO.height * width / LOGO.width)), Image.LANCZOS)
    canvas.alpha_composite(lg, (x, y))


DISPLAY = "/usr/share/fonts/opentype/inter/InterDisplay-{}.otf"


def display(size, weight="ExtraBold"):
    return ImageFont.truetype(DISPLAY.format(weight), size)


def rich_lines(draw, text, font, maxw):
    """Divide en líneas; las palabras entre *asteriscos* se marcan como destacadas."""
    out, hl = [], False
    for para in text.split("\n"):
        line = []
        for raw in para.split():
            on = raw.startswith("*")
            closes = "*" in raw[1:] if on else "*" in raw
            word = raw.replace("*", "")
            mark = hl or on
            if closes:
                hl = False
            elif on:
                hl = True
            trial = " ".join(w for w, _ in line + [(word, mark)])
            if line and draw.textlength(trial, font=font) > maxw:
                out.append(line)
                line = []
            line.append((word, mark))
        out.append(line)
    return out


def rich_block(draw, x, y, text, font, maxw, color=WHITE, accent=GOLD, spacing=1.04, measure=False):
    lines = rich_lines(draw, text, font, maxw)
    if measure:
        return len(lines) * int(font.size * spacing)
    sp = draw.textlength(" ", font=font)
    for line in lines:
        xx = x
        for word, mark in line:
            draw.text((xx, y), word, font=font, fill=accent if mark else color)
            xx += draw.textlength(word, font=font) + sp
        y += int(font.size * spacing)
    return y


def pill(draw, x, y, text, font, bg=TEAL, fg=NAVY, padx=22, pady=12):
    tw = draw.textlength(text, font=font)
    asc, desc = font.getmetrics()
    h = asc + desc + 2 * pady
    draw.rounded_rectangle((x, y, x + tw + 2 * padx, y + h), radius=h // 2, fill=bg)
    draw.text((x + padx, y + pady), text, font=font, fill=fg)
    return y + h


def counter(draw, w, y, i, n, m=80):
    if n <= 1:
        return
    f = sans(26, "Medium")
    t = f"{i + 1:02d} / {n:02d}"
    draw.text((w - m - draw.textlength(t, font=f), y), t, font=f, fill=(255, 255, 255, 220))


def dots(draw, w, y, n, i):  # compatibilidad
    counter(draw, w, y - 20, i, n)


def photo_slide(foto, kicker, title, body, size=(1080, 1350), fy=0.5, idx=0, total=1,
                title_size=92, swipe=False, safe_bottom=0):
    w, h = size
    img = cover(Image.open(FOTOS / foto).convert("RGB"), w, h, fy).convert("RGBA")
    img.alpha_composite(gradient(w, h, int(h * (0.36 if h < 1500 else 0.22)), max_alpha=240))
    top = gradient(w, 300 if h < 1500 else 520, 0, max_alpha=150).transpose(Image.FLIP_TOP_BOTTOM)
    img.alpha_composite(top, (0, 0))
    d = ImageDraw.Draw(img)
    m = 80
    tf, bf, kf = display(title_size), sans(36), sans(24, "Bold")
    maxw = w - 2 * m
    kh = (kf.getmetrics()[0] + kf.getmetrics()[1] + 24 + 26) if kicker else 0
    total_h = kh + rich_block(d, 0, 0, title, tf, maxw, measure=True) \
        + ((22 + block_height(d, body, bf, maxw, 1.35)) if body else 0)
    y = h - safe_bottom - 110 - total_h
    if kicker:
        y = pill(d, m, y, kicker.upper(), kf) + 26
    y = rich_block(d, m, y, title, tf, maxw)
    if body:
        text_block(d, m, y + 22, body, bf, (226, 232, 240), maxw, 1.35)
    ty = 70 if safe_bottom == 0 else 230
    paste_logo(img, m, ty, 200)
    counter(d, w, ty + 14, idx, total, m)
    if swipe:
        sf = sans(28, "SemiBold")
        t = "Desliza →"
        d.text((w - m - d.textlength(t, font=sf), h - safe_bottom - 72), t, font=sf, fill=GOLD)
    return img.convert("RGB")


def text_slide(kicker, title, lines, footer=None, size=(1080, 1350), idx=0, total=1,
               title_size=96, safe_top=0, safe_bottom=0, button=None):
    w, h = size
    img = Image.new("RGBA", size, NAVY + (255,))
    g = Image.new("RGBA", size)
    gd = ImageDraw.Draw(g)
    for y in range(h):
        t = y / h
        c = tuple(int(NAVY[i] * (1 - t) + PETROL[i] * t) for i in range(3))
        gd.line([(0, y), (w, y)], fill=c + (255,))
    img.alpha_composite(g)
    # círculo decorativo de marca
    deco = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(deco).ellipse((w - 420, h - 620 - safe_bottom, w + 380, h + 180 - safe_bottom),
                                 outline=TEAL + (60,), width=3)
    img.alpha_composite(deco)
    d = ImageDraw.Draw(img)
    m = 90
    maxw = w - 2 * m
    paste_logo(img, m, 80 + safe_top, 250)
    counter(d, w, 96 + safe_top, idx, total, m)
    tf = display(title_size)
    lf = sans(38 if h < 1500 else 46)
    kf = sans(24 if h < 1500 else 30, "Bold")
    y = 300 + safe_top
    if kicker:
        y = pill(d, m, y, kicker.upper(), kf) + 34
    y = rich_block(d, m, y, title, tf, maxw) + 36
    for ln in lines:
        if ln.startswith("•"):
            d.rounded_rectangle((m, y + 14, m + 14, y + 28), radius=4, fill=GOLD)
            y = text_block(d, m + 36, y, ln[1:].strip(), lf, WHITE, maxw - 36, 1.35) + 18
        elif ln.startswith("#"):
            num, _, rest = ln[1:].partition("|")
            nf = display(130, "Black")
            d.text((m, y), num, font=nf, fill=GOLD)
            y += 140
            y = text_block(d, m, y, rest, lf, (203, 213, 225), maxw, 1.35) + 34
        else:
            y = text_block(d, m, y, ln, lf, (203, 213, 225), maxw, 1.35) + 18
    by = h - 150 - safe_bottom
    if footer:
        ff = sans(32 if h < 1500 else 38, "Medium")
        fh = block_height(d, footer, ff, maxw, 1.4)
        text_block(d, m, by - fh, footer, ff, (226, 232, 240), maxw, 1.4)
        by -= fh + 30
    if button:
        bf = sans(36 if h < 1500 else 44, "Bold")
        asc, desc = bf.getmetrics()
        bh = asc + desc + 44
        tw = d.textlength(button, font=bf)
        d.rounded_rectangle((m, by - bh, m + tw + 80, by), radius=bh // 2, fill=GOLD)
        d.text((m + 40, by - bh + 22), button, font=bf, fill=NAVY)
    return img.convert("RGB")


def save_set(name, slides):
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.jpg"):
        old.unlink()
    for i, s in enumerate(slides, 1):
        s.save(folder / f"{i:02d}.jpg", quality=92)
    print(name, len(slides))




def main():
    CTA = dict(button="Escríbenos por WhatsApp", footer="300 471 1065 · qolect.co")

    # ---------- Carrusel 1: Así se vivió ----------
    c1 = [
        ("foto-05.jpg", 0.55, "Jardín Botánico · Bogotá", "Así se vivió\n*Pintura para\nel Alma*",
         "Una tarde para pintar, respirar y reconectar."),
        ("foto-09.jpg", 0.6, "El lugar", "Un domo rodeado de *naturaleza*",
         "El Jardín Botánico fue nuestro refugio para bajar el ritmo."),
        ("foto-10.jpg", 0.55, "Primero", "*Respirar*\nantes de pintar",
         "Hicimos una pausa juntos para dejar la mente quieta."),
        ("foto-14.jpg", 0.6, "El proceso", "Pintar con el *alma*",
         "Cada color, guiado por el Mapa de la Consciencia."),
        ("foto-12.jpg", 0.5, "Sin experiencia", "Acompañados en *cada trazo*",
         "Un guía nos llevó paso a paso de principio a fin."),
        ("foto-11.jpg", 0.5, "Compartir", "Almuerzo, postre y *buena conversación*", ""),
        ("foto-01.jpg", 0.45, "El final", "Cada lienzo,\n*una historia*",
         "Nos fuimos con una obra propia y el alma más liviana."),
    ]
    n1 = len(c1) + 1
    slides = [photo_slide(f, k, t, b, fy=fy, idx=i, total=n1, swipe=(i == 0),
                          title_size=104 if i == 0 else 90)
              for i, (f, fy, k, t, b) in enumerate(c1)]
    slides.append(text_slide("¿Te lo perdiste?", "Vuelve pronto.\nTe guardamos\n*un lugar.*",
                             ["Escríbenos y te avisamos primero de la próxima edición.",
                              "Explora. Siente. Despierta."],
                             idx=n1 - 1, total=n1, title_size=100, **CTA))
    save_set("carrusel-1-asi-se-vivio", slides)

    # ---------- Carrusel 2: Qué incluye ----------
    c2 = [
        ("foto-02.jpg", 0.5, "Experiencias Qolect", "¿Qué incluye\n*Pintura para\nel Alma?*", ""),
        ("foto-09.jpg", 0.6, "01 · El lugar", "Un espacio\nque *inspira*", "El domo del Jardín Botánico de Bogotá."),
        ("foto-07.jpg", 0.75, "02 · Materiales", "Tu *kit de arte*", "Lienzo numerado, pinturas, pinceles y la guía del Mapa de la Consciencia."),
        ("foto-10.jpg", 0.55, "03 · Acompañamiento", "Guía y *meditación*", "Un facilitador te acompaña. No necesitas saber pintar."),
        ("foto-08.jpg", 0.5, "04 · Alimentación", "Almuerzo y *postre*", "Comida, hidratación y torta de cuajada artesanal de Baruj Shefa."),
        ("foto-03.jpg", 0.45, "05 · El recuerdo", "Tu obra *para llevar*", "Te vas con tu lienzo y con una comunidad nueva."),
    ]
    n2 = len(c2) + 1
    slides = [photo_slide(f, k, t, b, fy=fy, idx=i, total=n2, swipe=(i == 0),
                          title_size=100 if i == 0 else 96)
              for i, (f, fy, k, t, b) in enumerate(c2)]
    slides.append(text_slide("Próxima edición", "¿Quieres *vivirla?*",
                             ["Escríbenos y te avisamos primero de la próxima edición.",
                              "Explora. Siente. Despierta."],
                             idx=n2 - 1, total=n2, title_size=110, **CTA))
    save_set("carrusel-2-que-incluye", slides)

    # ---------- Carrusel 3: Empresas (B2B, también para LinkedIn) ----------
    n3 = 6
    slides = [
        photo_slide("foto-10.jpg", "Qolect Empresas", "¿Y si el bienestar\nde tu equipo se\n*viviera así?*", "",
                    fy=0.55, idx=0, total=n3, swipe=True, title_size=94),
        photo_slide("foto-14.jpg", "Bienestar real", "Una pausa\nque *se siente*",
                    "Arte y meditación para bajar el estrés y unir equipos, sin necesitar experiencia previa.",
                    fy=0.6, idx=1, total=n3),
        photo_slide("foto-11.jpg", "Nosotros ponemos todo", "Tú *solo llegas*",
                    "Lugar, materiales, guía, alimentación y logística completa.",
                    fy=0.5, idx=2, total=n3),
        text_slide("Ya confían en Qolect", "Un beneficio que tu equipo *sí usa*",
                   ["#+3.980|empleados con el beneficio Qolect activo",
                    "#10+|experiencias diseñadas y operadas por nosotros"],
                   footer="Convenios activos: Linde Praxair Colombia · Fonprax", idx=3, total=n3, title_size=78),
        photo_slide("foto-04.jpg", "Convenios a tu medida", "Grupos desde\n*10 personas*",
                    "Cotización en 24 horas, portal con la marca de tu empresa y tarifas preferenciales.",
                    fy=0.45, idx=4, total=n3),
        text_slide("Hablemos", "Lleva esta\nexperiencia a\n*tu empresa*",
                   ["• Team building y días de bienestar", "• Viajes de incentivo",
                    "• Convenios para fondos de empleados"],
                   button="Agenda una llamada", footer="qolect.co/empresas · reservas@qolect.co",
                   idx=5, total=n3, title_size=86),
    ]
    save_set("carrusel-3-empresas", slides)

    # ---------- Historias ----------
    S = (1080, 1920)
    SAFE_T, SAFE_B = 160, 300
    stories = [
        photo_slide("foto-05.jpg", "Pintura para el Alma", "¡Gracias por\nvivirlo *con\nnosotros!*",
                    "Así se vio nuestra tarde en el Jardín Botánico.", size=S, fy=0.5,
                    title_size=100, safe_bottom=SAFE_B),
        photo_slide("foto-01.jpg", "Cuéntanos", "¿Qué te llevaste de *esta tarde?*",
                    "", size=S, fy=0.35, title_size=100, safe_bottom=SAFE_B + 120),
        photo_slide("foto-12.jpg", "Encuesta", "¿Repetirías la *experiencia?*",
                    "", size=S, fy=0.4, title_size=100, safe_bottom=SAFE_B + 120),
        photo_slide("foto-08.jpg", "Detalles que importan", "Lo dulce también fue *parte del plan*",
                    "Torta de cuajada artesanal de Baruj Shefa.", size=S, fy=0.5,
                    title_size=96, safe_bottom=SAFE_B),
        photo_slide("foto-13.jpg", "Pintar con el alma", "Un momento\n*para ti*",
                    "Sin pantallas, sin prisa. Solo color y calma.", size=S, fy=0.5,
                    title_size=100, safe_bottom=SAFE_B),
        text_slide("Próxima edición", "¿Quieres *vivirla?*",
                   ["Toca el enlace y escríbenos por WhatsApp.", "Te avisamos primero."],
                   footer="qolect.co", size=S, title_size=130, safe_top=SAFE_T, safe_bottom=SAFE_B + 200),
    ]
    save_set("historias", stories)


if __name__ == "__main__":
    main()
