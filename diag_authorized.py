# diag_authorized.py
import os, time, requests
from dotenv import load_dotenv
from sign_variants import sign_concat, sign_ampersand, build_url

load_dotenv()
APP_KEY      = os.getenv("TTS_APP_KEY")
APP_SECRET   = os.getenv("TTS_APP_SECRET")
ACCESS_TOKEN = os.getenv("TTS_ACCESS_TOKEN")
BASE         = os.getenv("TTS_BASE", "https://open-api.tiktokglobalshop.com")

PATH = "/authorization/202309/shops"

def common_query():
    return {
        "app_key": APP_KEY,
        "sign_method": "HMAC-SHA256",
        "timestamp": int(time.time()),
        # version có nơi yêu cầu, có nơi KHÔNG – sẽ thử cả 2
        # "version": "202309",
        "_app_secret": APP_SECRET,
    }

def try_call(name, query, body, signer):
    sig, sign_text = signer(PATH, query, body)
    url = build_url(BASE, PATH, query, sig)
    headers = {"x-tts-access-token": ACCESS_TOKEN}

    print(f"\n=== TRY {name} ===")
    print("[DEBUG] Sorted keys :", ", ".join(sorted([k for k in query.keys() if k != '_app_secret'])))
    print("[DEBUG] SignText    :", sign_text)
    print("[DEBUG] URL         :", url)
    r = requests.get(url, headers=headers, timeout=60)
    print("[DEBUG] HTTP        :", r.status_code)
    print("[DEBUG] Resp head   :", r.headers.get('content-type', ''))
    txt = r.text
    print("[DEBUG] Resp sample :", txt[:300].replace("\n"," "))
    return r.status_code, txt

def main():
    assert APP_KEY and APP_SECRET and ACCESS_TOKEN, "Thiếu APP_KEY/APP_SECRET/ACCESS_TOKEN trong .env"

    tests = []

    # 2 KIỂU KÝ
    signers = [("CONCAT", sign_concat), ("AMPERSAND", sign_ampersand)]

    # 4 BIẾN THỂ THAM SỐ
    # A) Không version, không access_token trong query
    baseA = common_query()
    # B) Có version
    baseB = dict(common_query(), **{"version":"202309"})
    # C) Có version + access_token (một số cụm yêu cầu đưa access_token vào query khi ký)
    baseC = dict(baseB, **{"access_token": ACCESS_TOKEN})
    # D) Không version + access_token
    baseD = dict(baseA, **{"access_token": ACCESS_TOKEN})

    variants = [("A(no version, no token in query)", baseA),
                ("B(version=202309)", baseB),
                ("C(version+access_token)", baseC),
                ("D(no version + access_token)", baseD)]

    # GET: body rỗng
    body = None

    for vname, q in variants:
        for sname, signer in signers:
            name = f"{sname} + {vname}"
            status, txt = try_call(name, dict(q), body, signer)
            if status == 200:
                print(f"\n>>> SUCCESS with: {name}")
                return

    print("\n>>> Không kịch bản nào 200. Dán toàn bộ output này cho mình để soi tiếp.")

if __name__ == "__main__":
    main()
