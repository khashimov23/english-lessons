"""Dars videosi, 2-ko'rinish: toza "darslik" uslubi, bitta ovoz, ovozsiz ham tushunarli.
Ishlatish: python3 lesson_v2.py lessons/dars-01.json [sheet]
Ovoz: voice_uz/dars-NN/{hook,slow0,norm0,uz0,...,example,exuz,turn,rep0,...,next}.wav (oldindan tayyorlangan)
Natija: videos/dars-NN/ ichida dars-NN.mp4, cover.jpg, caption.txt"""
import json, math, os, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{ROOT}/config.json"))
LES = json.load(open(sys.argv[1]))
N = LES["lesson"]
OUT = f"{ROOT}/videos/dars-{N:02d}"
VO = f"{ROOT}/voice_uz/dars-{N:02d}"
os.makedirs(OUT, exist_ok=True)
items = LES["items"]
NI = len(items)
W, H, FPS = 1080, 1920, 30
FD = f"{ROOT}/fonts/"

# ---------------------------------------------------------------- ranglar (brend): och binafsha fon, to'q siyohrang yozuv, nilufar marker
BG, INK, HL, CORAL = (251, 248, 254), (38, 28, 74), (208, 180, 244), (124, 78, 200)
GREY, SOFT, WHITE, GREEN, PADC = (124, 118, 146), (240, 233, 249), (255, 255, 255), (38, 158, 108), (224, 204, 247)
# Instagram xavfsiz hududi: tepadan ~250, pastdan ~350 px interfeys; muhim matn 270..1560 oralig'ida
CARD = (90, 670, 990, 1085)


def pop(size, w="Bold"):
    return ImageFont.truetype(f"{FD}Poppins-{w}.ttf", size)


def lora(size, wght=600):
    f = ImageFont.truetype(f"{FD}Lora-Italic-Variable.ttf", size)
    f.set_variation_by_axes([wght])
    return f


def fra(size, wght=650):
    f = ImageFont.truetype(f"{FD}Fraunces-Variable.ttf", size)
    f.set_variation_by_axes([72, wght, 0, 0])
    return f


_tc = {}


def txt(s, font, fill):
    """Matn qatlami (kesh bilan)."""
    key = (s, font.path, font.size, fill, getattr(font, "_w", 0))
    if key not in _tc:
        asc, desc = font.getmetrics()
        im = Image.new("RGBA", (int(font.getlength(s)) + 24, asc + desc + 24), (0,) * 4)
        ImageDraw.Draw(im).text((12, 12), s, font=font, fill=fill)
        _tc[key] = im
    return _tc[key]


def fit(s, mk, size, maxw):
    f = mk(size)
    while f.getlength(s) > maxw and size > 28:
        size -= 4
        f = mk(size)
    return f


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def put(fr, lay, cx, cy, t, tin, tout=None, dur=0.26, rise=36):
    """Qatlamni markazi (cx, cy) ga qo'yadi: pastdan ko'tarilib paydo bo'ladi, oxirida so'nadi."""
    if t < tin or (tout is not None and t >= tout):
        return
    a = ease((t - tin) / dur)
    if tout is not None:
        a *= 1 - ease((t - (tout - 0.12)) / 0.12)
    if a <= 0.01:
        return
    if a < 0.995:
        lay = lay.copy()
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2 + (1 - ease((t - tin) / dur)) * rise)))


def marker(fr, cx, cy, w, h, p):
    """Sariq marker chizig'i: chapdan o'ngga yoyiladi (p: 0..1)."""
    if p <= 0:
        return
    x0 = cx - w / 2
    ImageDraw.Draw(fr).rounded_rectangle((x0, cy - h / 2, x0 + max(h * 0.6, w * ease(p)), cy + h / 2), radius=h * 0.28, fill=HL)


def pill(s, font, fg, bg, padx=30, pady=14, outline=None):
    key = ("pill", s, font.path, font.size, fg, bg, outline)
    if key not in _tc:
        tw = int(font.getlength(s))
        asc, desc = font.getmetrics()
        im = Image.new("RGBA", (tw + padx * 2, asc + desc + pady * 2), (0,) * 4)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=im.height // 2, fill=bg, outline=outline, width=3)
        d.text((padx, pady), s, font=font, fill=fg)
        _tc[key] = im
    return _tc[key]


