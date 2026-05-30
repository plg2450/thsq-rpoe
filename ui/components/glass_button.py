from PySide6.QtWidgets import QPushButton


class GlassButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "glassBtn")
        self.setStyleSheet("""
            QPushButton {
                background: #F0F0F5;
                border: 1px solid rgba(0, 0, 0, 5);
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                color: #444;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #E8E8F0;
                border: 1px solid rgba(0, 0, 0, 8);
            }
            QPushButton:pressed {
                background: #DDDDF0;
            }
            QPushButton:disabled {
                background: #F5F5F8;
                color: #BBB;
                border: 1px solid rgba(0, 0, 0, 3);
            }
        """)


class GlassPrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "glassBtnPrimary")
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C6CEB, stop:1 #6B9FFF);
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 13px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6B5BD6, stop:1 #5A8EEE);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5A4BC5, stop:1 #497DDD);
            }
            QPushButton:disabled {
                background: #D0D0E0;
                color: #999;
            }
        """)
