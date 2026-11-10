"""Dars videosi shabloni: oq fon, pastda o'qituvchi (7 poza), serif sarlavhalar, bepul inglizcha ovoz.
Ishlatish: python3 lesson.py lessons/dars-01.json [sheet] [--tts]
Natija: videos/dars-NN/ ichida dars-NN.mp4, cover.jpg, caption.txt"""
import json, math, os, shutil, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{ROOT}/config.json"))
W, H, FPS = 1080, 1920, 30
FD = f"{ROOT}/fonts/"
INK, CORAL, GREY, PAD, LIME = (16, 16, 20), (222, 96, 92), (120, 120, 128), (240, 214, 204), (214, 255, 92)
WHITE_BG = (252, 252, 252)
ORD = ["BIRINCHISI", "IKKINCHISI", "UCHINCHISI", "TO'RTINCHISI"]
LES = json.load(open(sys.argv[1]))
N = LES["lesson"]
OUT = f"{ROOT}/videos/dars-{N:02d}"
HANDLE, TEACHER, MUSIC = CFG["handle"], CFG["teacher"], CFG["music"]
os.makedirs(OUT, exist_ok=True)
items = LES["items"]
NI = len(items)


def sans(size, w="Bold"):
    return ImageFont.truetype(f"{FD}Poppins-{w}.ttf", size)