# ================================================================ ovoz yo'lagi (tayyor bo'laklardan, o'lik pauzasiz)
segs = [("hook", 0.45)]
for i in range(NI):
    segs += [(f"slow{i}", 0.5), (f"norm{i}", 0.4), (f"uz{i}", 0.75)]
segs += [("example", 0.4), ("exuz", 0.65), ("turn", 0.5)]
for i in range(NI):
    segs.append((f"rep{i}", 2.0))
segs.append(("next", 0.3))
sr = 24000
chunks, tcur, timing = [np.zeros(int(0.15 * sr), dtype=np.float32)], 0.15, []
for sid, gap in segs:
    s, _sr = sf.read(f"{VO}/{sid}.wav", dtype="float32")
    assert _sr == sr, sid
    idx = np.where(np.abs(s) > 0.02 * np.abs(s).max())[0]
    s = s[max(0, idx[0] - 500): idx[-1] + 1500]
    s = s / np.max(np.abs(s)) * 0.8
    timing.append({"id": sid, "start": round(tcur, 3), "end": round(tcur + len(s) / sr, 3)})
    chunks += [s, np.zeros(int(gap * sr), dtype=np.float32)]
    tcur += len(s) / sr + gap
voice = np.concatenate(chunks)
TV = len(voice) / sr
TOTAL = TV + 1.3
L = {x["id"]: x for x in timing}
json.dump({"total": round(TV, 3), "lines": timing}, open(f"{OUT}/timing.json", "w"), indent=1)
voice = np.concatenate([voice, np.zeros(int(TOTAL * sr) - len(voice))])
NF = int(TOTAL * FPS)
env = np.array([np.sqrt(np.mean(voice[int(i / FPS * sr): int((i + 1) / FPS * sr)] ** 2) + 1e-9) for i in range(NF + 1)])
env = env / env.max()

# ---------------------------------------------------------------- sahnalar
WA = [L[f"slow{i}"]["start"] - 0.25 for i in range(NI)]
t_ex = L["example"]["start"] - 0.3
WB = WA[1:] + [t_ex]
t_turn = L["turn"]["start"] - 0.25
REP = []
for i in range(NI):
    b = (L[f"rep{i + 1}"]["start"] - 0.2) if i < NI - 1 else L["next"]["start"] - 0.25
    REP.append({"a": L[f"rep{i}"]["start"] - 0.2, "say0": L[f"rep{i}"]["end"] + 0.1, "say1": b - 0.5, "b": b})
t_rep, t_end = REP[0]["a"], REP[-1]["b"]
CUTS = WA + [t_ex, t_turn, t_rep] + [r["a"] for r in REP[1:]] + [t_end]

# ================================================================ tovush: fon musiqa, yumshoq o'tish tovushlari
rng = np.random.default_rng(3)
sfx = np.zeros(len(voice))
for c in CUTS:
    m = int(0.28 * sr)
    nz = np.convolve(rng.standard_normal(m + 80), np.ones(60) / 60, mode="valid")[:m]
    i0 = int(max(c - 0.16, 0) * sr)
    sfx[i0: i0 + m] += (nz / np.max(np.abs(nz)) * np.sin(np.linspace(0, math.pi, m)) ** 2 * 0.08)[: len(sfx) - i0]
for h in [L[f"uz{i}"]["start"] - 0.1 for i in range(NI)] + [r["say1"] for r in REP]:      # tarjima / "zo'r" belgisi: yumshoq qo'ng'iroqcha
    tt_ = np.arange(int(0.35 * sr)) / sr
    s_ = (np.sin(2 * np.pi * 880 * tt_) + 0.5 * np.sin(2 * np.pi * 1320 * tt_)) * np.exp(-tt_ / 0.07)
    i0 = int(h * sr)
    sfx[i0: i0 + len(s_)] += s_ * 0.05
