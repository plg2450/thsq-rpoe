from PySide6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


class Toast(QLabel):
    """轻量级提示框"""

    def __init__(self, message: str, parent=None):
        super().__init__(message, parent)
        self.setStyleSheet("""
            QLabel {
                background: #333;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(36)
        self.adjustSize()

        # 透明度效果
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)

        # 自动隐藏
        QTimer.singleShot(2000, self.fade_out)

        # 居中显示
        if parent:
            self._center_in_parent()

    def _center_in_parent(self):
        parent = self.parent()
        if parent:
            x = (parent.width() - self.width()) // 2
            y = parent.height() - 60
            self.move(x, y)

    def fade_out(self):
        anim = QPropertyAnimation(self._opacity, b"opacity")
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.finished.connect(self.deleteLater)
        anim.start()
        # 保持引用
        self._anim = anim


def show_toast(parent, message: str):
    """显示提示框"""
    toast = Toast(message, parent)
    toast.show()
