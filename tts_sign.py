# tts_sign.py
import hmac, hashlib, json


def _minify(body):
    if body is None:
        return ""
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False)

def build_signature(path: str, query: dict, body: dict | None, app_secret: str) -> str:
    """
    TikTok Shop 202309: sign_text = app_secret + path + (concat params sorted key+value, bỏ 'sign') + (body minified hoặc "")
                         + app_secret
    Sau đó HMAC-SHA256 (hex lowercase) với key = app_secret.
    """
    # 1) Bỏ 'sign' khỏi query
    q = dict(query)
    q.pop("sign", None)

    # 2) Nối key+value theo thứ tự ASCII của key
    param_concat = "".join(f"{k}{q[k]}" for k in sorted(q.keys()))

    # 3) Body minified ("" nếu None)
    body_part = _minify(body)

    # 4) Quấn secret 2 đầu
    sign_text = f"{app_secret}{path}{param_concat}{body_part}{app_secret}"

    # 5) HMAC-SHA256
    return hmac.new(app_secret.encode("utf-8"),
                    sign_text.encode("utf-8"),
                    hashlib.sha256).hexdigest()

def build_signature_with_text(path: str, query: dict, body: dict | None, app_secret: str):
    """
    Trả về (sign_hex, param_concat, sign_text) để debug.
    """
    q = dict(query); q.pop("sign", None)
    param_concat = "".join(f"{k}{q[k]}" for k in sorted(q.keys()))
    body_part = _minify(body)
    sign_text = f"{app_secret}{path}{param_concat}{body_part}{app_secret}"
    sign_hex = hmac.new(app_secret.encode("utf-8"),
                        sign_text.encode("utf-8"),
                        hashlib.sha256).hexdigest()
    return sign_hex, param_concat, sign_text
