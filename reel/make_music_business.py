#!/usr/bin/env python3
"""Pista original estilo "business / pitch": 116 BPM, bombo constante, bajo en corcheas,
acordes cortos, subidas (risers) e impactos en los cambios de sección. Pensada para ir
debajo de una voz en off (deja espacio en medios).

Uso: python3 make_music_business.py <segundos> <salida.wav> [impactos_en_segundos,separados,por,coma]
"""
import sys, wave
import numpy as np

DUR, OUT = float(sys.argv[1]), sys.argv[2]
HITS = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[3] else []
SR, BPM = 44100, 116
B = 60 / BPM
N = int(SR * (DUR + 3)); L, R = np.zeros(N), np.zeros(N)
rng = np.random.default_rng(8)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(SR * d)) / SR
def put(s, t, g=1., pan=0.):
    i = int(t * SR); j = min(N, i + len(s))
    if 0 <= i < N: L[i:j] += s[:j - i] * g * (1 - pan); R[i:j] += s[:j - i] * g * (1 + pan)
def kick():
    t = tt(.32); f = 45 + 110 * np.exp(-t * 32); return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 9)
def snare():
    t = tt(.22); n = rng.standard_normal(len(t)); return (np.convolve(n, [1, -.8], "same") * .6 + np.sin(2 * np.pi * 190 * t) * .5) * np.exp(-t * 20)
def hat(o=False):
    t = tt(.15 if o else .04); return np.diff(rng.standard_normal(len(t) + 1)) * np.exp(-t * (18 if o else 80)) * .2
def bass(m, d):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * hz(m) * t)) * .35 + np.sin(2 * np.pi * hz(m) * t)
    return s * np.exp(-t * 6) * np.minimum(1, t * 300)
def stab(ch, d=.18):
    t = tt(d); s = sum(np.sin(2 * np.pi * hz(n) * t) + .4 * np.sin(2 * np.pi * hz(n) * 2.01 * t) for n in ch)
    return s * np.exp(-t * 14) * np.minimum(1, t * 400)
def riser(d=1.6):
    t = tt(d); n = rng.standard_normal(len(t)); n = np.convolve(n, np.ones(6) / 6, "same")
    return n * (t / d) ** 2 * .5 + np.sin(2 * np.pi * (200 + 900 * (t / d) ** 2) * t) * (t / d) ** 2 * .15
def impact():
    t = tt(1.4); f = 40 + 60 * np.exp(-t * 8)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3) + rng.standard_normal(len(t)) * np.exp(-t * 6) * .3

# La menor: Am - F - C - G
CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
BS = [45, 41, 48, 43]
bar = 4 * B; nb = int(DUR / bar) + 1
for i in range(nb):
    t0 = i * bar; k = i % 4; intro = i < 1; end = t0 > DUR - 2.5
    if end: break
    for q in range(4):
        put(kick(), t0 + q * B, .7)
        if q in (1, 3) and not intro: put(snare(), t0 + q * B, .35, .05)
        put(hat(True), t0 + q * B + B / 2, .55, .25)
        for s in range(2): put(hat(), t0 + q * B + s * B / 2 + B / 4, .5, -.25)
    for e in range(8): put(bass(BS[k], B / 2 * .9), t0 + e * B / 2, .42 if e % 2 == 0 else .3)
    if not intro:
        for e in [0, 1.5, 3, 3.5]: put(stab([n + 12 for n in CH[k]]), t0 + e * B, .09, .15)
for h in HITS:
    if h - 1.6 > 0: put(riser(), h - 1.6, .35)
    put(impact(), h, .55)
tend = DUR - 2.3
put(impact(), tend, .7); put(stab([n + 12 for n in CH[0]] + [69], 1.8), tend, .14)

st = np.stack([L, R], 1)[:int(SR * DUR)]
fo = int(SR * 1.8); st[-fo:] *= np.linspace(1, 0, fo)[:, None]
st = np.tanh(st * 1.3); st /= np.abs(st).max() / .85
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok")
