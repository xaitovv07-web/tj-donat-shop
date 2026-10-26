# Donat do'koni — Telegram Mini App (tojik/rus tilida), 24/7

Mijoz botga kiradi → o'yinni tanlaydi → ID kiritadi → paket tanlaydi → balansdan to'laydi.
Balansni to'ldirish: mijoz to'lov usulini tanlaydi, pul o'tkazadi, **chek rasmini** yuklaydi → sizga Telegramda keladi → **✅ Tasdiqlash** bossangiz balansga tushadi.
Buyurtma kelganda sizga xabar keladi → donatni o'zingiz tashlaysiz → **✅ Bajarildi** bosasiz → mijozga xabar ketadi.

## Fayllar (hammasi bitta papkada, papkasiz)

| Fayl | Nima uchun |
|---|---|
| `main.py` | Bot + server + API |
| `config.py` | **O'yinlar, narxlar, to'lov kartalari** (asosan shuni o'zgartirasiz) |
| `db.py` | Ma'lumotlar bazasi (balans, buyurtmalar) |
| `auth.py` | Soxta so'rovlardan himoya |
| `index.html` | Mini App ko'rinishi |
| `requirements.txt`, `Procfile` | Server uchun kerak, tegmang |

---

## 1-QADAM. Bot yaratish (Telegramda, 3 daqiqa)

1. Telegramda **@BotFather** ni oching → `/newbot`.
2. Bot nomini yozing (masalan: `My Donat`), keyin username (oxiri `bot` bilan tugaydi, masalan `mydonat_bot`).
3. BotFather **token** beradi (`123456:ABC-...`). Nusxalab, xavfsiz joyga saqlang. **Hech kimga bermang.**
4. **@userinfobot** ga `/start` yozing → sizning **ID** raqamingizni ko'rsatadi. Saqlang (bu admin ID).
5. O'zingizning **username**ingiz kerak (Telegram → Sozlamalar → Username). Mijozlar yordam uchun shunga yozadi.

## 2-QADAM. Kodni GitHub ga qo'yish (telefon brauzerida)

Server kodni GitHub dan oladi, shuning uchun avval u yerga qo'yamiz.

1. Brauzerda **github.com** → Sign up (bepul akkaunt oching).
2. Tepada **+** → **New repository**. Nomi: `donat-shop`. **Private** ni tanlang (kodingiz ochiq bo'lmasin) → **Create repository**.
3. Ochilgan sahifada **uploading an existing file** havolasini bosing.
4. Bu chatdagi 8 ta faylni telefoningizga yuklab oling (fayl kartalarini bosib) va GitHub ga **hammasini birga** tanlab yuklang.
5. Pastda **Commit changes** ni bosing.

> Fayllar repo'ning **asosiy joyida** turishi kerak (`main.py` ochilganda yo'lida papka bo'lmasin).

## 3-QADAM. Serverga joylash (Railway) — 24/7 ishlashi uchun

1. **railway.app** → **Login with GitHub**.
2. **New Project → Deploy from GitHub repo** → `donat-shop` ni tanlang. Railway o'zi Python ekanini topadi.
3. Loyiha ichida servisni bosing → **Variables** bo'limi → shularni qo'shing:

| Nomi | Qiymati |
|---|---|
| `BOT_TOKEN` | 1-qadamdagi token |
| `ADMIN_IDS` | Sizning ID (bir nechta admin bo'lsa vergul bilan: `111,222`) |
| `SUPPORT_USERNAME` | Sizning username (@ siz) |
| `DB_PATH` | `/data/shop.db` |

4. **Settings → Networking → Generate Domain**. Sizga `https://xxxx.up.railway.app` manzil beradi. Uni nusxalang.
5. **Variables** ga yana bitta qo'shing: `WEBAPP_URL` = shu manzil (**oxirida `/` siz**).
6. **Muhim — Volume:** servis ichida **Volumes** (yoki Ctrl+K → "Volume") → yangi Volume yarating, **Mount path:** `/data`.
   Buni qilmasangiz, har safar yangilanganda **balanslar va buyurtmalar o'chib ketadi!**
7. Servis o'zi qayta ishga tushadi. **Deployments → Logs** da `Server ... portda ishga tushdi` yozuvini ko'rsangiz — tayyor.

> Railway interfeysi va narxlari o'zgarib turadi. Odatda sinov krediti beriladi, keyin oyiga taxminan 5$ atrofida to'lanadi — hozirgi narxni saytdan tekshiring. Bepul xizmatlarning ko'pi "uxlab qoladi" va 24/7 ishlamaydi.

## 4-QADAM. Sinab ko'rish

1. Botingizga `/start` yozing → **🎮 Кушодани мағоза** tugmasi chiqadi.
2. Mini App ochiladi. **Профил → Пур кардани ҳисоб** → summa → usul → chek rasmini yuklang.
3. Sizga (admin) chek keladi → **✅ Tasdiqlash** → mijoz balansi to'ladi.
4. Endi o'yin tanlab xarid qiling → sizga buyurtma keladi → **✅ Bajarildi**.

Yordam matni: `/start` ni boshqa akkauntdan ham sinab ko'ring (mijoz ko'zi bilan).

## 5-QADAM. O'yin, narx, karta o'zgartirish

1. GitHub → repo → `config.py` → ✏️ (Edit) belgisi.
2. **`PAYMENT_METHODS`** — o'zingizning karta/telefon raqamlaringizni yozing (hozir `0000...` namuna).
3. **`GAMES`** — narxlar `_items("ffd", [(110, 10), ...])` ko'rinishida: `(miqdor, narx somoni'da)`.
4. Yangi o'yin qo'shish uchun mavjud o'yin blokini nusxalab, `id` va nomini o'zgartiring. `id` takrorlanmasin.
5. **Commit changes** → Railway 1–2 daqiqada o'zi yangilaydi.

**O'yin rasmi:** `img` maydoniga to'g'ridan-to'g'ri havola yozing: `"img": "https://.../ff.jpg"`. Rasmni o'zingiz yaratgan yoki ruxsati bor manbadan oling (o'yin logotiplari mualliflik huquqi bilan himoyalangan bo'lishi mumkin).

## Admin buyruqlari (faqat siz uchun, botda yozasiz)

- `/stats` — foydalanuvchilar, sotuv, kutayotgan buyurtmalar
- `/addcode balance BONUS5 5 100` — **sovg'a kod**: kiritgan odam balansiga 5 somoni oladi, 100 kishi ishlata oladi (Gift Code bo'limida)
- `/addcode discount SALE10 10 50` — **promo**: xaridda 10% chegirma, 50 marta (har kishi 1 marta)
- `/addbalance 123456789 20` — foydalanuvchiga qo'lda 20 somoni qo'shish (minus ham bo'ladi)
- `/broadcast matn` — hammaga xabar (Огоҳиҳо'ni o'chirmaganlarga)
- `/backup` — bazani fayl qilib yuboradi. **Haftada bir marta oling.**

## Muhim eslatmalar

- **Chekni o'zingiz tekshiring.** Tasdiqlashdan oldin pul haqiqatan kartaga tushganini bankdan ko'ring. Soxta cheklar bo'lishi mumkin.
- **Donatni qo'lda tashlaysiz.** Avtomatik yetkazish uchun donat yetkazuvchi (distribyutor)ning rasmiy API'si kerak — u bilan shartnoma va uning hujjatlari asosida qo'shiladi.
- **«Санҷидан» tugmasi** hozircha faqat ID formatini (raqamlar soni) tekshiradi. O'yinchi nomini ko'rsatish uchun ham tashqi API kerak.
- **Referal:** do'st havola orqali kirib, birinchi marta balans to'ldirsa, taklif qilgan odam `config.py` dagi `REF_PERCENT` (3%) bonus oladi.
- **Balans faqat butun somoni.** Kasr yo'q.
- O'yin nashriyotlarining qoidalari va sizning mamlakatingizdagi savdo/soliq talablariga rioya qilish o'zingiz uchun muhim — bu kod yuridik maslahat emas.

## Muammolar bo'lsa

| Belgi | Sabab / yechim |
|---|---|
| Mini App «Барномаро тавассути бот кушоед» deydi | Uni brauzerdan emas, bot ichidagi tugma orqali oching |
| Bot javob bermaydi | Railway → Logs ni oching. `XATO: ... to'ldirilmagan` bo'lsa — Variables (BOT_TOKEN, ADMIN_IDS, WEBAPP_URL) ni tekshiring |
| `Conflict: terminated by other getUpdates` | Bot ikki joyda ishlayapti (masalan kompyuterda ham). Bittasini o'chiring |
| Mini App ochilmaydi, oq ekran | `WEBAPP_URL` oxirida `/` bo'lmasin va `https://` bilan boshlansin |
| O'zgartirish ko'rinmaydi | Railway yangilanishini kuting (1–2 daq), Mini App'ni yopib qayta oching |
| Balanslar yo'qoldi | Volume (`/data`) ulanmagan yoki `DB_PATH` xato edi — 3-qadamning 6-bandi |

## VPS'da ishlatmoqchi bo'lsangiz (Railway o'rniga)

Arzon Ubuntu VPS oling, domenni unga yo'naltiring va HTTPS qo'ying (Caddy eng oson), keyin:
```
pip install -r requirements.txt
export BOT_TOKEN=... ADMIN_IDS=... WEBAPP_URL=https://domen.uz SUPPORT_USERNAME=... PORT=8080
python main.py
```
va `systemd` bilan doimiy ishlatib qo'ying. Buni telefon orqali qilish qiyin, shuning uchun boshlovchiga Railway yo'li tavsiya etiladi.
