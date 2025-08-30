# tts_client.py  — robust token lifecycle with preemptive refresh
import os, time, json, requests, threading
from urllib.parse import urlencode
from dotenv import load_dotenv
from tts_sign import build_signature_with_text  # 202309 sign scheme



load_dotenv()

APP_KEY     = os.getenv("TTS_APP_KEY")
APP_SECRET  = os.getenv("TTS_APP_SECRET")
SHOP_CIPHER = os.getenv("TTS_SHOP_CIPHER")  # ưu tiên nếu có
SHOP_ID     = os.getenv("TTS_SHOP_ID")
BASE        = os.getenv("TTS_BASE", "https://open-api.tiktokglobalshop.com")

# State file cho token (không commit git)
STATE_FILE  = os.getenv("TTS_TOKEN_STATE", "token_state.json")

# Lock để an toàn đa luồng/đa request
_state_lock = threading.Lock()

def _load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
            # đảm bảo key cần thiết
            s.setdefault("access_token", None)
            s.setdefault("refresh_token", os.getenv("TTS_REFRESH_TOKEN") or None)
            s.setdefault("expires_at", 0)
            return s
    except Exception:
        # bootstrap từ .env nếu có
        return {
            "access_token": os.getenv("TTS_ACCESS_TOKEN") or None,
            "refresh_token": os.getenv("TTS_REFRESH_TOKEN") or None,
            "expires_at": 0
        }

def _save_state(s):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

_state = _load_state()

def _require_app():
    if not APP_KEY or not APP_SECRET:
        raise RuntimeError("Thiếu TTS_APP_KEY/TTS_APP_SECRET trong .env")

def _require_shop():
    if not (SHOP_CIPHER or SHOP_ID):
        raise RuntimeError("Thiếu TTS_SHOP_CIPHER hoặc TTS_SHOP_ID trong .env")

def _common_query():
    _require_app()
    return {
        "app_key": APP_KEY,
        "sign_method": "HMAC-SHA256",
        "timestamp": int(time.time()),
        "version": "202309",
    }

def _update_tokens(access_token: str, refresh_token: str | None, expire_in: int | None):
    now = int(time.time())
    expires_at = now + int(expire_in or 3600)  # fallback 1h nếu không trả expire
    _state["access_token"] = access_token
    if refresh_token:
        _state["refresh_token"] = refresh_token
    _state["expires_at"] = expires_at
    _save_state(_state)
    # Đồng bộ vào process env để các chỗ khác (nếu có) còn đọc
    os.environ["TTS_ACCESS_TOKEN"]  = _state["access_token"]
    if _state.get("refresh_token"):
        os.environ["TTS_REFRESH_TOKEN"] = _state["refresh_token"]

def _refresh_access_token_or_fail():
    _require_app()
    if not _state.get("refresh_token"):
        raise RuntimeError(
            "Không có refresh_token để làm mới access_token. "
            "Hãy lấy lại ủy quyền (authorized_code → token/get) hoặc bổ sung TTS_REFRESH_TOKEN."
        )
    params = {
        "app_key": APP_KEY,
        "app_secret": APP_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": _state["refresh_token"],
    }
    url = "https://auth.tiktok-shops.com/api/v2/token/refresh"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json() or {}
    payload = data.get("data") or data
    access = payload.get("access_token")
    refresh = payload.get("refresh_token") or _state.get("refresh_token")
    # TikTok có thể trả 'access_token_expire_in' hoặc 'expire_in' (tùy tài liệu/cụm)
    expire_in = payload.get("access_token_expire_in", payload.get("expire_in"))
    if not access:
        raise RuntimeError(f"Refresh không trả access_token: {data}")
    _update_tokens(access, refresh, expire_in)
    return _state["access_token"]

def ensure_access_token():
    """Trả về access_token hợp lệ, refresh sớm 10 phút trước hạn."""
    with _state_lock:
        now = int(time.time())
        token = _state.get("access_token")
        expires_at = int(_state.get("expires_at") or 0)
        # Chưa có hạn → nếu có token thì dùng tạm, nếu không thì buộc refresh (nếu có refresh_token)
        if not token:
            if _state.get("refresh_token"):
                return _refresh_access_token_or_fail()
            raise RuntimeError("Thiếu access_token. Bổ sung TTS_REFRESH_TOKEN hoặc re-authorize shop.")
        # Refresh sớm 10 phút
        if expires_at and now >= (expires_at - 600):
            return _refresh_access_token_or_fail()
        return token

def _build_signed_url(path: str, body: dict | None, query_extra: dict | None):
    q = _common_query()
    if SHOP_CIPHER:
        q["shop_cipher"] = SHOP_CIPHER
    elif SHOP_ID:
        q["shop_id"] = SHOP_ID
    if query_extra:
        q.update(query_extra)
    sign_hex, _, _ = build_signature_with_text(path, q, body, APP_SECRET)
    url = f"{BASE}{path}?{urlencode({**q, 'sign': sign_hex})}"
    payload = None if body is None else json.dumps(body, separators=(",", ":"))
    return url, payload

def get_signed_no_shop(path: str, query_extra: dict | None = None):
    """GET ký (không cần param shop), ví dụ /authorization/202309/shops"""
    _require_app()
    token = ensure_access_token()
    q = _common_query()
    if query_extra:
        q.update(query_extra)
    sign_hex, _, _ = build_signature_with_text(path, q, None, APP_SECRET)
    url = f"{BASE}{path}?{urlencode({**q, 'sign': sign_hex})}"
    headers = {"x-tts-access-token": token}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code in (400, 401) and "expired" in r.text.lower():
        # refresh-on-401 dự phòng
        token = _refresh_access_token_or_fail()
        headers["x-tts-access-token"] = token
        r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()

def post_signed_with_shop(path: str, body: dict | None, query_extra: dict | None = None):
    """
    POST đã ký. Tự ensure token còn hạn (preemptive) + fallback refresh-on-401 một lần.
    """
    _require_app(); _require_shop()
    token = ensure_access_token()
    url, payload = _build_signed_url(path, body, query_extra)
    headers = {"x-tts-access-token": token, "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, data=payload, timeout=60)
    if r.ok:
        return r.json()

    # fallback khi token hết hạn bất ngờ
    try:
        j = r.json()
    except Exception:
        j = {}
    if r.status_code == 401 and (j.get("code") == 105002 or "expired" in (j.get("message") or "").lower()):
        token = _refresh_access_token_or_fail()
        headers["x-tts-access-token"] = token
        r2 = requests.post(url, headers=headers, data=payload, timeout=60)
        if r2.ok:
            return r2.json()
        raise RuntimeError(f"Retry after refresh failed: HTTP {r2.status_code} - {r2.text}")

    raise RuntimeError(f"HTTP {r.status_code} - {r.text}")
