import os
import json
import wave
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QSizePolicy, QProgressBar,
    QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudioInput, QMediaRecorder, QMediaCaptureSession

from ..dialogs import show_warning, show_question, show_error, show_info, ask_text

from .slider_control import SliderControl
from .audio_player_widget import AudioPlayerWidget


class VoiceCloneWorker(QThread):
    finished = Signal(str, float)
    error = Signal(str)

    def __init__(self, audio_path: str, save_path: str):
        super().__init__()
        self.audio_path = audio_path
        self.save_path = save_path

    def run(self):
        try:
            from core import get_voice_cloner

            duration = 0.0
            try:
                with wave.open(self.audio_path, 'rb') as wav:
                    duration = wav.getnframes() / wav.getframerate()
            except (wave.Error, FileNotFoundError):
                pass

            cloner = get_voice_cloner()
            se = cloner.extract_embedding(self.audio_path)
            cloner.save_embedding(se, self.save_path)
            self.finished.emit(self.save_path, duration)
        except Exception as e:
            self.error.emit(str(e))


class GenerateSpeechWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, text: str, voice_info_path: str, output_path: str,
                 speed: float = 1.0, pitch: int = 0, volume: int = 100):
        super().__init__()
        self.text = text
        self.voice_info_path = voice_info_path
        self.output_path = output_path
        self.speed = speed
        self.pitch = pitch
        self.volume = volume

    def run(self):
        try:
            from core import get_voice_cloner
            from ui.audio_processing import AudioProcessor

            cloner = get_voice_cloner()
            voice_info = cloner.load_embedding(self.voice_info_path)
            voice_id = voice_info.get("voice_id")

            if not voice_id:
                raise Exception("未找到有效的voice_id")

            raw_output = self.output_path
            if self.speed != 1.0 or self.pitch != 0 or self.volume != 100:
                raw_output = self.output_path.replace('.wav', '_raw.wav')

            cloner.generate_speech_from_text(self.text, raw_output, voice_id)

            if self.speed != 1.0 or self.pitch != 0 or self.volume != 100:
                AudioProcessor.apply_all(
                    raw_output, self.speed, self.pitch, self.volume, self.output_path
                )
                if os.path.exists(raw_output) and raw_output != self.output_path:
                    os.remove(raw_output)

            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


# ========== 样式常量 ==========

_SECTION_STYLE = """
    QFrame {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
    }
"""
_SECTION_TITLE_STYLE = "font-size: 12px; font-weight: 500; color: #888; background: transparent;"

_RECORD_BTN = """
    QPushButton {
        background-color: #111111;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #333333; }
    QPushButton:pressed { background-color: #000000; }
"""
_RECORD_BTN_ACTIVE = """
    QPushButton {
        background-color: #ef4444;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #dc2626; }
    QPushButton:pressed { background-color: #b91c1c; }
"""
_SAMPLE_BTN = """
    QPushButton {
        background-color: #f5f5f5;
        color: #333333;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #ebebeb; border-color: #d5d5d5; }
    QPushButton:pressed { background-color: #e0e0e0; }
"""
_LISTEN_BTN = """
    QPushButton {
        background-color: #22c55e;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #16a34a; }
    QPushButton:pressed { background-color: #15803d; }
"""
_CLONE_BTN = """
    QPushButton {
        background-color: #111111;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #333333; }
    QPushButton:pressed { background-color: #000000; }
    QPushButton:disabled { background-color: #666666; color: rgba(255,255,255,0.5); }
"""
_GENERATE_BTN = """
    QPushButton {
        background-color: #22c55e;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 14px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #16a34a; }
    QPushButton:pressed { background-color: #15803d; }
    QPushButton:disabled { background-color: #86efac; color: rgba(255,255,255,0.7); }
"""
_VOICE_COMBO_STYLE = """
    QComboBox {
        background: #f9f9f9;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        min-height: 20px;
    }
    QComboBox:hover {
        border-color: #22c55e;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid #e5e5e5;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        background: #f5f5f5;
    }
    QComboBox::down-arrow {
        width: 10px;
        height: 10px;
    }
    QComboBox QAbstractItemView {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 4px;
        selection-background-color: #dcfce7;
        selection-color: #166534;
    }
"""
_HINT_STYLE = "font-size: 12px; color: #999; background: transparent; border: none;"
_PROGRESS_STYLE = """
    QProgressBar {
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        text-align: center;
        background: #f5f5f5;
        height: 22px;
        font-size: 11px;
        color: #666;
    }
    QProgressBar::chunk {
        background: #22c55e;
        border-radius: 5px;
    }
"""


