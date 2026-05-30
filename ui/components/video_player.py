from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class VideoPlayer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #F5F5F8;
                border: 2px dashed rgba(0, 0, 0, 10);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_label.setText("\U0001F3AC")
        icon_label.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("播放原视频")
        text_label.setStyleSheet("font-size: 14px; color: #999; background: transparent; border: none;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("拖入视频文件或点击选择")
        hint_label.setStyleSheet("font-size: 11px; color: #BBB; background: transparent; border: none;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)
