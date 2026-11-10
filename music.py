"""Ritmli fon musiqasi (sintez): lofi, house, pop. make(style, total, sr) -> mono massiv, cho'qqisi 1.0"""
import numpy as np


def _env_tone(freq, dur, decay, sr, harm=((1, 1.0),), attack=0.004):
    t = np.arange(int(dur * sr)) / sr
    s = sum(a * np.sin(2 * np.pi * freq * h * t) for h, a in harm)
    return s * np.exp(-t / decay) * np.minimum(t / attack, 1)


def rhodes(freq, dur, sr, decay=1.4):
    t = np.arange(int(dur * sr)) / sr
    idx = 1.6 * np.exp(-t / 0.35) + 0.25
    s = np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * t))
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    return s * trem * np.exp(-t / decay) * np.minimum(t / 0.006, 1)


def saw(freq, dur, decay, sr, nh=8):
    return _env_tone(freq, dur, decay, sr, harm=tuple((h, 1.0 / h) for h in range(1, nh + 1)))


def kick(sr, dur=0.3, f0=125, f1=46):
    t = np.arange(int(dur * sr)) / sr
    f = f1 + (f0 - f1) * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.11)


def _hp(x, k):
    return x - np.convolve(x, np.ones(k) / k, mode="same")


def _lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def hat(sr, rng, decay=0.018, dur=0.08):
    m = int(dur * sr)
    return _hp(rng.standard_normal(m), 4) * np.exp(-np.arange(m) / (decay * sr))


def snare(sr, rng, soft=False):
    m = int(0.2 * sr)
    t = np.arange(m) / sr
    nz = _lp(_hp(rng.standard_normal(m), 30), 6 if soft else 2) * np.exp(-t / 0.07)
    return nz / np.max(np.abs(nz)) * 0.8 + 0.5 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05)


def clap(sr, rng):
    m = int(0.22 * sr)
    out = np.zeros(m)
    for k, d in enumerate((0.0, 0.011, 0.023)):
        b = _lp(_hp(rng.standard_normal(int(0.16 * sr)), 14), 2) * np.exp(-np.arange(int(0.16 * sr)) / ((0.012 if k < 2 else 0.06) * sr))
        i0 = int(d * sr)
        out[i0: i0 + len(b)] += b[: m - i0]
    return out / np.max(np.abs(out))


N = {"A1": 55.0, "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.0, "A2": 110.0, "C3": 130.81, "D3": 146.83,
     "E3": 164.81, "F3": 174.61, "G3": 196.0, "A3": 220.0, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63,
     "F4": 349.23, "G4": 392.0, "A4": 440.0, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99}


