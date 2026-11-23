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


def dots(draw, w, y, n, i):
    if n <= 1:
        return
    gap, r = 26, 6
    x0 = w // 2 - (n - 1) * gap // 2
    for k in range(n):
        c = GOLD if k == i else (255, 255, 255, 110)
        draw.ellipse((x0 + k * gap - r, y - r, x0 + k * gap + r, y + r), fill=c)


def photo_slide(foto, kicker, title, body, size=(1080, 1350), fy=0.5, idx=0, total=1,
                title_size=92, swipe=False, safe_bottom=0):
    w, h = size
    img = cover(Image.open(FOTOS / foto).convert("RGB"), w, h, fy).convert("RGBA")
    img.alpha_composite(gradient(w, h, int(h * (0.38 if h < 1500 else 0.22)), max_alpha=235 if h < 1500 else 245))
    top = gradient(w, 320 if h < 1500 else 520, 0, max_alpha=170).transpose(Image.FLIP_TOP_BOTTOM)
    img.alpha_composite(top, (0, 0))
    d = ImageDraw.Draw(img)
    m = 80
    tf, bf, kf = serif(title_size), sans(36), sans(26, "SemiBold")
    total_h = (40 if kicker else 0) + block_height(d, title, tf, w - 2 * m, 1.0) + 20 \
        + (block_height(d, body, bf, w - 2 * m, 1.35) if body else 0)
    y = h - safe_bottom - 120 - total_h
    if kicker:
        d.text((m, y), kicker.upper(), font=kf, fill=GOLD)
        y += 40
    y = text_block(d, m, y, title, tf, WHITE, w - 2 * m, 1.0) + 20
    if body:
        text_block(d, m, y, body, bf, MUTED, w - 2 * m, 1.35)
    paste_logo(img, m, 70 if safe_bottom == 0 else 230, 210)
    if swipe:
        sf = sans(28, "Medium")
        t = "Desliza  →"
        d.text((w - m - d.textlength(t, font=sf), 92 if safe_bottom == 0 else 252), t, font=sf, fill=WHITE)
    dots(d, w, h - 60, total, idx)
    return img.convert("RGB")


def text_slide(kicker, title, lines, footer=None, size=(1080, 1350), idx=0, total=1,
               title_size=96, safe_top=0, safe_bottom=0):
    w, h = size
    img = Image.new("RGBA", size, NAVY + (255,))
    # degradado de marca diagonal suave
    g = Image.new("RGBA", size)
    gd = ImageDraw.Draw(g)
    for y in range(h):
        t = y / h
        c = tuple(int(NAVY[i] * (1 - t) + PETROL[i] * t) for i in range(3))
        gd.line([(0, y), (w, y)], fill=c + (255,))
    img.alpha_composite(g)
    d = ImageDraw.Draw(img)
    m = 90
    paste_logo(img, m, 80 + safe_top, 260)
    tf, lf, kf = serif(title_size), sans(38 if h < 1500 else 48), sans(26 if h < 1500 else 32, "SemiBold")
    y = 330 + safe_top
    if kicker:
        d.text((m, y), kicker.upper(), font=kf, fill=GOLD)
        y += 50
    y = text_block(d, m, y, title, tf, WHITE, w - 2 * m, 1.02) + 30
    d.line([(m, y), (m + 120, y)], fill=TEAL, width=5)
    y += 50
    for ln in lines:
        if ln.startswith("•"):
            d.ellipse((m, y + 16, m + 12, y + 28), fill=TEAL)
            y = text_block(d, m + 34, y, ln[1:].strip(), lf, WHITE, w - 2 * m - 34, 1.35) + 18
        elif ln.startswith("#"):  # cifra destacada
            num, _, rest = ln[1:].partition("|")
            nf = serif(120, "Bold")
            d.text((m, y), num, font=nf, fill=GOLD, features=["lnum"])
            y += 125
            y = text_block(d, m, y, rest, lf, MUTED, w - 2 * m, 1.35) + 30
        else:
            y = text_block(d, m, y, ln, lf, MUTED, w - 2 * m, 1.35) + 18
    if footer:
        ff = sans(32, "SemiBold")
        fy = h - 170 - safe_bottom - block_height(d, footer, ff, w - 2 * m, 1.4)
        text_block(d, m, fy, footer, ff, TEAL, w - 2 * m, 1.4)
    dots(d, w, h - 60, total, idx)
    return img.convert("RGB")


