import sys
from PyQt5.QtWidgets import QApplication

# Assuming the structure frontend/ui and frontend/controllers
# Adjust imports based on where main.py is located
from frontend.ui.main_window import InventoryUI
from frontend.controllers.main_controller import MainController

# Ensure backend path is discoverable if running from root
# (This might be needed depending on your project setup)
# import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. Create the View instance
    main_view = InventoryUI()

    # 2. Create the Controller instance, passing the view to it
    controller = MainController(view=main_view)

    # 3. Show the main window (via controller or directly)
    # controller.show_view() # Controller can manage showing the view
    main_view.show() # Or show it directly after controller setup

    # 4. Start the event loop
    sys.exit(app.exec_())