MAIN_STYLE = """
/* ===== 全局 ===== */
QMainWindow {
    background: transparent;
}

QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
    color: #1a1a1a;
}

/* ===== 背景 ===== */
#appBackground {
    background: #fafafa;
    border-radius: 12px;
}

/* ===== 标题栏 ===== */
#titleBar {
    background: white;
    border-bottom: 1px solid #f0f0f0;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}
#titleLabel {
    font-size: 15px;
    font-weight: 600;
    color: #111;
    letter-spacing: -0.3px;
}
#closeBtn {
    background: transparent;
    border: none;
    font-size: 16px;
    color: #999;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 6px;
}
#closeBtn:hover {
    color: #fff;
    background: #e74c3c;
}

/* ===== 面板标题 ===== */
.panelTitle {
    font-size: 14px;
    font-weight: 600;
    color: #111;
    letter-spacing: -0.2px;
}

/* ===== 区块标题 ===== */
.sectionLabel {
    font-size: 12px;
    font-weight: 500;
    color: #888;
    letter-spacing: 0.2px;
}

/* ===== 默认按钮 ===== */
QPushButton {
    background: #f5f5f5;
    color: #333;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background: #ebebeb;
    border-color: #d5d5d5;
}
QPushButton:pressed {
    background: #e0e0e0;
    border-color: #ccc;
}
QPushButton:disabled {
    background: #f9f9f9;
    color: #bbb;
    border-color: #eee;
}

/* ===== 绿色按钮 ===== */
.greenBtn {
    background: #22c55e;
    color: white;
    border: none;
    font-weight: 600;
}
.greenBtn:hover {
    background: #16a34a;
}
.greenBtn:pressed {
    background: #15803d;
}
.greenBtn:disabled {
    background: #86efac;
    color: rgba(255,255,255,0.7);
}

/* ===== 黑色按钮 ===== */
.blackBtn {
    background: #111;
    color: white;
    border: none;
    font-weight: 600;
}
.blackBtn:hover {
    background: #333;
}
.blackBtn:pressed {
    background: #000;
}
.blackBtn:disabled {
    background: #666;
    color: rgba(255,255,255,0.5);
}

/* ===== 红色按钮（录音中） ===== */
.redBtn {
    background: #ef4444;
    color: white;
    border: none;
    font-weight: 600;
}
.redBtn:hover {
    background: #dc2626;
}
.redBtn:pressed {
    background: #b91c1c;
}

/* ===== 输入框 ===== */
QLineEdit {
    background: #f5f5f5;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    color: #222;
    selection-background-color: #bbf7d0;
}
QLineEdit:focus {
    border-color: #22c55e;
    background: white;
}

/* ===== 多行文本框 ===== */
QTextEdit {
    background: #f5f5f5;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    color: #222;
    selection-background-color: #bbf7d0;
}
QTextEdit:focus {
    border-color: #22c55e;
    background: white;
}

/* ===== 分割线 ===== */
#separator {
    background: #f0f0f0;
    max-width: 1px;
    min-width: 1px;
}

/* ===== 滑块 ===== */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #e5e5e5;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #111;
    border: none;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #333;
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
}
QSlider::sub-page:horizontal {
    background: #22c55e;
    border-radius: 2px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #ddd;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #ccc;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #ddd;
    border-radius: 3px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #ccc;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===== 对话框 ===== */
QDialog {
    background: white;
    color: #1a1a1a;
}

QInputDialog {
    background: white;
    color: #1a1a1a;
}

QMessageBox {
    background: white;
    color: #1a1a1a;
}

QInputDialog QLabel, QMessageBox QLabel {
    color: #333;
    background: transparent;
    font-size: 13px;
}

QInputDialog QLineEdit, QMessageBox QLineEdit {
    background: white;
    border: 1px solid #22c55e;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1a1a1a;
    font-size: 13px;
}

QInputDialog QPushButton, QMessageBox QPushButton {
    background: #22c55e;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 20px;
    font-size: 13px;
    font-weight: 600;
    min-width: 60px;
}

QInputDialog QPushButton:hover, QMessageBox QPushButton:hover {
    background: #16a34a;
}

QInputDialog QPushButton:pressed, QMessageBox QPushButton:pressed {
    background: #15803d;
}

/* 对话框标题栏 */
QMessageBox QLabel#qt_msgbox_label {
    color: #1a1a1a;
    font-size: 14px;
    font-weight: 600;
    background: transparent;
}
"""
