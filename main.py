import sys

from PyQt5.QtWidgets import QApplication, QStyleFactory

from frontend.ui.main_window import InventoryUI
from frontend.controllers.main_controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)

    available_styles = QStyleFactory.keys()
    print("Available styles on this system:", available_styles)

    app.setStyle(QStyleFactory.create('Fusion'))

    main_view = InventoryUI()

    controller = MainController(view=main_view)

    main_view.show()
    sys.exit(app.exec_())