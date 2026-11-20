#!/usr/bin/env python3
"""Videolarni to'g'ridan-to'g'ri Instagram (Reels) va YouTube (Shorts) ga joylaydi — Metricool'siz.

Jadval manbai: state.json dagi `scheduled` (darslar) va `xato_scheduled` (xato videolari).
Nima joylangani: published.json (har video, har tarmoq uchun alohida yoziladi).

Ishlatish:
  tools/publish.py list                 # jadval va holat (hech narsa joylamaydi)
  tools/publish.py check                # kalitlar ishlashini tekshiradi (hech narsa joylamaydi)
  tools/publish.py due                  # vaqti kelgan, hali joylanmagan videolarni joylaydi
  tools/publish.py one dars-13          # bitta videoni hozir joylaydi (vaqtiga qaramay)

Muhit o'zgaruvchilari (GitHub Actions secrets):
  IG_USER_ID, IG_ACCESS_TOKEN                          — Instagram
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN     — YouTube
  ONLY=instagram|youtube     faqat bitta tarmoq
  YT_PRIVACY=public|unlisted|private   (sukut: public; sinov uchun private)
  LOOKBACK_HOURS=6           vaqti shu soatdan ko'p o'tgan post o'tkazib yuboriladi
"""
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/khashimov23/english-lessons/main/"
IG = "https://graph.instagram.com/v25.0"
LOG = ROOT / "published.json"
NETWORKS = ("instagram", "youtube")
SECRETS = ("IG_ACCESS_TOKEN", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")


def clean(s):
    """Xato matnidan kalitlarni olib tashlaydi."""
    s = str(s)
    for k in SECRETS:
        v = os.environ.get(k)
        if v:
            s = s.replace(v, "***")
    return s


def http(url, data=None, headers=None, method=None, raw=False):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            body = r.read()
            if raw:
                return r, body
            return json.loads(body or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(clean(f"HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")) from None


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def items():
    """Jadvaldagi hamma videolar: [{id, when, video, cover, caption, title, tags}]"""
    st = load("state.json")
    titles = {c["lesson"]: c["title"] for c in load("curriculum.json")}
    out = []
    for n, when in st.get("scheduled", {}).items():
        i = f"dars-{int(n):02d}"
        out.append(dict(id=i, when=when, title=f"0 dan ingliz tili, {int(n)}-dars: {titles.get(int(n), '')}"[:100],
                        tags=["ingliz tili", "0 dan ingliz tili", "inglizcha", "english", "uzbekistan"]))
    for n, when in st.get("xato_scheduled", {}).items():
        i = f"xato-{int(n):02d}"
        spec = ROOT / "specials" / f"{i}.json"
        title = json.loads(spec.read_text(encoding="utf-8"))["yt_title"] if spec.exists() else i
        out.append(dict(id=i, when=when, title=title[:100],
                        tags=["ingliz tili", "inglizcha xatolar", "inglizcha", "english", "uzbekistan"]))
    for it in out:
        d = f"videos/{it['id']}/"
        it.update(video=d + f"{it['id']}.mp4", cover=d + "cover.jpg", caption=d + "caption.txt",
                  dt=datetime.datetime.fromisoformat(it["when"]))
    return sorted(out, key=lambda x: x["dt"])


def read_log():
    return json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}


def write_log(log):
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------- Instagram ----------
def ig_publish(it, caption):
    uid, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    base = dict(media_type="REELS", video_url=RAW + it["video"], cover_url=RAW + it["cover"],
                caption=caption, share_to_feed="true", access_token=tok)
    try:  # ovoz sintetik — sun'iy intellekt belgisi bilan
        c = http(f"{IG}/{uid}/media", dict(base, is_ai_generated="true"))
        ai = True
    except RuntimeError as e:
        print("  instagram: AI belgisi bilan qabul qilinmadi, belgisiz urinib ko'riladi:", e)
        c = http(f"{IG}/{uid}/media", base)
        ai = False
    cid = c["id"]
    for _ in range(40):  # ~10 daqiqagacha
        time.sleep(15)
        s = http(f"{IG}/{cid}?" + urllib.parse.urlencode(dict(fields="status_code,status", access_token=tok)))
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"konteyner {s.get('status_code')}: {s.get('status')}")
    else:
        raise RuntimeError("konteyner 10 daqiqada tayyor bo'lmadi")
    m = http(f"{IG}/{uid}/media_publish", dict(creation_id=cid, access_token=tok))
    info = dict(id=m["id"], ai_label=ai)
    try:
        p = http(f"{IG}/{m['id']}?" + urllib.parse.urlencode(dict(fields="permalink", access_token=tok)))
        info["url"] = p.get("permalink")
    except RuntimeError:
        pass
    return info


def ig_check():
    uid, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    me = http(f"{IG}/me?" + urllib.parse.urlencode(dict(fields="user_id,username,account_type", access_token=tok)))
    print("  instagram: @%s (%s), user_id=%s" % (me.get("username"), me.get("account_type"), me.get("user_id")))
    if str(me.get("user_id")) != str(uid):
        print("  DIQQAT: IG_USER_ID (%s) token egasiga (%s) mos emas" % (uid, me.get("user_id")))
    lim = http(f"{IG}/{uid}/content_publishing_limit?" + urllib.parse.urlencode(dict(fields="quota_usage,config", access_token=tok)))
    print("  instagram: 24 soatlik limit:", json.dumps(lim.get("data", lim)))


