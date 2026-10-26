"""Ma'lumotlar bazasi (SQLite). Balans, buyurtmalar, to'ldirishlar, kodlar."""
import os
import sqlite3
import time
from contextlib import contextmanager

import config

_conn = None


def init():
    global _conn
    d = os.path.dirname(config.DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False, isolation_level=None)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY, name TEXT, username TEXT,
        lang TEXT DEFAULT 'tj', dark INTEGER DEFAULT 1, notify INTEGER DEFAULT 1,
        balance INTEGER DEFAULT 0, spent INTEGER DEFAULT 0,
        ref_by INTEGER, ref_paid INTEGER DEFAULT 0, banned INTEGER DEFAULT 0, created INTEGER);
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, game_id TEXT, game_name TEXT,
        item_id TEXT, title TEXT, emoji TEXT, player_id TEXT, region TEXT,
        price INTEGER, status TEXT DEFAULT 'pending', created INTEGER);
    CREATE TABLE IF NOT EXISTS topups(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, method TEXT, amount INTEGER,
        file_id TEXT, status TEXT DEFAULT 'pending', created INTEGER);
    CREATE TABLE IF NOT EXISTS tx(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, kind TEXT, amount INTEGER,
        note TEXT, created INTEGER);
    CREATE TABLE IF NOT EXISTS codes(
        code TEXT PRIMARY KEY, kind TEXT, value INTEGER, uses_left INTEGER);
    CREATE TABLE IF NOT EXISTS code_uses(
        code TEXT, user_id INTEGER, PRIMARY KEY(code, user_id));
    """)


@contextmanager
def tx():
    """Bir nechta o'zgarishni yoki hammasini, yoki hech birini saqlaydi."""
    _conn.execute("BEGIN")
    try:
        yield _conn
        _conn.execute("COMMIT")
    except BaseException:
        _conn.execute("ROLLBACK")
        raise


def _now():
    return int(time.time())


def _row(r):
    return dict(r) if r else None


# ---------------- foydalanuvchilar ----------------
def upsert_user(uid, name, username, ref_by=None):
    u = _conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if u is None:
        if ref_by == uid or (ref_by and not _conn.execute("SELECT 1 FROM users WHERE id=?", (ref_by,)).fetchone()):
            ref_by = None
        _conn.execute(
            "INSERT INTO users(id,name,username,ref_by,created) VALUES(?,?,?,?,?)",
            (uid, name, username, ref_by, _now()))
    else:
        _conn.execute("UPDATE users SET name=?, username=? WHERE id=?", (name, username, uid))
    return get_user(uid)


def get_user(uid):
    return _row(_conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())


def set_settings(uid, lang=None, dark=None, notify=None):
    if lang in ("tj", "ru"):
        _conn.execute("UPDATE users SET lang=? WHERE id=?", (lang, uid))
    if dark is not None:
        _conn.execute("UPDATE users SET dark=? WHERE id=?", (1 if dark else 0, uid))
    if notify is not None:
        _conn.execute("UPDATE users SET notify=? WHERE id=?", (1 if notify else 0, uid))


def notify_user_ids():
    return [r["id"] for r in _conn.execute("SELECT id FROM users WHERE notify=1 AND banned=0")]


# ---------------- balans ----------------
def _add_tx(uid, kind, amount, note=""):
    _conn.execute("INSERT INTO tx(user_id,kind,amount,note,created) VALUES(?,?,?,?,?)",
                  (uid, kind, amount, note, _now()))


def add_balance(uid, amount, note="admin"):
    with tx():
        if not _conn.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
            raise ValueError("nouser")
        _conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, uid))
        _add_tx(uid, "admin", amount, note)
    return get_user(uid)["balance"]


def get_tx(uid, limit=50):
    rows = _conn.execute("SELECT * FROM tx WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit)).fetchall()
    return [dict(r) for r in rows]


# ---------------- promo va gift kodlar ----------------
def discounted(price, percent):
    return max(1, int(price * (100 - percent) / 100 + 0.5))


def promo_percent(uid, code):
    """Chegirma kodi to'g'ri bo'lsa foizni qaytaradi, aks holda None."""
    code = (code or "").strip().upper()
    c = _conn.execute("SELECT * FROM codes WHERE code=? AND kind='discount' AND uses_left>0", (code,)).fetchone()
    used = _conn.execute("SELECT 1 FROM code_uses WHERE code=? AND user_id=?", (code, uid)).fetchone()
    return c["value"] if c and not used else None


def add_code(kind, code, value, uses):
    _conn.execute("INSERT OR REPLACE INTO codes(code,kind,value,uses_left) VALUES(?,?,?,?)",
                  (code.strip().upper(), kind, value, uses))


def redeem_code(uid, code):
    code = (code or "").strip().upper()
    with tx():
        c = _conn.execute("SELECT * FROM codes WHERE code=? AND kind='balance'", (code,)).fetchone()
        if not c or c["uses_left"] <= 0:
            raise ValueError("notfound")
        if _conn.execute("SELECT 1 FROM code_uses WHERE code=? AND user_id=?", (code, uid)).fetchone():
            raise ValueError("used")
        _conn.execute("INSERT INTO code_uses(code,user_id) VALUES(?,?)", (code, uid))
        _conn.execute("UPDATE codes SET uses_left=uses_left-1 WHERE code=?", (code,))
        _conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (c["value"], uid))
        _add_tx(uid, "gift", c["value"], code)
    return c["value"]


