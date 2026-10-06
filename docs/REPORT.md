# Hisobot — Reading Juice for Kids 1–4 (3-sinf)

Sana: 2026-10-06

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
| JR2 U12 C5 | Jackson Haines made a blade skate in 1865. | **True** — u tig‘ni etikka o‘rnatgan. |
| JR3 U13 C4 | …but they are not the ___. | **same** — matn “they are not” bilan tugaydi (KNOWN). |
| JR3 U14 C3 | One plant can make at least eight potatoes. | **True** — matnda “more than eight”. |
| JR4 U4 C2 | What do astronauts need to grow vegetables? | **water** — “wet box”; quyosh emas, lampa. |
| JR4 U8 C3 | …almost 2,000,000 people… | **True** — matnda “more than 2 million” (kitobdagi g‘alizlik). |
| JR4 VC4 MC1 / MC3 | risk / wrap | “venture”, “close” ham ma’noli, lekin kitob niyati — risk, wrap. |

## Audio

Audio Telegram kanalda (“Juice Reading 1, 2, 3, 4”). Bu muhitdan Telegram’ga ulanib bo‘lmaydi, shuning uchun audio yuklash o‘qituvchi portaliga qo‘shildi:

- **Kutubxona → Reading Juice → “Audiolarni yuklash (bir nechta fayl)”**: bir kitobning hamma fayllarini birdan tanlaysiz; unit raqami fayl nomidan aniqlanadi (`Unit 07.mp3`, `Track 12.mp3`…), tekshirib yuklaysiz.
- Yoki har bir unit qatoridagi **“Audio yuklash”** tugmasi.
- Audio yopiq `juice-audio` bucket’da; o‘quvchi vaqtinchalik (3 soatlik) havola orqali eshitadi. Audio qo‘yilmagan unitda “Audio hali qo‘yilmagan” deb yoziladi, sahifa ishlayveradi.

## Tekshiruv doirasidan tashqari

O‘zbekcha tarjima uslubi (338 so‘z, qo‘lda), rasm kesimi didi, audio sifati.
