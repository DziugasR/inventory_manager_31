# frontend/ui/utils.py

import os
from pathlib import Path

def load_stylesheet(filename="styles/button_styles.qss") -> str:
    try:
        utils_dir = Path(__file__).parent
        style_path = utils_dir / filename

        if not style_path.is_file():
             style_path = utils_dir.parent / filename
             if not style_path.is_file():
                 print(f"Warning: Stylesheet not found at expected locations relative to utils.py: {filename}")
                 return ""

        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Stylesheet file not found: {style_path}")
        return ""
    except Exception as e:
        print(f"Warning: Error reading stylesheet {style_path}: {e}")
        return ""