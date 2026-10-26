"""
SOZLAMALAR — do'kon shu fayldan boshqariladi.
Maxfiy narsalar (token, admin ID) bu yerga emas, Railway/VPS "Variables" ga yoziladi.
O'yin, narx va to'lov kartalarini shu faylda o'zgartirasiz.
"""
import os

# ---------- Maxfiy sozlamalar (muhit o'zgaruvchilaridan olinadi) ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.strip().isdigit()]
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")          # https://sizning-domen.up.railway.app
DB_PATH = os.getenv("DB_PATH", "shop.db")                     # Railway'da: /data/shop.db
PORT = int(os.getenv("PORT", "8080"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "admin").lstrip("@")   # yordam uchun admin username
REVIEWS_URL = os.getenv("REVIEWS_URL", "")                    # sharhlar kanali (ixtiyoriy)

BOT_USERNAME = ""   # bot ishga tushganda o'zi to'ldiriladi

# ---------- Umumiy qoidalar ----------
REF_PERCENT = 3                        # do'st birinchi marta balans to'ldirsa, taklif qilgan odamga % bonus
MIN_TOPUP = 5                          # eng kam to'ldirish (somoni)
MAX_TOPUP = 5000
TOPUP_PRESETS = [10, 20, 50, 100, 200, 500]

# ---------- To'lov usullari ----------
# kind: "phone" yoki "card"
# currency: "TJS" yoki boshqa valyuta; rate: 1 birlik valyuta = necha somoni (TJS uchun 1)
PAYMENT_METHODS = [
    {"id": "dcnext",  "name": "DC Next",       "kind": "phone", "number": "+992 000 00 00 00",
     "holder": "Ism F.", "currency": "TJS", "rate": 1},
    {"id": "dccard",  "name": "Dushanbe City", "kind": "card",  "number": "0000 0000 0000 0000",
     "holder": "Ism F.", "currency": "TJS", "rate": 1},
    {"id": "alif",    "name": "Alif",          "kind": "card",  "number": "0000 0000 0000 0000",
     "holder": "Ism F.", "currency": "TJS", "rate": 1},
    {"id": "tbank",   "name": "T-Банк",        "kind": "phone", "number": "+7 000 000 00 00",
     "holder": "Ism F.", "currency": "RUB", "rate": 0.11},   # 1 ₽ = 0.11 somoni
]


# ---------- O'yinlar ----------
def _items(prefix, pairs):
    """[(miqdor, narx), ...] -> paketlar ro'yxati. Narx somoni'da (butun son)."""
    return [{"id": f"{prefix}{a}", "title": str(a), "price": p} for a, p in pairs]


GAMES = [
    {
        "id": "pubg", "name": "PUBG Mobile", "badge": "GLOBAL", "subtitle": "UC",
        "img": "",                         # masalan "/img/pubg.png" (rasmni img papkasiga qo'ying)
        "colors": ["#f59e0b", "#7c2d12"],
        "regions": [], "need_zone": False,
        "categories": [
            {"id": "uc", "emoji": "💎", "title": {"tj": "UC", "ru": "UC"},
             "items": _items("uc", [(60, 12), (325, 60), (660, 120), (1800, 300)])},
        ],
    },
    {
        "id": "ff", "name": "Free Fire", "badge": "TOP", "subtitle": "Diamonds & Pass",
        "img": "", "colors": ["#ef4444", "#7f1d1d"],
        "regions": [
            {"id": "GLOBAL", "flag": "🌐"}, {"id": "CIS", "flag": "🇷🇺"}, {"id": "ID", "flag": "🇮🇩"},
            {"id": "BR", "flag": "🇧🇷"}, {"id": "MENA", "flag": "🇦🇪"},
        ],
        "need_zone": False,
        "categories": [
            {"id": "dia", "emoji": "💎", "title": {"tj": "Алмосҳо", "ru": "Алмазы"},
             "items": _items("ffd", [(110, 10), (341, 28), (572, 45), (1166, 90), (2398, 179), (6160, 454)])},
            {"id": "pass", "emoji": "🎟️", "title": {"tj": "Пропуск", "ru": "Пропуск"},
             "items": [
                 {"id": "ffp_wl", "title": "Weekly Lite", "price": 5},
                 {"id": "ffp_wv", "title": "Weekly Voucher", "price": 18},
                 {"id": "ffp_mv", "title": "Monthly Voucher", "price": 65},
             ]},
        ],
    },
    {
        "id": "ml", "name": "Mobile Legends", "badge": "GLOBAL", "subtitle": "Diamonds",
        "img": "", "colors": ["#3b82f6", "#1e3a8a"],
        "regions": [], "need_zone": True,          # ML da Zone ID ham kerak
        "categories": [
            {"id": "dia", "emoji": "💎", "title": {"tj": "Алмосҳо", "ru": "Алмазы"},
             "items": _items("mld", [(86, 14), (172, 28), (257, 42), (429, 70), (878, 140)])},
        ],
    },
    {
        "id": "genshin", "name": "Genshin Impact", "badge": "GLOBAL", "subtitle": "Genesis Crystals",
        "img": "", "colors": ["#a78bfa", "#4c1d95"],
        "regions": [
            {"id": "EU", "flag": "🇪🇺"}, {"id": "ASIA", "flag": "🌏"}, {"id": "AMERICA", "flag": "🌎"},
            {"id": "TW/HK/MO", "flag": "🇭🇰"},
        ],
        "need_zone": False,
        "categories": [
            {"id": "gc", "emoji": "💠", "title": {"tj": "Кристаллҳо", "ru": "Кристаллы"},
             "items": _items("gc", [(60, 12), (330, 60), (1090, 190), (2240, 380)])},
        ],
    },
    {
        "id": "delta", "name": "Delta Force", "badge": "NEW", "subtitle": "Delta Coins",
        "img": "", "colors": ["#22c55e", "#14532d"],
        "regions": [], "need_zone": False,
        "categories": [
            {"id": "coin", "emoji": "🪙", "title": {"tj": "Тангаҳо", "ru": "Монеты"},
             "items": _items("dc", [(60, 12), (300, 58), (680, 120), (1580, 280)])},
        ],
    },
    {
        "id": "standoff", "name": "Standoff 2", "badge": "NEW", "subtitle": "Gold",
        "img": "", "colors": ["#eab308", "#713f12"],
        "regions": [], "need_zone": False,
        "categories": [
            {"id": "gold", "emoji": "🥇", "title": {"tj": "Голд", "ru": "Голд"},
             "items": _items("so", [(100, 11), (500, 52), (1000, 100), (2000, 195)])},
        ],
    },
]

GAME_BY_ID = {g["id"]: g for g in GAMES}
PAY_BY_ID = {p["id"]: p for p in PAYMENT_METHODS}


def find_item(game, item_id):
    """(kategoriya, paket) qaytaradi yoki (None, None)."""
    for c in game["categories"]:
        for it in c["items"]:
            if it["id"] == item_id:
                return c, it
    return None, None
