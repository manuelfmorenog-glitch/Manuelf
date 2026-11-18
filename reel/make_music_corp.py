#!/usr/bin/env python3
"""Pista original corporativa-inspiradora (piano + pulso + pad + bajo), 100 BPM, en crescendo.

Uso: python3 make_music_corp.py <segundos> <salida.wav>
"""
import sys, wave
import numpy as np

DUR, OUT = float(sys.argv[1]), sys.argv[2]
SR, BPM = 44100, 100
B = 60 / BPM
N = int(SR * (DUR + 3))
L, R = np.zeros(N), np.zeros(N)
rng = np.random.default_rng(5)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(SR * d)) / SR
def put(sig, t, g=1., pan=0.):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    L[i:j] += sig[:j - i] * g * (1 - pan); R[i:j] += sig[:j - i] * g * (1 + pan)
def piano(m, d=2.5):
    t = tt(d); f = hz(m)
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * k * .7) for k, a in [(1, 1), (2, .4), (3, .18), (4, .08)])
    return s * np.exp(-t * 2.4) * (1 - np.exp(-t * 300))
def pad(m, d):
    t = tt(d); env = np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.5)
    return (np.sin(2 * np.pi * hz(m) * t) + .5 * np.sin(2 * np.pi * hz(m) * 1.003 * t) + .3 * np.sin(2 * np.pi * hz(m + 12) * t)) * env
def kick():
    t = tt(.3); f = 48 + 90 * np.exp(-t * 28); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
def hat():
    t = tt(.06); return np.diff(rng.standard_normal(len(t) + 1)) * np.exp(-t * 60) * .18
def bass(m, d):
    t = tt(d); return (np.sin(2 * np.pi * hz(m) * t) + .2 * np.sin(4 * np.pi * hz(m) * t)) * np.minimum(1, t * 150) * np.exp(-t * 1.2)

# Re mayor: D - A/C# - Bm - G
CH = [[50, 57, 62, 66], [49, 57, 61, 64], [47, 54, 59, 62], [43, 55, 59, 62]]
MEL = [[74, None, 76, 78], [76, None, 73, None], [74, 76, 78, 81], [79, None, 78, None]]
bar = 4 * B; nb = int(DUR / bar) + 1
for i in range(nb):
    t0 = i * bar; c = CH[i % 4]; stage = 0 if i < 2 else 1 if i < 6 else 2
    put(pad(c[0], bar + 1.5), t0, .06 + .02 * stage)
    for q in range(8):
        n = c[[1, 2, 3, 2, 1, 2, 3, 2][q]] + 12
        put(piano(n, 2), t0 + q * B / 2, .07 if q % 2 else .1, -.2 + .1 * (q % 4))
    if stage >= 1:
        for q in range(4): put(kick(), t0 + q * B, .45 + .15 * (stage == 2))
        put(bass(c[0] - 12, bar * .95), t0, .35)
    if stage == 2:
        for q in range(8): put(hat(), t0 + q * B / 2 + B / 4, .8, .3)
        for q, mn in enumerate(MEL[i % 4]):
            if mn: put(piano(mn, 3), t0 + q * B, .14, .25)
# acorde final
tend = DUR - 3.5
for n in [50, 57, 62, 66, 74]: put(piano(n, 4), tend, .16)
put(pad(50, 4), tend, .1)

ir = rng.standard_normal(int(SR * 2.2)) * np.exp(-np.arange(int(SR * 2.2)) / SR * 2.6); ir[:800] = 0
def verb(x):
    size = 1 << (len(x) + len(ir) - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
L = L + .02 * verb(L); R = R + .02 * verb(R)
st = np.stack([L, R], 1)[:int(SR * DUR)]
fo = int(SR * 2.5); st[-fo:] *= np.linspace(1, 0, fo)[:, None]
st[:int(SR * .6)] *= np.linspace(0, 1, int(SR * .6))[:, None]
st = np.tanh(st * 1.2); st /= np.abs(st).max() / .88
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok")
