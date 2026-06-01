from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt, Signal


class SliderControl(QWidget):
    """大尺寸滑块控制组件"""

    value_changed = Signal(float)

    def __init__(self, label: str, min_val: float, max_val: float, default: float,
                 step: float = 0.1, suffix: str = "", parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.suffix = suffix

        self.scale = int(1 / step) if step < 1 else 1
        self.slider_min = int(min_val * self.scale)
        self.slider_max = int(max_val * self.scale)
        self.slider_default = int(default * self.scale)

        self._setup_ui(label)

    def _setup_ui(self, label: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 标签 + 当前值
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.label = QLabel(label)
        self.label.setProperty("class", "bigSliderLabel")
        top_row.addWidget(self.label)
        top_row.addStretch()

        self.value_label = QLabel(self._format_value(self.slider_default))
        self.value_label.setProperty("class", "bigSliderValue")
        top_row.addWidget(self.value_label)

        layout.addLayout(top_row)

        # 滑块 + 范围
        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)

        self.min_label = QLabel(f"{self.min_val}{self.suffix}")
        self.min_label.setProperty("class", "bigSliderRange")
        slider_row.addWidget(self.min_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.slider_min)
        self.slider.setMaximum(self.slider_max)
        self.slider.setValue(self.slider_default)
        self.slider.setSingleStep(1)
        self.slider.setMinimumHeight(28)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #E0E0E8;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C6CEB, stop:1 #6B9FFF);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #7C6CEB;
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }
            QSlider::handle:horizontal:hover {
                background: #F0F0FF;
                border: 2px solid #5A4BC5;
                width: 24px;
                height: 24px;
                margin: -9px 0;
                border-radius: 12px;
            }
            QSlider::handle:horizontal:pressed {
                background: #7C6CEB;
                border: 2px solid #5A4BC5;
            }
        """)
        self.slider.valueChanged.connect(self._on_value_changed)
        slider_row.addWidget(self.slider, stretch=1)

        self.max_label = QLabel(f"{self.max_val}{self.suffix}")
        self.max_label.setProperty("class", "bigSliderRange")
        slider_row.addWidget(self.max_label)

        layout.addLayout(slider_row)

    def _format_value(self, slider_value: int) -> str:
        real_value = slider_value / self.scale
        if self.suffix == "x":
            return f"{real_value:.1f}x"
        elif self.suffix == "%":
            return f"{int(real_value)}%"
        else:
            return f"{real_value:+.0f}" if real_value != 0 else "0"

    def _on_value_changed(self, slider_value: int):
        self.value_label.setText(self._format_value(slider_value))
        real_value = slider_value / self.scale
        self.value_changed.emit(real_value)

    def value(self) -> float:
        return self.slider.value() / self.scale

    def setValue(self, value: float):
        self.slider.setValue(int(value * self.scale))
