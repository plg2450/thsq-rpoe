from PySide6.QtWidgets import QPushButton


class GlassButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "secondaryBtn")


class GlassPrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "primaryBtn")
