import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory

# --- Manually load .env file for reliability ---
def load_env_manually(path):
    variables = {}
    if not os.path.exists(path):
        return variables
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    variables[key] = value
    except Exception as e:
        print(f"CRITICAL: Failed to manually read .env file: {e}")
    return variables

# --- Determine application path ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# --- Load Environment Variables ---
env_path = os.path.join(application_path, '.env')
env_variables = load_env_manually(env_path)

# --- Define Database Paths ---
DEFAULT_INVENTORY_DB = os.path.join(application_path, "inventory_main.db")
DEFAULT_CONFIG_DB = os.path.join(application_path, "config.db")

inventory_db_url_final = f"sqlite:///{DEFAULT_INVENTORY_DB}"
config_db_url_final = f"sqlite:///{DEFAULT_CONFIG_DB}"

print(f"INFO: main.py - Config DB URL: {config_db_url_final}")
print(f"INFO: main.py - Initial Inventory DB URL: {inventory_db_url_final}")

def main():
    # --- Prepare Application ---
    app = QApplication(sys.argv)

    # --- Set Fusion as the base style for a consistent look ---
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    print("INFO: Set 'Fusion' as the base application style.")

    # --- Import backend modules after path setup ---
    from backend import database, settings_manager
    from backend.type_manager import type_manager
    from frontend import theme_manager
    from frontend.ui.main_window import InventoryUI
    from frontend.controllers.main_controller import MainController

    # --- Initialize Databases (MUST be done before using settings) ---
    try:
        database.initialize_databases(
            config_db_url=config_db_url_final,
            inventory_db_url=inventory_db_url_final
        )
        print("INFO: Databases initialized successfully.")
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Could not initialize databases:\n{e}\n\nApplication will exit.")
        sys.exit(1)

    # --- Apply the Saved Theme (layered on top of Fusion) ---
    saved_theme = settings_manager.get_setting("theme", "System Default")
    theme_manager.apply_theme(app, saved_theme)

    # --- Load Component Type Definitions ---
    type_manager.load_types()

    # --- Get API Key from .env (fallback to environment) ---
    api_key = env_variables.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("CRITICAL WARNING: OPENAI_API_KEY not found in .env file or environment!")

    # --- Create and Show UI ---
    icon_path = os.path.join(application_path, 'frontend', 'ui', 'assets', 'EMLogo.ico')
    view = InventoryUI(icon_path=icon_path)

    controller = MainController(
        view=view,
        openai_model='gpt-4o-mini',  # Default model, will be overwritten by settings in controller
        app_path=application_path,
        api_key=api_key
    )

    view.controller = controller

    controller.show_view()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()