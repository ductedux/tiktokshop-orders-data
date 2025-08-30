# sign_variants.py
import hmac, hashlib, json
from urllib.parse import urlencode



def _minify(body):
    if body is None:
        return ""
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False)

def _sorted_pairs_excluding_secret(d: dict):
    # Loại cả 'sign' và '_app_secret' khỏi tập tham số dùng để ký
    return [(k, d[k]) for k in sorted(d.keys()) if k not in ("sign", "_app_secret")]

def sign_concat(path: str, query: dict, body) -> tuple[str, str]:
    """
    Kiểu theo doc: path + (key+value nối liền, sort theo key) + body_minified
    KHÔNG gồm 'sign' và '_app_secret' trong phần param concat
    """
    q_pairs = _sorted_pairs_excluding_secret(query)
    param_concat = "".join(f"{k}{v}" for k, v in q_pairs)
    sign_text = f"{path}{param_concat}{_minify(body)}"
    sig = hmac.new(query["_app_secret"].encode(), sign_text.encode(), hashlib.sha256).hexdigest()
    return sig, sign_text

def sign_ampersand(path: str, query: dict, body) -> tuple[str, str]:
    """
    Biến thể: path + "?" + "k1=v1&k2=v2..." + body_minified (không URL-encode giá trị)
    KHÔNG gồm 'sign' và '_app_secret'
    """
    q_pairs = _sorted_pairs_excluding_secret(query)
    joined = "&".join(f"{k}={v}" for k, v in q_pairs)
    sign_text = f"{path}?{joined}{_minify(body)}"
    sig = hmac.new(query["_app_secret"].encode(), sign_text.encode(), hashlib.sha256).hexdigest()
    return sig, sign_text

def build_url(base: str, path: str, query: dict, sig: str) -> str:
    q = dict(query)
    q.pop("_app_secret", None)
    q["sign"] = sig
    return f"{base}{path}?{urlencode(q)}"
