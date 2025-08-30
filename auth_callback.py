# auth_callback.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        auth_code = qs.get("auth_code", [None])[0]
        code = qs.get("code", [None])[0]  # TikTok có thể dùng 'code' thay vì 'auth_code'
        state = qs.get("state", [None])[0]
        final_code = auth_code or code
        print("\n=== AUTH_CODE:", final_code, "STATE:", state, "===\n")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK, you can close this tab.")

HTTPServer(("0.0.0.0", 9000), H).serve_forever()
