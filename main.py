"""
Donat do'koni: Telegram bot + Mini App serveri + API — hammasi bitta faylda.
Ishga tushirish:  python main.py
"""
import asyncio
import logging
import math
import re
import sys
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BufferedInputFile, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
    MenuButtonWebApp, Message, WebAppInfo,
)

import config
import db
from auth import check_init_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("shop")
BASE = Path(__file__).parent
dp = Dispatcher()
bot = None  # main() ichida yaratiladi

# ======================================================================
# Mijozga yuboriladigan xabarlar (tojik / rus)
# ======================================================================
BOT_T = {
    "tj": {
        "welcome": "Салом! 👋\nБарои харидани алмос ва бастаҳои бозиҳо тугмаи поёнро пахш кунед.",
        "open": "🎮 Кушодани мағоза",
        "order_done": "🎉 Фармоиши #{id} иҷро шуд!\n{game} — {title}\nЛутфан бозиро санҷед.",
        "order_cancel": "❌ Фармоиши #{id} бекор шуд. {price} сомонӣ ба баланси шумо баргашт.",
        "topup_ok": "✅ Баланси шумо {amount} сомонӣ пур шуд.",
        "topup_no": "❌ Пардохти шумо (#{id}) тасдиқ нашуд. Барои маълумот ба дастгирӣ нависед.",
        "ref_bonus": "🎁 Дӯсти шумо ҳисобро пур кард — ба шумо {amount} сомонӣ бонус дода шуд!",
    },
    "ru": {
        "welcome": "Привет! 👋\nЧтобы купить алмазы и пропуска для игр, нажмите кнопку ниже.",
        "open": "🎮 Открыть магазин",
        "order_done": "🎉 Заказ #{id} выполнен!\n{game} — {title}\nПроверьте игру.",
        "order_cancel": "❌ Заказ #{id} отменён. {price} сомонӣ возвращены на ваш баланс.",
        "topup_ok": "✅ Ваш баланс пополнен на {amount} сомонӣ.",
        "topup_no": "❌ Ваш платёж (#{id}) не подтверждён. Напишите в поддержку.",
        "ref_bonus": "🎁 Ваш друг пополнил баланс — вам начислен бонус {amount} сомонӣ!",
    },
}


def bt(lang, key, **kw):
    return BOT_T.get(lang, BOT_T["tj"])[key].format(**kw)


def app_button(lang):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=bt(lang, "open"), web_app=WebAppInfo(url=config.WEBAPP_URL))
    ]])


async def tell(uid, text):
    try:
        await bot.send_message(uid, text)
    except Exception as e:
        log.info("Foydalanuvchi %s ga yozib bo'lmadi: %s", uid, e)


async def send_admins(text, kb=None, photo=None):
    """Hamma adminlarga yuboradi. Rasm bo'lsa, birinchi yuborishdan file_id qaytaradi."""
    file_id = None
    for aid in config.ADMIN_IDS:
        try:
            if photo is not None:
                m = await bot.send_photo(aid, photo if file_id is None else file_id, caption=text, reply_markup=kb)
                if file_id is None:
                    file_id = m.photo[-1].file_id
            else:
                await bot.send_message(aid, text, reply_markup=kb)
        except Exception as e:
            log.warning("Adminga (%s) yuborib bo'lmadi: %s", aid, e)
    return file_id


def who(u):
    return f"{u['name']} (@{u['username']})" if u["username"] else u["name"]


# ======================================================================
# BOT: buyruqlar
# ======================================================================
@dp.message(CommandStart())
async def cmd_start(m: Message, command: CommandObject):
    ref = None
    if command.args and command.args.startswith("ref_") and command.args[4:].isdigit():
        ref = int(command.args[4:])
    u = db.upsert_user(m.from_user.id, m.from_user.full_name, m.from_user.username, ref)
    await m.answer(bt(u["lang"], "welcome"), reply_markup=app_button(u["lang"]))


admin_only = F.from_user.id.in_(config.ADMIN_IDS)


@dp.message(Command("stats"), admin_only)
async def cmd_stats(m: Message):
    s = db.stats()
    await m.answer(
        f"📊 Statistika\n👥 Foydalanuvchilar: {s['users']}\n💰 Mijozlar balansi: {s['balance']} somoni\n"
        f"⏳ Kutayotgan buyurtma: {s['orders_pending']}\n✅ Bajarilgan: {s['orders_done']}\n"
        f"🛒 Sotuv (bajarilgan): {s['sales']} somoni\n➕ Jami to'ldirilgan: {s['topups']} somoni")


