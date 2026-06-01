from PySide6.QtWidgets import QLineEdit, QTextEdit


class GlassInput(QLineEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setProperty("class", "glassInput")


class GlassTextEdit(QTextEdit):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setProperty("class", "glassTextEdit")
