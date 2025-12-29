import logging
import sys
import os
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap
from database.db_conn import create_connection

from Python.App.槐序.gui.login_window import LoginWindow


# =========================
# 后台加载线程（仅更新进度，不操作UI）
# =========================
class LoadingThread(QThread):
    progress_updated = pyqtSignal(int)       # 进度更新信号 [0 ~ 100]
    loading_completed = pyqtSignal()         # 加载完成信号

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # 真实数据加载之后再说吧，模拟一下就当好看
            # ===== 模拟分阶段加载过程 =====
            # 阶段1: 初始化 (0~20%)
            for i in range(20):
                time.sleep(0.01)
                self.progress_updated.emit(int((i + 1) / 20 * 20))

            # 阶段2: 准备数据库连接 (20~50%)
            for i in range(30):
                time.sleep(0.01)
                self.progress_updated.emit(20 + int((i + 1) / 30 * 30))

            # 阶段3: 加载资源（慢一些，模拟真实加载）(50~80%)
            for i in range(30):
                time.sleep(0.03)
                self.progress_updated.emit(50 + int((i + 1) / 30 * 30))

            # 阶段4: 最终准备 (80~100%)
            for i in range(20):
                time.sleep(0.01)
                self.progress_updated.emit(80 + int((i + 1) / 20 * 20))

            # 最后等待一下，然后发出完成信号
            time.sleep(0.3)
            self.loading_completed.emit()

        except Exception as e:
            print(f"[LoadingThread Run Error] {e}")


# =========================
# 启动窗口（显示加载动画，然后跳转登录页）
# =========================
class StartupWindow(QWidget):
    loading_completed = pyqtSignal()  # 定义信号
    def __init__(self, db_file):
        super().__init__()
        logging.info("[StartupWindow] 初始化中...")
        self.db_file = db_file  # 数据库文件路径，传给登录窗口
        self.loading_thread = None
        self.login_window = None
        self.init_ui()
        self.setup_window()

    def open_login(self):
        self.login_window = LoginWindow(self.db_conn)
        self.login_window.show()
        self.hide()

    def setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(800, 600)
        self.center_window()  # 居中显示

    def center_window(self):
        # 获取屏幕中心点，移动窗口至此
        screen = QApplication.desktop().screenGeometry()
        win_geo = self.geometry()
        x = (screen.width() - win_geo.width()) // 2
        y = (screen.height() - win_geo.height()) // 2
        self.move(x, y)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 主容器
        main_frame = QWidget()
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 整体样式
        self.setStyleSheet("""
            QWidget {
                background: #001f3f;
                border: 2px solid white;
                border-radius: 20px;
            }
            #mainFrame {
                background: #001f3f;
                border-radius: 20px;
                padding: 0px;
            }
            QLabel {
                background: rgba(255, 255, 255, 0.85);
                border: 2px solid white;
                border-radius: 20px;
                color: #333;
                font-weight: bold;
                padding: 10px;
            }
            QLabel#titleLabel {
                font-size: 24px;
                color: #2c3e50;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 10px;
            }
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                color: #333;
                background: #f8f9fa;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 8px;
            }
        """)

        # 标题
        title_label = QLabel("HuaiXu - 槐序")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        # 副标题
        subtitle_label = QLabel("正在启动系统，请稍候...")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)

        # 图标/图片区域（可放logo，这里用文字代替）
        image_label = QLabel("槐序启动中...")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(120)
        image_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 48px;
                background: transparent;
            }
        """)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # 进度文字
        self.progress_text = QLabel("0%")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                margin-top: 5px;
            }
        """)

        # 组装界面
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addWidget(image_label)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_text)

        layout.addWidget(main_frame)
        self.setLayout(layout)

        # 启动加载线程
        self.start_loading()

    def start_loading(self):
        self.loading_thread = LoadingThread()
        self.loading_thread.progress_updated.connect(self.update_progress)
        self.loading_thread.loading_completed.connect(self.safe_jump_to_login)
        self.loading_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.progress_text.setText(f"{value}%")

    def safe_jump_to_login(self):
        logging.info("加载完成，即将跳转到登录窗口")
        # 延时200ms后关闭窗口
        QTimer.singleShot(200, self.close_and_open_login)

    def close_and_open_login(self):
        self.loading_completed.emit()
        self.close()  # 关闭启动窗口

    def closeEvent(self, event):
        if not hasattr(self, '_allow_close'):
            event.ignore()
            self.hide()
        else:
            event.accept()