@dp.message(Command("addcode"), admin_only)
async def cmd_addcode(m: Message, command: CommandObject):
    a = (command.args or "").split()
    if len(a) != 4 or a[0] not in ("balance", "discount") or not a[2].isdigit() or not a[3].isdigit():
        await m.answer("Format:\n/addcode balance KOD SUMMA SONI  (sovg'a kod: balansga pul)\n"
                       "/addcode discount KOD FOIZ SONI  (promo: chegirma %)\n\nMasalan: /addcode balance BONUS5 5 100")
        return
    db.add_code(a[0], a[1], int(a[2]), int(a[3]))
    await m.answer(f"✅ Kod yaratildi: {a[1].upper()} ({a[0]}, {a[2]}, {a[3]} marta)")


@dp.message(Command("addbalance"), admin_only)
async def cmd_addbalance(m: Message, command: CommandObject):
    a = (command.args or "").split()
    try:
        uid, amount = int(a[0]), int(a[1])
        new = db.add_balance(uid, amount)
    except (IndexError, ValueError):
        await m.answer("Format: /addbalance USER_ID SUMMA   (minus ham bo'ladi)")
        return
    await m.answer(f"✅ Yangi balans: {new} somoni")


@dp.message(Command("broadcast"), admin_only)
async def cmd_broadcast(m: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text:
        await m.answer("Format: /broadcast xabar matni")
        return
    ok = 0
    for uid in db.notify_user_ids():
        try:
            await bot.send_message(uid, text)
            ok += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)   # Telegram limitiga tushmaslik uchun
    await m.answer(f"✅ Yuborildi: {ok}")


@dp.message(Command("backup"), admin_only)
async def cmd_backup(m: Message):
    await m.answer_document(FSInputFile(config.DB_PATH, filename="shop-backup.db"))


@dp.message()
async def fallback(m: Message):
    u = db.upsert_user(m.from_user.id, m.from_user.full_name, m.from_user.username)
    await m.answer(bt(u["lang"], "welcome"), reply_markup=app_button(u["lang"]))


# ======================================================================
# BOT: admin tugmalari (to'lov va buyurtmani tasdiqlash)
# ======================================================================
async def _mark(call: CallbackQuery, status_text):
    base = call.message.caption if call.message.photo else call.message.text
    new = f"{base}\n\n{status_text} — {call.from_user.full_name}"
    if call.message.photo:
        await call.message.edit_caption(caption=new, reply_markup=None)
    else:
        await call.message.edit_text(new, reply_markup=None)


@dp.callback_query(F.data.regexp(r"^(tp|od)_(ok|no):\d+$"), admin_only)
async def admin_click(call: CallbackQuery):
    kind, rest = call.data.split("_")
    action, num = rest.split(":")
    num = int(num)

    if kind == "tp":   # balans to'ldirish
        if action == "ok":
            r = db.approve_topup(num)
            if not r:
                await call.answer("Bu allaqachon ko'rib chiqilgan", show_alert=True)
                return
            t = r["topup"]
            lang = db.get_user(t["user_id"])["lang"]
            await tell(t["user_id"], bt(lang, "topup_ok", amount=t["amount"]))
            if r["ref"]:
                rid, bonus = r["ref"]
                await tell(rid, bt(db.get_user(rid)["lang"], "ref_bonus", amount=bonus))
            await _mark(call, "✅ TASDIQLANDI")
        else:
            t = db.reject_topup(num)
            if not t:
                await call.answer("Bu allaqachon ko'rib chiqilgan", show_alert=True)
                return
            lang = db.get_user(t["user_id"])["lang"]
            await tell(t["user_id"], bt(lang, "topup_no", id=num))
            await _mark(call, "❌ RAD ETILDI")
    else:              # buyurtma
        o = db.set_order_status(num, "done" if action == "ok" else "canceled")
        if not o:
            await call.answer("Bu allaqachon ko'rib chiqilgan", show_alert=True)
            return
        lang = db.get_user(o["user_id"])["lang"]
        if action == "ok":
            await tell(o["user_id"], bt(lang, "order_done", id=num, game=o["game_name"], title=o["title"]))
            await _mark(call, "✅ BAJARILDI")
        else:
            await tell(o["user_id"], bt(lang, "order_cancel", id=num, price=o["price"]))
            await _mark(call, "❌ BEKOR QILINDI (pul qaytarildi)")
    await call.answer("Tayyor")