sys.path.insert(0, ROOT)
from music import make as make_music
_e = np.convolve(np.abs(voice), np.ones(int(0.05 * sr)) / int(0.05 * sr), mode="same")
duck = 1 - 0.6 * np.clip(_e / _e.max() * 10, 0, 1)
duck = np.convolve(duck, np.ones(int(0.18 * sr)) / int(0.18 * sr), mode="same")
tt = np.arange(len(voice)) / sr
fade = np.minimum(1, np.minimum(tt / 0.3, (TOTAL - tt) / 1.2)).clip(0)
mix = voice + 0.17 * make_music(CFG["music"], TOTAL, sr)[: len(voice)] * duck * fade + sfx
sf.write(f"{OUT}/mix.wav", mix / np.max(np.abs(mix)) * 0.95, sr)

# ================================================================ fon va o'qituvchi
_bg = Image.new("RGB", (W, H), BG)
_d = ImageDraw.Draw(_bg)
for yy in range(60, H, 60):                                   # daftar nuqtalari
    for xx in range(60, W, 60):
        _d.ellipse((xx - 2, yy - 2, xx + 2, yy + 2), fill=(234, 226, 244))
BGIM = _bg.convert("RGBA")

TS = 0.62                                                    # o'qituvchi kichikroq: mazmunga ko'proq joy
ALIGN = json.load(open(f"{ROOT}/assets/poses/align.json"))
POSE = {}
for nm, (top, cx, _) in ALIGN.items():
    im = Image.open(f"{ROOT}/assets/poses/{nm}_cut.png").convert("RGBA")
    im = im.resize((int(im.width * TS), int(im.height * TS)), Image.LANCZOS)
    POSE[nm] = (im, int(540 - cx * TS), int(1170 - top * TS))
PAD_BOX = (540 - 292, 1312, 540 + 292, 2100)
PR = 126


def pose_at(t):
    if t < WA[0]:
        return "wave"
    for i in range(NI):
        if WA[i] <= t < WB[i]:
            return "point" if t < L[f"uz{i}"]["start"] - 0.1 else "open"
    if t_ex <= t < t_turn:
        return "smile" if t < L["exuz"]["start"] - 0.1 else "open"
    for r in REP:
        if r["a"] <= t < r["b"]:
            return "point" if t < r["say0"] else ("open" if t < r["say1"] else "thumbs")
    if t >= t_end:
        return "down" if t < TOTAL - 1.4 else "heart"
    return "smile"


POSE_CUTS, _p = [0.0], None
for _i in range(NF):
    _q = pose_at(_i / FPS)
    if _q != _p and _i:
        POSE_CUTS.append(_i / FPS)
    _p = _q


def teacher(fr, t, pose=None):
    img0, x0, y0 = POSE[pose or pose_at(t)]
    last = max([c for c in POSE_CUTS + CUTS if c <= t] or [0])
    k = (t - last) / 0.32
    bob = 5 * math.sin(t * 2 * math.pi / 4.0)
    px0, py0, px1, py1 = PAD_BOX
    ImageDraw.Draw(fr).rounded_rectangle(PAD_BOX, radius=PR, fill=PADC)
    sc = 1 + 0.035 * math.sin(min(k, 1) * math.pi) if (k < 1 and last > 0) else 1.0
    img = img0 if sc == 1.0 else img0.resize((int(img0.width * sc), int(img0.height * sc)), Image.BILINEAR)
    x = int(x0 - (img.width - img0.width) / 2)
    y = int(y0 + bob - (img.height - img0.height) * 0.6)
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((0, 0, img.width, py0 + PR - y), fill=255)
    md.rounded_rectangle((px0 - x, py0 - y, px1 - x, py1 - y), radius=PR, fill=255)
    side = Image.new("L", img.size, 0)
    ImageDraw.Draw(side).rectangle((px0 - x, 0, px1 - x, img.height), fill=255)
    top = Image.new("L", img.size, 0)
    ImageDraw.Draw(top).rectangle((0, 0, img.width, py0 - y), fill=255)
    m = np.maximum(np.array(top), np.minimum(np.array(mask), np.array(side)))
    m = np.minimum(m, np.array(img.getchannel("A")))
    fr.paste(img.convert("RGB"), (x, y), Image.fromarray(m))


