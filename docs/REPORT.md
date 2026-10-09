# Hisobot — Reading Juice for Kids 1–4 (3-sinf)

Sana: 2026-10-09 (2-versiya: rasmiy javoblar kaliti, testlar va audio qo‘shildi)

## Yangi (2-versiya)

### 1. Rasmiy javoblar kaliti (AK) bilan solishtirildi
Google Drive’dagi to‘rtta Answer Key PDF har bir savol bo‘yicha avtomatik solishtirildi (`tools/ak_compare.py`).
**Natija: 0 ta farq.** Kalit bo‘yicha 4 ta javob tuzatildi (JR2 U12 C5, JR3 U2 C5, JR3 U4 C5, JR3 U10 C4 — yozma javoblarga kalitdagi shakllar qo‘shildi).

Ataylab kalitdan farq qiladigan joylar (matn bilan isbotlangan):

| Joy | Savol | Kalitda | Platformada | Sabab |
|---|---|---|---|---|
| JR1 U5 C4 | Frogs and toads look alike. | True | **False** | Matn: “Frogs and toads look different.” |
| JR2 U8 C5 | Winter Carnival celebrates fun and night. | True | **False** | Matn: “celebrates fun … celebrates winter”. |
| JR2 U12 C5 | Jackson Haines made a blade skate in 1865. | False | **True** | Matn: “put a blade on a boot in 1865”; nashriyotning Lv2 Mid-Term testi (8-savol) ham True. |
| JR2 U14 C5 | Scientists are trying to make clean cars. | False | **True** | Matn: “trying to make new cars to keep the air clean”. |
| JR3 U8 V3 | The water is ___ all day. | drips | **dripping** | Kitobdagi so‘zlar qutisida “dripping”; gap -ing talab qiladi. |

Qolgan 4 tasi PDF matn qatlamidagi texnik nuqson (apostrof, “9.4” rasmda) — javob bir xil.

### 2. Nashriyotning rasmiy testlari (8 ta)
Har kitobga Mid-Term (15 savol) va Final (20 savol) — jami 140 savol, avtomatik tekshiriladi.
Matnli savollarda matn savoldan oldin bir marta ko‘rsatiladi. Testlardagi matbaa xatolari tuzatildi
(sigh→sign, vocanoes→volcanoes, becojmes→becomes va b.); rasmiy javob qatoridagi 2 ta raqam xatosi ham tuzatildi.

### 3. Audio (nashriyot CD’si)
Har kitobda 33 trek: 01 — kirish, keyin har unit uchun ikkitadan: juft raqam — **yangi so‘zlar** (Get Ready, “listen and repeat”),
toq raqam — **matn**. Bu davomiylik va matn uzunligi korrelyatsiyasi bilan tasdiqlandi (r = 0.74–0.82).
- Platforma: o‘quvchi unitda ikkita pleer ko‘radi (matn va so‘zlar). So‘zlar audiosi qo‘yilmagan bo‘lsa, u pleer ko‘rinmaydi.
- O‘qituvchi zip faylni to‘g‘ridan-to‘g‘ri yuklaydi (ochish shart emas).
- Oflayn sahifalar: 128 trek nomlangan (8 ta `RJ_audio_kitob…zip`; ularni platformaga ham yuklash mumkin), brauzer testida 128/128 pleer ochildi.

### Tekshiruvlar
- `npm run all` (juice-reading): build, audit (DEFECTS 0), AK solishtirish (0 farq), 89 sahifa brauzer testi, 128 audio — hammasi o‘tdi.
- Platforma: yangi `test` turi va `library_import` huquq cheklovi jonli bazaga qo‘llandi (avval lokal PostgreSQL 16 da sinaldi).

---

## 1-versiya hisoboti

## Xulosa

- To‘rtta kitobning hammasi tayyor: **64 unit + 16 Vocabulary Check = 80 material, 992 savol**.
- Kitoblarda javoblar kaliti yo‘q. Shu sabab har bir javob matndan isbotlandi va qo‘lda ikkinchi marta tekshirildi (to‘rt kitobning hamma savoli, matn bilan yonma-yon).
- Avtomatik audit: `DEFECTS: 0` (KNOWN: 1 — pastda).
- Brauzer testi: 81 sahifa (80 material + bosh sahifa), telefon kengligida — konsolda xato yo‘q, rasmlar ochiladi, gorizontal scroll yo‘q. Kalit bo‘yicha javob berilganda 100%, bo‘sh qog‘ozda 0%.
- Platforma testlari: unit 78/78, brauzer (e2e) 69/69. Yangi Reading Juice oqimi alohida tekshirildi: o‘qituvchi audio yuklaydi → materialni qo‘shadi → topshiriq beradi → o‘quvchi telefonda rasm, audio, yangi so‘zlar, Get Ready va matnni ko‘radi → tanlov va yozma javoblarni server baholaydi (100%).
- SQL fayllar lokal PostgreSQL 16 da sinaldi: hammasi xatosiz yuklandi, qayta yuklash xavfsiz. Kirmagan foydalanuvchi rasmlarni ham olmaydi, o‘quvchi materialni Kutubxonadan qo‘sha olmaydi, javob kaliti kontentga tushmaydi (0 ta).

