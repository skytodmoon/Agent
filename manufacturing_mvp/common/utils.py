import shortuuid
from datetime import datetime

def generate_id(prefix: str = "") -> str:
    base_id = shortuuid.uuid()[:8].upper()
    return f"{prefix}{base_id}"

def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

def get_current_time() -> datetime:
    return datetime.now()