class VoiceClonePanel(QWidget):

    voice_ready = Signal(str)
    speech_generated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._voice_info_path = None
        self._generated_audio_path = None
        self._sample_audio_path = None
        self._media_player = None
        self._audio_output = None
        self._sample_player = None
        self._sample_audio_output = None
        self._input_text = ""
        self._is_recording = False
        self._voices = []
        self._active_voice_idx = -1
        self._voice_profiles_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'voice_profiles'
        )
        self._setup_ui()
        self._setup_recorder()
        self._load_existing_voices()

    def set_input_text(self, text: str):
        self._input_text = text

    def _setup_recorder(self):
        self._capture_session = QMediaCaptureSession()
        self._audio_input = QAudioInput()
        self._capture_session.setAudioInput(self._audio_input)
        self._recorder = QMediaRecorder()
        self._capture_session.setRecorder(self._recorder)
        self._recorder.recorderStateChanged.connect(self._on_recorder_state_changed)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # ===== 音色列表 =====
        voice_section = self._create_voice_list_section()
        main_layout.addWidget(voice_section)

        # ===== 声音样本输入 =====
        sample_section = self._create_sample_section()
        main_layout.addWidget(sample_section)

        # ===== 调节参数 =====
        params_section = self._create_params_section()
        main_layout.addWidget(params_section)

        # ===== 试听音频 =====
        self.player_widget = AudioPlayerWidget()
        self.player_widget.play_clicked.connect(self._on_play)
        self.player_widget.pause_clicked.connect(self._on_pause)
        self.player_widget.stop_clicked.connect(self._on_stop)
        self.player_widget.regenerate_clicked.connect(self._on_generate)
        self.player_widget.save_profile_clicked.connect(self._on_save_profile)
        main_layout.addWidget(self.player_widget)

        # ===== 生成按钮 =====
        self.generate_btn = QPushButton("生成语音")
        self.generate_btn.setFixedHeight(44)
        self.generate_btn.setStyleSheet(_GENERATE_BTN)
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self._on_generate)
        main_layout.addWidget(self.generate_btn)

        self._update_ui_state()

    def _create_voice_list_section(self) -> QWidget:
        section = QFrame()
        section.setStyleSheet(_SECTION_STYLE)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 标题行 + 删除按钮
        title_row = QHBoxLayout()
        title = QLabel("音色列表")
        title.setStyleSheet(_SECTION_TITLE_STYLE)
        title_row.addWidget(title)
        title_row.addStretch()

        self._rename_voice_btn = QPushButton("重命名")
        self._rename_voice_btn.setStyleSheet("""
            QPushButton {
                background: #e0f2fe;
                color: #0369a1;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background: #bae6fd; }
            QPushButton:disabled { background: #f5f5f5; color: #ccc; }
        """)
        self._rename_voice_btn.setCursor(Qt.PointingHandCursor)
        self._rename_voice_btn.setEnabled(False)
        self._rename_voice_btn.clicked.connect(self._on_rename_selected)
        title_row.addWidget(self._rename_voice_btn)

        self._delete_voice_btn = QPushButton("删除")
        self._delete_voice_btn.setStyleSheet("""
            QPushButton {
                background: #fee2e2;
                color: #ef4444;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background: #fecaca; }
            QPushButton:disabled { background: #f5f5f5; color: #ccc; }
        """)
        self._delete_voice_btn.setCursor(Qt.PointingHandCursor)
        self._delete_voice_btn.setEnabled(False)
        self._delete_voice_btn.clicked.connect(self._on_delete_selected)
        title_row.addWidget(self._delete_voice_btn)
        layout.addLayout(title_row)

        # 下拉列表
        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet(_VOICE_COMBO_STYLE)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_selected)
        layout.addWidget(self.voice_combo)

        self.voice_hint = QLabel("克隆后的声音会显示在这里")
        self.voice_hint.setStyleSheet(_HINT_STYLE)
        self.voice_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.voice_hint)

        return section

    def _create_sample_section(self) -> QWidget:
        section = QFrame()
        section.setStyleSheet(_SECTION_STYLE)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("声音样本")
        title.setStyleSheet(_SECTION_TITLE_STYLE)
        layout.addWidget(title)

        # 状态提示
        self.preview_text = QLabel("录制或上传 5-15 秒清晰人声")
        self.preview_text.setStyleSheet("font-size: 12px; color: #999; background: transparent; border: none;")
        self.preview_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_text)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.record_btn = QPushButton("开始录音")
        self.record_btn.setFixedHeight(36)
        self.record_btn.setStyleSheet(_RECORD_BTN)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.clicked.connect(self._on_record_toggle)
        btn_layout.addWidget(self.record_btn)

        self.upload_btn = QPushButton("选择音频")
        self.upload_btn.setFixedHeight(36)
        self.upload_btn.setStyleSheet(_SAMPLE_BTN)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self._on_upload)
        btn_layout.addWidget(self.upload_btn)

        self.listen_btn = QPushButton("聆听")
        self.listen_btn.setFixedHeight(36)
        self.listen_btn.setStyleSheet(_LISTEN_BTN)
        self.listen_btn.setCursor(Qt.PointingHandCursor)
        self.listen_btn.clicked.connect(self._on_listen_sample)
        self.listen_btn.setVisible(False)
        btn_layout.addWidget(self.listen_btn)

        self.clone_btn = QPushButton("开始克隆")
        self.clone_btn.setFixedHeight(36)
        self.clone_btn.setStyleSheet(_CLONE_BTN)
        self.clone_btn.setCursor(Qt.PointingHandCursor)
        self.clone_btn.clicked.connect(self._on_clone)
        self.clone_btn.setVisible(False)
        btn_layout.addWidget(self.clone_btn)

        layout.addLayout(btn_layout)

        # 克隆进度条
        self.clone_progress = QProgressBar()
        self.clone_progress.setStyleSheet(_PROGRESS_STYLE)
        self.clone_progress.setRange(0, 0)
        self.clone_progress.setVisible(False)
        self.clone_progress.setTextVisible(True)
        self.clone_progress.setFormat("正在克隆音色...")
        layout.addWidget(self.clone_progress)

        return section

    def _create_params_section(self) -> QWidget:
        section = QFrame()
        section.setStyleSheet(_SECTION_STYLE)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        title = QLabel("调节参数")
        title.setStyleSheet(_SECTION_TITLE_STYLE)
        layout.addWidget(title)

        self.speed_slider = SliderControl("语速", 0.5, 2.0, 1.0, 0.1, "x")
        self.speed_slider.setMinimumHeight(48)
        layout.addWidget(self.speed_slider)

        self.pitch_slider = SliderControl("音调", -5, 5, 0, 1, "")
        self.pitch_slider.setMinimumHeight(48)
        layout.addWidget(self.pitch_slider)

        self.volume_slider = SliderControl("音量", 0, 200, 150, 1, "%")
        self.volume_slider.setMinimumHeight(48)
        layout.addWidget(self.volume_slider)

        return section

    # ========== 加载已有音色 ==========

    def _load_existing_voices(self):
        if not os.path.exists(self._voice_profiles_dir):
            return

        for filename in sorted(os.listdir(self._voice_profiles_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(self._voice_profiles_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    name = data.get("name", f"音色 {len(self._voices) + 1}")
                    duration = data.get("duration", 0)
                    if duration > 0:
                        mins = int(duration // 60)
                        secs = int(duration % 60)
                        dur_text = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"
                    else:
                        dur_text = "未知"

                    voice = {
                        'path': filepath,
                        'name': name,
                        'duration': dur_text,
                        'duration_sec': duration
                    }
                    self._voices.append(voice)
                except Exception:
                    continue

        if self._voices:
            self.voice_hint.hide()
            for i, voice in enumerate(self._voices):
                self._add_voice_card(voice, i)
            # 自动选中第一个音色
            self._select_voice(0)

    # ========== 录音 ==========

    def _on_record_toggle(self):
        if self._is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        self._record_path = os.path.join(output_dir, f'recording_{uuid.uuid4().hex[:8]}.wav')

        self._recorder.setOutputLocation(QUrl.fromLocalFile(self._record_path))
        self._recorder.record()

    def _stop_recording(self):
        self._recorder.stop()

    def _on_recorder_state_changed(self, state):
        if state == QMediaRecorder.RecordingState:
            self._is_recording = True
            self.record_btn.setText("停止录音")
            self.record_btn.setStyleSheet(_RECORD_BTN_ACTIVE)
            self.preview_text.setText("录音中...点击停止")
        elif state == QMediaRecorder.StoppedState:
            self._is_recording = False
            self.record_btn.setText("开始录音")
            self.record_btn.setStyleSheet(_RECORD_BTN)
            self.preview_text.setText("录制或上传 5-15 秒清晰人声")

            if hasattr(self, '_record_path') and os.path.exists(self._record_path):
                if os.path.getsize(self._record_path) > 1000:
                    self._load_audio(self._record_path)
                else:
                    show_warning(self, "提示", "录音太短，请重试")

    # ========== 文件上传 ==========

    def _on_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.wav *.mp3 *.m4a);;所有文件 (*)"
        )
        if file_path:
            self._load_audio(file_path)

    # ========== 加载音频 ==========

    def _load_audio(self, audio_path: str):
        self._sample_audio_path = audio_path

        duration = 0.0
        try:
            with wave.open(audio_path, 'rb') as wav:
                duration = wav.getnframes() / wav.getframerate()
        except (wave.Error, FileNotFoundError):
            pass

        mins = int(duration // 60)
        secs = int(duration % 60)
        duration_text = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}秒"
        self.preview_text.setText(f"已加载: {os.path.basename(audio_path)} ({duration_text})")

        self.listen_btn.setVisible(True)
        self.clone_btn.setVisible(True)
        self.clone_btn.setEnabled(True)
        self.clone_btn.setText("开始克隆")

    # ========== 聆听样本 ==========

    def _on_listen_sample(self):
        if not self._sample_audio_path or not os.path.exists(self._sample_audio_path):
            return

        if not self._sample_player:
            self._sample_player = QMediaPlayer()
            self._sample_audio_output = QAudioOutput()
            self._sample_player.setAudioOutput(self._sample_audio_output)
            self._sample_player.mediaStatusChanged.connect(self._on_sample_media_status_changed)

        # 根据播放状态切换：播放/暂停
        if self._sample_player.playbackState() == QMediaPlayer.PlayingState:
            self._sample_player.pause()
            self.listen_btn.setText("聆听")
        else:
            # 如果是暂停状态，继续播放；否则从头开始
            if self._sample_player.playbackState() == QMediaPlayer.PausedState:
                self._sample_player.play()
            else:
                self._sample_player.setSource(QUrl.fromLocalFile(self._sample_audio_path))
                self._sample_audio_output.setVolume(1.0)
                self._sample_player.play()
            self.listen_btn.setText("暂停")

    def _on_sample_media_status_changed(self, status):
        """播放结束时重置按钮文字"""
        if status == QMediaPlayer.EndOfMedia:
            self.listen_btn.setText("聆听")

    # ========== 开始克隆 ==========

    def _on_clone(self):
        if not self._sample_audio_path or not os.path.exists(self._sample_audio_path):
            show_warning(self, "提示", "请先录制或上传声音样本")
            return

        self.clone_btn.setEnabled(False)
        self.clone_btn.setText("克隆中...")
        self.clone_progress.setVisible(True)

        os.makedirs(self._voice_profiles_dir, exist_ok=True)
        save_path = os.path.join(self._voice_profiles_dir, f'profile_{uuid.uuid4().hex[:8]}.json')

        self._clone_worker = VoiceCloneWorker(self._sample_audio_path, save_path)
        self._clone_worker.finished.connect(self._on_extract_done)
        self._clone_worker.error.connect(self._on_extract_error)
        self._clone_worker.start()

    def _on_extract_done(self, voice_info_path: str, duration: float):
        self._voice_info_path = voice_info_path

        self.clone_progress.setVisible(False)
        self.clone_btn.setText("开始克隆")
        self.clone_btn.setEnabled(True)

        name = f"音色 {len(self._voices) + 1}"
        mins = int(duration // 60)
        secs = int(duration % 60)
        dur_text = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"

        # 保存名称到配置文件
        try:
            with open(voice_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["name"] = name
            data["duration"] = duration
            with open(voice_info_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        voice = {
            'path': voice_info_path,
            'name': name,
            'duration': dur_text,
            'duration_sec': duration
        }
        self._voices.append(voice)

        self._refresh_voice_list()
        self._select_voice(len(self._voices) - 1)

        self.voice_hint.hide()
        self._update_ui_state()
        self.voice_ready.emit(voice_info_path)

    def _on_extract_error(self, msg: str):
        self.clone_progress.setVisible(False)
        self.clone_btn.setText("开始克隆")
        self.clone_btn.setEnabled(True)
        show_error(self, "错误", f"声音特征提取失败: {msg}")

    def _add_voice_card(self, voice: dict, idx: int):
        item_text = f"{voice['name']}  ({voice['duration']})"
        self.voice_combo.addItem(item_text)

    def _on_voice_selected(self, idx: int):
        if idx < 0 or idx >= len(self._voices):
            self._active_voice_idx = -1
            self._voice_info_path = None
            self._delete_voice_btn.setEnabled(False)
            self._rename_voice_btn.setEnabled(False)
            self._update_ui_state()
            return

        # 先停止当前播放
        if self._sample_player:
            self._sample_player.stop()
            self.listen_btn.setText("聆听")

        self._active_voice_idx = idx
        self._voice_info_path = self._voices[idx]['path']
        self._delete_voice_btn.setEnabled(True)
        self._rename_voice_btn.setEnabled(True)

        # 加载并显示该音色的样本音频
        self._load_voice_sample(self._voices[idx])

        self._update_ui_state()

    def _load_voice_sample(self, voice: dict):
        """加载音色的样本音频用于试听"""
        try:
            with open(voice['path'], 'r', encoding='utf-8') as f:
                data = json.load(f)

            voice_id = data.get("voice_id", "")
            if not voice_id or not voice_id.startswith("data:audio"):
                return

            # 解码 base64 音频数据
            import base64
            header, audio_data = voice_id.split(",", 1)
            audio_bytes = base64.b64decode(audio_data)

            # 保存到临时文件
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'generated')
            os.makedirs(temp_dir, exist_ok=True)

            # 清理之前的临时文件
            if self._sample_audio_path and 'temp_sample_' in self._sample_audio_path:
                try:
                    if os.path.exists(self._sample_audio_path):
                        os.remove(self._sample_audio_path)
                except:
                    pass

            temp_path = os.path.join(temp_dir, f'temp_sample_{uuid.uuid4().hex[:8]}.wav')

            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)

            # 更新声音样本显示
            duration = voice.get('duration_sec', 0)
            if duration == 0:
                try:
                    with wave.open(temp_path, 'rb') as wav:
                        duration = wav.getnframes() / wav.getframerate()
                except:
                    pass

            mins = int(duration // 60)
            secs = int(duration % 60)
            duration_text = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}秒"

            self._sample_audio_path = temp_path
            self.preview_text.setText(f"当前音色: {voice['name']} ({duration_text})")
            self.listen_btn.setVisible(True)
            self.clone_btn.setVisible(False)  # 选择已有音色时不需要克隆

            # 重置播放器状态，确保下次播放使用新音频
            if self._sample_player:
                self._sample_player.stop()

        except Exception as e:
            print(f"加载音色样本失败: {e}")

    def _on_rename_selected(self):
        idx = self.voice_combo.currentIndex()
        if idx < 0 or idx >= len(self._voices):
            return

        voice = self._voices[idx]
        new_name, ok = ask_text(self, "重命名音色", "输入新名称:", voice['name'])

        if ok and new_name:
            new_name = new_name.strip()
            if new_name and new_name != voice['name']:
                # 更新配置文件
                try:
                    with open(voice['path'], 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data["name"] = new_name
                    with open(voice['path'], 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

                # 更新内存中的名称
                self._voices[idx]['name'] = new_name

                # 刷新下拉列表
                self._refresh_voice_list()
                self._select_voice(idx)

    def _select_voice(self, idx: int):
        if idx < 0 or idx >= len(self._voices):
            return

        self._active_voice_idx = idx
        self._voice_info_path = self._voices[idx]['path']
        self.voice_combo.setCurrentIndex(idx)
        self._delete_voice_btn.setEnabled(True)
        self._update_ui_state()

    def _on_delete_selected(self):
        idx = self.voice_combo.currentIndex()
        if idx < 0 or idx >= len(self._voices):
            return

        voice = self._voices[idx]

        reply = show_question(
            self, "确认删除",
            f"确定要删除音色 \"{voice['name']}\" 吗？"
        )

        if reply:
            # 删除配置文件
            try:
                if os.path.exists(voice['path']):
                    os.remove(voice['path'])
            except Exception:
                pass

            # 从列表移除
            self._voices.pop(idx)
            self.voice_combo.removeItem(idx)

            # 重置选中状态
            if self._active_voice_idx == idx:
                self._active_voice_idx = -1
                self._voice_info_path = None
            elif self._active_voice_idx > idx:
                self._active_voice_idx -= 1

            self._delete_voice_btn.setEnabled(False)
            self._rename_voice_btn.setEnabled(False)
            self._update_ui_state()

    def _refresh_voice_list(self):
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        for voice in self._voices:
            item_text = f"{voice['name']}  ({voice['duration']})"
            self.voice_combo.addItem(item_text)

        if 0 <= self._active_voice_idx < len(self._voices):
            self.voice_combo.setCurrentIndex(self._active_voice_idx)

        self.voice_combo.blockSignals(False)

        if not self._voices:
            self.voice_hint.show()
        else:
            self.voice_hint.hide()

    # ========== 参数 ==========

    def get_speed(self) -> float:
        return self.speed_slider.value()

    def get_pitch(self) -> int:
        return int(self.pitch_slider.value())

    def get_volume(self) -> int:
        return int(self.volume_slider.value())

    # ========== 生成语音 ==========

    def _on_generate(self):
        text = self._input_text.strip()
        if not text:
            show_warning(self, "提示", "请先输入或识别口稿文字")
            return

        if not self._voice_info_path or not os.path.exists(self._voice_info_path):
            show_warning(self, "提示", "请先选择一个音色")
            return

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")

        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'generated_{uuid.uuid4().hex[:8]}.wav')

        speed = self.speed_slider.value()
        pitch = int(self.pitch_slider.value())
        volume = int(self.volume_slider.value())

        self._generate_worker = GenerateSpeechWorker(
            text, self._voice_info_path, output_path, speed, pitch, volume
        )
        self._generate_worker.finished.connect(self._on_generate_done)
        self._generate_worker.error.connect(self._on_generate_error)
        self._generate_worker.start()

    def _on_generate_done(self, output_path: str):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成语音")
        self._generated_audio_path = output_path
        self.player_widget.load_audio(output_path)
        self._update_ui_state()
        self.speech_generated.emit(output_path)

    def _on_generate_error(self, msg: str):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成语音")
        show_error(self, "错误", f"语音生成失败: {msg}")

    # ========== 播放控制 ==========

    def _on_play(self):
        if not self._generated_audio_path:
            return
        if not self._media_player:
            self._media_player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._media_player.setAudioOutput(self._audio_output)
            self._media_player.positionChanged.connect(self._on_position_changed)

        self._media_player.setSource(QUrl.fromLocalFile(self._generated_audio_path))
        self._audio_output.setVolume(1.0)
        self._media_player.play()

    def _on_pause(self):
        if self._media_player:
            self._media_player.pause()

    def _on_stop(self):
        if self._media_player:
            self._media_player.stop()

    def _on_position_changed(self, position: int):
        if self._media_player and self._media_player.duration() > 0:
            current_time = position / 1000.0
            self.player_widget.update_progress(current_time)

    # ========== 保存配置 ==========

    def _on_save_profile(self):
        if not self._voice_info_path:
            return

        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "保存配置", "输入配置名称:")
        if ok and name:
            with open(self._voice_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["name"] = name
            with open(self._voice_info_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if 0 <= self._active_voice_idx < len(self._voices):
                self._voices[self._active_voice_idx]['name'] = name
                self._refresh_voice_list()
                self._select_voice(self._active_voice_idx)

            show_info(self, "成功", f"配置 '{name}' 已保存")

    # ========== 状态更新 ==========

    def _update_ui_state(self):
        has_voice = self._voice_info_path is not None and os.path.exists(self._voice_info_path)
        self.generate_btn.setEnabled(has_voice)
