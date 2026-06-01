from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint


class LoadingDots(QLabel):
    """加载动画 - 省略号"""

    def __init__(self, parent=None):
        super().__init__("...", parent)
        self.setStyleSheet("""
            QLabel {
                background: transparent;
                color: rgba(255,255,255,0.7);
                font-size: 12px;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_dots)
        self._timer.start(300)

    def _update_dots(self):
        self._dots = (self._dots + 1) % 4
        self.setText("." * self._dots + " " * (3 - self._dots))

    def stop(self):
        self._timer.stop()


class LoadingSpinner(QWidget):
    """加载旋转动画"""

    def __init__(self, size=24, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(50)

    def _rotate(self):
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 画圆弧
        pen = QPen(QColor("#4CAF50"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        margin = 4
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.drawArc(rect, self._angle * 16, 270 * 16)

    def stop(self):
        self._timer.stop()
