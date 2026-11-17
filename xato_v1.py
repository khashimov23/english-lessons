"""Maxsus video: "Xato va to'g'risi" (bunday demang — bunday deng). lesson_v2.py bilan bir xil brend ko'rinishi.
Ishlatish: python3 xato_v1.py specials/xato-01.json [sheet]
Ovoz: voice_uz/dars-NN/{hook,slow0,norm0,uz0,...,example,exuz,turn,rep0,...,next}.wav (oldindan tayyorlangan)
Natija: videos/dars-NN/ ichida dars-NN.mp4, cover.jpg, caption.txt"""
import json, math, os, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{ROOT}/config.json"))
LES = json.load(open(sys.argv[1]))
ID = LES["id"]
OUT = f"{ROOT}/videos/{ID}"
VO = f"{ROOT}/voice_uz/{ID}"
os.makedirs(OUT, exist_ok=True)
items = LES["items"]
NI = len(items)
W, H, FPS = 1080, 1920, 30
FD = f"{ROOT}/fonts/"

# ---------------------------------------------------------------- ranglar (brend): och binafsha fon, to'q siyohrang yozuv, nilufar marker
BG, INK, HL, CORAL = (251, 248, 254), (38, 28, 74), (208, 180, 244), (124, 78, 200)
GREY, SOFT, WHITE, GREEN, PADC = (124, 118, 146), (240, 233, 249), (255, 255, 255), (38, 158, 108), (224, 204, 247)
# Instagram xavfsiz hududi: tepadan ~250, pastdan ~350 px interfeys; muhim matn 270..1560 oralig'ida
CARD = (90, 650, 990, 1100)
RED = (214, 69, 80)


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
segs = [("hook", 0.5)]
for i in range(NI):
    segs += [(f"uz{i}", 1.55), (f"en{i}", 1.5)]
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
WA = [L[f"uz{i}"]["start"] - 0.25 for i in range(NI)]
t_end = L["next"]["start"] - 0.25
WB = WA[1:] + [t_end]
TW = [L[f"uz{i}"]["end"] + 0.1 for i in range(NI)]            # xato varianti chiqadi
TS_ = [L[f"uz{i}"]["end"] + 0.75 for i in range(NI)]          # ustidan chiziladi
TR = [L[f"en{i}"]["start"] - 0.2 for i in range(NI)]          # to'g'risi chiqadi
CUTS = WA + [t_end]

# ================================================================ tovush: fon musiqa, yumshoq o'tish tovushlari
rng = np.random.default_rng(3)
sfx = np.zeros(len(voice))
for c in CUTS:
    m = int(0.28 * sr)
    nz = np.convolve(rng.standard_normal(m + 80), np.ones(60) / 60, mode="valid")[:m]
    i0 = int(max(c - 0.16, 0) * sr)
    sfx[i0: i0 + m] += (nz / np.max(np.abs(nz)) * np.sin(np.linspace(0, math.pi, m)) ** 2 * 0.08)[: len(sfx) - i0]
for h in TS_:                                                 # xato: past "bzz"
    tt_ = np.arange(int(0.3 * sr)) / sr
    s_ = np.sign(np.sin(2 * np.pi * 140 * tt_)) * np.exp(-tt_ / 0.12)
    s_ = np.convolve(s_, np.ones(24) / 24, mode="same")
    i0 = int(h * sr)
    sfx[i0: i0 + len(s_)] += s_ * 0.07
for h in TR:                                                  # to'g'risi: yumshoq qo'ng'iroqcha
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
            return "point" if t < TW[i] else ("open" if t < TR[i] else "thumbs")
    return "down" if t < TOTAL - 1.4 else "heart"


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
STAGES = NI + 1                                              # xatolar + yakun


def stage_at(t):
    for k in range(NI):
        if WA[k] <= t < WB[k]:
            return k, f"XATO  {k + 1}/{NI}"
    return NI, "YAKUN"


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


def badge(fr, cx, cy, ok, k=1.0):
    """Yumaloq belgi: yashil ✓ yoki qizil ✗."""
    d = ImageDraw.Draw(fr)
    r = 30 * (0.6 + 0.4 * ease(k))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GREEN if ok else RED)
    if ok:
        d.line((cx - 14, cy + 1, cx - 4, cy + 12, cx + 15, cy - 11), fill=WHITE, width=7, joint="curve")
    else:
        d.line((cx - 11, cy - 11, cx + 11, cy + 11), fill=WHITE, width=7)
        d.line((cx - 11, cy + 11, cx + 11, cy - 11), fill=WHITE, width=7)


