import sys
from PyQt5.QtWidgets import QApplication

from frontend.ui.main_window import InventoryUI
from frontend.controllers.main_controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_view = InventoryUI()

    controller = MainController(view=main_view)

    main_view.show()
    sys.exit(app.exec_())