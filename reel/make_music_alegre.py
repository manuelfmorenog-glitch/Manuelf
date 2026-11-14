#!/usr/bin/env python3
"""Pista original alegre, estilo tropical-pop, 128 BPM.

Uso: python3 make_music_alegre.py <segundos> <salida.wav>
"""
import sys, wave
import numpy as np

DUR, OUT = float(sys.argv[1]), sys.argv[2]
SR, BPM = 44100, 128
B = 60 / BPM
N = int(SR * (DUR + 2))
L, R = np.zeros(N), np.zeros(N)
rng = np.random.default_rng(3)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    L[i:j] += sig[:j - i] * gain * (1 - pan)
    R[i:j] += sig[:j - i] * gain * (1 + pan)

def tt(d): return np.arange(int(SR * d)) / SR

def kick():
    t = tt(.35); f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)

def clap():
    t = tt(.25); n = rng.standard_normal(len(t))
    env = np.exp(-t * 18) * (1 + .6 * np.exp(-((t - .012) ** 2) / 1e-5))
    return np.convolve(n, [1, -0.9], "same") * env * .5

def hat(open_=False):
    t = tt(.2 if open_ else .05); n = np.diff(rng.standard_normal(len(t) + 1))
    return n * np.exp(-t * (14 if open_ else 70)) * .25

def shaker():
    t = tt(.08); n = np.diff(rng.standard_normal(len(t) + 1))
    return n * np.sin(np.pi * t / .08) * .12

def pluck(m, d=.28):
    t = tt(d); f = hz(m)
    s = (np.sign(np.sin(2 * np.pi * f * t)) * .25 + np.sin(2 * np.pi * f * t)
         + .3 * np.sin(4 * np.pi * f * t))
    return s * np.exp(-t * 11) * (1 - np.exp(-t * 400))

def marimba(m, d=.5):
    t = tt(d); f = hz(m)
    return (np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 30)) * np.exp(-t * 7)

def bass(m, d):
    t = tt(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t * 200) * np.exp(-t * 3)

# Sol mayor: G - D - Em - C
CH = [[55, 59, 62, 67], [50, 54, 57, 62], [52, 55, 59, 64], [48, 52, 55, 60]]
BASS = [43, 38, 40, 36]
MEL = [[79, None, 79, 81, 83, None, 81, 79], [78, None, 74, None, 76, 78, 79, None],
       [76, None, 79, None, 83, 81, 79, 76], [74, 76, 79, None, 81, None, 79, None]]

bars = int(DUR / (4 * B)) + 1
for b in range(bars):
    t0 = b * 4 * B
    k = b % 4
    intro = b < 1
    end = t0 + 4 * B > DUR - 0.2
    for q in range(4):
        tq = t0 + q * B
        if not intro: put(kick(), tq, .9)
        if q in (1, 3) and not intro: put(clap(), tq, .55, .1)
        put(hat(True), tq + B / 2, .5, .3)
        for s16 in range(4): put(shaker(), tq + s16 * B / 4, .7 if s16 % 2 else .4, -.4)
        # acordes en contratiempo (estilo tropical)
        for nn in CH[k][1:]:
            put(pluck(nn + 12), tq + B / 2, .12, -.15)
    if not intro:
        for q, off in enumerate([0, 1.5, 2, 3, 3.5]):
            put(bass(BASS[k] + (12 if q == 3 else 0), B * .9), t0 + off * B, .5)
    if b >= 2:
        for q, mn in enumerate(MEL[k]):
            if mn: put(marimba(mn), t0 + q * B / 2, .28, .25)
    if end: break

# golpe final
tend = DUR - 1.4
put(kick(), tend, 1.2); put(clap(), tend, .8)
for nn in CH[0]: put(pluck(nn + 12, 1.2), tend, .25)

st = np.stack([L, R], 1)[:int(SR * DUR)]
st = np.tanh(st * 1.4)
fo = int(SR * 1.0); st[-fo:] *= np.linspace(1, 0, fo)[:, None]
st /= np.abs(st).max() / .9
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok")
