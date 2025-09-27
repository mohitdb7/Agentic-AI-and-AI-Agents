import os
import json
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import asyncio, functools, inspect

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

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Exception while writing the logs: {e}")

def log_with_context(event_name: str, context: dict, *, source: str, request_id: str, error: str = None):
    context.update({
        "source": source,
        "request_id": request_id
    })
    _log_node_activity(event_name, context, error=error)

def cleanup_old_logs(days: int = 0, hours: int = 0, minutes: int = 0):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days, hours=hours, minutes=minutes)

    try:
        for folder in os.listdir(LOG_DIR):
            folder_path = os.path.join(LOG_DIR, folder)
            if os.path.isdir(folder_path):
                folder_time = datetime.fromtimestamp(os.path.getmtime(folder_path), tz=timezone.utc)

                print(f"{folder_time}, {cutoff} - {folder_time < cutoff}")

                if folder_time < cutoff:
                    for f in os.listdir(folder_path):
                        os.remove(os.path.join(folder_path, f))
                    os.rmdir(folder_path)
    except Exception as e:
        print(f"Exception while cleaning logs: {e}")

def log_node(node_name: str):
    def decorator(func):
        is_coroutine = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract 'state' from args or kwargs
            state = kwargs.get("state")
            if not state:
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if len(params) >= 2:
                    state = args[1]  # for methods (self, state)
                elif len(params) == 1:
                    state = args[0]  # for standalone function
                else:
                    state = {}

            try:
                result = await func(*args, **kwargs)
                _log_node_activity(node_name, input_data=state, output_data=result)
                return result
            except Exception as e:
                _log_node_activity(node_name, input_data=state, error=str(e))
                if isinstance(state, dict):
                    state["has_error"] = True
                raise e

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract 'state' from args or kwargs
            state = kwargs.get("state")
            if not state:
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if len(params) >= 2:
                    state = args[1]  # for methods (self, state)
                elif len(params) == 1:
                    state = args[0]  # for standalone function
                else:
                    state = {}

            try:
                result = func(*args, **kwargs)
                _log_node_activity(node_name, input_data=state, output_data=result)
                return result
            except Exception as e:
                _log_node_activity(node_name, input_data=state, error=str(e))
                if isinstance(state, dict):
                    state["has_error"] = True
                raise e

        return async_wrapper if is_coroutine else sync_wrapper

    return decorator


