from PyQt5.QtWidgets import QApplication
from frontend.ui import InventoryUI

if __name__ == "__main__":
    app = QApplication([])
    window = InventoryUI()
    window.show()
    app.exec_()
