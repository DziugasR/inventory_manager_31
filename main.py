import sys
import os
from dotenv import load_dotenv
import configparser

from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory

# We import these later, inside main(), to control the order of operations
# from backend import database
# from frontend.ui.main_window import InventoryUI
# from frontend.controllers.main_controller import MainController
# from backend.type_manager import type_manager


# ---Path, Env Loading---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
print(f"DEBUG: main.py - Looking for .env at: {env_path}")
loaded_env = load_dotenv(dotenv_path=env_path, override=True, verbose=True)
if not loaded_env:
    print(f"WARNING: main.py - .env file not found or empty at {env_path}")

# --- Config Reading ---
config = configparser.ConfigParser()
config_path = os.path.join(application_path, 'config.ini')
print(f"DEBUG: main.py - Looking for config.ini at: {config_path}")

DEFAULT_DB_FILENAME = 'inventory.db'
DEFAULT_OPENAI_MODEL = 'gpt-4o-mini'
DEFAULT_APP_STYLE = 'Fusion'

db_filename_or_path = DEFAULT_DB_FILENAME
openai_model = DEFAULT_OPENAI_MODEL
app_style_name = DEFAULT_APP_STYLE

try:
    if config.read(config_path):
        print(f"INFO: main.py - Successfully read config file: {config_path}")
        openai_model = config.get('OpenAI', 'model', fallback=DEFAULT_OPENAI_MODEL)

        app_style_name = config.get('Appearance', 'style', fallback=DEFAULT_APP_STYLE)

        db_url_from_config = config.get('Database', 'url', fallback=None)
        if db_url_from_config:
            if db_url_from_config.startswith("sqlite:///"):
                db_filename_or_path = db_url_from_config[len("sqlite///"):]
                print(f"INFO: Extracted DB path from config 'url': {db_filename_or_path}")
            else:
                db_filename_or_path = db_url_from_config
                print(f"INFO: Using DB path directly from config 'url' (not full sqlite URI): {db_filename_or_path}")
            db_filename_or_path = db_filename_or_path.lstrip('/\\')
        else:
            print(f"INFO: DB 'url' not found in config. Using default filename: {DEFAULT_DB_FILENAME}")
            db_filename_or_path = DEFAULT_DB_FILENAME
    else:
        print(f"WARNING: main.py - config.ini not found or empty at {config_path}. Using default settings.")

except configparser.Error as e:
    print(f"Error reading configuration file '{config_path}': {e}. Using default settings.")
except Exception as e:
    print(f"Unexpected error processing config file '{config_path}': {e}. Using default settings.")

# --- Construct DB Path/URL ---
if os.path.isabs(db_filename_or_path):
    absolute_db_path = db_filename_or_path
    if os.path.dirname(absolute_db_path).replace('\\', '/') == os.path.abspath(os.sep).replace('\\', '/'):
        print(f"CRITICAL WARNING: Configured database path '{absolute_db_path}' points to the drive root!")
else:
    absolute_db_path = os.path.join(application_path, db_filename_or_path)
db_url_final = f"sqlite:///{absolute_db_path}"

print(f"INFO: main.py - Using OpenAI Model: {openai_model}")
print(f"INFO: main.py - Using Appearance Style: {app_style_name}")
print(f"INFO: main.py - Final absolute DB path: {absolute_db_path}")
print(f"INFO: main.py - Using Database URL: {db_url_final}")


# --- Main function ---
def main():
    api_key_check = os.getenv("OPENAI_API_KEY")
    if not api_key_check:
        print("CRITICAL WARNING: OPENAI_API_KEY not found in environment or .env file!")

    # Import and initialize in the correct order
    from backend import database
    try:
        database.initialize_database(db_url_final)
        print("INFO: Database initialized successfully.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize database with URL {db_url_final}: {e}")
        QMessageBox.critical(None, "Database Error", f"Could not initialize database:\n{e}\n\nApplication will exit.")
        sys.exit(1)

    # Initialize the TypeManager AFTER the database is ready
    from backend.type_manager import type_manager
    type_manager.load_types()

    # Now it is safe to import UI and Controller modules
    from frontend.ui.main_window import InventoryUI
    from frontend.controllers.main_controller import MainController

    app = QApplication(sys.argv)

    # --- Apply Style using Config Value ---
    available_styles = QStyleFactory.keys()
    style_to_apply_config = app_style_name
    actual_style_name = None

    for style in available_styles:
        if style.lower() == style_to_apply_config.lower():
            actual_style_name = style
            break

    if actual_style_name:
        QApplication.setStyle(QStyleFactory.create(actual_style_name))
        print(f"INFO: Applied style '{actual_style_name}' from config.")
    else:
        print(f"WARNING: Configured style '{style_to_apply_config}' not found.")
        if DEFAULT_APP_STYLE in available_styles and style_to_apply_config != DEFAULT_APP_STYLE:
            QApplication.setStyle(QStyleFactory.create(DEFAULT_APP_STYLE))
            print(f"INFO: Falling back to default style '{DEFAULT_APP_STYLE}'.")
        else:
            print(f"INFO: Letting Qt use its default style.")
        print(f"Available styles: {available_styles}")
    # --- End Apply Style ---

    view = InventoryUI()
    controller = MainController(view, openai_model=openai_model)
    controller.show_view()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()