# ================================================================ umumiy elementlar
def _card():
    x0, y0, x1, y1 = CARD
    M = 70
    im = Image.new("RGBA", (x1 - x0 + M * 2, y1 - y0 + M * 2), (0,) * 4)
    sh = Image.new("RGBA", im.size, (0,) * 4)
    ImageDraw.Draw(sh).rounded_rectangle((M, M + 18, im.width - M, im.height - M + 18), radius=56, fill=(38, 28, 74, 46))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    ImageDraw.Draw(im).rounded_rectangle((M, M, im.width - M, im.height - M), radius=56, fill=WHITE, outline=(232, 224, 243), width=3)
    return im


CARD_IM = _card()
CCX, CCY = (CARD[0] + CARD[2]) // 2, (CARD[1] + CARD[3]) // 2
STAGES = NI + 2                                              # so'zlar + misol + mashq


def stage_at(t):
    for k in range(NI):
        if WA[k] <= t < WB[k]:
            return k, items[k]["en"].upper()
    if t_ex <= t < t_turn:
        return NI, "MISOL"
    for k in range(NI):
        if REP[k]["a"] <= t < REP[k]["b"]:
            return NI + 1, f"MASHQ  {k + 1}/{NI}"
    return (NI + 1, "MASHQ") if t < t_end else (STAGES, "YAKUN")


def header(fr, t):
    """Tepada: raqamlangan bo'lim ("01 — HELLO") va nuqtalar — dars qayerga kelgani doim ko'rinadi."""
    d = ImageDraw.Draw(fr)
    k, label = stage_at(t)
    num = f"{min(k + 1, STAGES):02d}"
    d.text((90, 292), num, font=pop(36), fill=CORAL, anchor="lm")
    x = 90 + pop(36).getlength(num) + 18
    d.line((x, 292, x + 44, 292), fill=INK, width=3)
    xx = x + 62
    for ch in label:                                          # harflar orasi ochiq
        d.text((xx, 292), ch, font=pop(30, "Medium"), fill=INK, anchor="lm")
        xx += pop(30, "Medium").getlength(ch) + 5
    for q in range(STAGES):
        cx = 990 - 11 - (STAGES - 1 - q) * 38
        if q == k:
            d.ellipse((cx - 11, 281, cx + 11, 303), fill=CORAL)
        elif q < k:
            d.ellipse((cx - 9, 283, cx + 9, 301), fill=INK)
        else:
            d.ellipse((cx - 9, 283, cx + 9, 301), outline=INK, width=3)
    d.line((90, 336, 990, 336), fill=(226, 216, 240), width=2)


def underline(fr, cx, y, w, p):
    """Qo'lda chizilgandek egri tagchiziq (p: 0..1)."""
    if p <= 0:
        return
    n = max(2, int(40 * ease(p)))
    pts = [(cx - w / 2 + w * q / 40, y + 9 * math.sin(math.pi * q / 40) - 3 * math.sin(2 * math.pi * q / 40)) for q in range(n + 1)]
    ImageDraw.Draw(fr).line(pts, fill=CORAL, width=7, joint="curve")


def headline(fr, t, l1, l2, tin, tout, y1=425, y2=525, s1=66, s2=100):
    """Har sahnada ikki qatorli sarlavha: qalin qator + nilufar kursiv qator, tagida chiziq."""
    f1 = fit(l1, pop, s1, 900)
    f2 = fit(l2, lambda z: lora(z, 600), s2, 900)
    put(fr, txt(l1, f1, INK), 540, y1, t, tin, tout)
    put(fr, txt(l2, f2, CORAL), 540, y2, t, tin + 0.1, tout)
    if tin + 0.2 <= t and (tout is None or t < tout - 0.12):
        underline(fr, 540, y2 + f2.size * 0.66, f2.getlength(l2) * 0.82, (t - tin - 0.2) / 0.35)


def eq(fr, x, y, t, col=INK):
    """Ovoz to'lqini: gapirilayotganda qimirlaydi."""
    d = ImageDraw.Draw(fr)
    e = env[min(int(t * FPS), NF)]
    for k in range(4):
        h = 8 + 26 * e * (0.55 + 0.45 * math.sin(t * 17 + k * 1.9))
        d.rounded_rectangle((x + k * 13, y - h / 2, x + k * 13 + 7, y + h / 2), radius=3.5, fill=col)


