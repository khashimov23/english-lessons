# English with Mubina — doimiy ish tartibi

2026-11-11 da tanlangan va tasdiqlangan standart. Har bir yangi dars shu tartibda tayyorlanadi.

## 1. Ovoz (doimiy)

Butun videoni **bitta ovoz** o'qiydi — o'zbekchani ham, inglizchani ham.

| Nima | Qanday |
|---|---|
| Ovoz namunasi | `voice_uz/ref/ovoz2.wav` (o'zbek ayol ovozi) |
| O'zbekcha gaplar | Navoiy TTS (`aisha-org/navoiy-tts`, CosyVoice2 asosida), ohang: **xursand** |
| Inglizcha gaplar | Kokoro (`af_heart`) to'g'ri talaffuz bilan o'qiydi → CosyVoice2 ovoz konvertatsiyasi bilan shu ovozga o'giriladi |
| Tekshiruv | Har bir bo'lak nutqni tanish modeli bilan matnga solishtiriladi |

Muhim qoidalar:

- **Kulgi muammosi.** "Xursand" ohangda model qisqa gap boshiga kulgi/"nah" qo'shadi. Shuning uchun har bir o'zbekcha gap oldiga `Assalomu alaykum, aziz o'quvchilar!` qo'shib chiqariladi va o'sha qism pauza joyidan kesib tashlanadi (`tools/3_kes_va_tekshir.py` buni o'zi qiladi).
- **Inglizchani o'zbekcha modelga to'g'ridan-to'g'ri o'qitmang** — talaffuz buziladi (sinab ko'rilgan).
- **Raqamlar so'z bilan yoziladi:** "2-dars" emas, "ikkinchi dars".
- **Apostrof oddiy `'`** bo'lsin (`o'`, `g'`).
- Har bir gap 2 variantda chiqariladi, tekshiruvdan yaxshi o'tgani olinadi.

Ovoz namunasi manbasi: Uzbek Speech Corpus (ISSAI), `murodbek/uzbek-speech-corpus`, CC-BY-4.0, yozuv `863397599_2_2262_2`.
Navoiy TTS — Apache-2.0, CosyVoice2 — Apache-2.0, Kokoro — Apache-2.0.

## 2. Video tuzilishi (`lesson_v2.py`)

Taxminan 35 soniya, 1080×1920, 30 kadr/s. 2026-11-11 da tasdiqlangan yakuniy ko'rinish.

Ekran uch qismdan iborat va butun video davomida o'zgarmaydi:

- **Tepada bo'lim belgisi:** "01 — HELLO", "02 — GOOD MORNING", …, "04 — MISOL", "05 — MASHQ" va o'ngda nuqtalar (dars qayerga kelgani ko'rinib turadi).
- **O'rtada mazmun:** ikki qatorli sarlavha (qalin qator + nilufar kursiv qator, tagida qo'lda chizilgandek chiziq) va uning ostida oq kartochka.
- **Pastda o'qituvchi:** katta rasm, lekin mazmunni siqmaydi (masshtab 0.62, bosh tepasi y≈1170). Sarlavha, belgi va kartochka bir-biriga yopishmasligi kerak.

Sahnalar:

1. **Hook (0–3 s):** "Inglizcha birinchi / 3 ta so'zingiz." — birinchi kadrdayoq to'liq ko'rinadi, aytilayotgan so'z ustida marker yuradi. Kirish so'zi, logotip yo'q. Va'da rost bo'lishi shart.
2. **Har bir so'z/ibora:** sarlavha — vaziyat va savol ("Ertalab ko'rishganda / nima deymiz?"); kartochkada inglizcha sekin → oddiy tezlikda → o'zbekchasi (marker bilan ochiladi).
3. **Misol:** "Endi gap ichida / eshitib ko'ring." — xabar ko'rinishida, so'zma-so'z belgilanadi → o'zbekchasi.
4. **Mashq:** to'q fonda "Endi sizning navbatingiz!" (so'zlar aytilgan paytda birma-bir chiqadi) → har so'z: Tinglang → Endi siz ayting (sanoq chizig'i) → Zo'r!
5. **Yakun:** "Unutmaslik uchun / saqlab qo'ying." + "Ertaga: N-dars · Mavzu" + `@englishwithmubina`.

Qoidalar:

- **Ovozsiz ham tushunarli:** aytilgan har bir narsa ekranda yozilgan.
- **Bo'sh pauza yo'q,** har 1–3 soniyada ekranda nimadir o'zgaradi.
- **Xavfsiz hudud:** muhim yozuv tepadan 250 px va pastdan 350 px ichiga tushmaydi; lentadagi 4:5 va profildagi 3:4 kesimda ham to'liq ko'rinadi.
- **Chaqiriq:** hozircha faqat "saqlab qo'ying". "Kommentga yozing" chaqirig'i yuboriladigan tayyor material bo'lgandagina qo'shiladi.
- Ovoz bo'laklari orasidagi pauzalar: sekin→oddiy 0.5 s, oddiy→o'zbekcha 0.4 s, keyingi so'zgacha 0.75 s, takrorlash uchun 2.0 s.

## 3. Brend ko'rinishi

| Element | Rang (RGB) |
|---|---|
| Fon | `251, 248, 254` — juda och binafsha-oq, daftar nuqtalari bilan |
| Yozuv | `38, 28, 74` — to'q siyohrang |
| Marker | `208, 180, 244` — nilufar (asosiy brend rangi) |
| Belgilar, handle | `124, 78, 200` — to'q binafsha |
| O'qituvchi orqasidagi shakl | `224, 204, 247` |
| "Zo'r!" belgisi | `38, 158, 108` — yashil |

Shriftlar: **Poppins** (qalin sarlavha qatori, inglizcha so'zlar, belgilar), **Lora Italic** (nilufar kursiv sarlavha qatori), **Fraunces** (o'zbekcha tarjima, "Endi sizning navbatingiz!"). Sariq rang ishlatilmaydi.

## 4. Dars fayli (`lessons/dars-NN.json`)

Eski maydonlarga qo'shimcha:

```json
"hook_big": ["Inglizcha birinchi", "3 ta so'zingiz."],
"hook_weights": [9, 8, 2, 3, 20],
"hook_say": "Inglizcha birinchi uchta so'zingizni o'rganamiz!",
"end_say": "Saqlab qo'ying! Ertaga ikkinchi dars: tanishish.",
"items": [{"en": "Hello", "tr": "helou", "uz": "Salom", "when": "Ko'rishganda"}]
```

- `hook_big` — ekrandagi sarlavha: birinchi qator qalin, ikkinchi qator nilufar kursiv.
- `hook_weights` — sarlavhadagi har bir so'z ovozda qancha vaqt olishi (marker shunga qarab yuradi); berilmasa, so'z uzunligidan olinadi.
- `when` — har bir so'z uchun vaziyat ("Ko'rishganda"); sarlavhaning birinchi qatori bo'ladi, ikkinchisi doim "nima deymiz?".
- `hook_say`, `end_say` — ovozda aytiladigan kirish va yakun.
- `caption` — birinchi jumlada kalit so'z ("0 dan ingliz tili, N-dars: …"), oxirida "saqlab qo'ying" va "do'stingizga yuboring".

## 5. Yangi darsni tayyorlash

Bir martalik tayyorgarlik (yangi muhitda): `./setup_v2.sh` — kutubxonalar va ovoz modellarini o'rnatadi (~8 GB, 10–20 daqiqa). Modellar `$TTS_ROOT` ga tushadi (sukut bo'yicha `~/tts`). Tarmoqda `github.com`, `pypi.org`, `huggingface.co` va `us.aws.cdn.hf.co` ochiq bo'lishi kerak.

