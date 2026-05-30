import os
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QMenu, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal


class ProfileCard(QFrame):
    """单个声音配置卡片"""

    use_clicked = Signal(str)
    delete_clicked = Signal(str)
    rename_clicked = Signal(str, str)

    def __init__(self, profile_id: str, name: str, duration: float, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.profile_id = profile_id
        self._name = name
        self._duration = duration
        self._is_active = is_active

        self.setFixedSize(140, 90)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # 名称
        self.name_label = QLabel(self._name)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #333;
                background: transparent;
                border: none;
            }
        """)
        self.name_label.setMaximumWidth(120)
        layout.addWidget(self.name_label)

        # 时长
        mins = int(self._duration // 60)
        secs = int(self._duration % 60)
        duration_text = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}秒"
        self.duration_label = QLabel(duration_text)
        self.duration_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #888;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.duration_label)

        # 使用按钮
        self.use_btn = QPushButton("使用")
        self.use_btn.setFixedHeight(24)
        self.use_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C6CEB, stop:1 #6B9FFF);
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6B5CEB, stop:1 #5A8EEF);
            }
        """)
        self.use_btn.clicked.connect(lambda: self.use_clicked.emit(self.profile_id))
        layout.addWidget(self.use_btn)

        layout.addStretch()

    def _update_style(self):
        border = "2px solid #7C6CEB" if self._is_active else "1px solid rgba(0, 0, 0, 5)"
        self.setStyleSheet(f"""
            ProfileCard {{
                background: white;
                border: {border};
                border-radius: 12px;
            }}
            ProfileCard:hover {{
                border: 2px solid #7C6CEB;
            }}
        """)

    def set_active(self, active: bool):
        self._is_active = active
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            rename_action = menu.addAction("重命名")
            delete_action = menu.addAction("删除")

            action = menu.exec(event.globalPos())
            if action == rename_action:
                new_name, ok = QInputDialog.getText(self, "重命名", "输入新名称:", text=self._name)
                if ok and new_name:
                    self.rename_clicked.emit(self.profile_id, new_name)
            elif action == delete_action:
                reply = QMessageBox.question(
                    self, "确认删除",
                    f"确定要删除声音配置 '{self._name}' 吗？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.delete_clicked.emit(self.profile_id)
        super().mousePressEvent(event)


class VoiceProfileSelector(QWidget):
    """声音配置选择器"""

    profile_selected = Signal(str)  # profile_id
    new_profile_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._profiles = []
        self._active_id = None
        self._data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'voice_profiles')
        self._registry_path = os.path.join(self._data_dir, 'profiles.json')
        self._setup_ui()
        self._load_profiles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 标题行
        header = QHBoxLayout()
        title = QLabel("声音配置")
        title.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #333;
                background: transparent;
                border: none;
            }
        """)
        header.addWidget(title)
        header.addStretch()

        self.new_btn = QPushButton("+ 新建")
        self.new_btn.setStyleSheet("""
            QPushButton {
                background: #F0F0F5;
                border: 1px solid rgba(0, 0, 0, 10);
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                color: #555;
            }
            QPushButton:hover {
                background: #E8E8ED;
            }
        """)
        self.new_btn.clicked.connect(self.new_profile_requested)
        header.addWidget(self.new_btn)

        layout.addLayout(header)

        # 配置卡片滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)

    def _load_profiles(self):
        """加载所有保存的配置"""
        os.makedirs(self._data_dir, exist_ok=True)

        if os.path.exists(self._registry_path):
            try:
                with open(self._registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                self._profiles = registry.get('profiles', [])
                self._active_id = registry.get('active_profile_id')
            except:
                self._profiles = []
                self._active_id = None
        else:
            # 向后兼容：扫描目录中的JSON文件
            self._scan_existing_profiles()

        self._refresh_ui()

    def _scan_existing_profiles(self):
        """扫描已存在的配置文件（向后兼容）"""
        self._profiles = []
        for filename in os.listdir(self._data_dir):
            if filename.endswith('.json') and filename != 'profiles.json':
                filepath = os.path.join(self._data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    profile_id = filename.replace('.json', '').replace('profile_', '')
                    self._profiles.append({
                        'id': profile_id,
                        'name': data.get('name', f'声音 {len(self._profiles) + 1}'),
                        'file': filename,
                        'created_at': data.get('created_at', datetime.now().isoformat()),
                        'duration_seconds': data.get('duration_seconds', 0)
                    })
                except:
                    pass

        self._save_registry()

    def _save_registry(self):
        """保存配置注册表"""
        registry = {
            'profiles': self._profiles,
            'active_profile_id': self._active_id
        }
        with open(self._registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

    def _refresh_ui(self):
        """刷新配置卡片列表"""
        # 清除现有卡片
        while self.cards_layout.count() > 1:  # 保留最后的stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加配置卡片
        for profile in self._profiles:
            card = ProfileCard(
                profile_id=profile['id'],
                name=profile['name'],
                duration=profile.get('duration_seconds', 0),
                is_active=profile['id'] == self._active_id
            )
            card.use_clicked.connect(self._on_use_profile)
            card.delete_clicked.connect(self._on_delete_profile)
            card.rename_clicked.connect(self._on_rename_profile)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _on_use_profile(self, profile_id: str):
        self._active_id = profile_id
        self._save_registry()
        self._refresh_ui()
        self.profile_selected.emit(profile_id)

    def _on_delete_profile(self, profile_id: str):
        # 删除文件
        for profile in self._profiles:
            if profile['id'] == profile_id:
                filepath = os.path.join(self._data_dir, profile['file'])
                if os.path.exists(filepath):
                    os.remove(filepath)
                break

        # 从列表中移除
        self._profiles = [p for p in self._profiles if p['id'] != profile_id]
        if self._active_id == profile_id:
            self._active_id = self._profiles[0]['id'] if self._profiles else None

        self._save_registry()
        self._refresh_ui()

    def _on_rename_profile(self, profile_id: str, new_name: str):
        for profile in self._profiles:
            if profile['id'] == profile_id:
                profile['name'] = new_name
                # 更新JSON文件
                filepath = os.path.join(self._data_dir, profile['file'])
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['name'] = new_name
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                break

        self._save_registry()
        self._refresh_ui()

    def add_profile(self, profile_id: str, name: str, audio_path: str, voice_data_url: str, duration: float):
        """添加新的声音配置"""
        # 保存配置文件
        profile_data = {
            'name': name,
            'voice_id': voice_data_url,
            'audio_path': audio_path,
            'created_at': datetime.now().isoformat(),
            'duration_seconds': duration
        }

        filename = f'profile_{profile_id}.json'
        filepath = os.path.join(self._data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        # 添加到注册表
        self._profiles.append({
            'id': profile_id,
            'name': name,
            'file': filename,
            'created_at': profile_data['created_at'],
            'duration_seconds': duration
        })

        self._active_id = profile_id
        self._save_registry()
        self._refresh_ui()

    def get_active_profile(self) -> dict:
        """获取当前激活的配置"""
        if not self._active_id:
            return None

        for profile in self._profiles:
            if profile['id'] == self._active_id:
                # 加载完整配置
                filepath = os.path.join(self._data_dir, profile['file'])
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data
        return None

    def get_active_profile_id(self) -> str:
        return self._active_id