def status(fr, t, label, tin):
    f = pop(28)
    w = int(f.getlength(label)) + 110
    lay = Image.new("RGBA", (w, 60), (0,) * 4)
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w - 1, 59), radius=30, fill=SOFT, outline=(226, 216, 240), width=3)
    ImageDraw.Draw(lay).text((84, 9), label, font=f, fill=INK)
    eq(lay, 26, 30, t)
    put(fr, lay, CCX, CARD[1], t, tin, dur=0.18, rise=0)


def word_scene(fr, t, i):
    it, a, b = items[i], WA[i], WB[i]
    headline(fr, t, it.get("when", f"{i + 1}-so'z"), "nima deymiz?", a, b)
    put(fr, CARD_IM, CCX, CCY, t, a + 0.05, b, rise=60)
    s0, n0, u0 = L[f"slow{i}"]["start"], L[f"norm{i}"]["start"], L[f"uz{i}"]["start"]
    if t < b - 0.12:
        if t < n0 - 0.15:
            status(fr, t, "SEKIN", a + 0.15)
        elif t < u0 - 0.1:
            status(fr, t, "ODDIY TEZLIKDA", n0 - 0.15)
        else:
            status(fr, t, "O'ZBEKCHASI", u0 - 0.1)
    put(fr, txt(it["en"], fit(it["en"], pop, 146, 800), INK), CCX, 795, t, a + 0.1, b)
    put(fr, txt(f"[ {it['tr']} ]", pop(46, "MediumItalic"), GREY), CCX, 900, t, s0 + 0.3, b)
    uz = it["uz"].split(" (")[0]
    fu = fit(uz, lambda z: fra(z, 650), 86, 780)
    if a + 0.3 <= t < u0 - 0.1:                               # tarjima hali ochilmagan: uch nuqta
        d = ImageDraw.Draw(fr)
        for k in range(3):
            ph = 0.5 + 0.5 * math.sin(t * 5 - k * 0.9)
            d.ellipse((CCX - 44 + k * 36, 1000 - 8, CCX - 28 + k * 36, 1000 + 8), fill=(int(214 - 40 * ph), int(204 - 40 * ph), int(232 - 30 * ph)))
    if u0 - 0.1 <= t < b - 0.1:
        marker(fr, CCX, 1008, fu.getlength(uz) + 44, fu.size * 0.62, (t - (u0 - 0.1)) / 0.3)
    put(fr, txt(uz, fu, INK), CCX, 999, t, u0 - 0.1, b, rise=20)


# misol: xabar ko'rinishida, so'zma-so'z belgilanadi
ex_words = LES["example"]["en"].split()
EXF = fit(LES["example"]["en"], lambda z: pop(z, "Medium"), 72, 640)
_sp = EXF.getlength(" ")
_x, ex_pos = 0, []
for w_ in ex_words:
    ex_pos.append((w_, _x, EXF.getlength(w_)))
    _x += EXF.getlength(w_) + _sp
EXW = _x - _sp
_wg = [len(w_) + 1.5 + (4 if w_[-1] in ".!?," else 0) for w_ in ex_words]
_wg[-1] -= 4
ex_t = [L["example"]["start"] + (L["example"]["end"] - L["example"]["start"]) * sum(_wg[:i]) / sum(_wg) for i in range(len(_wg))]
_sm, _sx, _sy = POSE["smile"]
_fx, _fy, _fr = int(ALIGN["smile"][1] * TS), int((ALIGN["smile"][0] + 290) * TS), int(255 * TS)
AV = Image.new("RGB", _sm.size, PADC)
AV.paste(_sm, (0, 0), _sm)
AV = AV.crop((_fx - _fr, _fy - _fr, _fx + _fr, _fy + _fr)).resize((88, 88), Image.LANCZOS)
AVM = Image.new("L", (88, 88), 0)
ImageDraw.Draw(AVM).ellipse((0, 0, 87, 87), fill=255)


