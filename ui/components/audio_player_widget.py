import os
import wave
import struct
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen


class WaveformWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self._samples = []
        self._progress = 0.0
        self._duration = 0.0

    def load_audio(self, audio_path: str):
        try:
            with wave.open(audio_path, 'rb') as wav:
                self._duration = wav.getnframes() / wav.getframerate()
                frames = wav.readframes(wav.getnframes())

                sample_size = wav.getsampwidth()
                if sample_size == 2:
                    self._samples = struct.unpack(f'<{wav.getnframes()}h', frames)
                elif sample_size == 1:
                    self._samples = [b - 128 for b in struct.unpack(f'<{wav.getnframes()}B', frames)]

                if len(self._samples) > 500:
                    step = len(self._samples) // 500
                    self._samples = [self._samples[i] for i in range(0, len(self._samples), step)]

                self.update()
        except Exception as e:
            print(f"加载波形失败: {e}")

    def set_progress(self, progress: float):
        self._progress = max(0.0, min(1.0, progress))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor("#F5F5F8"))

        if not self._samples:
            painter.setPen(QPen(QColor("#CCC"), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无音频")
            return

        width = self.width()
        height = self.height()
        center_y = height / 2
        bar_width = max(1, width / len(self._samples) - 1)

        max_amp = max(abs(s) for s in self._samples) if self._samples else 1
        if max_amp == 0:
            max_amp = 1

        progress_x = int(self._progress * width)

        for i, sample in enumerate(self._samples):
            x = i * (bar_width + 1)
            if x > width:
                break

            normalized = abs(sample) / max_amp
            bar_height = int(normalized * (height - 10))

            if x < progress_x:
                gradient = QLinearGradient(0, center_y - bar_height / 2, 0, center_y + bar_height / 2)
                gradient.setColorAt(0, QColor("#22c55e"))
                gradient.setColorAt(1, QColor("#16a34a"))
                painter.setPen(Qt.NoPen)
                painter.setBrush(gradient)
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 20))

            painter.drawRect(
                int(x),
                int(center_y - bar_height / 2),
                int(bar_width),
                bar_height
            )

        if self._progress > 0:
            painter.setPen(QPen(QColor("#22c55e"), 2))
            painter.drawLine(progress_x, 0, progress_x, height)

        painter.end()


_CTRL_BTN = """
    QPushButton {
        background: #f5f5f5;
        color: #333;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        font-size: 12px;
    }
    QPushButton:hover { background: #ebebeb; }
    QPushButton:pressed { background: #e0e0e0; }
    QPushButton:disabled { background: #f9f9f9; color: #bbb; border-color: #eee; }
"""
_PLAY_BTN = """
    QPushButton {
        background: #22c55e;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton:hover { background: #16a34a; }
    QPushButton:pressed { background: #15803d; }
    QPushButton:disabled { background: #86efac; color: rgba(255,255,255,0.7); }
"""
_ACTION_BTN = """
    QPushButton {
        background: #f5f5f5;
        color: #555;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 12px;
    }
    QPushButton:hover { background: #ebebeb; border-color: #d5d5d5; }
    QPushButton:pressed { background: #e0e0e0; }
    QPushButton:disabled { background: #f9f9f9; color: #bbb; border-color: #eee; }
"""


class AudioPlayerWidget(QWidget):

    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    regenerate_clicked = Signal()
    save_profile_clicked = Signal()
    export_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._current_time = 0.0
        self._total_time = 0.0
        self._audio_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("试听音频")
        title.setStyleSheet("font-size: 12px; font-weight: 500; color: #888; background: transparent;")
        layout.addWidget(title)

        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.reset_btn = QPushButton("重置")
        self.reset_btn.setFixedHeight(32)
        self.reset_btn.setStyleSheet(_CTRL_BTN)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self._on_reset)
        controls_layout.addWidget(self.reset_btn)

        self.play_btn = QPushButton("播放")
        self.play_btn.setFixedHeight(32)
        self.play_btn.setStyleSheet(_PLAY_BTN)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self._on_play_pause)
        controls_layout.addWidget(self.play_btn, stretch=1)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedHeight(32)
        self.stop_btn.setStyleSheet(_CTRL_BTN)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.clicked.connect(self._on_stop)
        controls_layout.addWidget(self.stop_btn)

        self.time_label = QLabel("0:00.0 / 0:00.0")
        self.time_label.setStyleSheet("font-size: 12px; color: #999; background: transparent;")
        controls_layout.addWidget(self.time_label)

        layout.addLayout(controls_layout)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.regenerate_btn = QPushButton("重新生成")
        self.regenerate_btn.setStyleSheet(_ACTION_BTN)
        self.regenerate_btn.setCursor(Qt.PointingHandCursor)
        self.regenerate_btn.clicked.connect(self.regenerate_clicked)
        actions_layout.addWidget(self.regenerate_btn)

        self.save_btn = QPushButton("保存到配置")
        self.save_btn.setStyleSheet(_ACTION_BTN)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_profile_clicked)
        actions_layout.addWidget(self.save_btn)

        self.export_btn = QPushButton("导出WAV")
        self.export_btn.setStyleSheet(_ACTION_BTN)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self._on_export)
        actions_layout.addWidget(self.export_btn)

        layout.addLayout(actions_layout)

        self._update_ui_state()

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:04.1f}"

    def _update_ui_state(self):
        has_audio = self._audio_path is not None and os.path.exists(self._audio_path)
        self.play_btn.setEnabled(has_audio)
        self.reset_btn.setEnabled(has_audio)
        self.stop_btn.setEnabled(has_audio)
        self.regenerate_btn.setEnabled(has_audio)
        self.save_btn.setEnabled(has_audio)
        self.export_btn.setEnabled(has_audio)

        self.time_label.setText(f"{self._format_time(self._current_time)} / {self._format_time(self._total_time)}")

    def load_audio(self, audio_path: str):
        self._audio_path = audio_path
        self._current_time = 0.0

        try:
            with wave.open(audio_path, 'rb') as wav:
                self._total_time = wav.getnframes() / wav.getframerate()
        except:
            self._total_time = 0.0

        self.waveform.load_audio(audio_path)
        self._update_ui_state()

    def _on_play_pause(self):
        if self._is_playing:
            self._is_playing = False
            self.play_btn.setText("播放")
            self.pause_clicked.emit()
        else:
            self._is_playing = True
            self.play_btn.setText("暂停")
            self.play_clicked.emit()

    def _on_stop(self):
        self._is_playing = False
        self._current_time = 0.0
        self.play_btn.setText("播放")
        self.waveform.set_progress(0.0)
        self._update_ui_state()
        self.stop_clicked.emit()

    def _on_reset(self):
        self._current_time = 0.0
        self.waveform.set_progress(0.0)
        self._update_ui_state()

    def _on_export(self):
        if not self._audio_path:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出音频", "generated_speech.wav", "WAV文件 (*.wav)"
        )
        if file_path:
            import shutil
            shutil.copy2(self._audio_path, file_path)

    def update_progress(self, current_time: float):
        self._current_time = current_time
        if self._total_time > 0:
            progress = current_time / self._total_time
            self.waveform.set_progress(progress)
        self._update_ui_state()
