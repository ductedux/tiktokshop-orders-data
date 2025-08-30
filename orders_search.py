# orders_search.py
import json
from datetime import datetime, timedelta, timezone
from tts_client import post_signed_with_shop



PATH = "/order/202309/orders/search"

# Giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

def fetch_orders_by_created(create_time_ge: int, create_time_lt: int, page_size: int = 50):
    """
    Lấy toàn bộ đơn trong [create_time_ge, create_time_lt) (server-side),
    sau đó lọc lại client-side để đảm bảo đúng tuyệt đối.
    """
    page_token = None
    all_orders = []

    while True:
        # Tham số phân trang/sắp xếp: đặt trên URL
        query_params = {
            "page_size": int(page_size),
            "sort_order": "DESC",
            "sort_field": "create_time",
        }
        if page_token:
            query_params["page_token"] = page_token

        # Lọc thời gian: để trong BODY (giữ int64)
        body = {
            "time_filter": {
                "create_time_ge": int(create_time_ge),
                "create_time_lt": int(create_time_lt),
            }
        }

        data = post_signed_with_shop(PATH, body=body, query_extra=query_params)
        batch = (data.get("data") or {}).get("orders") or []
        all_orders.extend(batch)

        page_token = (data.get("data") or {}).get("next_page_token")
        if not page_token:
            break

    # --- LỌC LẠI Ở CLIENT: chỉ giữ đơn có create_time trong khoảng yêu cầu ---
    ge, lt = int(create_time_ge), int(create_time_lt)
    filtered = [o for o in all_orders if ge <= int(o.get("create_time", 0)) < lt]

    # Sắp xếp lại cho chắc (mới -> cũ)
    filtered.sort(key=lambda o: int(o.get("create_time", 0)), reverse=True)
    return filtered

if __name__ == "__main__":
    # “Hôm nay” theo giờ VN: 00:00:00 -> 24:00:00
    now_vn = datetime.now(VN_TZ)
    start_of_day = datetime(now_vn.year, now_vn.month, now_vn.day, 0, 0, 0, tzinfo=VN_TZ)
    end_of_day   = start_of_day + timedelta(days=1)  # exclusive

    ge = int(start_of_day.timestamp())  # 00:00 hôm nay (epoch giây UTC)
    lt = int(end_of_day.timestamp())    # 00:00 ngày mai (exclusive)

    # Gọi API và lấy đúng ĐƠN TẠO HÔM NAY (đã lọc lại client-side)
    orders = fetch_orders_by_created(ge, lt, page_size=50)

    # Tên file theo thời điểm chạy (giờ VN) để mỗi lần/ mỗi ngày ra file riêng
    stamp = now_vn.strftime("%Y%m%d_%H%M%S")
    filename = f"orders_{stamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã ghi {len(orders)} đơn **tạo trong hôm nay** (giờ VN) vào file {filename}")