def example_scene(fr, t):
    a, b = t_ex, t_turn
    headline(fr, t, "Endi gap ichida", "eshitib ko'ring.", a, b)
    put(fr, CARD_IM, CCX, CCY, t, a + 0.05, b, rise=60)
    if t < L["exuz"]["start"] - 0.1:
        status(fr, t, "TINGLANG", a + 0.15)
    elif t < b - 0.12:
        status(fr, t, "O'ZBEKCHASI", L["exuz"]["start"] - 0.1)
    lay = Image.new("RGBA", (W, 250), (0,) * 4)
    d = ImageDraw.Draw(lay)
    lay.paste(AV.resize((72, 72), Image.LANCZOS), (140, 4), AVM.resize((72, 72)))
    d.text((228, 40), CFG["teacher"], font=pop(34, "Medium"), fill=INK, anchor="lm")
    d.text((228 + pop(34, "Medium").getlength(CFG["teacher"]) + 14, 42), "hozir", font=pop(28, "Regular"), fill=GREY, anchor="lm")
    bx0 = 140
    d.rounded_rectangle((bx0, 96, bx0 + EXW + 76, 216), radius=40, fill=(243, 237, 251))
    cur = max([i for i, st in enumerate(ex_t) if t >= st], default=-1) if t <= L["example"]["end"] + 0.15 else -1
    for i, (w_, x, ww) in enumerate(ex_pos):
        if i == cur:
            d.rounded_rectangle((bx0 + 38 + x - 10, 156 - 42, bx0 + 38 + x + ww + 10, 156 + 44), radius=16, fill=HL)
        d.text((bx0 + 38 + x, 156), w_, font=EXF, fill=INK, anchor="lm")
    put(fr, lay, 540, 722 + 125, t, a + 0.12, b)
    uz = LES["example"]["uz"]
    fu = fit(uz, lambda z: fra(z, 650), 70, 780)
    u0 = L["exuz"]["start"] - 0.1
    if u0 <= t < b - 0.1:
        marker(fr, CCX, 1018, fu.getlength(uz) + 40, fu.size * 0.64, (t - u0) / 0.3)
    put(fr, txt(uz, fu, INK), CCX, 1010, t, u0, b, rise=20)


def mic(d, cx, cy, col):
    d.rounded_rectangle((cx - 34, cy - 84, cx + 34, cy + 24), radius=34, fill=col)
    d.arc((cx - 62, cy - 50, cx + 62, cy + 62), 0, 180, fill=col, width=10)
    d.line((cx, cy + 62, cx, cy + 96), fill=col, width=10)
    d.rounded_rectangle((cx - 40, cy + 92, cx + 40, cy + 102), radius=5, fill=col)


TURN_W = [("Endi", BG), ("sizning", BG), ("navbatingiz!", HL)]
_tw = [len(w_[0]) for w_ in TURN_W]


def turn_scene(fr, t):
    ic = Image.new("RGBA", (220, 240), (0,) * 4)
    mic(ImageDraw.Draw(ic), 110, 110, BG)
    put(fr, ic, 540, 480, t, t_turn + 0.02)
    t0, t1 = L["turn"]["start"], L["turn"]["end"]
    f = fra(170, 700)
    l1w = f.getlength("Endi sizning")
    x0 = 540 - l1w / 2
    pos = [(x0 + f.getlength("Endi") / 2, 760), (x0 + l1w - f.getlength("sizning") / 2, 760), (540, 950)]
    for k, (w_, col) in enumerate(TURN_W):                    # har so'z aytilgan paytda chiqadi
        tk = t0 + (t1 - t0) * sum(_tw[:k]) / sum(_tw) - 0.08
        put(fr, txt(w_, f, col), pos[k][0], pos[k][1], t, tk, dur=0.16, rise=24)
    put(fr, txt(f"{NI} ta so'zni ovoz chiqarib takrorlang", pop(44, "Medium"), (204, 194, 230)), 540, 1140, t, t1 + 0.05)