def save_set(name, slides):
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.jpg"):
        old.unlink()
    for i, s in enumerate(slides, 1):
        s.save(folder / f"{i:02d}.jpg", quality=92)
    print(name, len(slides))


CTA_FOOTER = "WhatsApp 300 471 1065\nqolect.co"


def main():

    # ---------- Carrusel 1: Así se vivió ----------
    c1 = [
        ("foto-05.jpg", 0.55, "Pintura para el Alma · Jardín Botánico", "Así se vivió",
         "Una tarde para pintar, respirar y reconectar."),
        ("foto-09.jpg", 0.6, "El lugar", "Un domo rodeado de naturaleza",
         "El Jardín Botánico de Bogotá fue nuestro refugio para bajar el ritmo."),
        ("foto-10.jpg", 0.55, "Primero, conectar", "Respirar antes de pintar",
         "Hicimos una pausa juntos para dejar la mente quieta."),
        ("foto-14.jpg", 0.6, "El proceso", "Pintar con el alma",
         "Cada color, guiado por el Mapa de la Consciencia."),
        ("foto-12.jpg", 0.5, "Sin experiencia, sin presión", "Acompañados en cada trazo",
         "Un guía nos llevó paso a paso de principio a fin."),
        ("foto-11.jpg", 0.5, "Compartir la mesa", "Almuerzo, postre y buena conversación", ""),
        ("foto-01.jpg", 0.45, "El final", "Cada lienzo, una historia",
         "Nos fuimos con una obra propia y el alma más liviana."),
    ]
    n1 = len(c1) + 1
    slides = [photo_slide(f, k, t, b, fy=fy, idx=i, total=n1, swipe=(i == 0),
                          title_size=110 if i == 0 else 88)
              for i, (f, fy, k, t, b) in enumerate(c1)]
    slides.append(text_slide("¿Te lo perdiste?", "Vuelve pronto.\nTe guardamos un lugar.",
                             ["Escríbenos y te avisamos primero de la próxima edición.",
                              "Explora. Siente. Despierta."],
                             footer=CTA_FOOTER, idx=n1 - 1, total=n1))
    save_set("carrusel-1-asi-se-vivio", slides)

    # ---------- Carrusel 2: Qué incluye ----------
    c2 = [
        ("foto-02.jpg", 0.5, "Experiencias Qolect", "¿Qué incluye Pintura para el Alma?", ""),
        ("foto-09.jpg", 0.6, "01", "Un lugar que inspira", "El domo del Jardín Botánico de Bogotá."),
        ("foto-07.jpg", 0.75, "02", "Tu kit de arte", "Lienzo numerado, pinturas, pinceles y la guía del Mapa de la Consciencia."),
        ("foto-10.jpg", 0.55, "03", "Guía y meditación", "Un facilitador te acompaña. No necesitas saber pintar."),
        ("foto-08.jpg", 0.5, "04", "Almuerzo y postre", "Comida, hidratación y torta de cuajada artesanal de Baruj Shefa."),
        ("foto-03.jpg", 0.45, "05", "Tu obra para llevar", "Te vas con tu lienzo y con una comunidad nueva."),
    ]
    n2 = len(c2) + 1
    slides = [photo_slide(f, k, t, b, fy=fy, idx=i, total=n2, swipe=(i == 0),
                          title_size=100 if i == 0 else 92)
              for i, (f, fy, k, t, b) in enumerate(c2)]
    slides.append(text_slide("Todo en un solo plan", "Desde $169.900",
                             ["• Precio cerrado, sin sorpresas", "• Cupos limitados",
                              "• Reserva en línea o con un asesor"],
                             footer=CTA_FOOTER, idx=n2 - 1, total=n2, title_size=120))
    save_set("carrusel-2-que-incluye", slides)

    # ---------- Carrusel 3: Empresas (B2B, también para LinkedIn) ----------
    n3 = 6
    slides = [
        photo_slide("foto-10.jpg", "Qolect Empresas", "¿Y si el bienestar de tu equipo se viviera así?", "",
                    fy=0.55, idx=0, total=n3, swipe=True, title_size=96),
        photo_slide("foto-14.jpg", "Bienestar real", "Una pausa que se siente",
                    "Arte y meditación para bajar el estrés y unir equipos, sin necesitar experiencia previa.",
                    fy=0.6, idx=1, total=n3),
        photo_slide("foto-11.jpg", "Nosotros ponemos todo", "Tú solo llegas",
                    "Lugar, materiales, guía, alimentación y logística completa.",
                    fy=0.5, idx=2, total=n3),
        text_slide("Ya confían en Qolect", "Un beneficio que tu equipo sí usa",
                   ["#+3.980|empleados con el beneficio Qolect activo",
                    "#10+|experiencias diseñadas y operadas por nosotros"],
                   footer="Convenios activos: Linde Praxair Colombia · Fonprax", idx=3, total=n3, title_size=80),
        photo_slide("foto-04.jpg", "Convenios a tu medida", "Grupos desde 10 personas",
                    "Cotización en 24 horas, portal con la marca de tu empresa y tarifas preferenciales.",
                    fy=0.45, idx=4, total=n3),
        text_slide("Hablemos", "Lleva esta experiencia a tu empresa",
                   ["• Team building y días de bienestar", "• Viajes de incentivo",
                    "• Convenios para fondos de empleados"],
                   footer="qolect.co/empresas\nreservas@qolect.co", idx=5, total=n3, title_size=90),
    ]
    save_set("carrusel-3-empresas", slides)

    # ---------- Historias ----------
    S = (1080, 1920)
    SAFE_T, SAFE_B = 160, 300
    stories = [
        photo_slide("foto-05.jpg", "Pintura para el Alma", "¡Gracias por vivirlo con nosotros!",
                    "Así se vio nuestra tarde en el Jardín Botánico.", size=S, fy=0.5,
                    title_size=100, safe_bottom=SAFE_B),
        photo_slide("foto-01.jpg", "Cuéntanos", "¿Qué te llevaste de esta tarde?",
                    "", size=S, fy=0.35, title_size=96, safe_bottom=SAFE_B + 120),
        photo_slide("foto-12.jpg", "Encuesta", "¿Repetirías la experiencia?",
                    "", size=S, fy=0.4, title_size=96,
                    safe_bottom=SAFE_B + 120),
        photo_slide("foto-08.jpg", "Detalles que importan", "Lo dulce también fue parte del plan",
                    "Torta de cuajada artesanal de Baruj Shefa.", size=S, fy=0.5,
                    title_size=92, safe_bottom=SAFE_B),
        photo_slide("foto-13.jpg", "Pintar con el alma", "Un momento para ti",
                    "Sin pantallas, sin prisa. Solo color y calma.", size=S, fy=0.5,
                    title_size=96, safe_bottom=SAFE_B),
        text_slide("Próxima edición", "¿Quieres vivirla?",
                   ["Toca el enlace y escríbenos por WhatsApp.", "Te avisamos primero."],
                   footer="qolect.co", size=S, title_size=120, safe_top=SAFE_T, safe_bottom=SAFE_B),
    ]
    save_set("historias", stories)


if __name__ == "__main__":
    main()
