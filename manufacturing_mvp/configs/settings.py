import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WORKSPACE_DIR, exist_ok=True)

MODEL_TYPE = os.getenv("MODEL_TYPE", "openai")

PRIORITY_LEVELS = {
    "P0": "紧急",
    "P1": "高",
    "P2": "中",
    "P3": "低",
}

STATUS_CODES = {
    "pending": "待处理",
    "processing": "处理中",
    "resolved": "已解决",
    "closed": "已关闭",
}
