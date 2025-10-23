import logging

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal


class LoginWindow(QWidget):
    login_success = pyqtSignal(int, str)

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.setWindowTitle("4+X 成绩管理系统 - 登录")
        self.setFixedSize(1200, 900)  # 4:3 比例，可调整
        self.center_window()
        self.init_ui()
        self.logger = logging.getLogger(__name__)

    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(screen.center())
        self.move(geo.topLeft())

    def init_ui(self):
        # ======================
        # 最底层布局：整个窗口背景为深蓝色
        # ======================
        self.setStyleSheet("""
            QWidget {
                background: #001f3f;  /* 深蓝色背景（最底层） */
            }
        """)

        # 主布局：左右分栏（水平布局 QHBoxLayout）
        main_layout = QHBoxLayout()
        main_layout.setSpacing(40)  # 左右两个区域之间的间隙
        main_layout.setContentsMargins(40, 40, 40, 40)  # 窗口四周边距

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
                /* 可设置最小宽度，比如 400px，让左右平衡 */
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
        form_title.setAlignment(Qt.AlignCenter)  # 添加这一行
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
                background: white;  /* 白色不透明 */
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
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)

        password_label.setStyleSheet("font-size: 22px; color: #000; min-width: 80px;")

        self.password_input.setStyleSheet("""
            QLineEdit {
                background: white;  /* 白色不透明 */
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

        # --- 登录按钮 ---
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        button_layout.setContentsMargins(20, 25, 20, 25)

        login_btn = QPushButton("登 录")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 80))  # 半透明黑色
        login_btn.setGraphicsEffect(shadow)
        login_btn.setMinimumHeight(45)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.handle_login)

        login_btn.setStyleSheet("""
            QPushButton {
                background: white;  /* 纯白不透明 */
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
        form_layout.addWidget(button_frame)
        form_layout.addStretch()

        right_layout.addLayout(form_layout)

        # ======================
        # 将左右区域加入主布局
        # ======================
        main_layout.addWidget(left_frame, 1)   # 左侧占1份
        main_layout.addWidget(right_frame, 1)  # 右侧占1份

        self.setLayout(main_layout)

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

                from gui.main_window import MainWindow
                self.main_window = MainWindow(self.db_conn, user_id, role)
                self.main_window.show()
                self.close()
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误",
                                    QMessageBox.Ok, QMessageBox.Ok)
                self.password_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}",
                                 QMessageBox.Ok, QMessageBox.Ok)
            self.logger.error(f"登录错误: {str(e)}")

    def closeEvent(self, event):
        event.accept()