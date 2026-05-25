import os
import json

os.makedirs("data/sessions", exist_ok=True)

def save_session(session_id: str, data: dict):
    """Saves session intelligence to disk for persistence across planning workflows."""
    filepath = f"data/sessions/{session_id}.json"
    
    # We only save primitive types (remove DataFrames before calling this)
    safe_data = {
        "city": data.get("city"),
        "recommendations": data.get("recommendations"),
        "timestamp": data.get("timestamp")
    }
    
    with open(filepath, 'w') as f:
        json.dump(safe_data, f)
        
def load_session(session_id: str) -> dict:
    """Loads a previously saved planning session."""
    filepath = f"data/sessions/{session_id}.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None
