MAIN_STYLE = """
QMainWindow {
    background: #F5F5F8;
}

/* ===== 标题栏 ===== */
#titleBar {
    background: #FFFFFF;
    padding: 8px 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 6);
}

#titleLabel {
    font-size: 16px;
    font-weight: 600;
    color: #1A1A2E;
    background: transparent;
    border: none;
}

#minBtn, #maxBtn, #closeBtn {
    background: transparent;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    color: #999;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
#minBtn:hover, #maxBtn:hover {
    background: rgba(0, 0, 0, 6);
    color: #666;
}
#closeBtn:hover {
    background: #FF5F57;
    color: white;
}

/* ===== 卡片 ===== */
.glassCard {
    background: #FFFFFF;
    border: 1px solid rgba(0, 0, 0, 5);
    border-radius: 16px;
}

/* ===== 按钮 ===== */
.glassBtn {
    background: #F0F0F5;
    border: 1px solid rgba(0, 0, 0, 5);
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 13px;
    color: #444;
    font-weight: 500;
}
.glassBtn:hover {
    background: #E8E8F0;
    border: 1px solid rgba(0, 0, 0, 8);
}
.glassBtn:pressed {
    background: #DDDDF0;
}
.glassBtn:disabled {
    background: #F5F5F8;
    color: #BBB;
    border: 1px solid rgba(0, 0, 0, 3);
}

.glassBtnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7C6CEB, stop:1 #6B9FFF);
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-size: 13px;
    color: white;
    font-weight: 600;
}
.glassBtnPrimary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6B5BD6, stop:1 #5A8EEE);
}
.glassBtnPrimary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5A4BC5, stop:1 #497DDD);
}

/* ===== 输入框 ===== */
.glassInput {
    background: #F5F5F8;
    border: 1px solid rgba(0, 0, 0, 8);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: #1A1A2E;
}
.glassInput:focus {
    border: 1px solid #7C6CEB;
    background: #FFFFFF;
}
.glassInput::placeholder {
    color: #B0B0B8;
}

/* ===== 多行文本框 ===== */
.glassTextEdit {
    background: #F5F5F8;
    border: 1px solid rgba(0, 0, 0, 8);
    border-radius: 12px;
    padding: 12px;
    font-size: 13px;
    color: #1A1A2E;
}
.glassTextEdit:focus {
    border: 1px solid #7C6CEB;
    background: #FFFFFF;
}

/* ===== 标签 ===== */
.sectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #1A1A2E;
    background: transparent;
    border: none;
    padding: 4px 0;
}

.sectionSubtitle {
    font-size: 12px;
    color: #999;
    background: transparent;
    border: none;
}

/* ===== 进度条 ===== */
QProgressBar {
    background: #F0F0F5;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 10px;
    color: #666;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7C6CEB, stop:1 #6B9FFF);
    border-radius: 6px;
}

/* ===== 分割线 ===== */
#separator {
    background: rgba(0, 0, 0, 6);
    max-width: 1px;
    min-width: 1px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 12);
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 20);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""
