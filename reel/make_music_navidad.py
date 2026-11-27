#!/usr/bin/env python3
"""Pista navideña ORIGINAL con aire colombiano: campanas (glockenspiel), maracas,
guacharaca, bajo saltarín y acordes de guitarra. 128 BPM, Sol mayor.

Uso: python3 make_music_navidad.py <segundos> <salida.wav>
"""
import sys, wave
import numpy as np

DUR, OUT = float(sys.argv[1]), sys.argv[2]
SR, BPM = 44100, 128
B = 60 / BPM
N = int(SR * (DUR + 3)); L, R = np.zeros(N), np.zeros(N)
rng = np.random.default_rng(12)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(SR * d)) / SR
def put(s, t, g=1., pan=0.):
    i = int(t * SR); j = min(N, i + len(s))
    if 0 <= i < N: L[i:j] += s[:j - i] * g * (1 - pan); R[i:j] += s[:j - i] * g * (1 + pan)
def bell(m, d=1.4):
    t = tt(d); f = hz(m)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
            + .25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 12)) * np.exp(-t * 3.2)
def guitar(m, d=.35):
    t = tt(d); f = hz(m)
    return sum(a * np.sin(2 * np.pi * f * k * t) for k, a in [(1, 1), (2, .5), (3, .3), (4, .15)]) * np.exp(-t * 9)
def bass(m, d):
    t = tt(d); return (np.sin(2 * np.pi * hz(m) * t) + .3 * np.sin(4 * np.pi * hz(m) * t)) * np.exp(-t * 4) * np.minimum(1, t * 200)
def maraca():
    t = tt(.07); return np.diff(rng.standard_normal(len(t) + 1)) * np.sin(np.pi * t / .07) * .2
def guacharaca():
    t = tt(.12); n = np.diff(rng.standard_normal(len(t) + 1)); return n * (1 + np.sign(np.sin(2 * np.pi * 60 * t))) * .5 * np.exp(-t * 15) * .25
def kick():
    t = tt(.25); f = 55 + 80 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
def chime(d=2.0):
    t = tt(d); return sum(np.sin(2 * np.pi * hz(m) * t) * np.exp(-t * 2.5) for m in (91, 95, 98, 103)) * .25

CH = [[55, 59, 62], [60, 64, 67], [62, 66, 69], [55, 59, 62]]   # G C D G
CH2 = [[52, 55, 59], [60, 64, 67], [62, 66, 69], [55, 59, 62]]  # Em C D G
BS = [43, 48, 50, 43]
MEL = [[79, 81, 83, None, 83, 81, 79, None], [76, None, 79, 76, 72, None, None, None],
       [74, 76, 78, 81, 78, None, 74, None], [79, None, None, None, 83, 81, 79, None],
       [76, 79, 83, None, 81, 79, 76, None], [72, 76, 79, None, 76, None, 72, None],
       [74, None, 78, 81, 86, None, 81, None], [83, None, 79, None, 79, None, None, None]]
bar = 4 * B; nb = int(DUR / bar) + 1
put(chime(), 0.0, .5)
for i in range(nb):
    t0 = i * bar
    if t0 > DUR - 2.6: break
    k = i % 4; ch = (CH if (i // 4) % 2 == 0 else CH2)[k]; full = i >= 1
    for q in range(4):
        if full: put(kick(), t0 + q * B, .5)
        for s in range(4): put(maraca(), t0 + q * B + s * B / 4, .8 if s % 2 else .45, -.35)
        if full: put(guacharaca(), t0 + q * B + B / 2, .7, .3)
        for e in (0, .5):  # rasgueo
            for j, n in enumerate(ch): put(guitar(n + 12), t0 + q * B + e * B + j * .012, .08 if e else .1, -.1)
    if full:
        for e, off in enumerate([0, 1.5, 2, 3]): put(bass(BS[k] - 12 + (7 if e == 3 else 0), B * .9), t0 + off * B, .38)
    if i >= 1:
        for q, mn in enumerate(MEL[(i - 1) % 8]):
            if mn: put(bell(mn), t0 + q * B / 2, .2, .25)
tend = DUR - 2.4
put(chime(2.4), tend, .7); put(kick(), tend, .7)
for n in (55, 59, 62, 67): put(guitar(n + 12, 1.5), tend, .15)
put(bell(91, 2.4), tend, .25)
st = np.stack([L, R], 1)[:int(SR * DUR)]
fo = int(SR * 1.6); st[-fo:] *= np.linspace(1, 0, fo)[:, None]
st = np.tanh(st * 1.3); st /= np.abs(st).max() / .88
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok")
