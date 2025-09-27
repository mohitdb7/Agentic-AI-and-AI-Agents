# news_agent_flow/logging_utils/logger.py

import os
import json
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

def _make_serializable(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()  # For Pydantic v2
    elif isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    else:
        return obj  # Assume it's already serializable

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')

def _get_log_path(node_name: str):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dir_path = os.path.join(LOG_DIR, date_str)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{node_name}.json")

def _log_node_activity(node_name: str, input_data: dict, output_data: dict = None, error: str = None):
    log_path = _get_log_path(node_name)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": _make_serializable(input_data),
        "output": _make_serializable(output_data),
        "error": error
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def cleanup_old_logs(days: int = 0, hours: int = 0, minutes: int = 0):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days, hours=hours, minutes=minutes)

    for folder in os.listdir(LOG_DIR):
        try:
            folder_path = os.path.join(LOG_DIR, folder)
            if os.path.isdir(folder_path):
                folder_time = datetime.fromtimestamp(os.path.getmtime(folder_path), tz=timezone.utc)

                if folder_time < cutoff:
                    for f in os.listdir(folder_path):
                        os.remove(os.path.join(folder_path, f))
                    os.rmdir(folder_path)
        except Exception as e:
            print(f"Exception while writing the logs {str(e)}")

def log_node(node_name: str):
    def decorator(func):
        def wrapper(state: dict):
            try:
                result = func(state)
                _log_node_activity(node_name, input_data=state, output_data=result)
                return result
            except Exception as e:
                _log_node_activity(node_name, input_data=state, error=str(e))
                state['has_error'] = True
                return state
        return wrapper
    return decorator