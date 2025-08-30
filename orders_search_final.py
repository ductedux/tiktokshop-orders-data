# orders_search_final.py
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
        query_params = {
            "page_size": int(page_size),
            "sort_order": "DESC",
            "sort_field": "create_time",
        }
        if page_token:
            query_params["page_token"] = page_token

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

    # Lọc lại cho chắc chắn
    ge, lt = int(create_time_ge), int(create_time_lt)
    filtered = [o for o in all_orders if ge <= int(o.get("create_time", 0)) < lt]

    # Sắp xếp mới -> cũ
    filtered.sort(key=lambda o: int(o.get("create_time", 0)), reverse=True)
    return filtered

if __name__ == "__main__":
    # “Hôm nay” theo giờ VN: 00:00:00 -> 24:00:00
    now_vn = datetime.now(VN_TZ)
    start_of_day = datetime(now_vn.year, now_vn.month, now_vn.day, 0, 0, 0, tzinfo=VN_TZ)
    end_of_day   = start_of_day + timedelta(days=1)

    ge = int(start_of_day.timestamp())
    lt = int(end_of_day.timestamp())

    # Lấy đơn hôm nay
    orders = fetch_orders_by_created(ge, lt, page_size=50)

    # In trực tiếp ra terminal dưới dạng JSON đẹp
    print(json.dumps(orders, ensure_ascii=False, indent=2))

    print(f"\n✅ Tổng cộng {len(orders)} đơn tạo hôm nay (giờ VN).")
