from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QColor

class ComponentTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, has_image=False):
        super().__init__(text)
        self.has_image = has_image
        self._apply_styling()

    def _apply_styling(self):
        if self.has_image:
            # A nice light blue or cyan color that stands out
            self.setForeground(QColor("#00BFFF"))