def serif(size, wght=600):
    f = ImageFont.truetype(f"{FD}Lora-Italic-Variable.ttf", size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def text_layer(txt, fnt, top, bot=None, squeeze=1.0, track=0):
    """Matn qatlami: vertikal gradient, gorizontal siqish (kondensat ko'rinish), harf oralig'i."""
    bot = bot or top
    wd = sum(fnt.getlength(c) for c in txt) + track * (len(txt) - 1) if track else fnt.getlength(txt)
    asc, desc = fnt.getmetrics()
    mask = Image.new("L", (int(wd) + 40, asc + desc + 30), 0)
    d = ImageDraw.Draw(mask)
    if track:
        x = 20
        for c in txt:
            d.text((x, 10), c, font=fnt, fill=255)
            x += fnt.getlength(c) + track
    else:
        d.text((20, 10), txt, font=fnt, fill=255)
    g = np.linspace(0, 1, mask.height)[:, None, None]
    col = (np.array(top) + (np.array(bot) - np.array(top)) * g).astype(np.uint8)
    im = Image.fromarray(np.repeat(col, mask.width, axis=1), "RGB").convert("RGBA")
    im.putalpha(mask)
    if squeeze != 1.0:
        im = im.resize((int(im.width * squeeze), im.height), Image.LANCZOS)
    return im


def fit_layer(txt, mk, size, maxw, **kw):
    lay = text_layer(txt, mk(size), **kw)
    while lay.width > maxw and size > 24:
        size -= 4
        lay = text_layer(txt, mk(size), **kw)
    return lay


def card_layer(inner, pad=(70, 50), minw=0, radius=64, fill=(255, 255, 255)):
    cw, ch = max(inner.width + pad[0] * 2, minw), inner.height + pad[1] * 2
    M = 60
    im = Image.new("RGBA", (cw + M * 2, ch + M * 2), (0,) * 4)
    sh = Image.new("RGBA", im.size, (0,) * 4)
    ImageDraw.Draw(sh).rounded_rectangle((M, M + 16, M + cw, M + ch + 16), radius=radius, fill=(0, 0, 0, 60))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    ImageDraw.Draw(im).rounded_rectangle((M, M, M + cw, M + ch), radius=radius, fill=fill, outline=(232, 232, 236), width=3)
    im.alpha_composite(inner, (M + (cw - inner.width) // 2, M + pad[1]))
    return im


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ================================================================ ovoz (v3 dagi ovozdan foydalanadi)
segs = [("hook", LES["hook_voice"], 0.95, 0.55)]
for i, it in enumerate(items):
    segs += [(f"slow{i}", it["en"] + ".", 0.75, 1.0), (f"norm{i}", it["en"] + ".", 0.9, 2.1)]
segs += [("example", LES["example"]["en"], 0.8, 1.9), ("turn", "Your turn!", 0.9, 0.9)]
for i, it in enumerate(items):
    segs.append((f"rep{i}", it["en"] + ".", 0.85, 2.7 if i < NI - 1 else 3.2))
if not os.path.exists(f"{OUT}/voice.wav") or "--tts" in sys.argv:
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{ROOT}/models/kokoro-v1.0.onnx", f"{ROOT}/models/voices-v1.0.bin")
    sr = 24000
    chunks, t, timing = [np.zeros(int(0.3 * sr), dtype=np.float32)], 0.3, []
    for sid, text, speed, gap in segs:
        s, sr = k.create(text, voice="af_heart", speed=speed, lang="en-us")
        s = np.asarray(s, dtype=np.float32)
        idx = np.where(np.abs(s) > 0.01)[0]
        s = s[max(0, idx[0] - 600): idx[-1] + 1800]
        s = s / np.max(np.abs(s)) * 0.8
        timing.append({"id": sid, "start": round(t, 3), "end": round(t + len(s) / sr, 3)})
        chunks += [s, np.zeros(int(gap * sr), dtype=np.float32)]
        t += len(s) / sr + gap
    v = np.concatenate(chunks)
    sf.write(f"{OUT}/voice.wav", v, sr)
    json.dump({"total": round(len(v) / sr, 3), "lines": timing}, open(f"{OUT}/timing.json", "w"), indent=1)

T = json.load(open(f"{OUT}/timing.json"))
L = {x["id"]: x for x in T["lines"]}
TV = T["total"]
TOTAL = TV + 1.8                       # oxirida chaqiriq (CTA) uchun qo'shimcha vaqt
voice, sr = sf.read(f"{OUT}/voice.wav")
voice = np.concatenate([voice, np.zeros(int(TOTAL * sr) - len(voice))])
n = int(TOTAL * FPS) + 1
env = np.array([np.sqrt(np.mean(voice[int(i / FPS * sr): int((i + 1) / FPS * sr)] ** 2) + 1e-9) for i in range(n)])
env = env / env.max()

# ---------------------------------------------------------------- sahnalar chegarasi
t_items = L["slow0"]["start"] - 0.3
t_black1 = t_items                 # boshidagi qora kadr olib tashlangan: kirishdan to'g'ri birinchi so'zga
t_ex = L["example"]["start"] - 0.4
t_black2 = L["turn"]["start"] - 0.35
REP = []
for i in range(NI):
    nxt = (L[f"rep{i + 1}"]["start"] - 0.25) if i < NI - 1 else TV - 0.9
    REP.append({"a": L[f"rep{i}"]["start"] - 0.15, "say0": L[f"rep{i}"]["end"] + 0.1, "say1": nxt - 0.45, "b": nxt})
t_rep = REP[0]["a"]
t_cta = REP[-1]["b"]
CUTS = [t_items] + [L[f"slow{i}"]["start"] - 0.3 for i in range(1, NI)] + [t_ex, t_black2, t_rep] + \
       [r["a"] for r in REP[1:]] + [t_cta]


# ================================================================ tovush: sokin fon, whoosh, yumshoq zarba
def tone(freq, dur, decay):
    t = np.arange(int(dur * sr)) / sr
    return np.sin(2 * np.pi * freq * t) * np.exp(-t / decay)


def music(total):
    out = np.zeros(int(total * sr) + 6 * sr)
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6],
              [196.0, 246.9, 293.7, 349.2]]
    bar = 3.4
    for b in range(int(total / bar) + 1):
        i0 = int(b * bar * sr)
        for j, fq in enumerate(chords[b % 4]):
            s_ = tone(fq, 4.2, 2.4) * np.minimum(np.arange(int(4.2 * sr)) / (0.7 * sr), 1)
            j0 = i0 + int(j * 0.09 * sr)
            out[j0: j0 + len(s_)] += s_ * 0.22
        s_ = tone(chords[b % 4][0] / 2, 2.8, 1.2) * np.minimum(np.arange(int(2.8 * sr)) / (0.05 * sr), 1)
        out[i0: i0 + len(s_)] += s_ * 0.4
    out = out[: int(total * sr)]
    return out / np.max(np.abs(out))


rng = np.random.default_rng(3)
sfx = np.zeros(len(voice))
for c in CUTS:                                               # whoosh: kadr almashganda
    m = int(0.32 * sr)
    nz = np.convolve(rng.standard_normal(m + 80), np.ones(60) / 60, mode="valid")[:m]
    e = np.sin(np.linspace(0, math.pi, m)) ** 2
    i0 = int(max(c - 0.2, 0) * sr)
    sfx[i0: i0 + m] += (nz / np.max(np.abs(nz)) * e * 0.10)[: len(sfx) - i0]
for h in [L[f"slow{i}"]["start"] - 0.2 for i in range(NI)] + [t_black2 + 0.05]:   # yumshoq zarba
    s_ = tone(64, 0.5, 0.12)
    i0 = int(h * sr)
    sfx[i0: i0 + len(s_)] += s_ * 0.22
sys.path.insert(0, ROOT)
from music import make as make_music
_e = np.convolve(np.abs(voice), np.ones(int(0.05 * sr)) / int(0.05 * sr), mode="same")
duck = 1 - 0.55 * np.clip(_e / _e.max() * 10, 0, 1)                    # ovoz chiqqanda musiqa pasayadi
duck = np.convolve(duck, np.ones(int(0.18 * sr)) / int(0.18 * sr), mode="same")
tt = np.arange(len(voice)) / sr
fade = np.minimum(1, np.minimum(tt / 0.4, (TOTAL - tt) / 1.5)).clip(0)
mus = make_music(MUSIC, TOTAL, sr)[: len(voice)] * duck * fade
mix = voice + 0.2 * mus + sfx * 0.8
sf.write(f"{OUT}/mix.wav", mix / np.max(np.abs(mix)) * 0.95, sr)

# ================================================================ o'qituvchi: 6 ta poza + yostiqcha
TS = 0.74
ALIGN = json.load(open(f"{ROOT}/assets/poses/align.json"))
POSE = {}
for nm, (top, cx, _) in ALIGN.items():
    im = Image.open(f"{ROOT}/assets/poses/{nm}_cut.png").convert("RGBA")
    im = im.resize((int(im.width * TS), int(im.height * TS)), Image.LANCZOS)
    # hamma pozada bosh bir joyda tursin: soch tepasi y=1070, bosh markazi x=540
    POSE[nm] = (im, int(540 - cx * TS), int(1000 - top * TS))
TCH = POSE["smile"][0]
PAD_BOX = (540 - 348, 1170, 540 + 348, 2100)


def pose_at(t):
    if t < t_black1:
        return "wave"
    for i in range(NI):
        a = L[f"slow{i}"]["start"] - 0.3
        b = (L[f"slow{i + 1}"]["start"] - 0.3) if i < NI - 1 else t_ex
        if a <= t < b:
            return "point" if t < L[f"norm{i}"]["end"] + 0.25 else "open"
    if t_ex <= t < t_black2:
        return "smile" if t < L["example"]["end"] + 0.3 else "open"
    for r in REP:
        if r["a"] <= t < r["b"]:
            return "point" if t < r["say0"] else ("open" if t < r["say1"] else "thumbs")
    if t >= t_cta:
        return "down" if t < TOTAL - 1.2 else "heart"
    return "smile"


POSE_CUTS = [0.0]
_p = None
for _i in range(int(TOTAL * FPS)):
    _q = pose_at(_i / FPS)
    if _q != _p and _i:
        POSE_CUTS.append(_i / FPS)
    _p = _q


def teacher(fr, t, show, pop):
    if show <= 0.01:
        return
    img0, x0, y0 = POSE[pose_at(t)]
    off = int((1 - ease(show)) * 900)
    bob = 5 * math.sin(t * 2 * math.pi / 4.0)
    px0, py0, px1, py1 = PAD_BOX
    ImageDraw.Draw(fr).rounded_rectangle((px0, py0 + off, px1, py1 + off), radius=150, fill=PAD)
    sc = 1 + 0.04 * math.sin(min(pop, 1) * math.pi) if pop < 1 else 1.0
    img = img0 if sc == 1.0 else img0.resize((int(img0.width * sc), int(img0.height * sc)), Image.BILINEAR)
    x = int(x0 - (img.width - img0.width) / 2)
    y = int(y0 + off + bob - (img.height - img0.height) * 0.6)
    # yostiqcha tepasidan yuqorida erkin, pastda faqat yostiqcha ichida
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((0, 0, img.width, py0 + off + 150 - y), fill=255)
    md.rounded_rectangle((px0 - x, py0 + off - y, px1 - x, py1 + off - y), radius=150, fill=255)
    side = Image.new("L", img.size, 0)
    ImageDraw.Draw(side).rectangle((px0 - x, 0, px1 - x, img.height), fill=255)
    top = Image.new("L", img.size, 0)
    ImageDraw.Draw(top).rectangle((0, 0, img.width, py0 + off - y), fill=255)
    m = np.maximum(np.array(top), np.minimum(np.array(mask), np.array(side)))
    m = np.minimum(m, np.array(img.getchannel("A")))
    fr.paste(img.convert("RGB"), (x, y), Image.fromarray(m))


# ================================================================ sahna elementlari
# (qatlam, cx, cy, kirish, chiqish)
EL = []
C2 = (238, 170, 164)                    # serif yorliq gradientining pastki rangi
lab = lambda s: fit_layer(s, lambda z: serif(z, 600), 150, 900, top=CORAL, bot=C2, squeeze=0.74)
name = lambda s, z=130: fit_layer(s.upper(), lambda q: serif(q, 600), z, 940, top=INK, bot=(150, 150, 156), squeeze=0.74)
word = lambda s: card_layer(fit_layer(s, lambda z: sans(z, "Bold"), 124, 760, top=INK), minw=560)

# A: kirish
EL += [(text_layer(HANDLE, sans(48, "Medium"), INK), 540, 300, 0.0, t_black1),
       (fit_layer(LES["hook"][0], lambda z: sans(z, "BoldItalic"), 140, 980, top=INK), 540, 490, 0.05, t_black1),
       (fit_layer(LES["hook"][1], lambda z: sans(z, "BoldItalic"), 140, 980, top=INK), 540, 640, 0.15, t_black1),
       (text_layer(f"{N}-dars · 0 dan ingliz tili", serif(84, 600), CORAL, C2, squeeze=0.8), 540, 830, 0.4, t_black1)]
# C: so'zlar
for i, it in enumerate(items):
    a = L[f"slow{i}"]["start"] - 0.3
    b = (L[f"slow{i + 1}"]["start"] - 0.3) if i < NI - 1 else t_ex
    EL += [(lab(ORD[i]), 540, 305, a, b), (word(it["en"]), 540, 565, a + 0.08, b),
           (text_layer(f"[ {it['tr']} ]", sans(50, "MediumItalic"), GREY), 540, 760, L[f"slow{i}"]["start"] + 0.5, b),
           (name(it["uz"].split(" (")[0]), 540, 890, L[f"norm{i}"]["start"] - 0.1, b)]
# D: misol
EL += [(text_layer("Misol:", sans(120, "BoldItalic"), INK), 540, 330, t_ex, t_black2),
       (fit_layer(LES["example"]["uz"], lambda z: serif(z, 600), 96, 940, top=INK, bot=(150, 150, 156), squeeze=0.8),
        540, 900, L["example"]["start"] + 0.4, t_black2)]
# F: takrorlash
for i, it in enumerate(items):
    r = REP[i]
    EL += [(lab("TAKRORLANG"), 540, 305, r["a"], r["b"]), (word(it["en"]), 540, 565, r["a"] + 0.08, r["b"]),
           (name(it["uz"].split(" (")[0], 110), 540, 780, r["a"] + 0.2, r["b"])]
# G: chaqiriq
EL += [(text_layer("Kommentga yozing:", serif(104, 600), INK, squeeze=0.8), 540, 380, t_cta, TOTAL + 9),
       (text_layer(f"“{items[0]['en']}”", serif(190, 600), CORAL, C2, squeeze=0.8), 540, 590, t_cta + 0.15, TOTAL + 9),
       (text_layer(f"Ertaga: {LES['next']}", sans(46, "Medium"), GREY), 540, 830, t_cta + 0.4, TOTAL + 9)]

# misol kartochkasi (xabar ko'rinishida), so'zma-so'z belgilash
ex_words = LES["example"]["en"].split()
EXF = sans(70, "Medium")
while EXF.getlength(LES["example"]["en"]) > 760:
    EXF = sans(EXF.size - 2, "Medium")
SP = EXF.getlength(" ")
EX_BOX = (90, 440, 990, 770)
x_ = 150
ex_pos = []
for w in ex_words:
    ex_pos.append((w, x_, 650, EXF.getlength(w)))
    x_ += EXF.getlength(w) + SP
wg = [len(w) + 1.5 + (4 if w[-1] in ".!?," else 0) for w in ex_words]
wg[-1] -= 4
ex_t = [L["example"]["start"] + (L["example"]["end"] - L["example"]["start"]) * sum(wg[:i]) / sum(wg) for i in range(len(wg))]
AV = Image.new("RGB", TCH.size, PAD)
AV.paste(TCH, (0, 0), TCH)
_fx, _fy, _fr = int(ALIGN["smile"][1] * TS), int((ALIGN["smile"][0] + 290) * TS), int(255 * TS)      # yuz markazi va radiusi
AV = AV.crop((_fx - _fr, _fy - _fr, _fx + _fr, _fy + _fr)).resize((84, 84), Image.LANCZOS)
AVM = Image.new("L", (84, 84), 0)
ImageDraw.Draw(AVM).ellipse((0, 0, 83, 83), fill=255)


def blurred(lay, x):
    """Kirish: xira va pastdan siljib; x: 0..1"""
    a = ease(x)
    r = (1 - a) * 14
    if r > 1:
        lay = lay.filter(ImageFilter.GaussianBlur(r))
    return lay, a, (1 - a) * 70


def put(fr, lay, cx, cy, x_in, x_out=0.0):
    lay, a, dy = blurred(lay, x_in)
    a *= 1 - ease(x_out)
    if a <= 0.01:
        return
    if a < 0.995:
        lay = lay.copy()
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2 + dy)))


