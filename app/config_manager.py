import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "chatbot_config.json"

def load_config():
    """Đọc file JSON và trả về dict"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(new_data: dict):
    """Ghi lại file JSON với dữ liệu mới"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    return new_data