def rep_scene(fr, t, i):
    it, r = items[i], REP[i]
    a, b = r["a"], r["b"]
    headline(fr, t, "Takrorlang", "ovoz chiqarib!", a, b)
    put(fr, CARD_IM, CCX, CCY, t, a + 0.05, b, rise=60)
    put(fr, txt(it["en"], fit(it["en"], pop, 140, 800), INK), CCX, 780, t, a + 0.1, b)
    put(fr, txt(it["uz"].split(" (")[0], fit(it["uz"].split(" (")[0], lambda z: fra(z, 600), 58, 700), GREY), CCX, 884, t, a + 0.15, b)
    d = ImageDraw.Draw(fr)
    y = 990
    if a + 0.2 <= t < r["say0"]:
        eq(fr, CCX - 150, y, t)
        fr.alpha_composite(txt("Tinglang", pop(40, "Medium"), INK), (CCX - 90, y - 42))
    elif r["say0"] <= t < r["say1"]:
        p = (t - r["say0"]) / (r["say1"] - r["say0"])
        fr.alpha_composite(tl := txt("Endi siz ayting", pop(38, "Medium"), INK), (int(CCX - tl.width / 2), y - 62))
        d.rounded_rectangle((CCX - 260, y + 22, CCX + 260, y + 40), radius=9, fill=SOFT)
        d.rounded_rectangle((CCX - 260, y + 22, CCX - 260 + max(18, int(520 * (1 - p))), y + 40), radius=9, fill=HL)
    elif r["say1"] <= t < b - 0.1:
        k = ease((t - r["say1"]) / 0.22)
        rr = 34 * (0.6 + 0.4 * k)
        d.ellipse((CCX - 112 - rr, y - rr, CCX - 112 + rr, y + rr), fill=GREEN)
        d.line((CCX - 128, y + 2, CCX - 116, y + 14, CCX - 94, y - 12), fill=WHITE, width=8, joint="curve")
        fr.alpha_composite(txt("Zo'r!", pop(48), GREEN), (CCX - 62, y - 48))


def end_scene(fr, t):
    a = t_end
    headline(fr, t, "Unutmaslik uchun", "saqlab qo'ying.", a, None, y1=500, y2=650, s1=74, s2=156)
    t_nx = L["next"]["start"] + (L["next"]["end"] - L["next"]["start"]) * 0.42      # "Ertaga ..." aytilgan payt
    nx = LES["next"].replace(": ", " · ")
    put(fr, txt(f"Ertaga: {nx}", fit(f"Ertaga: {nx}", lambda z: pop(z, "Medium"), 54, 820), INK), 540, 860, t, t_nx)
    put(fr, txt(CFG["handle"], pop(46), CORAL), 540, 960, t, t_nx + 0.25)


# kirish (hook): birinchi kadrdan to'liq ko'rinadi — ovozsiz ham va'da tushunarli
HOOK = LES["hook_big"]                                      # [qalin qator, kursiv qator]
HK1 = fit(HOOK[0], pop, 112, 920)
HK2 = fit(HOOK[1], lambda z: lora(z, 650), 176, 940)
_hw = HOOK[0].split() + HOOK[1].split()
_hwg = LES.get("hook_weights") or [len(w_) for w_ in _hw]


def hook_scene(fr, t):
    b = WA[0]
    put(fr, pill(f"0 DAN INGLIZ TILI  ·  {N}-DARS", pop(36), CORAL, BG, 32, 15, outline=CORAL), 540, 400, t, -1, b)
    t0, t1 = L["hook"]["start"], L["hook"]["end"]
    cur = max([k for k in range(len(_hw)) if t >= t0 + (t1 - t0) * sum(_hwg[:k]) / sum(_hwg)], default=-1) if t0 <= t < t1 else -1
    k = 0
    for line, f, cy, col in ((HOOK[0], HK1, 590, INK), (HOOK[1], HK2, 780, CORAL)):
        x = 540 - f.getlength(line) / 2
        for w_ in line.split():
            ww = f.getlength(w_)
            if k == cur and t < b - 0.1:                       # aytilayotgan so'z marker bilan
                ImageDraw.Draw(fr).rounded_rectangle((x - 14, cy - f.size * 0.42, x + ww + 14, cy + f.size * 0.5), radius=f.size * 0.16, fill=HL)
            x += ww + f.getlength(" ")
            k += 1
        put(fr, txt(line, f, col), 540, cy, t, -1, b)
    if t < b - 0.12:
        underline(fr, 540, 780 + HK2.size * 0.66, HK2.getlength(HOOK[1]) * 0.8, (t - 0.1) / 0.4)


