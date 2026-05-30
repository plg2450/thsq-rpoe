import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, QPoint, QThread, Signal
from PySide6.QtGui import QFont

from .components import (
    GlassCard, GlassButton, GlassPrimaryButton,
    GlassInput, GlassTextEdit, VideoPlayer,
    VoiceClonePanel
)
from .styles import MAIN_STYLE
from core import Downloader, Recognizer, Polisher, get_voice_cloner


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
            polisher = Polisher()
            result = polisher.polish(self.text)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("口播助手")
        self.setMinimumSize(1100, 680)
        self.resize(1280, 780)

        self._drag_pos = None
        self._is_dragging = False

        self.setStyleSheet(MAIN_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 背景容器
        self._bg = QWidget()
        self._bg.setStyleSheet("""
            QWidget {
                background: #F5F5F8;
                border-radius: 16px;
            }
        """)
        bg_layout = QVBoxLayout(self._bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(0)
        main_layout.addWidget(self._bg)

        # ===== 自定义标题栏 =====
        title_bar = self._create_title_bar()
        bg_layout.addWidget(title_bar)

        # ===== 三栏内容区 =====
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(24, 12, 24, 24)
        content_layout.setSpacing(20)

        # 左栏
        left_col = self._create_left_column()
        content_layout.addWidget(left_col, stretch=3)

        # 分割线
        sep1 = QFrame()
        sep1.setObjectName("separator")
        sep1.setFixedWidth(1)
        content_layout.addWidget(sep1)

        # 中栏
        mid_col = self._create_mid_column()
        content_layout.addWidget(mid_col, stretch=3)

        # 分割线
        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFixedWidth(1)
        content_layout.addWidget(sep2)

        # 右栏
        right_col = self._create_right_column()
        content_layout.addWidget(right_col, stretch=4)

        bg_layout.addWidget(content, stretch=1)

    # ------------------------------------------------------------------ title bar
    def _create_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("titleBar")
        bar.setFixedHeight(48)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("🎬 口播助手")
        title.setObjectName("titleLabel")
        bar_layout.addWidget(title)
        bar_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.close)
        bar_layout.addWidget(close_btn)

        return bar

    # ------------------------------------------------------------------ left column
    def _create_left_column(self) -> QWidget:
        col = QWidget()
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 卡片1：粘贴链接
        card1 = GlassCard("粘贴同行视频链接")
        self.link_input = GlassInput("粘贴抖音/快手分享链接...")
        card1.layout().addWidget(self.link_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.extract_btn = GlassPrimaryButton("提取文案")
        self.extract_btn.clicked.connect(self._on_extract)
        btn_row.addWidget(self.extract_btn)
        card1.layout().addLayout(btn_row)
        layout.addWidget(card1)

        # 卡片2：识别结果
        card2 = GlassCard("识别文案")
        self.recognized_text = GlassTextEdit("识别出的文字将显示在这里...")
        self.recognized_text.setMinimumHeight(140)
        card2.layout().addWidget(self.recognized_text)
        layout.addWidget(card2)

        # 卡片3：润色口稿
        card3 = GlassCard("润色口稿")
        self.polished_text = GlassTextEdit("润色后的口播稿将显示在这里...")
        self.polished_text.setMinimumHeight(140)
        card3.layout().addWidget(self.polished_text)

        polish_row = QHBoxLayout()
        polish_row.setSpacing(8)
        self.polish_btn = GlassButton("润色")
        self.polish_btn.clicked.connect(self._on_polish)
        polish_row.addWidget(self.polish_btn)
        polish_row.addStretch()
        card3.layout().addLayout(polish_row)
        layout.addWidget(card3)

        return col

    # ------------------------------------------------------------------ mid column
    def _create_mid_column(self) -> QWidget:
        col = QWidget()
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 声音克隆面板
        self.voice_clone_panel = VoiceClonePanel()
        self.voice_clone_panel.voice_ready.connect(self._on_voice_ready)
        self.voice_clone_panel.speech_generated.connect(self._on_speech_generated)
        layout.addWidget(self.voice_clone_panel)

        layout.addStretch()

        return col

    # ------------------------------------------------------------------ right column
    def _create_right_column(self) -> QWidget:
        col = QWidget()
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 视频播放器
        card1 = GlassCard("原视频预览")
        self.video_player = VideoPlayer()
        self.video_player.setMinimumHeight(220)
        card1.layout().addWidget(self.video_player)

        upload_row = QHBoxLayout()
        upload_row.setSpacing(8)
        self.upload_video_btn = GlassButton("选择视频文件")
        upload_row.addWidget(self.upload_video_btn)
        upload_row.addStretch()
        card1.layout().addLayout(upload_row)
        layout.addWidget(card1)

        # 口型同步
        card2 = GlassCard("口型同步 & 导出")
        hint2 = QLabel("将原视频的口型与新配音自动匹配，生成最终视频")
        hint2.setStyleSheet("font-size: 12px; color: #888; background: transparent; border: none;")
        hint2.setWordWrap(True)
        card2.layout().addWidget(hint2)

        from PySide6.QtWidgets import QProgressBar
        self.lipsync_progress = QProgressBar()
        self.lipsync_progress.setValue(0)
        self.lipsync_progress.setFixedHeight(14)
        card2.layout().addWidget(self.lipsync_progress)

        self.lipsync_btn = GlassPrimaryButton("开始口型同步")
        card2.layout().addWidget(self.lipsync_btn)

        export_row = QHBoxLayout()
        export_row.setSpacing(8)
        self.preview_btn = GlassButton("预览成品")
        self.preview_btn.setEnabled(False)
        self.export_btn = GlassButton("导出视频")
        self.export_btn.setEnabled(False)
        export_row.addWidget(self.preview_btn)
        export_row.addWidget(self.export_btn)
        card2.layout().addLayout(export_row)

        layout.addWidget(card2)
        layout.addStretch()

        return col

    # ------------------------------------------------------------------ extract text
    def _on_extract(self):
        url = self.link_input.text().strip()
        if not url:
            self.recognized_text.setPlainText("请先粘贴视频链接")
            return

        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("下载中...")
        self.recognized_text.setPlainText("正在下载音频...")

        self._download_worker = DownloadWorker(url)
        self._download_worker.finished.connect(self._on_download_done)
        self._download_worker.error.connect(self._on_download_error)
        self._download_worker.start()

    def _on_download_done(self, audio_path: str):
        self.recognized_text.setPlainText("音频下载完成，正在识别文字...")
        self.extract_btn.setText("识别中...")

        self._recognize_worker = RecognizeWorker(audio_path)
        self._recognize_worker.finished.connect(self._on_recognize_done)
        self._recognize_worker.error.connect(self._on_recognize_error)
        self._recognize_worker.start()

    def _on_download_error(self, msg: str):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("提取文案")
        self.recognized_text.setPlainText(f"下载失败: {msg}")

    def _on_recognize_done(self, text: str):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("提取文案")
        self.recognized_text.setPlainText(text if text else "未识别到文字内容")

    def _on_recognize_error(self, msg: str):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("提取文案")
        self.recognized_text.setPlainText(f"识别失败: {msg}")

    # ------------------------------------------------------------------ polish text
    def _on_polish(self):
        text = self.recognized_text.toPlainText().strip()
        if not text:
            self.polished_text.setPlainText("请先识别文案")
            return

        self.polish_btn.setEnabled(False)
        self.polish_btn.setText("润色中...")
        self.polished_text.setPlainText("正在润色口稿...")

        self._polish_worker = PolishWorker(text)
        self._polish_worker.finished.connect(self._on_polish_done)
        self._polish_worker.error.connect(self._on_polish_error)
        self._polish_worker.start()

    def _on_polish_done(self, text: str):
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText("润色")
        self.polished_text.setPlainText(text if text else "润色失败")

    def _on_polish_error(self, msg: str):
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText("润色")
        self.polished_text.setPlainText(f"润色失败: {msg}")

    # ------------------------------------------------------------------ voice cloning callbacks
    def _on_voice_ready(self, voice_info_path: str):
        """声音特征提取完成"""
        pass

    def _on_speech_generated(self, audio_path: str):
        """语音生成完成"""
        pass

    # ------------------------------------------------------------------ window drag
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < 48:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        self._drag_pos = None

    # ------------------------------------------------------------------ keyboard shortcut
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Slash and event.modifiers() == Qt.ControlModifier:
            self._reset_all()
            return
        super().keyPressEvent(event)

    def _reset_all(self):
        self.link_input.clear()
        self.recognized_text.setPlainText("")
        self.polished_text.setPlainText("")
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("提取文案")
        self.polish_btn.setEnabled(True)
        self.polish_btn.setText("润色")
        self.lipsync_progress.setValue(0)
        self.preview_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