# ---------------- buyurtmalar ----------------
def create_order(uid, game, item, emoji, player, region, promo=None):
    price = item["price"]
    with tx():
        u = _conn.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
        if promo:
            code = promo.strip().upper()
            pct = promo_percent(uid, code)
            if pct is None:
                raise ValueError("promo")
            price = discounted(price, pct)
            _conn.execute("INSERT INTO code_uses(code,user_id) VALUES(?,?)", (code, uid))
            _conn.execute("UPDATE codes SET uses_left=uses_left-1 WHERE code=?", (code,))
        if u["balance"] < price:
            raise ValueError("balance")
        _conn.execute("UPDATE users SET balance=balance-?, spent=spent+? WHERE id=?", (price, price, uid))
        cur = _conn.execute(
            "INSERT INTO orders(user_id,game_id,game_name,item_id,title,emoji,player_id,region,price,created)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (uid, game["id"], game["name"], item["id"], item["title"], emoji, player, region, price, _now()))
        oid = cur.lastrowid
        _add_tx(uid, "purchase", -price, f"#{oid} {game['name']} {item['title']}")
    return {"id": oid, "price": price, "balance": get_user(uid)["balance"]}


def get_orders(uid, status=None, limit=50):
    if status in ("pending", "done", "canceled"):
        rows = _conn.execute("SELECT * FROM orders WHERE user_id=? AND status=? ORDER BY id DESC LIMIT ?",
                             (uid, status, limit)).fetchall()
    else:
        rows = _conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT ?",
                             (uid, limit)).fetchall()
    return [dict(r) for r in rows]


def set_order_status(oid, status):
    """Faqat 'pending' buyurtmani o'zgartiradi. Bekor qilinsa pul qaytariladi."""
    with tx():
        o = _conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        if not o or o["status"] != "pending":
            return None
        _conn.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
        if status == "canceled":
            _conn.execute("UPDATE users SET balance=balance+?, spent=spent-? WHERE id=?",
                          (o["price"], o["price"], o["user_id"]))
            _add_tx(o["user_id"], "refund", o["price"], f"#{oid}")
    return dict(o)


# ---------------- balans to'ldirish ----------------
def count_pending_topups(uid):
    return _conn.execute("SELECT COUNT(*) c FROM topups WHERE user_id=? AND status='pending'", (uid,)).fetchone()["c"]


def pending_topups(uid):
    rows = _conn.execute("SELECT * FROM topups WHERE user_id=? AND status='pending' ORDER BY id DESC", (uid,)).fetchall()
    return [dict(r) for r in rows]


def create_topup(uid, method, amount):
    cur = _conn.execute("INSERT INTO topups(user_id,method,amount,created) VALUES(?,?,?,?)",
                        (uid, method, amount, _now()))
    return cur.lastrowid


def set_topup_file(tid, file_id):
    _conn.execute("UPDATE topups SET file_id=? WHERE id=?", (file_id, tid))


def approve_topup(tid):
    """Tasdiqlaydi. {topup, ref:(referrer_id, bonus)|None} yoki None (allaqachon ko'rib chiqilgan)."""
    with tx():
        t = _conn.execute("SELECT * FROM topups WHERE id=?", (tid,)).fetchone()
        if not t or t["status"] != "pending":
            return None
        _conn.execute("UPDATE topups SET status='done' WHERE id=?", (tid,))
        _conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (t["amount"], t["user_id"]))
        _add_tx(t["user_id"], "topup", t["amount"], f"#{tid} {t['method']}")
        ref = None
        u = _conn.execute("SELECT * FROM users WHERE id=?", (t["user_id"],)).fetchone()
        if u["ref_by"] and not u["ref_paid"]:
            _conn.execute("UPDATE users SET ref_paid=1 WHERE id=?", (u["id"],))
            bonus = t["amount"] * config.REF_PERCENT // 100
            if bonus > 0:
                _conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (bonus, u["ref_by"]))
                _add_tx(u["ref_by"], "bonus", bonus, f"ref {u['id']}")
                ref = (u["ref_by"], bonus)
    return {"topup": dict(t), "ref": ref}


def reject_topup(tid):
    with tx():
        t = _conn.execute("SELECT * FROM topups WHERE id=?", (tid,)).fetchone()
        if not t or t["status"] != "pending":
            return None
        _conn.execute("UPDATE topups SET status='canceled' WHERE id=?", (tid,))
    return dict(t)


# ---------------- statistika ----------------
def stats():
    q = lambda s: _conn.execute(s).fetchone()[0] or 0
    return {
        "users": q("SELECT COUNT(*) FROM users"),
        "balance": q("SELECT SUM(balance) FROM users"),
        "orders_pending": q("SELECT COUNT(*) FROM orders WHERE status='pending'"),
        "orders_done": q("SELECT COUNT(*) FROM orders WHERE status='done'"),
        "sales": q("SELECT SUM(price) FROM orders WHERE status='done'"),
        "topups": q("SELECT SUM(amount) FROM topups WHERE status='done'"),
    }
