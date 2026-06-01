import os
import subprocess
import shutil
import uuid
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QScrollArea, QSizePolicy, QProgressBar,
    QSlider, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer
from PySide6.QtGui import QFont

from .styles import MAIN_STYLE
from .toast import show_toast
from core import Downloader, Recognizer
from core.lip_sync import LipSyncer
from config import DATA_DIR, FFMPEG_PATH

# 文本保存目录
TEXT_DIR = os.path.join(DATA_DIR, "text")
os.makedirs(TEXT_DIR, exist_ok=True)

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False

from .components.voice_clone_panel import VoiceClonePanel


# ========== 按钮样式 ==========

GREEN_BTN = """
    QPushButton {
        background-color: #22c55e;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #16a34a; }
    QPushButton:pressed { background-color: #15803d; }
    QPushButton:disabled { background-color: #86efac; color: rgba(255,255,255,0.7); }
"""

BLACK_BTN = """
    QPushButton {
        background-color: #111111;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #333333; }
    QPushButton:pressed { background-color: #000000; }
    QPushButton:disabled { background-color: #666666; color: rgba(255,255,255,0.5); }
"""

DEFAULT_BTN = """
    QPushButton {
        background-color: #f5f5f5;
        color: #333333;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #ebebeb; border-color: #d5d5d5; }
    QPushButton:pressed { background-color: #e0e0e0; border-color: #cccccc; }
    QPushButton:disabled { background-color: #f9f9f9; color: #bbbbbb; border-color: #eeeeee; }
"""


# ========== 工作线程 ==========

class DownloadWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            dl = Downloader()
            audio_path = dl.download_audio(self.url)
            self.finished.emit(audio_path)
        except Exception as e:
            self.error.emit(str(e))


class RecognizeWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, audio_path: str):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        try:
            rec = Recognizer()
            text = rec.transcribe(self.audio_path)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))


class PolishWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            from core.polisher import Polisher
            polisher = Polisher()
            result = polisher.polish(self.text)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class VideoComposerWorker(QThread):
    """视频合成：唇形同步或音轨替换"""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, video_path: str, audio_path: str, output_path: str, use_lipsync: bool = False):
        super().__init__()
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.use_lipsync = use_lipsync

    def run(self):
        try:
            if self.use_lipsync:
                lip_syncer = LipSyncer()
                lip_syncer.sync_with_fallback(self.video_path, self.audio_path, self.output_path)
            else:
                # 直接音轨替换
                lip_syncer = LipSyncer()
                lip_syncer._replace_audio(self.video_path, self.audio_path, self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


# ========== 主窗口 ==========

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("口播工作台")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        self._drag_pos = None
        self._is_dragging = False
        self._original_video_path = None
        self._generated_audio_path = None
        self._composed_video_path = None

        self.setStyleSheet(MAIN_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 背景容器
        self._bg = QWidget()
        self._bg.setObjectName("appBackground")
        bg_layout = QVBoxLayout(self._bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(0)
        main_layout.addWidget(self._bg)

        # ===== 标题栏 =====
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(44)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 16, 0)

        title = QLabel("口播工作台")
        title.setObjectName("titleLabel")
        title_layout.addWidget(title)
        title_layout.addStretch()

        close_btn = QPushButton("x")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        bg_layout.addWidget(title_bar)

        # ===== 三栏内容区 =====
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)

        # 左栏
        content_layout.addWidget(self._create_left_panel(), stretch=1)

        sep1 = QFrame()
        sep1.setObjectName("separator")
        sep1.setFixedWidth(1)
        content_layout.addWidget(sep1)

        # 中栏
        content_layout.addWidget(self._create_center_panel(), stretch=1)

        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFixedWidth(1)
        content_layout.addWidget(sep2)

        # 右栏
        content_layout.addWidget(self._create_right_panel(), stretch=1)

        bg_layout.addWidget(content, stretch=1)

    # ==================== 左栏 ====================

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("文案提取与润色")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        layout.addSpacing(4)

        # 输入框
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("粘贴抖音视频分享链接...")
        self.link_input.setFixedHeight(38)
        layout.addWidget(self.link_input)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.extract_btn = QPushButton("提取文案")
        self.extract_btn.setStyleSheet(GREEN_BTN)
        self.extract_btn.setFixedHeight(38)
        self.extract_btn.setCursor(Qt.PointingHandCursor)
        self.extract_btn.clicked.connect(self._on_extract)
        btn_row.addWidget(self.extract_btn)

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet(DEFAULT_BTN)
        clear_btn.setFixedHeight(38)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)

        # 箭头
        layout.addWidget(self._create_arrow())

        # 音频转文字
        label1 = QLabel("音频转文字")
        label1.setObjectName("sectionLabel")
        layout.addWidget(label1)

        self.recognized_text = QTextEdit()
        self.recognized_text.setPlaceholderText("视频音频转换后的文字将显示在这里...")
        self.recognized_text.setMinimumHeight(120)
        layout.addWidget(self.recognized_text)

        # 润色按钮
        self.polish_btn = QPushButton("润色")
        self.polish_btn.setStyleSheet(BLACK_BTN)
        self.polish_btn.setFixedHeight(36)
        self.polish_btn.setCursor(Qt.PointingHandCursor)
        self.polish_btn.clicked.connect(self._on_polish)
        layout.addWidget(self.polish_btn)

        # 箭头
        layout.addWidget(self._create_arrow())

        # 润色口稿
        label2 = QLabel("润色口稿")
        label2.setObjectName("sectionLabel")
        layout.addWidget(label2)

        self.polished_text = QTextEdit()
        self.polished_text.setPlaceholderText("AI 润色后的口播稿将显示在这里...")
        self.polished_text.setMinimumHeight(120)
        self.polished_text.textChanged.connect(self._on_polished_text_changed)
        layout.addWidget(self.polished_text)

        return panel

    # ==================== 中栏 ====================

    def _create_center_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("声音克隆与配音")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        layout.addSpacing(4)

        # 嵌入 VoiceClonePanel
        self._voice_clone_panel = VoiceClonePanel()
        self._voice_clone_panel.speech_generated.connect(self._on_speech_generated)
        layout.addWidget(self._voice_clone_panel, stretch=1)

        return panel

    # ==================== 右栏 ====================

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("视频合成与预览")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        layout.addSpacing(4)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.upload_btn = QPushButton("上传原视频")
        self.upload_btn.setStyleSheet(DEFAULT_BTN)
        self.upload_btn.setFixedHeight(38)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self._on_select_video)
        btn_row.addWidget(self.upload_btn)

        self.compose_btn = QPushButton("开始合成")
        self.compose_btn.setStyleSheet(GREEN_BTN)
        self.compose_btn.setFixedHeight(38)
        self.compose_btn.setCursor(Qt.PointingHandCursor)
        self.compose_btn.clicked.connect(self._on_compose)
        btn_row.addWidget(self.compose_btn)

        self.regenerate_btn = QPushButton("重新生成")
        self.regenerate_btn.setStyleSheet(DEFAULT_BTN)
        self.regenerate_btn.setFixedHeight(38)
        self.regenerate_btn.setCursor(Qt.PointingHandCursor)
        self.regenerate_btn.clicked.connect(self._on_compose)
        self.regenerate_btn.setEnabled(False)
        btn_row.addWidget(self.regenerate_btn)

        self.download_btn = QPushButton("下载到本地")
        self.download_btn.setStyleSheet(DEFAULT_BTN)
        self.download_btn.setFixedHeight(38)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.clicked.connect(self._on_download)
        btn_row.addWidget(self.download_btn)

        layout.addLayout(btn_row)

        # 唇形同步选项
        lipsync_row = QHBoxLayout()
        lipsync_row.setSpacing(8)

        self._lipsync_checkbox = QCheckBox("启用唇形同步（需要较强GPU，处理较慢）")
        self._lipsync_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #666;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #22c55e;
                border-color: #22c55e;
            }
        """)
        lipsync_row.addWidget(self._lipsync_checkbox)
        lipsync_row.addStretch()
        layout.addLayout(lipsync_row)

        # 合成进度条
        self._compose_progress = QProgressBar()
        self._compose_progress.setFixedHeight(6)
        self._compose_progress.setRange(0, 0)  # 不确定模式
        self._compose_progress.setTextVisible(False)
        self._compose_progress.setStyleSheet("""
            QProgressBar {
                background-color: #e5e5e5;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #22c55e;
                border-radius: 3px;
            }
        """)
        self._compose_progress.hide()
        layout.addWidget(self._compose_progress)

        # 原视频标签
        video_label = QLabel("原视频")
        video_label.setObjectName("sectionLabel")
        layout.addWidget(video_label)

        # 视频预览区
        if HAS_VIDEO:
            self._video_player = QMediaPlayer()
            self._video_audio_output = QAudioOutput()
            self._video_audio_output.setVolume(2.0)
            self._video_player.setAudioOutput(self._video_audio_output)

            self._video_widget = QVideoWidget()
            self._video_widget.setMinimumHeight(200)
            self._video_widget.setStyleSheet("background-color: #1a1a1a; border-radius: 10px;")
            self._video_player.setVideoOutput(self._video_widget)

            # 占位提示（视频加载后隐藏）
            self._video_placeholder = QLabel("上传视频后自动播放", self._video_widget)
            self._video_placeholder.setAlignment(Qt.AlignCenter)
            self._video_placeholder.setStyleSheet("font-size: 13px; color: #666; background: transparent;")
            self._video_placeholder.setGeometry(0, 0, 400, 100)
            self._video_placeholder.move(
                (self._video_widget.width() - self._video_placeholder.width()) // 2,
                (self._video_widget.height() - self._video_placeholder.height()) // 2
            )

            self._video_player.positionChanged.connect(self._on_video_position_changed)
            self._video_player.durationChanged.connect(self._on_video_duration_changed)
            self._video_player.mediaStatusChanged.connect(self._on_video_media_status_changed)

            layout.addWidget(self._video_widget, stretch=1)

            # 视频控制栏
            video_ctrl = QHBoxLayout()
            video_ctrl.setSpacing(8)

            self._video_play_btn = QPushButton("播放")
            self._video_play_btn.setFixedHeight(32)
            self._video_play_btn.setStyleSheet("""
                QPushButton {
                    background: #111111;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 4px 16px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover { background: #333; }
            """)
            self._video_play_btn.setCursor(Qt.PointingHandCursor)
            self._video_play_btn.clicked.connect(self._on_video_play_pause)
            video_ctrl.addWidget(self._video_play_btn)

            self._video_slider = QSlider(Qt.Horizontal)
            self._video_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: none;
                    height: 4px;
                    background: #e5e5e5;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    background: #22c55e;
                    border: none;
                    width: 12px;
                    height: 12px;
                    margin: -4px 0;
                    border-radius: 6px;
                }
                QSlider::sub-page:horizontal {
                    background: #22c55e;
                    border-radius: 2px;
                }
            """)
            self._video_slider.sliderMoved.connect(self._on_video_slider_moved)
            self._video_slider.sliderPressed.connect(self._on_video_slider_pressed)
            self._video_slider.sliderReleased.connect(self._on_video_slider_released)
            self._video_slider_pos = 0
            video_ctrl.addWidget(self._video_slider, stretch=1)

            self._video_time_label = QLabel("0:00 / 0:00")
            self._video_time_label.setStyleSheet("font-size: 11px; color: #666; background: transparent;")
            self._video_time_label.setFixedWidth(80)
            video_ctrl.addWidget(self._video_time_label)

            layout.addLayout(video_ctrl)
        else:
            placeholder = QLabel("视频播放需要 PySide6 QtMultimedia")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 13px; color: #999; padding: 40px;")
            layout.addWidget(placeholder, stretch=1)

        # 状态栏
        self._status_label = QLabel("")
        self._status_label.setObjectName("sectionLabel")
        self._status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status_label)

        return panel

    # ==================== 辅助方法 ====================

    def _create_arrow(self) -> QLabel:
        arrow = QLabel("↓")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("color: #cccccc; font-size: 14px; background: transparent;")
        return arrow

    # ==================== 左栏事件 ====================

    def _on_extract(self):
        url = self.link_input.text().strip()
        if not url:
            self.recognized_text.setPlainText("请先粘贴视频链接")
            return
        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("下载中...")
        self.recognized_text.setPlainText("正在下载音频...")

        self._worker = DownloadWorker(url)
        self._worker.finished.connect(self._on_download_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_download_done(self, audio_path: str):
        self.recognized_text.setPlainText("正在识别文字...")
        self._worker = RecognizeWorker(audio_path)
        self._worker.finished.connect(self._on_recognize_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_recognize_done(self, text: str):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("提取文案")
        self.recognized_text.setPlainText(text or "未识别到文字")

        if text:
            filename = f"recognized_{uuid.uuid4().hex[:8]}.txt"
            filepath = os.path.join(TEXT_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            show_toast(self, f"识别完成，已保存到: {filepath}")

    def _on_error(self, msg: str):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("提取文案")
        self.recognized_text.setPlainText(f"错误: {msg}")

    def _on_polish(self):
        text = self.recognized_text.toPlainText().strip()
        if not text:
            show_toast(self, "请先提取文案")
            return
        self.polish_btn.setEnabled(False)
        self.polish_btn.setText("润色中...")
        self._polish_worker = PolishWorker(text)
        self._polish_worker.finished.connect(self._on_polish_done)
        self._polish_worker.error.connect(self._on_polish_error)
        self._polish_worker.start()

    def _on_polish_done(self, text: str):
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText("润色")
        self.polished_text.setPlainText(text or "润色未返回结果")
        if text:
            filename = f"polished_{uuid.uuid4().hex[:8]}.txt"
            filepath = os.path.join(TEXT_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            show_toast(self, f"润色完成，已保存到: {filepath}")
            if self._voice_clone_panel:
                self._voice_clone_panel.set_input_text(text)

    def _on_polish_error(self, msg: str):
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText("润色")
        self.polished_text.setPlainText(f"润色错误: {msg}")

    def _on_clear(self):
        self.link_input.clear()
        self.recognized_text.clear()
        self.polished_text.clear()

    def _on_polished_text_changed(self):
        """润色口稿内容变化时，同步到配音区域"""
        text = self.polished_text.toPlainText().strip()
        if text and self._voice_clone_panel:
            self._voice_clone_panel.set_input_text(text)

    # ==================== 中栏事件 ====================

    def _on_speech_generated(self, audio_path: str):
        self._generated_audio_path = audio_path
        show_toast(self, f"配音生成完成，已保存到: {audio_path}")

    # ==================== 右栏事件 ====================

    def _on_select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mov *.avi);;所有文件 (*)"
        )
        if file_path:
            self._original_video_path = file_path
            name = os.path.basename(file_path)
            self.upload_btn.setText(f"已选择: {name[:15]}...")
            self._status_label.setText(f"原视频: {name}")

            if HAS_VIDEO and self._video_player:
                self._video_player.setSource(QUrl.fromLocalFile(file_path))
                QTimer.singleShot(100, self._video_player.play)
                if self._video_placeholder:
                    self._video_placeholder.hide()

            show_toast(self, f"已加载: {name}")

    def _on_video_position_changed(self, position: int):
        if not self._video_slider.isSliderDown():
            self._video_slider.setValue(position)
        self._update_video_time_label(position, self._video_player.duration())

    def _on_video_duration_changed(self, duration: int):
        self._video_slider.setRange(0, duration)
        self._update_video_time_label(0, duration)

    def _update_video_time_label(self, position: int, duration: int):
        def format_time(ms):
            s = ms // 1000
            m = s // 60
            s = s % 60
            return f"{m}:{s:02d}"
        self._video_time_label.setText(f"{format_time(position)} / {format_time(duration)}")

    def _on_video_play_pause(self):
        if not HAS_VIDEO or not self._video_player:
            return
        if self._video_player.playbackState() == QMediaPlayer.PlayingState:
            self._video_player.pause()
            self._video_play_btn.setText("播放")
        else:
            self._video_player.play()
            self._video_play_btn.setText("暂停")

    def _on_video_slider_pressed(self):
        pass

    def _on_video_slider_released(self):
        pos = self._video_slider.value()
        self._video_player.setPosition(pos)

    def _on_video_slider_moved(self, position: int):
        pass

    def _on_video_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self._video_play_btn.setText("播放")
            self._video_slider.setValue(0)

    def _on_compose(self):
        if not self._original_video_path:
            show_toast(self, "请先上传原视频")
            return
        if not self._generated_audio_path:
            show_toast(self, "请先生成配音")
            return

        self.compose_btn.setEnabled(False)
        self.compose_btn.setText("合成中...")
        self.regenerate_btn.setEnabled(False)
        self._status_label.setText("正在合成视频...")
        self._compose_progress.show()

        output_dir = os.path.join(DATA_DIR, "generated")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"composed_{uuid.uuid4().hex[:8]}.mp4")

        use_lipsync = self._lipsync_checkbox.isChecked()

        self._compose_worker = VideoComposerWorker(
            self._original_video_path, self._generated_audio_path, output_path, use_lipsync
        )
        self._compose_worker.finished.connect(self._on_compose_done)
        self._compose_worker.error.connect(self._on_compose_error)
        self._compose_worker.start()

    def _on_compose_done(self, path: str):
        self.compose_btn.setEnabled(True)
        self.compose_btn.setText("开始合成")
        self.regenerate_btn.setEnabled(True)
        self._compose_progress.hide()
        self._composed_video_path = path
        name = os.path.basename(path)
        self._status_label.setText(f"合成完成: {name}")

        if HAS_VIDEO and self._video_player:
            self._video_player.setSource(QUrl.fromLocalFile(path))
            QTimer.singleShot(100, self._video_player.play)

        show_toast(self, f"视频合成完成，已保存到: {path}")

    def _on_compose_error(self, msg: str):
        self.compose_btn.setEnabled(True)
        self.compose_btn.setText("开始合成")
        self.regenerate_btn.setEnabled(False)
        self._compose_progress.hide()
        self._status_label.setText(f"合成失败: {msg}")
        show_toast(self, f"合成失败: {msg}")

    def _on_download(self):
        source = self._composed_video_path or self._original_video_path
        if not source:
            show_toast(self, "没有可下载的视频")
            return

        default_name = os.path.basename(source)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "下载视频", default_name,
            "MP4 文件 (*.mp4);;所有文件 (*)"
        )
        if file_path:
            try:
                shutil.copy2(source, file_path)
                show_toast(self, f"已保存到: {os.path.basename(file_path)}")
            except Exception as e:
                show_toast(self, f"保存失败: {e}")

    # ==================== 窗口拖拽 ====================

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < 44:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        self._drag_pos = None
