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
npm run all                                   # testlar → build → audit → AK solishtirish → sahifalar → audio → brauzer testi
```

- `content/SCHEMA.md` — kitob JSON formati.
- `tools/build.py` — unitni platforma faoliyatiga aylantiradi: savollar, javob kaliti, rasm/audio havolalari; kitobdagi matbaa xatolarini tuzatadi (ro‘yxati `build/out/report.json` da).
- `tools/audit.py` — har savolning kaliti bor, indeks chegarada, takror variant yo‘q, yozma javob matnda bor, rasmlar mavjud, kalit bilan javob berilsa **100%**, bo‘sh qog‘oz **0%** (platforma serveri bilan bir xil qoida).
- `tools/site.py` — mustaqil sahifalar: har biri bitta HTML (rasmlar ichida), javobni brauzerda tekshiradi; audio `audio/jr1-u01.mp3` kabi nom bilan yonida tursa o‘ynaydi.
- `tools/tests_parse.py` — nashriyotning Mid-Term/Final testlari (.doc → `soffice --convert-to txt`, `build/tests/t1…t4.txt`) → `content/tests{1..4}.json`; har savolning javobi variantlar ichida ekanini tekshiradi.
- `tools/ak_compare.py` — javoblarni rasmiy Answer Key PDF bilan solishtiradi (`build/ak/ak1…ak4.pdf`); ataylab farqlar `KNOWN` ro‘yxatida, boshqa har farq — xato (exit 1).
- `tools/audio_pack.py` — nashriyot MP3 zip’lari (`build/audio/*.ZIP`) → `build/site/audio/jr1-u01.mp3` (matn) va `jr1-u01w.mp3` (so‘zlar). CD’da 01 — kirish, juft trek — so‘zlar, toq — matn.
- `tests/site.e2e.mjs` — 89 sahifa haqiqiy Chromium’da, 390 px telefon kengligida; audio paketi bo‘lsa, 128 pleer ochilishini ham tekshiradi.

Kitob, test va AK fayllari, audio repo’ga kirmaydi (`.gitignore`): mualliflik huquqi.

## Platformaga yuklash (Supabase `oiztlehwpmisjcykelsd`)

Sxema va funksiyalar loyihaga qo‘llangan (platforma repo’si: `20261006133339_juice_reading.sql`, `20261006133938_juice_reading_loader.sql`). Kontentni o‘qituvchining o‘zi yuklaydi — service kalit ham, SQL ham kerak emas:

1. **Bir marta:** Supabase → SQL Editor → platforma repo’sidagi `supabase/admin/juice_audio_bucket.sql` (audio uchun yopiq bucket).
2. Yangi `site/` Netlify’ga joylangan bo‘lsin (platforma README’si).
3. O‘qituvchi portali → **Kutubxona → Reading Juice → “Materiallar faylini yuklash”** → `build/out/juice-reading-bundle.json` (7 MB). 88 material (64 unit, 16 Vocabulary Check, 8 rasmiy test) va rasmlar partiyalab yuklanadi; qayta yuklash xavfsiz (yangilaydi).
4. **“Kitobni to‘liq qo‘shish”** → material topshiriqqa tayyor. **“Audiolarni yuklash (zip yoki mp3)”** — nashriyotning 5 ta MP3 zip’ini birdan tanlang; kitob, unit va qism (matn/so‘zlar) fayl nomidan aniqlanadi.

Muqobil yo‘l (SQL Editor): `build/out/sql/` dagi fayllar tartib bilan — `10_units_jr1…4.sql` → `20_media_*.sql` (platformaning `20261006192805_juice_reading_tests.sql` migratsiyasidan keyin).

Tekshiruv hisoboti: [`docs/REPORT.md`](docs/REPORT.md).
