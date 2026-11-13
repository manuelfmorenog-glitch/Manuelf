#!/usr/bin/env python3
"""Genera una pieza de piano suave y emotiva (original) para el reel.

Uso: python3 make_music.py <segundos> <salida.wav>
"""
import sys, wave
import numpy as np

DUR, OUT = float(sys.argv[1]), sys.argv[2]
SR = 44100
BPM = 68
beat = 60 / BPM
n = int(SR * (DUR + 4))
L = np.zeros(n); R = np.zeros(n)

def hz(m):
    return 440 * 2 ** ((m - 69) / 12)

def piano(freq, dur, vel):
    t = np.arange(int(SR * dur)) / SR
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 300))
    s = sum(a * np.sin(2 * np.pi * freq * k * t * (1 + 0.0004 * k)) * np.exp(-t * k * 0.6)
            for k, a in [(1, 1), (2, .45), (3, .2), (4, .1), (5, .05)])
    return s * env * vel

def pad(freq, dur, vel):
    t = np.arange(int(SR * dur)) / SR
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2)
    s = np.sin(2 * np.pi * freq * t) + .3 * np.sin(2 * np.pi * freq * 2.003 * t)
    return s * env * vel

def add(sig, at, pan=0.0):
    i = int(at * SR); j = min(n, i + len(sig))
    L[i:j] += sig[:j - i] * (1 - pan) / 2 * 2
    R[i:j] += sig[:j - i] * (1 + pan) / 2 * 2

# Progresión en Do mayor: C - G/B - Am - F  |  C - G - F - G  (cada acorde = 1 compás de 4 tiempos)
chords = [[48, 55, 60, 64], [47, 55, 59, 62], [45, 52, 57, 60], [41, 53, 57, 60],
          [48, 55, 60, 64], [43, 50, 55, 59], [41, 48, 57, 60], [43, 50, 55, 62]]
melody = [[76, None, 74, 72], [74, None, None, 71], [72, None, 76, 79], [77, None, 76, 72],
          [76, None, 79, 81], [79, None, 74, None], [72, 74, 76, None], [74, None, None, None]]
bar = 4 * beat
t, k = 0.0, 0
while t < DUR:
    c = chords[k % 8]
    intro = t < 2 * bar
    add(pad(hz(c[0] - 12), bar + 1.2, .05), t)
    for q in range(8):  # arpegio en corcheas
        note = c[[0, 1, 2, 3, 2, 1, 2, 3][q]]
        add(piano(hz(note), 3, .10 if q else .14), t + q * beat / 2, pan=-.3 + .1 * (q % 4))
    if not intro:
        for q, mn in enumerate(melody[k % 8]):
            if mn:
                add(piano(hz(mn), 3.5, .16), t + q * beat, pan=.25)
    t += bar; k += 1

# Reverb sencilla: convolución con ruido que decae
ir_t = np.arange(int(SR * 2.6)) / SR
rng = np.random.default_rng(7)
def verb(x, seed):
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.4)
    ir[:int(SR * .02)] = 0
    m = len(x) + len(ir)
    size = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
L = L + .025 * verb(L, 1); R = R + .025 * verb(R, 2)

st = np.stack([L, R], 1)[:int(SR * DUR)]
fade_out = int(SR * 3)
st[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
st[:int(SR * .5)] *= np.linspace(0, 1, int(SR * .5))[:, None]
st = st / np.abs(st).max() * 0.85
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", OUT)