def strike(fr, cx, cy, w, p):
    if p <= 0:
        return
    x0 = cx - w / 2 - 14
    ImageDraw.Draw(fr).line((x0, cy + 4, x0 + (w + 28) * ease(p), cy - 2), fill=RED, width=9)


YW, YR, YT, YN = 745, 880, 968, 1040                          # kartochka ichidagi qatorlar


def item_scene(fr, t, i):
    it, a, b = items[i], WA[i], WB[i]
    headline(fr, t, f"«{it['uz']}»", "inglizcha qanday?", a, b, y1=415, y2=512, s1=66, s2=92)
    put(fr, CARD_IM, CCX, CCY, t, a + 0.05, b, rise=60)
    tw, ts, tr = TW[i], TS_[i], TR[i]
    if t < b - 0.12:
        if t < tw:
            status(fr, t, "O'YLAB KO'RING", a + 0.15)
        elif t < tr:
            status(fr, t, "KO'PCHILIK SHUNDAY DEYDI", tw)
        else:
            status(fr, t, "TO'G'RISI", tr)
    if a + 0.3 <= t < tw:                                     # javob hali ochilmagan: uch nuqta
        d = ImageDraw.Draw(fr)
        for k in range(3):
            ph = 0.5 + 0.5 * math.sin(t * 5 - k * 0.9)
            d.ellipse((CCX - 44 + k * 36, YR - 30 - 8, CCX - 28 + k * 36, YR - 30 + 8), fill=(int(214 - 40 * ph), int(204 - 40 * ph), int(232 - 30 * ph)))
    # xato varianti
    fw = fit(it["wrong"], lambda z: pop(z, "Medium"), 92, 640)
    ww = fw.getlength(it["wrong"])
    put(fr, txt(it["wrong"], fw, INK if t < ts + 0.15 else GREY), CCX + 40, YW, t, tw, b)
    if tw + 0.05 <= t < b - 0.1:
        badge(fr, CCX + 40 - ww / 2 - 62, YW + 2, False, (t - tw) / 0.2)
        strike(fr, CCX + 40, YW, ww, (t - ts) / 0.25)
    # to'g'risi
    fe = fit(it["en"], pop, 118, 640)
    we = fe.getlength(it["en"])
    if tr <= t < b - 0.1:
        marker(fr, CCX + 40, YR + 8, we + 44, fe.size * 0.62, (t - tr) / 0.3)
        badge(fr, CCX + 40 - we / 2 - 70, YR + 4, True, (t - tr) / 0.2)
    put(fr, txt(it["en"], fe, INK), CCX + 40, YR, t, tr, b, rise=20)
    put(fr, txt(f"[ {it['tr']} ]", pop(42, "MediumItalic"), GREY), CCX, YT, t, L[f"en{i}"]["start"] + 0.3, b)
    put(fr, txt(it["note"], fit(it["note"], lambda z: fra(z, 600), 42, 800), CORAL), CCX, YN, t, L[f"en{i}"]["end"] + 0.1, b)


def end_scene(fr, t):
    a = t_end
    e1, e2 = LES["end_big"]
    headline(fr, t, e1, e2, a, None, y1=500, y2=650, s1=74, s2=150)
    t_nx = L["next"]["start"] + (L["next"]["end"] - L["next"]["start"]) * 0.55
    put(fr, txt(LES["end_note"], fit(LES["end_note"], lambda z: pop(z, "Medium"), 52, 820), INK), 540, 860, t, t_nx)
    put(fr, txt(CFG["handle"], pop(46), CORAL), 540, 960, t, t_nx + 0.25)


HOOK = LES["hook_big"]
HK1 = fit(HOOK[0], pop, 112, 920)
HK2 = fit(HOOK[1], lambda z: lora(z, 650), 176, 940)
_hw = HOOK[0].split() + HOOK[1].split()
_hwg = LES.get("hook_weights") or [len(w_) for w_ in _hw]


