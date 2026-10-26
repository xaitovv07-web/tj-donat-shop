"""Telegram Mini App ma'lumotlarini (initData) tekshirish — soxta so'rovlardan himoya."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def check_init_data(init_data: str, token: str, max_age: int = 86400):
    """To'g'ri bo'lsa foydalanuvchi dict'ini, aks holda None qaytaradi."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        got = pairs.pop("hash", None)
        if not got:
            return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, got):
            return None
        if time.time() - int(pairs.get("auth_date", "0")) > max_age:
            return None
        return json.loads(pairs["user"])
    except Exception:
        return None