def make(style, total, sr):
    rng = np.random.default_rng(11)
    out = np.zeros(int((total + 4) * sr))

    def add(sig, at, amp):
        i0 = int(at * sr)
        if 0 <= i0 < len(out):
            out[i0: i0 + len(sig)] += sig[: len(out) - i0] * amp

    if style == "lofi":
        beat, sw = 60 / 84, 0.09
        prog = [("D2", ["F3", "A3", "C4", "E4"]), ("G2", ["F3", "B3", "E4", "A4"]),
                ("C2", ["E3", "G3", "B3", "D4"]), ("A1", ["G3", "B3", "C4", "E4"])]
        for bar in range(int(total / (4 * beat)) + 1):
            t0 = bar * 4 * beat
            root, ch = prog[bar % 4]
            for j, nt in enumerate(ch):
                add(rhodes(N[nt], 3.0, sr, 1.5), t0 + j * 0.018, 0.2)
                add(rhodes(N[nt], 1.2, sr, 0.8), t0 + 2.5 * beat + j * 0.014, 0.11)
            for b, d, a in ((0, 0.6, 0.55), (1.5, 0.25, 0.4), (2.5, 0.5, 0.5)):
                add(_env_tone(N[root] * 2 if N[root] < 60 else N[root], d + 0.2, d, sr, harm=((1, 1), (2, 0.35))), t0 + b * beat, a)
            add(kick(sr), t0, 0.8), add(kick(sr), t0 + 2.5 * beat, 0.7)
            add(snare(sr, rng, soft=True), t0 + beat, 0.42), add(snare(sr, rng, soft=True), t0 + 3 * beat, 0.42)
            for e in range(8):
                add(hat(sr, rng), t0 + e * beat / 2 + (sw * beat if e % 2 else 0), 0.13 if e % 2 else 0.2)
        out[:] = _lp(out, 5)
        out += 0.004 * (rng.random(len(out)) < 0.0006) * rng.standard_normal(len(out)) * 40   # plastinka shitirlashi
    elif style == "house":
        beat = 60 / 118
        prog = [("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"]), ("C3", ["G3", "C4", "E4"]), ("G2", ["G3", "B3", "D4"])]
        for bar in range(int(total / (4 * beat)) + 1):
            t0 = bar * 4 * beat
            root, ch = prog[bar % 4]
            for b in range(4):
                add(kick(sr, f0=140), t0 + b * beat, 0.85)
                add(hat(sr, rng, 0.06, 0.2), t0 + (b + 0.5) * beat, 0.2)                     # ochiq hat
                add(saw(N[root], 0.22, 0.09, sr, 6), t0 + (b + 0.5) * beat, 0.38)             # offbit bas
                for q in (0.25, 0.75):
                    add(hat(sr, rng, 0.01, 0.04), t0 + (b + q) * beat, 0.08)
            add(clap(sr, rng), t0 + beat, 0.4), add(clap(sr, rng), t0 + 3 * beat, 0.4)
            for st in (0, 0.75, 1.5, 2.5, 3.25):                                              # sinkopli akkord
                for nt in ch:
                    add(saw(N[nt], 0.3, 0.1, sr, 5), t0 + st * beat, 0.11)
            for q in range(16):                                                               # yuqoridagi arpedjio
                nt = N[ch[(q * 2) % 3]] * 2
                add(_env_tone(nt, 0.18, 0.06, sr, harm=((1, 1), (3, 0.2))), t0 + q * beat / 4, 0.07 if q % 4 else 0.11)
        out[:] = _lp(out, 3)
    else:  # pop
        beat = 60 / 102
        prog = [("C3", ["E3", "G3", "C4", "E4"]), ("E2", ["G3", "B3", "D4", "E4"]),
                ("A2", ["G3", "C4", "E4", "A4"]), ("F2", ["A3", "C4", "E4", "F4"])]
        motif = [(0, 2), (0.5, 3), (1.0, 2), (1.5, 1), (2.5, 2), (3.0, 3), (3.5, 1)]
        for bar in range(int(total / (4 * beat)) + 1):
            t0 = bar * 4 * beat
            root, ch = prog[bar % 4]
            r = N[root]
            for j, nt in enumerate(ch):
                add(rhodes(N[nt], 2.0, sr, 1.0), t0 + j * 0.012, 0.15)
                add(rhodes(N[nt], 1.0, sr, 0.6), t0 + 2.5 * beat + j * 0.012, 0.1)
            for b, f, a in ((0, r, 0.5), (0.75, r, 0.38), (1.5, r * 2, 0.36), (2.5, r, 0.46), (3.5, r * 1.5, 0.36)):
                add(_env_tone(f, 0.32, 0.13, sr, harm=((1, 1), (2, 0.5), (3, 0.2))), t0 + b * beat, a)
            for b in (0, 1.5, 2):
                add(kick(sr), t0 + b * beat, 0.8)
            add(clap(sr, rng), t0 + beat, 0.38), add(clap(sr, rng), t0 + 3 * beat, 0.38)
            for e in range(8):
                add(hat(sr, rng), t0 + e * beat / 2, 0.11 if e % 2 else 0.17)
            if bar >= 1:
                for st, k in motif:                                                           # marimba kuyi
                    add(_env_tone(N[ch[k]] * 2, 0.5, 0.16, sr, harm=((1, 1), (4, 0.25))), t0 + st * beat, 0.2)
        out[:] = _lp(out, 3)
    out = out[: int(total * sr)]
    out = np.tanh(out / (np.max(np.abs(out)) * 0.6))        # yumshoq cheklagich
    return out / np.max(np.abs(out))