def teaser(fr, t, b):
    """Birinchi kadrdayoq nima haqida ekani ko'rinadi: ustidan chizilgan xato gap."""
    s = items[0]["wrong"]
    f = pop(64, "Medium")
    w = f.getlength(s)
    lay = Image.new("RGBA", (int(w) + 190, 116), (0,) * 4)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 0, lay.width - 1, 115), radius=58, fill=WHITE, outline=(232, 224, 243), width=3)
    badge(lay, 62, 58, False)
    d.text((116, 58), s, font=f, fill=GREY, anchor="lm")
    d.line((108, 62, 108 + (w + 16) * ease((t - 0.35) / 0.3), 56), fill=RED, width=8)
    put(fr, lay, 540, 1010, t, -1, b)


def hook_scene(fr, t):
    b = WA[0]
    put(fr, pill(LES["pill"], fit(LES["pill"], pop, 36, 800), CORAL, BG, 32, 15, outline=CORAL), 540, 400, t, -1, b)
    t0, t1 = L["hook"]["start"], L["hook"]["end"]
    cur = max([k for k in range(len(_hw)) if t >= t0 + (t1 - t0) * sum(_hwg[:k]) / sum(_hwg)], default=-1) if t0 <= t < t1 else -1
    k = 0
    for line, f, cy, col in ((HOOK[0], HK1, 590, INK), (HOOK[1], HK2, 780, CORAL)):
        x = 540 - f.getlength(line) / 2
        for w_ in line.split():
            ww = f.getlength(w_)
            if k == cur and t < b - 0.1:
                ImageDraw.Draw(fr).rounded_rectangle((x - 14, cy - f.size * 0.42, x + ww + 14, cy + f.size * 0.5), radius=f.size * 0.16, fill=HL)
            x += ww + f.getlength(" ")
            k += 1
        put(fr, txt(line, f, col), 540, cy, t, -1, b)
    if t < b - 0.12:
        underline(fr, 540, 780 + HK2.size * 0.66, HK2.getlength(HOOK[1]) * 0.8, (t - 0.1) / 0.4)
    teaser(fr, t, b)


def render(i):
    t = i / FPS
    fr = BGIM.copy()
    teacher(fr, t)
    if t < WA[0]:
        hook_scene(fr, t)
    else:
        header(fr, t)
        for k in range(NI):
            if WA[k] <= t < WB[k]:
                item_scene(fr, t, k)
        if t >= t_end:
            end_scene(fr, t)
    return fr.convert("RGB")


def cover():
    """Muqova: muhim matn markazda (3:4 kesimda ham to'liq ko'rinadi)."""
    fr = BGIM.copy()
    teacher(fr, 0.0, "point")
    fr.alpha_composite(p := pill("KO'P QILINADIGAN XATOLAR", pop(38), CORAL, BG, 34, 16, outline=CORAL), (540 - p.width // 2, 380))
    ft = fit(LES["title"], lambda z: fra(z, 700), 150, 880)
    marker(fr, 540, 570, ft.getlength(LES["title"]) + 56, ft.size * 0.62, 1)
    fr.alpha_composite(tl := txt(LES["title"], ft, INK), (540 - tl.width // 2, 560 - tl.height // 2))
    f = pop(62, "Medium")
    for k, it in enumerate(items):
        y = 740 + k * 110
        w = f.getlength(it["wrong"])
        x0 = 540 - (w + 84) / 2
        badge(fr, x0 + 30, y + 2, False)
        ImageDraw.Draw(fr).text((x0 + 84, y), it["wrong"], font=f, fill=GREY, anchor="lm")
        ImageDraw.Draw(fr).line((x0 + 76, y + 4, x0 + 84 + w + 10, y - 2), fill=RED, width=8)
    return fr.convert("RGB")


if "sheet" in sys.argv:
    ts = [0.0, 1.2]
    for i in range(NI):
        ts += [L[f"uz{i}"]["start"] + 0.5, TW[i] + 0.4, TS_[i] + 0.5, L[f"en{i}"]["end"] + 0.6]
    ts += [t_end + 0.6, TOTAL - 0.3]
    sheet = Image.new("RGB", (270 * 9, 480 * 2), "white")
    for j, t in enumerate(ts):
        sheet.paste(render(int(t * FPS)).resize((270, 480), Image.LANCZOS), (270 * (j % 9), 480 * (j // 9)))
    sheet.paste(cover().resize((270, 480), Image.LANCZOS), (270 * 8, 480))
    sheet.save(f"{OUT}/sheet.jpg", quality=90)
else:
    mp4 = f"{OUT}/{ID}.mp4"
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
