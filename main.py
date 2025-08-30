import sys
import os
import configparser
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory

# --- This is our new, reliable function to read the .env file ---
def load_env_manually(path):
    """
    Manually reads a .env file and returns a dictionary of variables.
    This has no dependencies and is reliable in a PyInstaller bundle.
    """
    variables = {}
    if not os.path.exists(path):
        print(f"WARNING: Manual .env loader could not find file at: {path}")
        return variables
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignore comments and empty lines
                if line and not line.startswith('#'):
                    # Find the first '=' to handle values that might contain '='
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove surrounding quotes if they exist
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        variables[key] = value
    except Exception as e:
        print(f"CRITICAL: Failed to manually read .env file: {e}")
    return variables
# --------------------------------------------------------------------


if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
print(f"DEBUG: main.py - Manually looking for .env at: {env_path}")

# --- We now call our new function instead of load_dotenv ---
env_variables = load_env_manually(env_path)
# -----------------------------------------------------------

config = configparser.ConfigParser()
config_path = os.path.join(application_path, 'config.ini')
print(f"DEBUG: main.py - Looking for config.ini at: {config_path}")

DEFAULT_DB_FILENAME = 'inventory_main.db'
DEFAULT_CONFIG_DB_FILENAME = 'config.db'
DEFAULT_OPENAI_MODEL = 'gpt-4o-mini'
DEFAULT_APP_STYLE = 'Fusion'

db_filename_or_path = DEFAULT_DB_FILENAME
config_db_filename = DEFAULT_CONFIG_DB_FILENAME
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
            else:
                db_filename_or_path = db_url_from_config
            db_filename_or_path = db_filename_or_path.lstrip('/\\')
        else:
            db_filename_or_path = DEFAULT_DB_FILENAME

        if config.has_option('Database', 'config_db'):
            config_db_filename = config.get('Database', 'config_db', fallback=DEFAULT_CONFIG_DB_FILENAME)
        else:
            print("INFO: 'config_db' not found in config.ini, will add it with default value.")
            if not config.has_section('Database'):
                config.add_section('Database')
            config.set('Database', 'config_db', DEFAULT_CONFIG_DB_FILENAME)
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            config_db_filename = DEFAULT_CONFIG_DB_FILENAME

        config_db_filename = config_db_filename.lstrip('/\\')

    else:
        print(f"WARNING: main.py - config.ini not found or empty. Using default settings.")

except configparser.Error as e:
    print(f"Error reading configuration file '{config_path}': {e}. Using default settings.")
except Exception as e:
    print(f"Unexpected error processing config file '{config_path}': {e}. Using default settings.")

def get_absolute_path(filename):
    if os.path.isabs(filename):
        return filename
    return os.path.join(application_path, filename)

absolute_inventory_db_path = get_absolute_path(db_filename_or_path)
absolute_config_db_path = get_absolute_path(config_db_filename)

inventory_db_url_final = f"sqlite:///{absolute_inventory_db_path}"
config_db_url_final = f"sqlite:///{absolute_config_db_path}"

print(f"INFO: main.py - Using OpenAI Model: {openai_model}")
print(f"INFO: main.py - Using Appearance Style: {app_style_name}")
print(f"INFO: main.py - Final Config DB path: {absolute_config_db_path}")
print(f"INFO: main.py - Final Inventory DB path: {absolute_inventory_db_path}")

def main():
    # --- We get the key from our dictionary, not the environment ---
    api_key_variable = env_variables.get("OPENAI_API_KEY")
    # As a fallback, check the actual environment too
    if not api_key_variable:
        api_key_variable = os.getenv("OPENAI_API_KEY")

    if not api_key_variable:
        print("CRITICAL WARNING: OPENAI_API_KEY not found in .env file or environment!")

    from backend import database
    try:
        database.initialize_databases(
            config_db_url=config_db_url_final,
            inventory_db_url=inventory_db_url_final
        )
        print("INFO: Databases initialized successfully.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize databases: {e}")
        QMessageBox.critical(None, "Database Error", f"Could not initialize databases:\n{e}\n\nApplication will exit.")
        sys.exit(1)

    from backend.type_manager import type_manager
    type_manager.load_types()

    from frontend.ui.main_window import InventoryUI
    from frontend.controllers.main_controller import MainController

    app = QApplication(sys.argv)

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

    view = InventoryUI()
    # This part remains the same from our last working attempt
    controller = MainController(
        view,
        openai_model=openai_model,
        app_path=application_path,
        api_key=api_key_variable
    )
    controller.show_view()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()