"""统一弹窗样式"""
from PySide6.QtWidgets import QMessageBox, QInputDialog


# 弹窗通用样式
_DIALOG_STYLE = """
    QMessageBox, QInputDialog {
        background: white;
        color: #1a1a1a;
    }
    QMessageBox QLabel, QInputDialog QLabel {
        color: #333;
        background: transparent;
        font-size: 13px;
        min-width: 300px;
    }
    QMessageBox QPushButton, QInputDialog QPushButton {
        background: #22c55e;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 20px;
        font-size: 13px;
        font-weight: 600;
        min-width: 70px;
        min-height: 28px;
    }
    QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {
        background: #16a34a;
    }
    QMessageBox QPushButton:pressed, QInputDialog QPushButton:pressed {
        background: #15803d;
    }
"""


def show_warning(parent, title, message):
    """显示警告弹窗"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet(_DIALOG_STYLE)
    return msg.exec()


def show_info(parent, title, message):
    """显示信息弹窗"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet(_DIALOG_STYLE)
    return msg.exec()


def show_error(parent, title, message):
    """显示错误弹窗"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet(_DIALOG_STYLE)
    return msg.exec()


def show_question(parent, title, message):
    """显示确认弹窗，返回 True/False"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    msg.setStyleSheet(_DIALOG_STYLE)
    return msg.exec() == QMessageBox.Yes


def ask_text(parent, title, label, default_text=""):
    """显示文本输入弹窗，返回 (text, ok)"""
    dialog = QInputDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setTextValue(default_text)
    dialog.setStyleSheet("""
        QInputDialog {
            background: white;
        }
        QLabel {
            color: #333;
            background: transparent;
            font-size: 13px;
        }
        QLineEdit {
            background: white;
            border: 1px solid #22c55e;
            border-radius: 6px;
            padding: 8px 12px;
            color: #1a1a1a;
            font-size: 13px;
        }
        QPushButton {
            background: #22c55e;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 20px;
            font-size: 13px;
            font-weight: 600;
            min-width: 70px;
        }
        QPushButton:hover {
            background: #16a34a;
        }
    """)

    ok = dialog.exec()
    return dialog.textValue(), ok
