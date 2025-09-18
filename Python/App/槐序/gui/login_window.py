from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging
from PyQt5.QtGui import QFont, QPalette, QColor


class LoginWindow(QWidget):
    """登录窗口 - 美化版"""
    login_success = pyqtSignal(int, str)  # 用户ID和角色

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.setWindowTitle("4+X成绩管理系统 - 登录")
        self.setFixedSize(650, 750)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        # 设置窗口居中
        self.center_window()

        self.init_ui()
        self.logger = logging.getLogger(__name__)

    def center_window(self):
        """窗口居中显示"""
        screen = self.screen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)

        # 设置背景渐变色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 248, 255))  # 浅蓝色背景
        self.setPalette(palette)

        # 标题区域
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setAlignment(Qt.AlignCenter)

        # 主标题
        title = QLabel("4+X 成绩管理系统")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("mainTitle")

        # 副标题
        subtitle = QLabel("Login System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subTitle")
        subtitle.setStyleSheet("color: #666666; font-size: 14px; margin-top: 5px;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        main_layout.addWidget(title_frame)

        # 装饰线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #e0e0e0; margin: 20px 0;")
        main_layout.addWidget(line)

        # 登录表单区域
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(20)
        form_layout.setAlignment(Qt.AlignCenter)

        # 表单标题
        form_title = QLabel("用户登录")
        form_title.setObjectName("formTitle")
        form_layout.addWidget(form_title)

        # ✅ 修复：使用正确的变量名 input_container_layout，避免与 input_layout 冲突
        input_container_layout = QVBoxLayout()  # 输入区域的主容器
        input_container_layout.setSpacing(15)

        # 用户名输入
        username_frame = QFrame()
        username_frame.setObjectName("inputFrame")
        username_layout = QHBoxLayout(username_frame)
        username_layout.setContentsMargins(15, 10, 15, 10)
        username_layout.setSpacing(10)

        username_label = QLabel("👤 用户名:")
        username_label.setObjectName("inputLabel")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setObjectName("inputField")
        self.username_input.setMinimumHeight(40)

        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        input_container_layout.addWidget(username_frame)

        # 密码输入
        password_frame = QFrame()
        password_frame.setObjectName("inputFrame")
        password_layout = QHBoxLayout(password_frame)
        password_layout.setContentsMargins(15, 10, 15, 10)
        password_layout.setSpacing(10)

        password_label = QLabel("🔒 密码:")
        password_label.setObjectName("inputLabel")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("inputField")
        self.password_input.setMinimumHeight(40)

        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        input_container_layout.addWidget(password_frame)

        # 将整个输入容器布局添加到表单布局中
        form_layout.addLayout(input_container_layout)

        # 记住密码和忘记密码（可选，目前注释）
        # remember_layout = QHBoxLayout()
        # remember_cb = QCheckBox("记住密码")
        # remember_cb.setStyleSheet("color: #666; font-size: 12px;")
        # remember_layout.addWidget(remember_cb)
        # remember_layout.addStretch()
        # forgot_label = QLabel("<a href='#' style='color: #007bff; text-decoration: none;'>忘记密码?</a>")
        # forgot_label.setAlignment(Qt.AlignRight)
        # remember_layout.addWidget(forgot_label)
        # form_layout.addLayout(remember_layout)

        # 登录按钮
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        button_layout.setContentsMargins(15, 20, 15, 15)

        login_btn = QPushButton("登 录")
        login_btn.setObjectName("loginButton")
        login_btn.setMinimumHeight(45)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.handle_login)

        # 登录按钮样式
        login_btn.setStyleSheet("""
            QPushButton#loginButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton#loginButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            QPushButton#loginButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d8b40, stop:1 #2e7d32);
            }
        """)

        button_layout.addWidget(login_btn)
        form_layout.addWidget(button_frame)

        main_layout.addWidget(form_frame)

        # 底部信息
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setAlignment(Qt.AlignCenter)

        version_label = QLabel("© 2025 4+X 成绩管理系统 v1.0")
        version_label.setObjectName("versionLabel")
        version_label.setStyleSheet("color: #999999; font-size: 10px; margin-top: 10px;")

        bottom_layout.addWidget(version_label)
        main_layout.addWidget(bottom_frame)

        self.setLayout(main_layout)

        # 设置整体样式
        self.setStyleSheet("""
            #titleFrame {
                background: transparent;
                margin-bottom: 10px;
            }
            #mainTitle {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }
            #subTitle {
                font-size: 14px;
                color: #7f8c8d;
                font-weight: normal;
            }
            #formFrame {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                border: 1px solid #e8e8e8;
            }
            #formTitle {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 25px;
                text-align: center;
            }
            #inputFrame {
                background: #fafafa;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            #inputLabel {
                font-size: 14px;
                font-weight: 500;
                color: #34495e;
                min-width: 80px;
            }
            #inputField {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                background: white;
                selection-background-color: #3498db;
            }
            #inputField:focus {
                border-color: #3498db;
                outline: none;
            }
            #versionLabel {
                font-size: 10px;
                color: #bdc3c7;
            }
        """)

    def handle_login(self):
        """处理登录逻辑"""
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

                # 显示主窗口
                from gui.main_window import MainWindow
                self.main_window = MainWindow(self.db_conn, user_id, role)
                self.main_window.show()

                # 关闭登录窗口
                self.close()
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误",
                                    QMessageBox.Ok, QMessageBox.Ok)
                self.logger.warning(f"登录失败: 用户名 {username} 或密码错误")
                # 清空密码框
                self.password_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}",
                                 QMessageBox.Ok, QMessageBox.Ok)
            self.logger.error(f"登录错误: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        event.accept()