## Qanday tayyorlandi

1. **Ko‘chirish.** PDF’lar skan (matn qatlami yo‘q). Har bir kitob sahifama-sahifa ko‘chirildi, so‘ng Tesseract OCR bilan so‘zma-so‘z solishtirildi. 16×4 matnning hammasi OCR bilan mos (farqlar faqat OCR xatolari).
2. **Rasmlar.** Unit fotosurati (sarlavhasi bilan), rasmli savollarning variantlari (a/b/c izohlari bilan) va Vocabulary Check rasmlari avtomatik kesildi. 216 tasining hammasi kontakt-varaqda ko‘z bilan tekshirildi.
3. **Savollar.**
   - Check Comprehension: test (a/b yoki a/b/c), True/False, “Fill in the blanks” (3–4-kitoblar, qisqa yozma javob; katta-kichik harf va tinish belgisi hisobga olinmaydi, muqobil to‘g‘ri shakllar ham qabul qilinadi).
   - Build Vocabulary va Organize Information: kitobdagi so‘zlar qutisidan tanlash (3-sinf o‘quvchisi uchun yozishdan qulay). Organizerdagi ikki bo‘sh joyli qatorlar alohida savolga bo‘lingan.
   - Get Ready: ko‘p javobi fikr yoki oldingi bilimga tayanadi, shuning uchun **baholanmaydigan warm-up** sifatida ko‘rsatiladi.
   - Yangi so‘zlar: 338 so‘zning o‘zbekcha tarjimasi + glossariydagi inglizcha izoh.

## Kitobdagi matbaa xatolari (platformada to‘g‘ri shakl ko‘rsatiladi)

| Kitob / joy | Kitobda | Platformada |
|---|---|---|
| JR1 U15, Comprehension 3 varianti | lightening | lightning |
| JR2 U6, organizer sarlavhasi | Broadledf Trees | Broadleaf Trees |
| JR3 U3, Comprehension 1 varianti | the life a baby kangaroo | the life of a baby kangaroo |
| JR3 Vocabulary Check 2, savol 4 | big cheery candies | big cherry candies |
| JR4 U16, Build Vocabulary 3 va glossariy | Lightening | Lightning |

Boshqa kichik g‘alizliklar (masalan, JR1 U12 “Ash fills the air dark.”, JR4 U14 “Indians are ___ Americans.”) kitobdagidek qoldirildi: ular javobga ta’sir qilmaydi.

## O‘qituvchi e’tiboriga: munozarali savollar

Javob kitob muallifi niyatiga va matnga mos keladi, lekin o‘quvchi so‘rashi mumkin:

| Joy | Savol | Javob va sabab |
|---|---|---|
| JR1 U4 C5 | ALVIN can carry three people. | **True** — “two scientists and a pilot” (2 + 1). |
| JR1 U5 C1 | catching / studying frogs and toads | **studying** — matn ularni solishtiradi. |
| JR2 U10 C4 | After several years, the bones become fossils. | **False** — matnda “many years”. Farq nozik. |
| JR2 U12 C5 | Jackson Haines made a blade skate in 1865. | **True** — u tig‘ni etikka o‘rnatgan (rasmiy Mid-Term testi ham True). |
| JR3 U13 C4 | …but they are not the ___. | **same** — matn “they are not” bilan tugaydi (KNOWN). |
| JR3 U14 C3 | One plant can make at least eight potatoes. | **True** — matnda “more than eight”. |
| JR4 U4 C2 | What do astronauts need to grow vegetables? | **water** — “wet box”; quyosh emas, lampa. |
| JR4 U8 C3 | …almost 2,000,000 people… | **True** — matnda “more than 2 million” (kitobdagi g‘alizlik). |
| JR4 VC4 MC1 / MC3 | risk / wrap | “venture”, “close” ham ma’noli, lekin kitob niyati — risk, wrap. |

## Audio

- **Kutubxona → Reading Juice → “Audiolarni yuklash (zip yoki mp3)”**: nashriyot zip fayllarini yoki mp3’larni birdan tanlaysiz; kitob, unit va qism (matn/so‘zlar) fayl nomidan aniqlanadi, tekshirib yuklaysiz.
- Yoki har bir unit qatoridagi **“Audio yuklash”** tugmasi.
- Audio yopiq `juice-audio` bucket’da; o‘quvchi vaqtinchalik (3 soatlik) havola orqali eshitadi. Audio qo‘yilmagan unitda “Audio hali qo‘yilmagan” deb yoziladi, sahifa ishlayveradi.

## Tekshiruv doirasidan tashqari

O‘zbekcha tarjima uslubi (338 so‘z, qo‘lda), rasm kesimi didi, audio sifati.
