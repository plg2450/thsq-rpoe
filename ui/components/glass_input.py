from PySide6.QtWidgets import QLineEdit, QTextEdit


class GlassInput(QLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background: #F5F5F8;
                border: 1px solid rgba(0, 0, 0, 8);
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
                color: #1A1A2E;
            }
            QLineEdit:focus {
                border: 1px solid #7C6CEB;
                background: #FFFFFF;
            }
        """)


class GlassTextEdit(QTextEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QTextEdit {
                background: #F5F5F8;
                border: 1px solid rgba(0, 0, 0, 8);
                border-radius: 12px;
                padding: 12px;
                font-size: 13px;
                color: #1A1A2E;
            }
            QTextEdit:focus {
                border: 1px solid #7C6CEB;
                background: #FFFFFF;
            }
        """)
