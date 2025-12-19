import json
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

CONFIG_PATH = Path(__file__).parent / "chatbot_config.json"

def load_config():
    """Đọc file JSON và trả về dict"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Load initial config
config = load_config()

class ConfigChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == str(CONFIG_PATH):
            global config
            config = load_config()
            print("Configuration reloaded.")

def start_config_watcher():
    event_handler = ConfigChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=CONFIG_PATH.parent, recursive=False)
    observer.start()
    return observer

# Start the config watcher in a separate thread
config_watcher = start_config_watcher()

def save_config(new_data: dict):
    """Ghi lại file JSON với dữ liệu mới"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    return new_data

# Ensure to stop the observer when the application exits
import atexit
atexit.register(lambda: config_watcher.stop())
