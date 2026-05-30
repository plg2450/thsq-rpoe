from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class GlassCard(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "glassCard")
        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 5);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        if title:
            label = QLabel(title)
            label.setProperty("class", "sectionTitle")
            label.setStyleSheet("""
                font-size: 14px;
                font-weight: 600;
                color: #1A1A2E;
                background: transparent;
                border: none;
                padding: 4px 0;
            """)
            layout.addWidget(label)
