# TikTok Shop Order Fetcher

Dự án Python này giúp **lấy danh sách đơn hàng từ TikTok Shop API** theo ngày, đồng thời xử lý tự động việc **làm mới access token** bằng refresh token.

---

## 📂 Cấu trúc thư mục

```
TIKTOKSHOP_UPDATE/
│── .env # Chứa APP_KEY, APP_SECRET, SHOP_ID/CIPHER, REFRESH_TOKEN (bảo mật, không push lên git)
│── auth_callback.py # Server mini để nhận auth_code khi authorize shop
│── authorized_shops.py # Test API: lấy danh sách shop đã ủy quyền
│── diag_authorized.py # Script debug chữ ký request
│── orders_search.py # Script lấy đơn theo ngày (ghi ra file JSON)
│── orders_search_7days.py # Script lấy đơn 7 ngày gần nhất (ghi ra file JSON)
│── orders_search_final.py # Script lấy đơn hôm nay và in trực tiếp ra terminal
│── refresh_env_token.py # Làm mới access_token bằng refresh_token (GET)
│── run_orders_today.ps1 # Script PowerShell: refresh token rồi chạy orders_search.py
│── requirements.txt # Danh sách thư viện cần cài
│── sign_variants.py # Các hàm hỗ trợ ký request
│── tts_client.py # Client gửi request có ký và kèm access_token
│── tts_sign.py # Hỗ trợ ký request theo chuẩn TikTok Shop
│── token_state.json # File lưu token hiện tại và thời gian hết hạn (auto tạo)
│── orders_xxx.json # Các file JSON đơn hàng sinh ra trong quá trình chạy
```

---

## ⚙️ Cài đặt

1.  **Clone repo và tạo môi trường ảo:**
    ```bash
    git clone https://github.com/yourusername/tiktokshop_update.git
    cd tiktokshop_update
    python -m venv .venv
    .venv\Scripts\activate   # Windows
    source .venv/bin/activate # Linux/Mac
    ```

2.  **Cài thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Tạo file `.env` (KHÔNG commit file này):**
    ```ini
    TTS_APP_KEY=your_app_key
    TTS_APP_SECRET=your_app_secret
    TTS_SHOP_ID=your_shop_id   # hoặc TTS_SHOP_CIPHER
    TTS_BASE=https://open-api.tiktokglobalshop.com
    TTS_REFRESH_TOKEN=your_refresh_token
    ```

---

## 🔑 Lấy Access Token & Refresh Token

1.  **Chạy `auth_callback.py`:**
    ```bash
    python auth_callback.py
    ```
    Thao tác này sẽ mở một server nhỏ để lắng nghe trên `http://localhost:9000/callback`.

2.  **Lấy authorization link** trong Partner Center và authorize shop của bạn.

3.  Sau khi authorize, terminal sẽ in ra `AUTH_CODE`.

4.  **Dùng Postman (hoặc công cụ tương tự) để gọi API lấy token:**
    - **URL:** `https://auth.tiktok-shops.com/api/v2/token/get`
    - **Method:** `POST`
    - **Params:**
        - `app_key`: *your_app_key*
        - `app_secret`: *your_app_secret*
        - `grant_type`: `authorized_code`
        - `auth_code`: *dán_auth_code_từ_terminal_vào_đây*

    → API sẽ trả về `access_token` và `refresh_token`.

5.  **Điền `refresh_token`** vừa nhận được vào file `.env`. Access token sẽ được các script tự động làm mới và ghi đè khi cần.

---

## 🚀 Cách chạy

*   **Lấy đơn hàng hôm nay và in ra màn hình:**
    ```bash
    python orders_search_final.py
    ```

*   **Lấy đơn hàng hôm nay và lưu vào file JSON:**
    ```bash
    python orders_search.py
    ```

*   **Lấy đơn hàng trong 7 ngày gần nhất:**
    ```bash
    python orders_search_7days.py
    ```

---

## ♻️ Tự động hóa (Windows)

File `run_orders_today.ps1` được cung cấp để tự động hóa quy trình:

1.  Chạy `refresh_env_token.py` để đảm bảo `access_token` trong `.env` là mới nhất.
2.  Chạy `orders_search.py` để lấy đơn hàng của ngày hôm nay.

