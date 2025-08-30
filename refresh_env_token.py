# refresh_env_token.py  -- refresh bằng GET
import os, sys, requests
from dotenv import load_dotenv, set_key

load_dotenv()
APP_KEY    = os.getenv("TTS_APP_KEY")
APP_SECRET = os.getenv("TTS_APP_SECRET")
REFRESH    = os.getenv("TTS_REFRESH_TOKEN")
ENV_FILE   = os.getenv("DOTENV_PATH", ".env")

if not (APP_KEY and APP_SECRET and REFRESH):
    print("❌ Thiếu TTS_APP_KEY/TTS_APP_SECRET/TTS_REFRESH_TOKEN trong .env", file=sys.stderr)
    sys.exit(2)

params = {
    "app_key": APP_KEY,
    "app_secret": APP_SECRET,
    "grant_type": "refresh_token",
    "refresh_token": REFRESH,
}

url = "https://auth.tiktok-shops.com/api/v2/token/refresh"

resp = requests.get(url, params=params, timeout=60)
if not resp.ok:
    print(f"❌ Refresh lỗi HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
    sys.exit(1)

j = resp.json()
payload = j.get("data") or j
access_token = payload.get("access_token")
new_refresh  = payload.get("refresh_token") or REFRESH
if not access_token:
    print(f"❌ Không có access_token trong response: {resp.text}", file=sys.stderr)
    sys.exit(1)

# Cập nhật .env
set_key(ENV_FILE, "TTS_ACCESS_TOKEN", access_token)
if new_refresh and new_refresh != REFRESH:
    set_key(ENV_FILE, "TTS_REFRESH_TOKEN", new_refresh)

print("✔ .env đã cập nhật TTS_ACCESS_TOKEN (và TTS_REFRESH_TOKEN nếu có).")