# ======================================================================
# WEB API (Mini App shu yerga murojaat qiladi)
# ======================================================================
def err(code, status=400):
    return web.json_response({"error": code}, status=status)


@web.middleware
async def api_middleware(request, handler):
    if not request.path.startswith("/api/"):
        return await handler(request)
    raw = request.headers.get("Authorization", "")
    tg_user = check_init_data(raw[4:] if raw.startswith("tma ") else "", config.BOT_TOKEN)
    if not tg_user:
        return err("auth", 401)
    name = " ".join(x for x in (tg_user.get("first_name"), tg_user.get("last_name")) if x) or "User"
    u = db.upsert_user(tg_user["id"], name, tg_user.get("username"))
    if u["banned"]:
        return err("banned", 403)
    request["uid"] = tg_user["id"]
    request["photo"] = tg_user.get("photo_url", "")
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception:
        log.exception("API xatosi: %s", request.path)
        return err("server", 500)


async def index(request):
    return web.FileResponse(BASE / "index.html", headers={"Cache-Control": "no-cache"})


async def health(request):
    return web.Response(text="ok")


async def api_catalog(request):
    return web.json_response({
        "games": config.GAMES,
        "payments": config.PAYMENT_METHODS,
        "cfg": {
            "support": config.SUPPORT_USERNAME, "reviews": config.REVIEWS_URL,
            "presets": config.TOPUP_PRESETS, "min": config.MIN_TOPUP, "max": config.MAX_TOPUP,
            "ref_percent": config.REF_PERCENT,
        },
    })


async def api_me(request):
    u = db.get_user(request["uid"])
    return web.json_response({
        "id": u["id"], "name": u["name"], "username": u["username"], "photo": request["photo"],
        "lang": u["lang"], "dark": bool(u["dark"]), "notify": bool(u["notify"]),
        "balance": u["balance"], "spent": u["spent"],
        "ref_link": f"https://t.me/{config.BOT_USERNAME}?start=ref_{u['id']}",
    })


async def api_settings(request):
    d = await request.json()
    db.set_settings(request["uid"], d.get("lang"), d.get("dark"), d.get("notify"))
    return web.json_response({"ok": True})


async def api_promo(request):
    d = await request.json()
    pct = db.promo_percent(request["uid"], d.get("code"))
    if pct is None:
        return err("promo")
    return web.json_response({"percent": pct})


async def api_redeem(request):
    d = await request.json()
    try:
        value = db.redeem_code(request["uid"], d.get("code"))
    except ValueError as e:
        return err(str(e))
    return web.json_response({"amount": value, "balance": db.get_user(request["uid"])["balance"]})


async def api_order(request):
    uid = request["uid"]
    d = await request.json()
    game = config.GAME_BY_ID.get(d.get("game"))
    if not game:
        return err("bad")
    cat, item = config.find_item(game, d.get("item"))
    if not item:
        return err("bad")
    pid = str(d.get("player_id", "")).strip()
    if not re.fullmatch(r"\d{4,15}", pid):
        return err("player_id")
    if game["need_zone"]:
        zone = str(d.get("zone", "")).strip()
        if not re.fullmatch(r"\d{2,6}", zone):
            return err("zone")
        pid = f"{pid} ({zone})"
    region = str(d.get("region", ""))
    if game["regions"]:
        if region not in [r["id"] for r in game["regions"]]:
            return err("region")
    else:
        region = ""
    try:
        o = db.create_order(uid, game, item, cat["emoji"], pid, region, d.get("promo") or None)
    except ValueError as e:
        return err(str(e))

    u = db.get_user(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"od_ok:{o['id']}"),
        InlineKeyboardButton(text="❌ Bekor (pul qaytadi)", callback_data=f"od_no:{o['id']}"),
    ]])
    await send_admins(
        f"🛒 Yangi buyurtma #{o['id']}\nMijoz: {who(u)}\nTelegram ID: {uid}\n\n"
        f"O'yin: {game['name']}" + (f" ({region})" if region else "") +
        f"\nPaket: {item['title']} {cat['emoji']}\nO'yinchi ID: {pid}\nNarx: {o['price']} somoni", kb)
    return web.json_response({"ok": True, "order_id": o["id"], "balance": o["balance"]})