def draw_example(fr, t):
    if not (t_ex <= t < t_black2):
        return
    lay = Image.new("RGBA", (W, H), (0,) * 4)
    sh = Image.new("RGBA", (W, H), (0,) * 4)
    ImageDraw.Draw(sh).rounded_rectangle((EX_BOX[0], EX_BOX[1] + 16, EX_BOX[2], EX_BOX[3] + 16), radius=48, fill=(0, 0, 0, 60))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle(EX_BOX, radius=48, fill=(255, 255, 255), outline=(232, 232, 236), width=3)
    lay.paste(AV, (130, 470), AVM)
    d.text((232, 512), TEACHER, font=sans(40, "Medium"), fill=INK, anchor="lm")
    d.text((232 + sans(40, "Medium").getlength(TEACHER) + 18, 514), "hozir", font=sans(32, "Regular"), fill=GREY, anchor="lm")
    bw = ex_pos[-1][1] + ex_pos[-1][3] + 36
    d.rounded_rectangle((120, 585, bw, 715), radius=40, fill=(240, 240, 244))
    cur = max([i for i, st in enumerate(ex_t) if t >= st], default=-1) if t <= L["example"]["end"] + 0.15 else -1
    for i, (w, x, y, ww) in enumerate(ex_pos):
        if i == cur:
            d.rounded_rectangle((x - 10, y - 44, x + ww + 10, y + 48), radius=16, fill=(255, 221, 128))
        d.text((x, y), w, font=EXF, fill=INK, anchor="lm")
    lay2, a, dy = blurred(lay, (t - t_ex - 0.1) / 0.3)
    a *= 1 - ease((t - (t_black2 - 0.15)) / 0.15)
    lay2.putalpha(lay2.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(lay2, (0, int(dy)))


def black_slide(fr, t, t0, lines, hi):
    """Qora kadr: jingalak qavs ichida oq matn, ajratilgan qism yorqin rangda."""
    d = ImageDraw.Draw(fr)
    x = ease((t - t0) / 0.45)
    cy = 760
    f = sans(72, "Medium")
    lh = 92
    y0 = cy - lh * (len(lines) - 1) / 2
    mw = max(f.getlength(s) for s in lines) * 0.86
    for k, s in enumerate(lines):
        shown = s[: max(1, int(len(s) * min(1, (t - t0 - 0.12 * k) / 0.35)))] if t - t0 > 0.12 * k else ""
        if shown:
            fr.alpha_composite(tl := text_layer(shown, f, LIME if k == hi else (255, 255, 255), squeeze=0.86),
                               (int(540 - text_layer(s, f, (255, 255, 255), squeeze=0.86).width / 2), int(y0 + k * lh - tl.height / 2)))
    gap = 60 + (mw / 2 + 40) * x
    bf = sans(150, "Light")
    d = ImageDraw.Draw(fr)
    d.text((540 - gap, cy - 6), "{", font=bf, fill=(255, 255, 255), anchor="mm")
    d.text((540 + gap, cy - 6), "}", font=bf, fill=(255, 255, 255), anchor="mm")
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = 540 + sx * (mw / 2 + 150) * (0.6 + 0.4 * x), cy + sy * 230
            d.line((px - 11, py, px + 11, py), fill=(255, 255, 255), width=3)
            d.line((px, py - 11, px, py + 11), fill=(255, 255, 255), width=3)
            d.line((px - 7, py - 7, px + 7, py + 7), fill=(255, 255, 255), width=2)
            d.line((px - 7, py + 7, px + 7, py - 7), fill=(255, 255, 255), width=2)


BIG = [text_layer("ENDI SIZ", sans(150, "Bold"), (255, 232, 226), CORAL, track=-4),
       text_layer("AYTING", sans(150, "Bold"), (255, 232, 226), CORAL, track=-4)]


def render(i):
    t = i / FPS
    if t_black1 <= t < t_items:
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        black_slide(fr, t, t_black1, [f"{N}-DARS:", f"[ {LES['title'].upper()} ]"], 1)
    elif t_black2 <= t < t_rep:
        fr = Image.new("RGBA", (W, H), (14, 14, 16, 255))
        for k, lay in enumerate(BIG):
            put(fr, lay, 540, 760 + k * 150, (t - t_black2 - 0.1 * k) / 0.3)
    else:
        fr = Image.new("RGBA", (W, H), WHITE_BG + (255,))
        last_cut = max([c for c in POSE_CUTS + CUTS if c <= t])
        show = (t / 0.6) if t < t_black1 else 1.0
        teacher(fr, t, show, (t - last_cut) / 0.35 if last_cut > 0 else 9)
        for lay, cx, cy, tin, tout in EL:
            if tin <= t < tout:
                put(fr, lay, cx, cy, (t - tin) / 0.3, (t - (tout - 0.12)) / 0.12)
        draw_example(fr, t)
        d = ImageDraw.Draw(fr)
        for r in REP:
            if r["say0"] <= t < r["say1"]:
                p = 1 - (t - r["say0"]) / (r["say1"] - r["say0"])
                d.rounded_rectangle((320, 900, 760, 914), radius=7, fill=(226, 226, 230))
                d.rounded_rectangle((320, 900, 320 + max(14, int(440 * p)), 914), radius=7, fill=CORAL)
    return fr.convert("RGB")


if "sheet" in sys.argv:
    ts = [0.4, 1.4, L["slow0"]["start"] + 0.3, L["norm0"]["end"] + 0.9, L["norm1"]["start"],
          L["example"]["start"] + 0.5, L["example"]["end"] + 0.9, t_black2 + 0.9, REP[0]["say0"] + 0.6,
          REP[0]["say1"] + 0.25, REP[2]["a"] + 0.5, TOTAL - 0.4]
    sheet = Image.new("RGB", (270 * 6, 480 * 2), "white")
    for j, t in enumerate(ts):
        sheet.paste(render(int(t * FPS)).resize((270, 480), Image.LANCZOS), (270 * (j % 6), 480 * (j // 6)))
    sheet.save(f"{OUT}/sheet.jpg", quality=88)
    render(int((L["norm0"]["end"] + 0.6) * FPS)).resize((540, 960), Image.LANCZOS).save(f"{OUT}/frame_a.jpg", quality=90)
else:
    mp4 = f"{OUT}/dars-{N:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                          f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", f"{OUT}/mix.wav", "-af",
                          "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest",
                          "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    for i in range(int(TOTAL * FPS)):
        p.stdin.write(render(i).tobytes())
    p.stdin.close()
    p.wait()
    render(int(1.3 * FPS)).save(f"{OUT}/cover.jpg", quality=92)
    open(f"{OUT}/caption.txt", "w").write(LES["caption"])
    json.dump(LES, open(f"{OUT}/video.json", "w"), ensure_ascii=False, indent=1)
print("total", TOTAL)
