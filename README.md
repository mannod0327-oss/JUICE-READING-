# Reading Juice for Kids 1–4 — 3-sinf uchun reading materiallari

To‘rtta kitob (Reading Juice for Kids 1, 2, 3, 4) → Turbo English platformasidagi **Kutubxona → Reading Juice** bo‘limi va mustaqil (oflayn) unit sahifalari.

| Kitob | Unit | Vocabulary Check | Savollar | Rasm |
|---|---:|---:|---:|---:|
| Reading Juice 1 | 16 | 4 | 224 | 60 |
| Reading Juice 2 | 16 | 4 | 224 | 60 |
| Reading Juice 3 | 16 | 4 | 272 | 48 |
| Reading Juice 4 | 16 | 4 | 272 | 48 |
| **Jami** | **64** | **16** | **992** | **216** (64 ta unit rasmi + 152 ta savol rasmi) |

Har bir unit: kitobdagi rasm · audio (Telegram kanaldagi yozuv) · yangi so‘zlar (o‘zbekcha tarjima va inglizcha izoh bilan) · Get Ready (baholanmaydigan warm-up) · matn · Check Comprehension · Build Vocabulary · Organize Information. Hamma savol avtomatik tekshiriladi (928 ta tanlov, 64 ta qisqa yozma javob). Har 4 unitdan keyin — Vocabulary Check testi.

> **Mualliflik huquqi.** Bu repo **ochiq (public)**, shuning uchun kitob matni, skan sahifalar, kesilgan rasmlar va ulardan yasalgan fayllar git’ga **kirmaydi** (`.gitignore`). Ular Supabase bazasida (faqat login bilan) va o‘qituvchiga berilgan zip arxivda saqlanadi. Repoda faqat skriptlar, testlar, sxema va o‘zbekcha so‘z tarjimalari bor.

## Qanday ishlaydi

```
PDF (4 ta, skan)  ──pdftoppm──▶ build/pages/       ──tools/extract_media.py──▶ build/media/*.jpg
   │                                                                              │
   └─ qo‘lda + OCR bilan ko‘chirish ─▶ content/book{1..4}.json  ──tools/build.py──┴─▶ build/out/units/*.json
                                       content/uz.json (tarjimalar)                    build/out/sql/*.sql
                                                                   tools/audit.py ──▶ DEFECTS: 0
                                                                   tools/site.py  ──▶ build/site/*.html
                                                                   tests/site.e2e.mjs (Chromium)
```

```bash
npm install                                   # playwright (testlar uchun)
JR_PDF_DIR=~/Downloads npm run media          # sahifalarni rasmga aylantirish + rasmlarni kesish
npm run all                                   # build → audit → standalone sahifalar → brauzer testi
```

- `content/SCHEMA.md` — kitob JSON formati.
- `tools/build.py` — unitni platforma faoliyatiga aylantiradi: savollar, javob kaliti, rasm/audio havolalari; kitobdagi matbaa xatolarini tuzatadi (ro‘yxati `build/out/report.json` da).
- `tools/audit.py` — har savolning kaliti bor, indeks chegarada, takror variant yo‘q, yozma javob matnda bor, rasmlar mavjud, kalit bilan javob berilsa **100%**, bo‘sh qog‘oz **0%** (platforma serveri bilan bir xil qoida).
- `tools/site.py` — mustaqil sahifalar: har biri bitta HTML (rasmlar ichida), javobni brauzerda tekshiradi; audio `audio/jr1-u01.mp3` kabi nom bilan yonida tursa o‘ynaydi.
- `tests/site.e2e.mjs` — 81 sahifa haqiqiy Chromium’da, 390 px telefon kengligida.

## Platformaga yuklash (Supabase `oiztlehwpmisjcykelsd`)

Sxema va funksiyalar loyihaga qo‘llangan (platforma repo’si: `20261006133339_juice_reading.sql`, `20261006133938_juice_reading_loader.sql`). Kontentni o‘qituvchining o‘zi yuklaydi — service kalit ham, SQL ham kerak emas:

1. **Bir marta:** Supabase → SQL Editor → platforma repo’sidagi `supabase/admin/juice_audio_bucket.sql` (audio uchun yopiq bucket).
2. Yangi `site/` Netlify’ga joylangan bo‘lsin (platforma README’si).
3. O‘qituvchi portali → **Kutubxona → Reading Juice → “Materiallar faylini yuklash”** → `build/out/juice-reading-bundle.json` (7 MB). 80 material va 216 rasm partiyalab yuklanadi; qayta yuklash xavfsiz (yangilaydi).
4. **“Kitobni to‘liq qo‘shish”** → material topshiriqqa tayyor. **“Audiolarni yuklash”** — Telegram’dagi yozuvlar (unit raqami fayl nomidan aniqlanadi).

Muqobil yo‘l (SQL Editor): `build/out/load/` dagi fayllar tartib bilan — `01` → `02_units.sql` → `03_media_01…09.sql` → `99_check.sql` (kutilgan natija: `80 | 992 | 216 | 1:20 2:20 3:20 4:20 | 0 | 80`).

Tekshiruv hisoboti: [`docs/REPORT.md`](docs/REPORT.md).
