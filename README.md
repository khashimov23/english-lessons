# english-lessons

`@englishwithmubina` Instagram akkaunti uchun "0 dan ingliz tili" kunlik dars videolari. Har video 30–35 soniya, 1080×1920, to'liq bepul vositalar bilan yig'iladi (Python, ffmpeg, Kokoro ovozi). O'qituvchi Mubina sun'iy intellekt yordamida yaratilgan personaj.

## Tuzilishi

| Yo'l | Nima |
|---|---|
| `lesson.py` | Video yig'uvchi shablon: `python3 lesson.py lessons/dars-NN.json` |
| `music.py` | Fon musiqasi (sintez), uslub `config.json` da |
| `config.json` | Akkaunt nomi, o'qituvchi ismi, musiqa, Metricool brendi, joylash vaqti |
| `curriculum.json` | 30 darslik reja: raqam, mavzu, o'rgatiladigan narsa |
| `lessons/dars-NN.json` | Bitta darsning "retsepti" (pastdagi sxema) |
| `assets/poses/` | O'qituvchining 7 ta kesib olingan pozasi va tekislash ma'lumoti |
| `fonts/` | Poppins va Lora (ochiq litsenziya) |
| `videos/dars-NN/` | Tayyor natija: `dars-NN.mp4`, `cover.jpg`, `caption.txt`, `video.json` |
| `state.json` | Oxirgi yig'ilgan va oxirgi joylangan dars raqami |

## Yangi dars yig'ish

```bash
./setup.sh                                   # bir marta: kutubxonalar va ovoz modeli
python3 lesson.py lessons/dars-02.json       # videos/dars-02/ paydo bo'ladi
```

## Dars fayli sxemasi

```json
{
  "lesson": 2,
  "title": "Tanishish",
  "hook": ["Inglizcha qanday", "tanishamiz?"],
  "hook_voice": "Lesson two. Introductions.",
  "items": [
    {"en": "What's your name?", "tr": "vots yor neym", "uz": "Ismingiz nima?"}
  ],
  "example": {"en": "Hi! My name is Mubina.", "uz": "Salom! Mening ismim Mubina."},
  "next": "3-dars: Hol-ahvol",
  "caption": "..."
}
```

Qoidalar:

- `items`: ko'pi bilan 3 ta so'z yoki ibora. Mavzu sig'masa, ikki darsga bo'linadi.
- `tr`: o'qilishi lotin harflarida, o'zbek o'quvchi o'qiy oladigan qilib (`hello` → `helou`).
- `uz`: qisqa tarjima. Qavs ichidagi izoh kartochkada ko'rsatilmaydi.
- `hook`: ikki qatorli savol, har qatori 16 belgidan oshmasin.
- `hook_voice` va `example.en`: faqat inglizcha, ovoz shularni o'qiydi.
- `caption`: dars raqami va mavzu, so'zlar tarjimasi bilan, keyingi dars, 4–5 ta hashtag.
- Har dars mustaqil tushunarli bo'lsin: tomoshabin oldingi darsni ko'rmagan bo'lishi mumkin.

## Joylash

1. Video va muqova `main` tarmog'iga yuklanadi. Ochiq havola:
   `https://raw.githubusercontent.com/khashimov23/english-lessons/main/videos/dars-NN/dars-NN.mp4`
2. Metricool orqali rejalashtiriladi: Instagram `REEL`, matn `caption.txt` dan so'zma-so'z, muqova `cover.jpg`, `isAiGenerated: true`.
3. `state.json` yangilanadi.

Joylashdan oldin tekshiriladi: video davomiyligi 25–45 soniya, kadrlar jadvalida (`python3 lesson.py ... sheet`) matn kesilmagan, ovoz darajasi −16…−19 LUFS.
