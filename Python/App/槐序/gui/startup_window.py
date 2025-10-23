import sys
import os
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QProgressBar, QGraphicsView, QGraphicsScene,
                             QGraphicsPixmapItem, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from database.db_conn import create_connection


class LoadingThread(QThread):
    """加载线程，模拟文件加载过程"""
    progress_updated = pyqtSignal(int)
    loading_completed = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file

    def run(self):
        try:
            # 模拟加载过程 - 这里可以替换为实际的文件加载逻辑
            total_steps = 100

            # 步骤1: 模拟初始化 (20%)
            for i in range(20):
                time.sleep(0.01)  # 模拟耗时操作
                progress = int((i + 1) / 20 * 20)
                self.progress_updated.emit(progress)

            # 步骤2: 模拟数据库连接准备 (30%)
            for i in range(30):
                time.sleep(0.01)
                progress = 20 + int((i + 1) / 30 * 30)
                self.progress_updated.emit(progress)

            # 步骤3: 模拟资源加载 (30%)
            for i in range(30):
                time.sleep(0.04)
                progress = 50 + int((i + 1) / 30 * 30)
                self.progress_updated.emit(progress)

            # 步骤4: 模拟最终准备 (20%)
            for i in range(20):
                time.sleep(0.02)
                progress = 80 + int((i + 1) / 20 * 20)
                self.progress_updated.emit(progress)

            # 加载完成
            time.sleep(0.4)  # 最后停顿一下
            self.loading_completed.emit()

        except Exception as e:
            self.error_occurred.emit(f"加载过程中发生错误: {str(e)}")


class StartupWindow(QWidget):
    def __init__(self, db_file, parent=None):
        super().__init__(parent)
        self.db_file = db_file
        self.loading_thread = None
        self.init_ui()
        self.setup_window()

    def setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.FramelessWindowHint)  # 无边框窗口
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setFixedSize(800, 600)  # 固定大小

        # 居中显示
        self.center_window()

    def center_window(self):
        """窗口居中"""
        screen = QApplication.desktop().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 主容器 - 用于圆角效果
        main_frame = QWidget()
        main_frame.setObjectName("mainFrame")
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 设置样式 - 深蓝容器，半透明白色内部布局
        self.setStyleSheet("""
            QWidget {
                background: #001f3f;  /* 深蓝色背景 */
                border: 2px solid white;  /* 白色描边 */
            }
            #mainFrame {
                background: #001f3f;  /* 深蓝色背景 */
                border-radius: 20px;  /* 圆角 */
                padding: 0px;
            }
            QLabel {
                background: rgba(255, 255, 255, 0.8);  /* 80%不透明度白色 */
                border: 2px solid white;  /* 白色描边 */
                border-radius: 20px;  /* 圆角 */
                color: #333;
                font-weight: bold;
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

        # 图片显示区域（如果图片存在）
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(120)
        image_label.setText("🚀 正在加载系统资源...")
        image_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 48px;
                background: transparent;
            }
        """)

        # 尝试加载图片
        image_path = "../img/icon.png"
        if os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 缩放图片以适应区域
                    scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    image_label.setText("")  # 清除文字
            except Exception:
                pass  # 如果图片加载失败，保持默认显示

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # 进度文本
        self.progress_text = QLabel("0%")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                margin-top: 5px;
            }
        """)

        # 添加到布局
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
        """启动加载过程"""
        self.loading_thread = LoadingThread(self.db_file)
        self.loading_thread.progress_updated.connect(self.update_progress)
        self.loading_thread.loading_completed.connect(self.loading_completed)
        self.loading_thread.error_occurred.connect(self.loading_error)
        self.loading_thread.start()

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        self.progress_text.setText(f"{value}%")

    def loading_completed(self):
        """加载完成"""
        # 延迟400后跳转到登录窗口
        QTimer.singleShot(400, self.jump_to_login)

    def loading_error(self, error_message):
        """加载出错"""
        QMessageBox.critical(self, "加载错误", error_message)
        self.close()

    def jump_to_login(self):
        """跳转到登录窗口"""
        try:
            conn = create_connection(self.db_file)
            if conn:
                print("[DEBUG] 数据库连接成功，准备跳转到登录窗口")
                self.close()  # 关闭启动窗口

                # 正确导入 LoginWindow
                from gui.login_window import LoginWindow

                # 关键：将登录窗口保存为成员变量，防止被垃圾回收
                self.login_window = LoginWindow(conn)
                self.login_window.show()  # 显示登录窗口
                print("[DEBUG] 登录窗口已显示")
            else:
                QMessageBox.critical(self, "错误", "无法连接到数据库")
                self.close()
        except Exception as e:
            print(f"[ERROR] 跳转登录时发生异常: {e}")  # 打印错误到控制台
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
            self.close()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.loading_thread and self.loading_thread.isRunning():
            self.loading_thread.quit()
            self.loading_thread.wait()
        event.accept()