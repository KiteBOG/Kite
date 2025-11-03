import re

def safe_name(name: str) -> str:
    if not name:
        return "node"
    # Replace invalid characters with underscore
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    if s and s[0].isdigit():
        s = "n_" + s
    return s or "node"
