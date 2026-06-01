from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class GlassCard(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "glassCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        if title:
            label = QLabel(title)
            label.setProperty("class", "sectionTitle")
            layout.addWidget(label)
