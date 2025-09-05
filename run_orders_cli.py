
#!/usr/bin/env python3
# run_orders_cli.py
# Usage examples at bottom of file (search for 'EXAMPLES').
import os, json, argparse
from datetime import datetime, timedelta, timezone
from importlib import import_module

VN_TZ = timezone(timedelta(hours=7))

def parse_args():
    p = argparse.ArgumentParser(description="Run TikTok Shop order search for any shop via CLI params (no .env needed).")
    # --- Auth & shop params ---
    p.add_argument("--app-key", required=True, help="TTS_APP_KEY")
    p.add_argument("--app-secret", required=True, help="TTS_APP_SECRET")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--shop-id", help="TTS_SHOP_ID")
    g.add_argument("--shop-cipher", help="TTS_SHOP_CIPHER")
    p.add_argument("--access-token", help="TTS_ACCESS_TOKEN")
    p.add_argument("--refresh-token", help="TTS_REFRESH_TOKEN (recommended so tool can refresh)")
    p.add_argument("--base", default="https://open-api.tiktokglobalshop.com", help="TTS_BASE")
    p.add_argument("--token-state", default="token_state.json", help="TTS_TOKEN_STATE path (created/used if given)")

    # --- What to run ---
    p.add_argument("--mode", choices=["today","range","7days"], default="today",
                   help="today: 00:00-24:00 today (VN); range: custom epoch seconds; 7days: last 7 days to tomorrow 00:00 (VN)")
    p.add_argument("--ge", type=int, help="create_time_ge (epoch seconds, used when --mode=range)")
    p.add_argument("--lt", type=int, help="create_time_lt (epoch seconds, used when --mode=range)")
    p.add_argument("--page-size", type=int, default=50, help="page_size for API")
    p.add_argument("--out", help="Output file (default prints JSON to stdout for --mode=today; otherwise writes orders_YYYYMMDD_HHMMSS.json)")
    p.add_argument("--module", default="orders_search", choices=["orders_search", "orders_search_final"],
                   help="Which module to use for fetch logic (both have fetch_orders_by_created(create_time_ge, create_time_lt, page_size))")

    return p.parse_args()

def compute_range(args):
    now_vn = datetime.now(VN_TZ)
    if args.mode == "today":
        start = datetime(now_vn.year, now_vn.month, now_vn.day, 0, 0, 0, tzinfo=VN_TZ)
        end   = start + timedelta(days=1)
    elif args.mode == "7days":
        start = datetime(now_vn.year, now_vn.month, now_vn.day, 0, 0, 0, tzinfo=VN_TZ) - timedelta(days=7)
        end   = datetime(now_vn.year, now_vn.month, now_vn.day, 0, 0, 0, tzinfo=VN_TZ) + timedelta(days=1)
    else:
        if args.ge is None or args.lt is None:
            raise SystemExit("When --mode=range you must provide --ge and --lt (epoch seconds).")
        return int(args.ge), int(args.lt), now_vn
    return int(start.timestamp()), int(end.timestamp()), now_vn

def main():
    args = parse_args()

    # Set process env so existing code reads it without modifications
    os.environ["TTS_APP_KEY"] = args.app_key
    os.environ["TTS_APP_SECRET"] = args.app_secret
    os.environ["TTS_BASE"] = args.base
    os.environ["TTS_TOKEN_STATE"] = args.token_state
    if args.shop_id:
        os.environ["TTS_SHOP_ID"] = args.shop_id
        os.environ.pop("TTS_SHOP_CIPHER", None)
    else:
        os.environ["TTS_SHOP_CIPHER"] = args.shop_cipher
        os.environ.pop("TTS_SHOP_ID", None)
    if args.access_token:
        os.environ["TTS_ACCESS_TOKEN"] = args.access_token
    if args.refresh_token:
        os.environ["TTS_REFRESH_TOKEN"] = args.refresh_token

    # Import after env is set
    mod = import_module(args.module)
    ge, lt, now_vn = compute_range(args)
    orders = mod.fetch_orders_by_created(ge, lt, page_size=args.page_size)

    # Output
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        print(f"✔ Wrote {len(orders)} orders to {args.out}")
    else:
        # default: print pretty JSON for --mode=today if --out not provided
        stamp = now_vn.strftime("%Y%m%d_%H%M%S")
        if args.mode == "today":
            print(json.dumps(orders, ensure_ascii=False, indent=2))
            print(f"\n✅ {len(orders)} orders created today (VN time).")
        else:
            filename = f"orders_{stamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(orders)} orders to {filename}")

if __name__ == "__main__":
    main()

# ------------------------
# EXAMPLES
# ------------------------
# 1) Today (VN), using shop_id + refresh_token (recommended):
# python run_orders_cli.py --app-key AK --app-secret SECRET --shop-id 123456789 \
#   --refresh-token ROW_... --mode today --module orders_search_final
#
# 2) Last 7 days (VN), using shop_cipher + access_token:
# python run_orders_cli.py --app-key AK --app-secret SECRET --shop-cipher ROW_xxx \
#   --access-token ROW_... --mode 7days --page-size 100
#
# 3) Custom range by epoch seconds:

