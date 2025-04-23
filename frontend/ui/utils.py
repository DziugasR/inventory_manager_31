import sys
import os
from pathlib import Path

def load_stylesheet(filename="styles/button_styles.qss") -> str:
    style_path = None
    try:
        if getattr(sys, 'frozen', False):
            application_path = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
            style_path = application_path / filename
            print(f"DEBUG (Bundled): Looking for stylesheet at: {style_path}")
        else:
            script_dir = Path(__file__).parent
            style_path = script_dir / filename
            print(f"DEBUG (Dev): Looking for stylesheet at: {style_path}")
            if not style_path.is_file():
                style_path_alt = script_dir.parent / filename
                print(f"DEBUG (Dev): Stylesheet not found, trying alternate path: {style_path_alt}")
                if style_path_alt.is_file():
                    style_path = style_path_alt
                else:
                    style_path = script_dir / filename


        if style_path is None or not style_path.is_file():
            print(f"Warning: Stylesheet file not found at calculated path: {style_path}")
            return ""

        with open(style_path, "r", encoding="utf-8") as f:
            print(f"INFO: Successfully loaded stylesheet from: {style_path}")
            return f.read()

    except Exception as e:
        print(f"Warning: An unexpected error occurred while loading stylesheet '{filename}': {e}")
        if style_path:
            print(f"Path attempted: {style_path}")
        return ""