# ---------- YouTube ----------
def yt_token():
    t = http("https://oauth2.googleapis.com/token", dict(
        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
        refresh_token=os.environ["YT_REFRESH_TOKEN"], grant_type="refresh_token"))
    return t["access_token"], t.get("scope", "")


def yt_publish(it, caption):
    tok, _ = yt_token()
    privacy = os.environ.get("YT_PRIVACY") or "public"
    meta = dict(snippet=dict(title=it["title"], description=caption, tags=it["tags"], categoryId="27"),
                status=dict(privacyStatus=privacy, selfDeclaredMadeForKids=False, containsSyntheticMedia=True))
    video = (ROOT / it["video"]).read_bytes()
    auth = {"Authorization": "Bearer " + tok}
    r, _ = http("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                json.dumps(meta).encode(), dict(auth, **{"Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))}), raw=True)
    _, body = http(r.headers["Location"], video, dict(auth, **{"Content-Type": "video/mp4"}), method="PUT", raw=True)
    v = json.loads(body)
    got = v.get("status", {}).get("privacyStatus")
    info = dict(id=v["id"], url="https://youtube.com/shorts/" + v["id"], privacy=got)
    if got != privacy:
        print(f"  DIQQAT: youtube {privacy} so'ralgan edi, lekin video {got} bo'ldi")
    return info


def yt_check():
    _, scope = yt_token()
    print("  youtube: kalit ishlayapti, ruxsatlar:", scope)
    if "youtube.upload" not in scope and "auth/youtube " not in scope + " ":
        print("  DIQQAT: youtube.upload ruxsati yo'q — video yuklab bo'lmaydi")


PUB = dict(instagram=ig_publish, youtube=yt_publish)
CHK = dict(instagram=ig_check, youtube=yt_check)


NEED = dict(instagram=("IG_USER_ID", "IG_ACCESS_TOKEN"), youtube=("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def networks(configured=False):
    """Tanlangan tarmoqlar; configured=True bo'lsa faqat kaliti berilganlari."""
    only = (os.environ.get("ONLY") or "").strip().lower()
    nets = (only,) if only in NETWORKS else NETWORKS
    if configured:
        skip = [n for n in nets if not all(os.environ.get(k) for k in NEED[n])]
        for n in skip:
            print(f"{n}: kalitlar berilmagan — o'tkazib yuborildi")
        nets = tuple(n for n in nets if n not in skip)
    return nets


def publish(todo, nets):
    log, failed = read_log(), []
    for it in todo:
        for f in (it["video"], it["cover"], it["caption"]):
            if not (ROOT / f).exists():
                print(f"XATO {it['id']}: fayl yo'q: {f}")
                failed.append(it["id"])
                break
        else:
            caption = (ROOT / it["caption"]).read_text(encoding="utf-8").rstrip("\n")
            for net in nets:
                if log.get(it["id"], {}).get(net):
                    continue
                print(f"{it['id']} -> {net} ...")
                try:
                    info = PUB[net](it, caption)
                except Exception as e:  # bitta tarmoq xatosi ikkinchisini to'xtatmaydi
                    print(f"XATO {it['id']} {net}: {clean(e)}")
                    failed.append(f"{it['id']}/{net}")
                    continue
                info["at"] = datetime.datetime.now(it["dt"].tzinfo).isoformat(timespec="seconds")
                log.setdefault(it["id"], {})[net] = info
                write_log(log)  # har muvaffaqiyatdan keyin darhol yoziladi
                print(f"OK {it['id']} {net}: {info.get('url') or info['id']}")
    return failed


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    its, log = items(), read_log()
    if mode == "list":
        for it in its:
            done = ",".join(n for n in NETWORKS if log.get(it["id"], {}).get(n)) or "-"
            print(it["when"], it["id"], "| joylangan:", done, "|", it["title"])
        return 0
    if mode == "check":
        bad = 0
        for net in networks():
            try:
                CHK[net]()
            except KeyError as e:
                print(f"  {net}: kalit berilmagan: {e}")
                bad = 1
            except Exception as e:
                print(f"  {net}: XATO: {clean(e)}")
                bad = 1
        print("CHECK_XATO" if bad else "CHECK_OK")
        return bad
    nets = networks(configured=True)
    if not nets:
        print("Hech bir tarmoq uchun kalit yo'q — hech narsa joylanmadi.")
        return 0 if mode == "due" else 1
    if mode == "due":
        back = datetime.timedelta(hours=float(os.environ.get("LOOKBACK_HOURS") or 6))
        todo = [it for it in its if it["dt"] <= now() <= it["dt"] + back
                and any(not log.get(it["id"], {}).get(n) for n in nets)]
        if not todo:
            print("Hozir joylanadigan video yo'q.")
            return 0
    elif mode == "one":
        todo = [it for it in its if it["id"] == sys.argv[2]]
        if not todo:
            print("Jadvalda bunday video yo'q:", sys.argv[2])
            return 1
    else:
        print(__doc__)
        return 1
    failed = publish(todo, nets)
    print("PUBLISH_XATO " + " ".join(failed) if failed else "PUBLISH_OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
