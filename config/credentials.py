import os


def load_brand_credentials(brand_id: str | None = None) -> dict:
    """Load brand-specific credentials from environment variables.

    Credentials are expected to follow the pattern
    META_ACCESS_TOKEN_<BRAND>, META_PHONE_NUMBER_ID_<BRAND>, and
    CATALOG_ID_<BRAND>. The brand identifier is upper-cased before
    lookup. If no brand_id is supplied, the BRAND_ID environment
    variable is used.
    """

    brand = (brand_id or os.getenv("BRAND_ID", "")).upper()

    access_token = os.getenv(f"META_ACCESS_TOKEN_{brand}")
    phone_number_id = os.getenv(f"META_PHONE_NUMBER_ID_{brand}")
    catalog_id = os.getenv(f"CATALOG_ID_{brand}")
    verify_token = os.getenv("META_VERIFY_TOKEN")

    whatsapp_api_url = (
        f"https://graph.facebook.com/v23.0/{phone_number_id}/messages"
        if phone_number_id
        else None
    )

    return {
        "META_ACCESS_TOKEN": access_token,
        "META_PHONE_NUMBER_ID": phone_number_id,
        "WHATSAPP_CATALOG_ID": catalog_id,
        "META_VERIFY_TOKEN": verify_token,
        "WHATSAPP_API_URL": whatsapp_api_url,
    }


_creds = load_brand_credentials()
META_ACCESS_TOKEN = _creds["META_ACCESS_TOKEN"]
META_PHONE_NUMBER_ID = _creds["META_PHONE_NUMBER_ID"]
WHATSAPP_CATALOG_ID = _creds["WHATSAPP_CATALOG_ID"]
META_VERIFY_TOKEN = _creds["META_VERIFY_TOKEN"]
WHATSAPP_API_URL = _creds["WHATSAPP_API_URL"]


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# CSV file paths (relative to project root)
ORDERS_CSV = "../data/orders.csv"
CART_REMINDERS_CSV = "../data/cart_reminders.csv"
USER_ACTIVITY_LOG_CSV = "../data/user_activity_log.csv"
BRANCHES_CSV = "../data/branches.csv"
BRANDS_CSV = "../data/brands.csv"