def render(i):
    t = i / FPS
    if t_turn <= t < t_rep:
        fr = Image.new("RGBA", (W, H), INK + (255,))
        turn_scene(fr, t)
        return fr.convert("RGB")
    fr = BGIM.copy()
    teacher(fr, t)
    if t < WA[0]:
        hook_scene(fr, t)
    else:
        header(fr, t)
        for k in range(NI):
            if WA[k] <= t < WB[k]:
                word_scene(fr, t, k)
        if t_ex <= t < t_turn:
            example_scene(fr, t)
        for k in range(NI):
            if REP[k]["a"] <= t < REP[k]["b"]:
                rep_scene(fr, t, k)
        if t >= t_end:
            end_scene(fr, t)
    return fr.convert("RGB")


def cover():
    """Muqova: muhim matn markazda (profil setkasidagi 3:4 kesimda ham to'liq ko'rinadi)."""
    fr = BGIM.copy()
    teacher(fr, 0.0, "smile")
    fr.alpha_composite(p := pill("0 DAN INGLIZ TILI", pop(40), CORAL, BG, 34, 16, outline=CORAL), (540 - p.width // 2, 380))
    fr.alpha_composite(tl := txt(f"{N}-dars", fra(240, 700), INK), (540 - tl.width // 2, 480))
    ft = fit(LES["title"], lambda z: fra(z, 700), 124, 860)
    marker(fr, 540, 880, ft.getlength(LES["title"]) + 56, ft.size * 0.62, 1)
    fr.alpha_composite(tl := txt(LES["title"], ft, INK), (540 - tl.width // 2, 870 - tl.height // 2))
    # o'rganiladigan so'zlar: bir qatorga sig'sa bitta qator, sig'masa o'qiladigan o'lchamda 2-3 qatorga bo'linadi
    one = "  ·  ".join(it["en"] for it in items)
    f = pop(46, "Medium")
    if f.getlength(one) <= 900:
        rows = [one]
    else:
        f, rows, cur = pop(42, "Medium"), [], ""
        for it in items:
            nxt = it["en"] if not cur else cur + "  ·  " + it["en"]
            if cur and f.getlength(nxt) > 900:
                rows.append(cur)
                cur = it["en"]
            else:
                cur = nxt
        rows.append(cur)
    for k, row in enumerate(rows):
        fr.alpha_composite(tl := txt(row, f, GREY), (540 - tl.width // 2, 1000 + k * 58 - (len(rows) - 1) * 12))
    return fr.convert("RGB")


if "sheet" in sys.argv:
    ts = [0.0, 1.2, L["slow0"]["start"] + 0.4, L["norm0"]["start"] + 0.3, L["uz0"]["start"] + 0.5, L["uz1"]["start"] + 0.5,
          L["example"]["start"] + 0.6, L["exuz"]["start"] + 0.7, t_turn + 0.8, REP[0]["a"] + 0.5, REP[0]["say0"] + 0.8,
          REP[2]["say1"] + 0.3, t_end + 1.2, TOTAL - 0.3]
    sheet = Image.new("RGB", (270 * 8, 480 * 2), "white")
    for j, t in enumerate(ts):
        sheet.paste(render(int(t * FPS)).resize((270, 480), Image.LANCZOS), (270 * (j % 8), 480 * (j // 8)))
    sheet.paste(cover().resize((270, 480), Image.LANCZOS), (270 * 6, 480))
    sheet.save(f"{OUT}/sheet.jpg", quality=90)
else:
    mp4 = f"{OUT}/dars-{N:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", f"{OUT}/mix.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac",
                          "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    for i in range(NF):
        p.stdin.write(render(i).tobytes())
    p.stdin.close()
    p.wait()
    cover().save(f"{OUT}/cover.jpg", quality=93)
    open(f"{OUT}/caption.txt", "w").write(LES["caption"])
    json.dump(LES, open(f"{OUT}/video.json", "w"), ensure_ascii=False, indent=1)
print("total", round(TOTAL, 2))
