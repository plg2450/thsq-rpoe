from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class VideoPlayer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "videoPlayer")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_label.setText("\U0001F3AC")
        icon_label.setProperty("class", "videoPlayerIcon")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("播放原视频")
        text_label.setProperty("class", "videoPlayerText")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("拖入视频文件或点击选择")
        hint_label.setProperty("class", "videoPlayerHint")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)