Bitta dars:

```bash
tools/dars.sh NN          # masalan: tools/dars.sh 06  (GPU'siz mashinada ~12 daqiqa)
```

Bu buyruq `lessons/dars-NN.json` dan ovozni chiqaradi, tekshiradi va `videos/dars-NN/` ga video, muqova va izohni yozadi. Oxirgi qatorda `DARS_OK NN` chiqsa hammasi joyida; `DARS_XATO …` chiqsa videoni ishlatmang.

Ichida bajariladigan qadamlar (alohida ham ishga tushirsa bo'ladi):

| Qadam | Skript |
|---|---|
| O'zbekcha matnlar | `tools/0_matnlar.py` |
| Inglizcha bo'laklar (Kokoro) | `tools/1_kokoro_inglizcha.py` |
| Inglizchani shu ovozga o'girish + o'zbekchani chiqarish | `tools/2_ovoz_chiqar.py` |
| Kirish jumlasini kesish va o'zbekchani tekshirish | `tools/3_kes_va_tekshir.py` |
| Inglizchani tekshirish | `tools/4_inglizcha_tekshir.py` |
| Video, muqova, izoh | `lesson_v2.py` |

Ovoz bo'laklari `voice_uz/dars-NN/` da saqlanadi: `hook, slow0, norm0, uz0, …, example, exuz, turn, rep0, …, next` (`.wav`, 24 kHz). "Endi sizning navbatingiz!" har darsda bir xil — `voice_uz/ref/turn.wav` dan olinadi.

Tekshiruv natijasini har doim o'qing: `OK` qatorlarida matn va tanilgan nutq mos kelishi kerak. Inglizcha tekshiruvda bir bo'g'inli so'zlar ("I", "You") va "Mubina" ismi ko'pincha noto'g'ri taniladi — bu ma'lum holat, quloq bilan tekshiriladi.

Oldindan ko'rish: `videos/dars-NN/sheet.jpg`.

## 6. Instagram'ga joylash

- **Vaqt:** har kuni **18:30** (Toshkent vaqti), kuniga bitta dars, tartib bilan.
- **Turi:** Reel, lentada ham ko'rinadi.
- **Muqova:** `videos/dars-NN/cover.jpg`. Barcha darslarda tuzilishi bir xil: "0 DAN INGLIZ TILI" belgisi → "N-dars" → mavzu (nilufar marker bilan) → o'rganiladigan so'zlar (sig'masa 2–3 qatorga bo'linadi) → o'qituvchi. Joylagandan keyin o'zgartirib bo'lmaydi.
- **Izoh:** `videos/dars-NN/caption.txt` — birinchi jumlada "0 dan ingliz tili, N-dars: …", oxirida saqlash va do'stga yuborish chaqirig'i, 5 ta heshteg.
- **Sun'iy intellekt belgisi:** yoqiladi (ovoz sintetik).
- **Vosita:** Metricool, brend "English with Mubina" (`@englishwithmubina`). Video va muqova uchun ochiq havola kerak: fayllar GitHub'ga yuklangach, `https://raw.githubusercontent.com/khashimov23/english-lessons/<branch>/videos/dars-NN/…` havolasi beriladi.
- `state.json` da qaysi dars qachonga belgilangani yozib boriladi.