async def api_orders(request):
    rows = db.get_orders(request["uid"], request.query.get("status"))
    return web.json_response([{
        "id": r["id"], "game": r["game_name"], "title": r["title"], "emoji": r["emoji"],
        "player_id": r["player_id"], "region": r["region"], "price": r["price"],
        "status": r["status"], "created": r["created"],
    } for r in rows])


async def api_tx(request):
    uid = request["uid"]
    out = [{"kind": "topup_pending", "amount": t["amount"], "note": f"#{t['id']}", "created": t["created"]}
           for t in db.pending_topups(uid)]
    out += [{"kind": r["kind"], "amount": r["amount"], "note": r["note"], "created": r["created"]}
            for r in db.get_tx(uid)]
    return web.json_response(out)


async def api_topup(request):
    uid = request["uid"]
    fields, blob = {}, bytearray()
    reader = await request.multipart()
    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == "file":
            while True:
                chunk = await part.read_chunk(65536)
                if not chunk:
                    break
                blob += chunk
                if len(blob) > 6 * 1024 * 1024:
                    return err("too_big")
        else:
            fields[part.name] = await part.text()

    method = config.PAY_BY_ID.get(fields.get("method"))
    try:
        amount = int(fields.get("amount", "0"))
    except ValueError:
        amount = 0
    if not method or not (config.MIN_TOPUP <= amount <= config.MAX_TOPUP):
        return err("bad")
    data = bytes(blob)
    if not (data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG")):
        return err("file")
    if db.count_pending_topups(uid) >= 5:
        return err("too_many")

    tid = db.create_topup(uid, method["id"], amount)
    u = db.get_user(uid)
    pay = amount if method["currency"] == "TJS" else math.ceil(amount / method["rate"])
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tp_ok:{tid}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tp_no:{tid}"),
    ]])
    caption = (f"💳 Balans to'ldirish #{tid}\nMijoz: {who(u)}\nTelegram ID: {uid}\n"
               f"Usul: {method['name']}\nSumma: {amount} somoni ({pay} {method['currency']})\n\n"
               f"Chekni tekshiring va tasdiqlang.")
    ext = "png" if data.startswith(b"\x89PNG") else "jpg"
    file_id = await send_admins(caption, kb, photo=BufferedInputFile(data, filename=f"receipt.{ext}"))
    if file_id:
        db.set_topup_file(tid, file_id)
    return web.json_response({"ok": True, "id": tid})


def make_app():
    app = web.Application(middlewares=[api_middleware], client_max_size=8 * 1024 * 1024)
    app.add_routes([
        web.get("/", index), web.get("/healthz", health),
        web.get("/api/catalog", api_catalog), web.get("/api/me", api_me),
        web.post("/api/settings", api_settings), web.post("/api/promo", api_promo),
        web.post("/api/redeem", api_redeem), web.post("/api/order", api_order),
        web.get("/api/orders", api_orders), web.get("/api/tx", api_tx),
        web.post("/api/topup", api_topup),
    ])
    img = BASE / "img"
    img.mkdir(exist_ok=True)
    app.router.add_static("/img", img)
    return app


# ======================================================================
# ISHGA TUSHIRISH
# ======================================================================
async def main():
    global bot
    if not config.BOT_TOKEN or not config.ADMIN_IDS or not config.WEBAPP_URL:
        sys.exit("XATO: BOT_TOKEN, ADMIN_IDS va WEBAPP_URL o'zgaruvchilari to'ldirilmagan (README ga qarang).")
    db.init()
    bot = Bot(config.BOT_TOKEN)
    config.BOT_USERNAME = (await bot.get_me()).username

    runner = web.AppRunner(make_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", config.PORT).start()
    log.info("Server %s portda ishga tushdi", config.PORT)

    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="🎮", web_app=WebAppInfo(url=config.WEBAPP_URL)))
    except Exception as e:
        log.warning("Menyu tugmasi o'rnatilmadi: %s", e)

    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
