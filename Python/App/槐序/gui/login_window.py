import logging
import sqlite3
import os

from PyQt5.QtGui import QColor, QPixmap
from utils.resource_path import get_img_path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QApplication, QGraphicsDropShadowEffect, QCheckBox,
    QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer, QPoint


class LoginWindow(QWidget):
    login_success = pyqtSignal(int, str)

    def __init__(self, db_conn):
        super().__init__()
        self.setWindowTitle("槐序 - HuaiXu - 登录")
        self.setFixedSize(1200, 900)  # 4:3 比例
        self.setWindowFlags(Qt.FramelessWindowHint)  # 取消系统菜单栏
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 纯透明窗口
        self.setStyleSheet("""
            background: transparent;
            border-radius: 20px;
        """)
        self.center_window()
        self.main_window = None
        self.logger = logging.getLogger(__name__)
        # self._switch_to_window(LoginWindow(self.db_conn))  # ✅ 传入数据库连接对象
        self.db_conn = db_conn  # ✅ 保存传入的数据库连接
        logging.info(f"[LoginWindow] 初始化时 db_conn 类型: {type(self.db_conn)}")  # 调试信息

        # 标题栏拖拽支持
        self._dragging = False
        self._drag_pos = QPoint()
        self._is_maximized = False
        self._normal_geometry = self.geometry()

        self.init_ui()
        QTimer.singleShot(300, self.load_saved_login_info)

    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(screen.center())
        self.move(geo.topLeft())

    def init_ui(self):
        # 创建背景容器
        background_container = QFrame()
        background_container.setStyleSheet("""
            background: transparent;
            border-radius: 20px;
        """)

        # 创建背景标签
        background_label = QLabel(background_container)
        # 使用绝对路径加载背景图片
        img_path = get_img_path('school.jpg')
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            # 按窗口大小缩放图片，保持比例并居中
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            background_label.setPixmap(scaled_pixmap)
            # 设置背景标签居中对齐
            background_label.setAlignment(Qt.AlignCenter)
        else:
            # 如果图片加载失败，使用深蓝色背景
            background_label.setStyleSheet("""
                background: #001f3f;
                border-radius: 20px;
            """)
        background_label.setGeometry(0, 0, self.width(), self.height())

        # 顶部标题栏（自定义：最小化 / 最大化 / 关闭）
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        self.title_bar = title_bar
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 8, 12, 8)
        title_layout.setSpacing(8)

        title_label = QLabel("槐序 - HuaiXu")
        title_label.setStyleSheet("font-size: 25px; font-weight: bold; color: #0d47a1;")

        title_layout.addWidget(title_label)
        title_layout.addStretch()

        btn_min = QToolButton()
        btn_min.setText("—")
        btn_min.setToolTip("最小化")
        btn_min.clicked.connect(self.showMinimized)

        btn_max = QToolButton()
        btn_max.setText("🗖")
        btn_max.setToolTip("最大化/还原")

        btn_close = QToolButton()
        btn_close.setText("✕")
        btn_close.setToolTip("关闭")
        btn_close.clicked.connect(self.close)

        def toggle_max_restore():
            if not self._is_maximized:
                self._normal_geometry = self.geometry()
                self.showMaximized()
                self._is_maximized = True
                btn_max.setText("🗗")
            else:
                self.showNormal()
                if self._normal_geometry:
                    self.setGeometry(self._normal_geometry)
                self._is_maximized = False
                btn_max.setText("🗖")

        btn_max.clicked.connect(toggle_max_restore)

        for btn in (btn_min, btn_max, btn_close):
            btn.setMinimumSize(32, 24)
            btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                    color: #ffffff;
                    transition: all 0.2s ease;
                }
                QToolButton:hover {
                    background: rgba(255, 255, 255, 80);
                    border: 1px solid rgba(255, 255, 255, 120);
                }
                QToolButton:pressed {
                    background: rgba(255, 255, 255, 150);
                    border: 1px solid rgba(255, 255, 255, 180);
                }
            """)

        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_max)
        title_layout.addWidget(btn_close)

        title_bar.setStyleSheet("""
            #titleBar {
                background: transparent;
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """)

        # 主布局：左右分栏（水平布局 QHBoxLayout）
        main_layout = QHBoxLayout()
        main_layout.setSpacing(40)  # 左右两个区域之间的间隙
        main_layout.setContentsMargins(40, 20, 40, 40)  # 窗口四周边距

        # ======================
        # 左侧 Layout：浅白色 80% 透明度 + 纯白描边
        # ======================
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(20)

        # 样式：浅白色 80% 透明度 + 纯白边框
        left_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.8);  /* 浅白色，80% 透明 */
                border: 2px solid white;               /* 纯白描边 */
                border-radius: 15px;
                min-width: 400px;
            }
        """)

        # ======================
        # 右侧 Layout：浅白色 80% 透明度 + 纯白描边 → 登录表单区域
        # ======================
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # 样式同左侧：浅白色 80% + 纯白描边
        right_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.8);  /* 浅白色，80% 透明 */
                border: 2px solid white;               /* 纯白描边 */
                border-radius: 15px;
                padding: 15px;
            }
        """)

        # 表单标题
        form_title = QLabel("用户登录")
        form_title.setAlignment(Qt.AlignCenter)
        form_title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #000;
            margin-bottom: 15px;
        """)

        # 表单内容
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # --- 用户名输入 ---
        username_frame = QFrame()
        username_layout = QHBoxLayout(username_frame)
        username_layout.setContentsMargins(20, 15, 20, 15)
        username_layout.setSpacing(15)

        username_label = QLabel("👤 用户名:")
        username_label.setStyleSheet("font-size: 22px; color: #000; min-width: 80px;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setMinimumHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 22px;
                color: #000;
            }
            QLineEdit:focus {
                border-color: #000;
                outline: none;
            }
        """)

        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)

        # --- 密码输入 ---
        password_frame = QFrame()
        password_layout = QHBoxLayout(password_frame)
        password_layout.setContentsMargins(20, 15, 20, 15)
        password_layout.setSpacing(15)

        password_label = QLabel("🔒 密码:")
        password_label.setStyleSheet("font-size: 22px; color: #000; min-width: 80px;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 22px;
                color: #000;
            }
            QLineEdit:focus {
                border-color: #000;
                outline: none;
            }
        """)

        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)

        # --- 记住我选项 ---
        remember_frame = QFrame()
        remember_layout = QHBoxLayout(remember_frame)
        remember_layout.setContentsMargins(20, 10, 20, 10)

        self.remember_username_cb = QCheckBox("记住用户名")
        self.remember_password_cb = QCheckBox("记住密码")  # ⚠️ 安全风险，建议加密或不保存
        self.auto_login_cb = QCheckBox("自动登录")  # 如果勾选，下次启动时自动登录

        checkbox_style = """
            QCheckBox {
                font-size: 16px;
                color: #000;
                background: transparent;  /* 移除背景颜色 */
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
        self.remember_username_cb.setStyleSheet(checkbox_style)
        self.remember_password_cb.setStyleSheet(checkbox_style)
        self.auto_login_cb.setStyleSheet(checkbox_style)

        remember_layout.addWidget(self.remember_username_cb)
        remember_layout.addWidget(self.remember_password_cb)
        remember_layout.addWidget(self.auto_login_cb)
        remember_layout.addStretch()  # 推到右侧

        # --- 登录按钮 ---
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        button_layout.setContentsMargins(20, 25, 20, 25)

        login_btn = QPushButton("登 录")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 80))
        login_btn.setGraphicsEffect(shadow)
        login_btn.setMinimumHeight(45)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.handle_login)

        login_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #000;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
            QPushButton:pressed {
                background: #e0e0e0;
            }
        """)

        button_layout.addWidget(login_btn)

        # 组装表单
        form_layout.addWidget(form_title)
        form_layout.addWidget(username_frame)
        form_layout.addWidget(password_frame)
        form_layout.addWidget(remember_frame)
        form_layout.addWidget(button_frame)
        form_layout.addStretch()

        right_layout.addLayout(form_layout)

        # ======================
        # 将左右区域加入主布局
        # ======================
        main_layout.addWidget(left_frame, 1)
        main_layout.addWidget(right_frame, 1)

        # 顶层布局，包含标题栏与主体
        root_layout = QVBoxLayout(background_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(title_bar)
        root_layout.addLayout(main_layout)

        # 主窗口布局
        main_window_layout = QVBoxLayout(self)
        main_window_layout.addWidget(background_container)
        main_window_layout.setContentsMargins(0, 0, 0, 0)

    def resizeEvent(self, event):
        """当窗口大小改变时，重新缩放背景图片"""
        super().resizeEvent(event)

        # 查找背景标签并重新缩放
        for child in self.findChildren(QLabel):
            if hasattr(child, 'pixmap') and child.pixmap() is not None:
                pixmap = child.pixmap()
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    child.setPixmap(scaled_pixmap)
                    child.setAlignment(Qt.AlignCenter)  # 设置居中对齐
                    child.setGeometry(0, 0, self.width(), self.height())
                break

    # ============== 无边框窗口拖拽支持 ==============
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, "title_bar"):
            if event.pos().y() <= self.title_bar.height() + 8:
                self._dragging = True
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and not self._is_maximized:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def save_login_info(self, username, password, remember_username, remember_password, auto_login):
        """
        登录成功后，根据用户勾选情况，保存登录信息到 QSettings
        """
        settings = QSettings("MyCompany", "ScoreManagementSystem")
        if remember_username:
            settings.setValue("saved_username", username)
        else:
            settings.remove("saved_username")

        if remember_password:
            settings.setValue("saved_password", password)  # 不明文保存
        else:
            settings.remove("saved_password")

        settings.setValue("auto_login", auto_login)
        settings.sync()

    def login_success_handler(self, username, password):
        """
        在登录成功后调用，用于保存信息
        """
        remember_username = self.remember_username_cb.isChecked()
        remember_password = self.remember_password_cb.isChecked()
        auto_login = self.auto_login_cb.isChecked()
        self.save_login_info(username, password, remember_username, remember_password, auto_login)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "输入错误", "用户名和密码不能为空",
                                QMessageBox.Ok, QMessageBox.Ok)
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT user_id, role FROM users WHERE username = ? AND password = ?",
                (username, password)
            )
            user = cursor.fetchone()

            if user:
                user_id, role = user
                self.logger.info(f"用户 {username} 登录成功, 角色: {role}")

                # ✅ 保存登录信息
                remember_username = self.remember_username_cb.isChecked()
                remember_password = self.remember_password_cb.isChecked()
                auto_login = self.auto_login_cb.isChecked()
                self.save_login_info(username, password, remember_username, remember_password, auto_login)

                from gui.main_window import MainWindow
                self.main_window = MainWindow(self.db_conn, user_id, role)
                self.main_window.logout_requested.connect(self.show_login_again)
                self.main_window.show()
                self.hide()
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误",
                                    QMessageBox.Ok, QMessageBox.Ok)
                self.password_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}",
                                 QMessageBox.Ok, QMessageBox.Ok)
            self.logger.error(f"登录错误: {str(e)}")

    def save_login_info(self, username, password, remember_username, remember_password, auto_login):
        settings = QSettings("MyCompany", "ScoreManagementSystem")
        if remember_username:
            settings.setValue("saved_username", username)
        else:
            settings.remove("saved_username")

        if remember_password:
            settings.setValue("saved_password", password)  # ⚠️ 明文，不安全
        else:
            settings.remove("saved_password")

        settings.setValue("auto_login", auto_login)
        settings.sync()

    def load_saved_login_info(self):
        settings = QSettings("MyCompany", "ScoreManagementSystem")
        saved_username = settings.value("saved_username", "")
        saved_password = settings.value("saved_password", "")
        auto_login = settings.value("auto_login", False, type=bool)

        if saved_username:
            self.username_input.setText(saved_username)
            self.remember_username_cb.setChecked(True)

        if saved_password:
            self.password_input.setText(saved_password)
            self.remember_password_cb.setChecked(True)

        if auto_login:
            self.auto_login_cb.setChecked(True)
            # 自动登录
            self.handle_auto_login()

    def show_login_again(self):
        self.logger.debug("收到退出登录信号，重新显示登录窗口")

        # 清除自动登录
        settings = QSettings("MyCompany", "ScoreManagementSystem")
        settings.setValue("auto_login", True)
        settings.sync()

        if self.main_window:
            self.main_window.close()
            self.main_window = None

        # 输入框可用
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.username_input.setReadOnly(False)
        self.password_input.setReadOnly(False)

        # 清空内容
        self.username_input.clear()
        self.password_input.clear()

        # 显示并激活窗口
        self.show()
        self.raise_()  # 提升到最前
        self.activateWindow()  # 获取焦点

        # 强制聚焦到用户名输入框
        self.username_input.setFocus()

    def handle_auto_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if username and password:
            self.username_input.setEnabled(False)
            self.password_input.setEnabled(False)
            self.auto_login_cb.setEnabled(True)
            QApplication.processEvents()
            logging.info(f"[LoginWindow] handle_auto_login 中 db_conn 类型: {type(self.db_conn)}")  # 调试信息
            self.attempt_login(username, password)

    def attempt_login(self, username, password):
        if not username or not password:
            return False
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT user_id, role FROM users WHERE username = ? AND password = ?",
                (username, password)
            )
            user = cursor.fetchone()
            if user:
                user_id, role = user
                self.logger.info(f"用户 {username} 登录成功, 角色: {role}")

                from gui.main_window import MainWindow
                self.main_window = MainWindow(self.db_conn, user_id, role)

                #连接退出登录信号
                self.main_window.logout_requested.connect(self.show_login_again)

                self.main_window.show()
                self.hide()  # 隐藏登录窗口

                remember_username = self.remember_username_cb.isChecked()
                remember_password = self.remember_password_cb.isChecked()
                auto_login = self.auto_login_cb.isChecked()
                self.save_login_info(username, password, remember_username, remember_password, auto_login)
                return True
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
                self.password_input.clear()
                return False
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}")
            self.logger.error(f"登录错误: {str(e)}")
            return False



