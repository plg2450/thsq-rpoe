from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class SliderControl(QWidget):
    """可复用的滑块控制组件"""

    value_changed = Signal(float)

    def __init__(self, label: str, min_val: float, max_val: float, default: float,
                 step: float = 0.1, suffix: str = "", parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.suffix = suffix

        # 转换为整数步长用于QSlider
        self.scale = int(1 / step) if step < 1 else 1
        self.slider_min = int(min_val * self.scale)
        self.slider_max = int(max_val * self.scale)
        self.slider_default = int(default * self.scale)

        self._setup_ui(label)

    def _setup_ui(self, label: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        # 设置最小高度
        self.setMinimumHeight(32)

        # 标签
        self.label = QLabel(label)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #555;
                background: rgba(0, 0, 0, 10);
                border: 1px solid rgba(0, 0, 0, 20);
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 40px;
                max-width: 60px;
            }
        """)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.label)

        # 滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.slider_min)
        self.slider.setMaximum(self.slider_max)
        self.slider.setValue(self.slider_default)
        self.slider.setSingleStep(1)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #E8E8ED;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C6CEB, stop:1 #6B9FFF);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #7C6CEB;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #F8F8FF;
                border: 2px solid #6B5CEB;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
        """)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, stretch=1)

        # 值显示
        self.value_label = QLabel(self._format_value(self.slider_default))
        self.value_label.setStyleSheet("""
            QLabel {
                background: #F0F0F5;
                border: 1px solid rgba(0, 0, 0, 5);
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 12px;
                color: #7C6CEB;
                font-weight: 600;
                min-width: 48px;
                text-align: center;
            }
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # 范围标签
        range_text = f"{self.min_val}{self.suffix}  {self.max_val}{self.suffix}"
        self.range_label = QLabel(range_text)
        self.range_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #999;
                background: transparent;
                border: none;
                min-width: 60px;
            }
        """)
        layout.addWidget(self.range_label)

    def _format_value(self, slider_value: int) -> str:
        real_value = slider_value / self.scale
        if self.suffix == "x":
            return f"{real_value:.1f}x"
        elif self.suffix == "%":
            return f"{int(real_value)}%"
        else:
            return f"{real_value:.1f}"

    def _on_value_changed(self, slider_value: int):
        real_value = slider_value / self.scale
        self.value_label.setText(self._format_value(slider_value))
        self.value_changed.emit(real_value)

    def value(self) -> float:
        return self.slider.value() / self.scale

    def setValue(self, value: float):
        self.slider.setValue(int(value * self.scale))
