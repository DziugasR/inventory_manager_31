import os


def get_stylesheet(theme_name: str) -> str:
    """
    Loads and returns the stylesheet content for a given theme name.
    Returns an empty string if the theme is 'System Default' or not found.
    """
    if theme_name.lower() == 'system default':
        return ""

    filename = f"{theme_name.lower()}.qss"
    # This assumes that this file is in 'frontend/' and the styles are in 'frontend/ui/styles/'
    current_dir = os.path.dirname(__file__)
    style_path = os.path.join(current_dir, 'ui', 'styles', filename)

    if not os.path.exists(style_path):
        print(f"WARNING: Stylesheet not found at path: {style_path}")
        return ""

    try:
        with open(style_path, "r", encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"ERROR: Could not load stylesheet '{filename}': {e}")
        return ""


def apply_theme(app, theme_name: str):
    """
    Applies a theme to the entire application.
    """
    stylesheet = get_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)
    print(f"INFO: Applied '{theme_name}' theme.")