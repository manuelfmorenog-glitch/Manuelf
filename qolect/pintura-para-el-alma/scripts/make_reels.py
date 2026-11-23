"""Construye los reels (1080x1920) de Pintura para el Alma con ffmpeg.

Uso: python3 qolect/pintura-para-el-alma/scripts/make_reels.py [wordtimestamps_dir] [--sin-resumen]
El directorio opcional contiene los JSON de Whisper con --word_timestamps (para subtítulos).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import make_graphics as g  # noqa: E402

ROOT = g.ROOT
VID = ROOT / "raw" / "videos"
OUT = ROOT / "contenido" / "reels"
TMP = Path(tempfile.mkdtemp(prefix="reels-"))
W, H, FPS = 1080, 1920, 30
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]


def v(name):
    return str(VID / f"WhatsApp_Video_2026-11-21_at_{name}.mp4")


def run(cmd):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *cmd], check=True)


# ---------- capas de texto ----------
def text_overlay(path, kicker, title, y_end=1380, title_size=96, top=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = 80
    tf, kf = g.serif(title_size), g.sans(30, "SemiBold")
    th = g.block_height(d, title, tf, W - 2 * m - 60, 1.02)
    block = (50 if kicker else 0) + th
    y0 = 260 if top else y_end - block
    # banda oscura suave detrás del texto
    band = Image.new("RGBA", (W, block + 260), g.NAVY + (0,))
    bd = band.load()
    for yy in range(band.height):
        a = int(175 * (1 - abs(yy - band.height / 2) / (band.height / 2)) ** 0.6)
        for xx in range(W):
            bd[xx, yy] = g.NAVY + (a,)
    img.alpha_composite(band, (0, max(0, y0 - 130)))
    y = y0
    if kicker:
        d.text((m, y), kicker.upper(), font=kf, fill=g.GOLD)
        y += 50
    g.text_block(d, m, y, title, tf, g.WHITE, W - 2 * m - 60, 1.02)
    img.save(path)
    return path


def logo_overlay(path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g.paste_logo(img, 80, 150, 200)
    img.save(path)
    return path


LOGO_PNG = logo_overlay(TMP / "logo.png")


# ---------- segmentos ----------
def seg_video(out, src, start, dur, overlay=None, keep_audio=False, extra_vf=""):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
          + (f",{extra_vf}" if extra_vf else ""))
    inputs = ["-ss", str(start), "-t", str(dur), "-i", src, "-i", str(LOGO_PNG)]
    fc = f"[0:v]{vf}[b];[b][1:v]overlay=0:0[b2]"
    last = "b2"
    if overlay:
        inputs += ["-loop", "1", "-t", str(dur), "-i", str(overlay)]
        fc += f";[2:v]format=rgba,fade=in:st=0.2:d=0.35:alpha=1[t];[{last}][t]overlay=0:0[vo]"
        last = "vo"
    if keep_audio:
        fc += ";[0:a]loudnorm=I=-16:TP=-1.5,aresample=48000[ao]"
        amap = ["-map", "[ao]"]
    else:
        inputs += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo"]
        amap = ["-map", f"{3 if overlay else 2}:a"]
    run([*inputs, "-filter_complex", fc, "-map", f"[{last}]", *amap, "-t", str(dur), *ENC, str(out)])
    return out


def seg_photo(out, foto, dur, overlay=None, fy=0.5, zoom_in=True):
    frames = int(dur * FPS)
    src = TMP / f"{Path(foto).stem}_cover.jpg"
    g.cover(Image.open(g.FOTOS / foto).convert("RGB"), W * 2, H * 2, fy).save(src, quality=95)
    z = f"min(1+0.10*on/{frames},1.10)" if zoom_in else f"max(1.10-0.10*on/{frames},1)"
    zp = f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    inputs = ["-i", str(src), "-i", str(LOGO_PNG)]
    fc = f"[0:v]{zp},setsar=1[b];[b][1:v]overlay=0:0[b2]"
    last = "b2"
    if overlay:
        inputs += ["-loop", "1", "-t", str(dur), "-i", str(overlay)]
        fc += f";[2:v]format=rgba,fade=in:st=0.2:d=0.35:alpha=1[t];[{last}][t]overlay=0:0[vo]"
        last = "vo"
    inputs += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo"]
    run([*inputs, "-filter_complex", fc, "-map", f"[{last}]", "-map", f"{3 if overlay else 2}:a",
         "-frames:v", str(frames), "-t", str(dur), *ENC, str(out)])
    return out


def seg_endcard(out, dur=3.5):
    card = TMP / "endcard.jpg"
    g.text_slide("¿Te lo perdiste?", "Vuelve pronto.\nTe guardamos un lugar.",
                 ["Escríbenos y te avisamos primero de la próxima edición.", "Explora. Siente. Despierta."],
                 footer="WhatsApp 300 471 1065\nqolect.co", size=(W, H), title_size=110,
                 safe_top=160, safe_bottom=380).save(card, quality=95)
    frames = int(dur * FPS)
    run(["-loop", "1", "-t", str(dur), "-i", str(card), "-f", "lavfi", "-t", str(dur),
         "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
         f"[0:v]fps={FPS},format=yuv420p,fade=in:st=0:d=0.4[v]", "-map", "[v]", "-map", "1:a",
         "-frames:v", str(frames), *ENC, str(out)])
    return out


def concat(segs, out, ass=None):
    lst = TMP / f"{Path(out).stem}.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    joined = TMP / f"{Path(out).stem}_joined.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    if ass:
        fontsdir = "/usr/share/fonts/opentype/inter"
        run(["-i", str(joined), "-vf", f"ass={ass}:fontsdir={fontsdir}", "-c:a", "copy",
             *[a for a in ENC if a not in ("-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2")],
             "-movflags", "+faststart", str(out)])
    else:
        run(["-i", str(joined), "-c", "copy", "-movflags", "+faststart", str(out)])
    print("OK", out)


# ---------- subtítulos (ASS) ----------
FIXES = {"SIGO": "consigo", "ala.": "Alma.", "cuéntanos": "Cuéntanos", "Marcella,": "", "viste": "viviste", "pintura": "Pintura"}


def chunks_from_whisper(jpath, offset=0.0, question_segments=(0,), maxc=30, maxdur=2.8):
    data = json.loads(Path(jpath).read_text())
    words = []  # (start, end, text, style)
    for si, seg in enumerate(data["segments"]):
        style = "Q" if si in question_segments else "A"
        for wd in seg.get("words", []):
            word = FIXES.get(wd["word"].strip(), wd["word"].strip())
            if word:
                words.append((wd["start"], wd["end"], word, style))
    out, cur = [], []
    for i, w in enumerate(words):
        if cur and (w[3] != cur[-1][3]
                    or len(" ".join(x[2] for x in cur + [w])) > maxc
                    or w[1] - cur[0][0] > maxdur):
            out.append(cur)
            cur = []
        cur.append(w)
        txt = " ".join(x[2] for x in cur)
        if w[2][-1] in ".?!," and len(txt) >= 14:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    # unir trozos muy cortos con el anterior
    merged = []
    for c in out:
        t = " ".join(x[2] for x in c)
        if merged and len(t) <= 9 and merged[-1][-1][3] == c[0][3] \
                and len(" ".join(x[2] for x in merged[-1] + c)) <= 40:
            merged[-1] += c
        else:
            merged.append(c)
    res = []
    for c in merged:
        t = " ".join(x[2] for x in c).replace("con consigo", "consigo").replace("la... ", "").replace("tener darse", "darse")
        res.append((c[0][0] + offset, c[-1][1] + offset, t, c[0][3]))
    fixed = []
    for i, (a, b, t, s) in enumerate(res):
        if i + 1 < len(res) and res[i + 1][0] - b < 0.35:
            b = res[i + 1][0]
        fixed.append((a, b, t, s))
    return fixed


def ts(x):
    h, r = divmod(max(0, x), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(path, chunks):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: A,Inter SemiBold,70,&H00FFFFFF,&H00FFFFFF,&H002A170F,&H96000000,0,0,0,0,100,100,0,0,1,5,2,2,90,150,600,1
Style: Q,Inter Medium,56,&H0042C5F5,&H0042C5F5,&H002A170F,&H96000000,0,1,0,0,100,100,0,0,1,4,2,2,90,150,600,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ts(a)},{ts(b)},{s},,0,0,0,,{{\\fad(80,60)}}{t}" for a, b, t, s in chunks]
    Path(path).write_text(head + "\n".join(lines) + "\n")
    return path


def duration(src):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", src]).strip())


# ---------- reels ----------
def reel_resumen():
    t = lambda n, k, ti, **kw: text_overlay(TMP / f"r1_{n}.png", k, ti, **kw)  # noqa: E731
    segs = [
        seg_video(TMP / "r1_00.mp4", v("15.22.59"), 0, 4.6, keep_audio=True,
                  overlay=t("00", "", "Y esto fue lo que vivimos en Pintura para el Alma", title_size=80)),
        seg_video(TMP / "r1_01.mp4", v("15.20.05"), 0.3, 3.0, overlay=t("01", "Jardín Botánico de Bogotá", "Un domo en medio de la naturaleza")),
        seg_photo(TMP / "r1_02.mp4", "foto-10.jpg", 2.6, overlay=t("02", "Primero", "Respirar y conectar"), fy=0.55),
        seg_video(TMP / "r1_03.mp4", v("15.24.17"), 0.5, 3.0, overlay=t("03", "El proceso", "Cada color, una emoción")),
        seg_photo(TMP / "r1_04.mp4", "foto-14.jpg", 2.6, overlay=t("04", "", "Pintar con el alma"), fy=0.6, zoom_in=False),
        seg_photo(TMP / "r1_05.mp4", "foto-12.jpg", 2.4, overlay=t("05", "Sin experiencia", "Guiados paso a paso"), fy=0.5),
        seg_video(TMP / "r1_06.mp4", v("15.24.06"), 0.5, 3.0, overlay=t("06", "", "Sin prisa. Sin pantallas.")),
        seg_photo(TMP / "r1_07.mp4", "foto-11.jpg", 2.4, overlay=t("07", "", "Compartir la mesa"), fy=0.5, zoom_in=False),
        seg_photo(TMP / "r1_08.mp4", "foto-03.jpg", 2.2, overlay=t("08", "", "Cada lienzo,"), fy=0.45),
        seg_photo(TMP / "r1_09.mp4", "foto-01.jpg", 2.6, overlay=t("09", "", "una historia."), fy=0.45),
        seg_endcard(TMP / "r1_10.mp4"),
    ]
    concat(segs, OUT / "reel-1-asi-se-vivio.mp4")


def reel_testimonio(name, clips, hook_kicker, hook_title, wt_dir):
    segs, chunks, offset = [], [], 0.0
    hook = text_overlay(TMP / f"{name}_hook.png", hook_kicker, hook_title, top=True, title_size=92)
    for i, (clip, qsegs) in enumerate(clips):
        src = v(clip)
        dur = duration(src)
        segs.append(seg_video(TMP / f"{name}_{i}.mp4", src, 0, dur, keep_audio=True,
                              overlay=hook if i == 0 else None))
        jp = Path(wt_dir) / f"WhatsApp_Video_2026-11-21_at_{clip}.json"
        chunks += chunks_from_whisper(jp, offset, qsegs)
        offset += dur
    segs.append(seg_endcard(TMP / f"{name}_end.mp4"))
    ass = write_ass(TMP / f"{name}.ass", chunks)
    concat(segs, OUT / f"{name}.mp4", ass=ass)
    srt = OUT / f"{name}.srt"
    srt.write_text("".join(
        f"{k}\n{ts(a).replace('.', ',')}0 --> {ts(b).replace('.', ',')}0\n{t}\n\n"
        for k, (a, b, t, _) in enumerate(chunks, 1)))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    wt = args[0] if args else None
    if "--sin-resumen" not in sys.argv:
        reel_resumen()
    if wt:
        reel_testimonio("reel-2-testimonio-inversion-para-el-alma",
                        [("15.22.28", (0,)), ("15.22.51", (0,))],
                        "Testimonio", "«Llegó al fondo de mí»", wt)
        reel_testimonio("reel-3-reconectar-contigo",
                        [("15.21.54", (0, 1))],
                        "Pintura para el Alma", "¿Qué necesitas para reconectar contigo?", wt)
