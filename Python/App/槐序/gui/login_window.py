from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging


class LoginWindow(QWidget):
    """登录窗口"""
    login_success = pyqtSignal(int, str)  # 用户ID和角色

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.setWindowTitle("4+X成绩管理系统 - 登录")
        self.setFixedSize(400, 300)
        self.init_ui()
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # 标题
        title = QLabel("4+X成绩管理系统")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # 表单区域
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)

        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)

        layout.addLayout(form_layout)

        # 登录按钮
        login_btn = QPushButton("登录")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def handle_login(self):
        """处理登录逻辑"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "输入错误", "用户名和密码不能为空")
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
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
                self.logger.warning(f"登录失败: 用户名 {username} 或密码错误")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}")
            self.logger.error(f"登录错误: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        event.accept()
