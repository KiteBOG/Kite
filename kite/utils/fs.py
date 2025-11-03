import os
import shutil
from typing import List


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def ensure_empty_dir(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def write_text(path: str, content: str) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def find_files(root: str, patterns: List[str]) -> List[str]:
    matches: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for pat in patterns:
            # naive glob match
            if pat.startswith("*."):
                ext = pat[1:]
                for fn in filenames:
                    if fn.endswith(ext):
                        matches.append(os.path.join(dirpath, fn))
            else:
                for fn in filenames:
                    if fn == pat:
                        matches.append(os.path.join(dirpath, fn))
    return matches
