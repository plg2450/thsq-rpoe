import os
import wave
import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QProgressBar, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

from .slider_control import SliderControl
from .audio_player_widget import AudioPlayerWidget
from .voice_profile_selector import VoiceProfileSelector


class VoiceCloneWorker(QThread):
    """声音特征提取线程"""
    finished = Signal(str, float)  # voice_info_path, duration
    error = Signal(str)

    def __init__(self, audio_path: str, save_path: str):
        super().__init__()
        self.audio_path = audio_path
        self.save_path = save_path

    def run(self):
        try:
            from core import get_voice_cloner

            # 获取音频时长
            duration = 0.0
            try:
                with wave.open(self.audio_path, 'rb') as wav:
                    duration = wav.getnframes() / wav.getframerate()
            except:
                pass

            cloner = get_voice_cloner()
            se = cloner.extract_embedding(self.audio_path)
            cloner.save_embedding(se, self.save_path)
            self.finished.emit(self.save_path, duration)
        except Exception as e:
            self.error.emit(str(e))


class GenerateSpeechWorker(QThread):
    """语音生成线程"""
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

            # 加载voice_id
            voice_info = cloner.load_embedding(self.voice_info_path)
            voice_id = voice_info.get("voice_id")

            if not voice_id:
                raise Exception("未找到有效的voice_id")

            # 生成原始音频
            raw_output = self.output_path
            if self.speed != 1.0 or self.pitch != 0 or self.volume != 100:
                raw_output = self.output_path.replace('.wav', '_raw.wav')

            cloner.generate_speech_from_text(self.text, raw_output, voice_id)

            # 应用音频处理
            if self.speed != 1.0 or self.pitch != 0 or self.volume != 100:
                AudioProcessor.apply_all(
                    raw_output, self.speed, self.pitch, self.volume, self.output_path
                )
                # 清理临时文件
                if os.path.exists(raw_output) and raw_output != self.output_path:
                    os.remove(raw_output)

            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class VoiceClonePanel(QWidget):
    """声音克隆面板"""

    # 信号
    voice_ready = Signal(str)  # voice_info_path
    speech_generated = Signal(str)  # audio_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._voice_info_path = None
        self._generated_audio_path = None
        self._media_player = None
        self._audio_output = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Section A: 声音配置选择器
        self.profile_selector = VoiceProfileSelector()
        self.profile_selector.profile_selected.connect(self._on_profile_selected)
        self.profile_selector.new_profile_requested.connect(self._on_new_profile)
        layout.addWidget(self.profile_selector)

        # Section B: 声音样本输入
        input_section = self._create_input_section()
        layout.addWidget(input_section)

        # Section C: 调节参数
        params_section = self._create_params_section()
        layout.addWidget(params_section)

        # Section D: 音频播放器
        self.player_widget = AudioPlayerWidget()
        self.player_widget.play_clicked.connect(self._on_play)
        self.player_widget.pause_clicked.connect(self._on_pause)
        self.player_widget.stop_clicked.connect(self._on_stop)
        self.player_widget.regenerate_clicked.connect(self._on_generate)
        self.player_widget.save_profile_clicked.connect(self._on_save_as_profile)
        layout.addWidget(self.player_widget)

        # Section E: 生成按钮
        generate_section = self._create_generate_section()
        layout.addWidget(generate_section)

        scroll.setWidget(content)
        main_layout.addWidget(scroll, stretch=1)

        # 初始状态
        self._update_ui_state()

    def _create_input_section(self) -> QWidget:
        """创建声音样本输入区域"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid rgba(0, 0, 0, 5);
                border-radius: 12px;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 标题
        title = QLabel("声音样本")
        title.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #333;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(title)

        # 音频预览区
        self.audio_preview = QFrame()
        self.audio_preview.setMinimumHeight(80)
        self.audio_preview.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 3);
                border: 2px dashed rgba(180, 180, 200, 80);
                border-radius: 12px;
            }
        """)
        preview_layout = QVBoxLayout(self.audio_preview)
        preview_layout.setAlignment(Qt.AlignCenter)

        self.preview_icon = QLabel("🎙️")
        self.preview_icon.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        self.preview_icon.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_icon)

        self.preview_text = QLabel("点击下方按钮录制或上传音频样本\n建议 5-15 秒清晰人声")
        self.preview_text.setStyleSheet("font-size: 12px; color: #888; background: transparent; border: none;")
        self.preview_text.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(self.audio_preview)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.record_btn = QPushButton("🎙️ 录制新音频")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: #F0F0F5;
                border: 1px solid rgba(0, 0, 0, 10);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                color: #555;
            }
            QPushButton:hover {
                background: #E8E8ED;
            }
        """)
        self.record_btn.clicked.connect(self._on_record)
        btn_layout.addWidget(self.record_btn)

        self.upload_btn = QPushButton("📁 上传音频文件")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #F0F0F5;
                border: 1px solid rgba(0, 0, 0, 10);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                color: #555;
            }
            QPushButton:hover {
                background: #E8E8ED;
            }
        """)
        self.upload_btn.clicked.connect(self._on_upload)
        btn_layout.addWidget(self.upload_btn)

        layout.addLayout(btn_layout)

        return section

    def _create_params_section(self) -> QWidget:
        """创建参数调节区域"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid rgba(0, 0, 0, 5);
                border-radius: 12px;
                padding: 12px;
            }
        """)
        section.setMinimumHeight(150)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # 标题
        title = QLabel("调节参数")
        title.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #333;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(title)

        # 语速滑块
        self.speed_slider = SliderControl("语速", 0.5, 2.0, 1.0, 0.1, "x")
        layout.addWidget(self.speed_slider)

        # 音调滑块
        self.pitch_slider = SliderControl("音调", -5, 5, 0, 1, "")
        layout.addWidget(self.pitch_slider)

        # 音量滑块
        self.volume_slider = SliderControl("音量", 0, 100, 100, 1, "%")
        layout.addWidget(self.volume_slider)

        return section

    def _create_generate_section(self) -> QWidget:
        """创建生成按钮区域"""
        container = QWidget()

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.generate_btn = QPushButton("🚀 生成语音")
        self.generate_btn.setFixedHeight(44)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C6CEB, stop:1 #6B9FFF);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 32px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6B5CEB, stop:1 #5A8EEF);
            }
            QPushButton:disabled {
                background: #CCC;
            }
        """)
        self.generate_btn.clicked.connect(self._on_generate)
        layout.addWidget(self.generate_btn)

        return container

    def _on_record(self):
        """录制新音频（暂时使用文件选择）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.wav *.mp3 *.m4a);;所有文件 (*)"
        )
        if file_path:
            self._load_audio(file_path)

    def _on_upload(self):
        """上传音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.wav *.mp3 *.m4a);;所有文件 (*)"
        )
        if file_path:
            self._load_audio(file_path)

    def _load_audio(self, audio_path: str):
        """加载音频文件"""
        # 更新预览区
        self.preview_icon.setText("🎵")

        # 获取音频时长
        duration = 0.0
        try:
            with wave.open(audio_path, 'rb') as wav:
                duration = wav.getnframes() / wav.getframerate()
        except:
            pass

        mins = int(duration // 60)
        secs = int(duration % 60)
        duration_text = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}秒"
        self.preview_text.setText(f"已加载: {os.path.basename(audio_path)}\n时长: {duration_text}")

        # 更新样式
        self.audio_preview.setStyleSheet("""
            QFrame {
                background: rgba(124, 108, 235, 5);
                border: 2px solid #7C6CEB;
                border-radius: 12px;
            }
        """)

        # 创建临时保存路径
        voice_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'voice_profiles')
        os.makedirs(voice_dir, exist_ok=True)

        # 生成唯一ID
        with open(audio_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        save_path = os.path.join(voice_dir, f'profile_{file_hash}.json')

        # 启动特征提取线程
        self._clone_worker = VoiceCloneWorker(audio_path, save_path)
        self._clone_worker.finished.connect(self._on_extract_done)
        self._clone_worker.error.connect(self._on_extract_error)
        self._clone_worker.start()

    def _on_extract_done(self, voice_info_path: str, duration: float):
        """特征提取完成"""
        self._voice_info_path = voice_info_path
        self._update_ui_state()
        self.voice_ready.emit(voice_info_path)

    def _on_extract_error(self, msg: str):
        """特征提取失败"""
        QMessageBox.warning(self, "错误", f"声音特征提取失败: {msg}")
        self.preview_icon.setText("🎙️")
        self.preview_text.setText("点击下方按钮录制或上传音频样本\n建议 5-15 秒清晰人声")
        self.audio_preview.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 3);
                border: 2px dashed rgba(180, 180, 200, 80);
                border-radius: 12px;
            }
        """)

    def _on_generate(self):
        """生成语音"""
        # 获取文本（从主窗口）
        main_window = self.window()
        if hasattr(main_window, 'polished_text') and hasattr(main_window, 'recognized_text'):
            text = main_window.polished_text.toPlainText().strip()
            if not text:
                text = main_window.recognized_text.toPlainText().strip()
        else:
            text = ""

        if not text:
            QMessageBox.warning(self, "提示", "请先输入或识别口稿文字")
            return

        if not self._voice_info_path or not os.path.exists(self._voice_info_path):
            QMessageBox.warning(self, "提示", "请先录制或上传声音样本")
            return

        # 禁用按钮
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")

        # 输出路径
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'generated_speech.wav')

        # 获取参数
        speed = self.speed_slider.value()
        pitch = int(self.pitch_slider.value())
        volume = int(self.volume_slider.value())

        # 启动生成线程
        self._generate_worker = GenerateSpeechWorker(
            text, self._voice_info_path, output_path,
            speed, pitch, volume
        )
        self._generate_worker.finished.connect(self._on_generate_done)
        self._generate_worker.error.connect(self._on_generate_error)
        self._generate_worker.start()

    def _on_generate_done(self, output_path: str):
        """生成完成"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 生成语音")

        self._generated_audio_path = output_path
        self.player_widget.load_audio(output_path)
        self._update_ui_state()

        self.speech_generated.emit(output_path)

    def _on_generate_error(self, msg: str):
        """生成失败"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 生成语音")
        QMessageBox.warning(self, "错误", f"语音生成失败: {msg}")

    def _on_profile_selected(self, profile_id: str):
        """选择声音配置"""
        profile = self.profile_selector.get_active_profile()
        if profile:
            self._voice_info_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'voice_profiles',
                self.profile_selector.get_active_profile_id() + '.json'
            )
            # 尝试从注册表获取正确的文件名
            for p in self.profile_selector._profiles:
                if p['id'] == profile_id:
                    self._voice_info_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        'data', 'voice_profiles',
                        p['file']
                    )
                    break

            # 更新预览区
            audio_path = profile.get('audio_path', '')
            if audio_path and os.path.exists(audio_path):
                self._load_audio(audio_path)
            else:
                self.preview_icon.setText("✓")
                self.preview_text.setText(f"已加载配置: {profile.get('name', '未知')}")

            self._update_ui_state()

    def _on_new_profile(self):
        """新建配置"""
        self._on_upload()

    def _on_play(self):
        """播放音频"""
        if not self._generated_audio_path:
            return

        if not self._media_player:
            self._media_player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._media_player.setAudioOutput(self._audio_output)
            self._media_player.positionChanged.connect(self._on_position_changed)
            self._media_player.durationChanged.connect(self._on_duration_changed)

        self._media_player.setSource(QUrl.fromLocalFile(self._generated_audio_path))
        self._audio_output.setVolume(1.0)
        self._media_player.play()

    def _on_pause(self):
        """暂停播放"""
        if self._media_player:
            self._media_player.pause()

    def _on_stop(self):
        """停止播放"""
        if self._media_player:
            self._media_player.stop()

    def _on_position_changed(self, position: int):
        """播放位置变化"""
        if self._media_player and self._media_player.duration() > 0:
            current_time = position / 1000.0
            self.player_widget.update_progress(current_time)

    def _on_duration_changed(self, duration: int):
        """音频时长变化"""
        pass

    def _on_save_as_profile(self):
        """保存为配置"""
        if not self._voice_info_path:
            return

        name, ok = QInputDialog.getText(self, "保存配置", "输入配置名称:")
        if ok and name:
            # 读取现有配置
            import json
            with open(self._voice_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 生成新的profile_id
            import hashlib
            from datetime import datetime
            profile_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]

            # 添加到配置选择器
            self.profile_selector.add_profile(
                profile_id=profile_id,
                name=name,
                audio_path=data.get('audio_path', ''),
                voice_data_url=data.get('voice_id', ''),
                duration=data.get('duration_seconds', 0)
            )

            QMessageBox.information(self, "成功", f"配置 '{name}' 已保存")

    def _update_ui_state(self):
        """更新UI状态"""
        has_voice = self._voice_info_path is not None and os.path.exists(self._voice_info_path)
        self.generate_btn.setEnabled(has_voice)

    def get_speed(self) -> float:
        return self.speed_slider.value()

    def get_pitch(self) -> int:
        return int(self.pitch_slider.value())

    def get_volume(self) -> int:
        return int(self.volume_slider.value())
