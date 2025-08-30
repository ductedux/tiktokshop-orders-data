# authorized_shops.py
from tts_client import get_signed_no_shop
PATH = "/authorization/202309/shops"
if __name__ == "__main__":
    data = get_signed_no_shop(PATH, query_extra={})
    print(data)
