from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QComboBox, QLabel, QMessageBox,
    QInputDialog, QHeaderView
)
from PyQt5.QtCore import Qt
import logging


class SettingsWindow(QWidget):
    """系统设置窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("系统设置")
        self.resize(800, 500)
        self.init_ui()
        self.load_users()
        self.load_courses()

    def init_ui(self):
        layout = QVBoxLayout()

        # 选项卡
        self.tab_widget = QTabWidget()

        # 用户管理选项卡
        user_tab = QWidget()
        user_layout = QVBoxLayout()
        self.setup_user_tab(user_layout)
        user_tab.setLayout(user_layout)

        # 课程管理选项卡
        course_tab = QWidget()
        course_layout = QVBoxLayout()
        self.setup_course_tab(course_layout)
        course_tab.setLayout(course_layout)

        # 班级管理选项卡
        class_tab = QWidget()
        class_layout = QVBoxLayout()
        self.setup_class_tab(class_layout)
        class_tab.setLayout(class_layout)

        self.tab_widget.addTab(user_tab, "用户管理")
        self.tab_widget.addTab(course_tab, "课程管理")
        self.tab_widget.addTab(class_tab, "班级管理")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def setup_user_tab(self, layout):
        """设置用户管理选项卡"""
        # 用户表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["ID", "用户名", "角色", "真实姓名", "操作"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 操作按钮
        btn_layout = QHBoxLayout()

        add_user_btn = QPushButton("添加用户")
        add_user_btn.clicked.connect(self.add_user)

        reset_pwd_btn = QPushButton("重置密码")
        reset_pwd_btn.clicked.connect(self.reset_password)

        btn_layout.addWidget(add_user_btn)
        btn_layout.addWidget(reset_pwd_btn)

        layout.addWidget(self.user_table)
        layout.addLayout(btn_layout)

    def setup_course_tab(self, layout):
        """设置课程管理选项卡"""
        # 课程表格
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["ID", "课程名称", "学分", "类型", "操作"])
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 操作按钮
        btn_layout = QHBoxLayout()

        add_course_btn = QPushButton("添加课程")
        add_course_btn.clicked.connect(self.add_course)

        btn_layout.addWidget(add_course_btn)

        layout.addWidget(self.course_table)
        layout.addLayout(btn_layout)

    def setup_class_tab(self, layout):
        """设置班级管理选项卡"""
        # 班级表格
        self.class_table = QTableWidget()
        self.class_table.setColumnCount(5)
        self.class_table.setHorizontalHeaderLabels(["ID", "班级名称", "年级", "专业", "操作"])
        self.class_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 操作按钮
        btn_layout = QHBoxLayout()

        add_class_btn = QPushButton("添加班级")
        add_class_btn.clicked.connect(self.add_class)

        btn_layout.addWidget(add_class_btn)

        layout.addWidget(self.class_table)
        layout.addLayout(btn_layout)

    def load_users(self):
        """加载用户列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT user_id, username, role, real_name FROM users ORDER BY user_id")
            users = cursor.fetchall()

            self.user_table.setRowCount(len(users))
            for row, user in enumerate(users):
                for col in range(4):
                    self.user_table.setItem(row, col, QTableWidgetItem(str(user[col])))

                # 操作按钮
                if user[2] != 'admin':  # 不能删除管理员
                    delete_btn = QPushButton("删除")
                    delete_btn.clicked.connect(lambda _, uid=user[0]: self.delete_user(uid))
                    self.user_table.setCellWidget(row, 4, delete_btn)
        except Exception as e:
            self.logger.error(f"加载用户列表错误: {str(e)}")

    def load_courses(self):
        """加载课程列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT course_id, course_name, credit, course_type FROM courses ORDER BY course_id")
            courses = cursor.fetchall()

            self.course_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col in range(4):
                    self.course_table.setItem(row, col, QTableWidgetItem(str(course[col])))

                # 操作按钮
                edit_btn = QPushButton("编辑")
                edit_btn.clicked.connect(lambda _, cid=course[0]: self.edit_course(cid))
                self.course_table.setCellWidget(row, 4, edit_btn)
        except Exception as e:
            self.logger.error(f"加载课程列表错误: {str(e)}")

    def load_classes(self):
        """加载班级列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_id, class_name, grade, major FROM classes ORDER BY class_id")
            classes = cursor.fetchall()

            self.class_table.setRowCount(len(classes))
            for row, class_ in enumerate(classes):
                for col in range(4):
                    self.class_table.setItem(row, col, QTableWidgetItem(str(class_[col])))

                # 操作按钮
                edit_btn = QPushButton("编辑")
                edit_btn.clicked.connect(lambda _, cid=class_[0]: self.edit_class(cid))
                self.class_table.setCellWidget(row, 4, edit_btn)
        except Exception as e:
            self.logger.error(f"加载班级列表错误: {str(e)}")

    def add_user(self):
        """添加用户"""
        username, ok = QInputDialog.getText(self, "添加用户", "请输入用户名:")
        if not ok or not username:
            return

        password, ok = QInputDialog.getText(self, "添加用户", "请输入密码:", QLineEdit.Password)
        if not ok or not password:
            return

        roles = ["admin", "teacher", "student"]
        role, ok = QInputDialog.getItem(self, "添加用户", "选择角色:", roles, 0, False)
        if not ok:
            return

        real_name, ok = QInputDialog.getText(self, "添加用户", "请输入真实姓名:")
        if not ok:
            real_name = ""

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           INSERT INTO users (username, password, role, real_name)
                           VALUES (?, ?, ?, ?)
                           """, (username, password, role, real_name))
            self.db_conn.commit()
            self.load_users()
            self.logger.info(f"添加用户: {username}")
        except Exception as e:
            self.logger.error(f"添加用户错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"添加用户失败: {str(e)}")

    def delete_user(self, user_id):
        """删除用户"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个用户吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                self.db_conn.commit()
                self.load_users()
                self.logger.info(f"删除用户: {user_id}")
            except Exception as e:
                self.logger.error(f"删除用户错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除用户失败: {str(e)}")

    def reset_password(self):
        """重置密码"""
        selected = self.user_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要重置密码的用户")
            return

        user_id = self.user_table.item(selected[0].row(), 0).text()
        username = self.user_table.item(selected[0].row(), 1).text()

        new_password, ok = QInputDialog.getText(
            self, "重置密码", f"为 {username} 设置新密码:", QLineEdit.Password
        )

        if ok and new_password:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "UPDATE users SET password = ? WHERE user_id = ?",
                    (new_password, user_id)
                )
                self.db_conn.commit()
                QMessageBox.information(self, "成功", "密码重置成功")
                self.logger.info(f"重置用户密码: {username}")
            except Exception as e:
                self.logger.error(f"重置密码错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"重置密码失败: {str(e)}")

    def add_course(self):
        """添加课程"""
        name, ok = QInputDialog.getText(self, "添加课程", "请输入课程名称:")
        if not ok or not name:
            return

        credit, ok = QInputDialog.getDouble(self, "添加课程", "请输入学分:", min=0.5, max=10, decimals=1)
        if not ok:
            return

        types = ["必修", "选修"]
        course_type, ok = QInputDialog.getItem(self, "添加课程", "选择课程类型:", types, 0, False)
        if not ok:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           INSERT INTO courses (course_name, credit, course_type)
                           VALUES (?, ?, ?)
                           """, (name, credit, course_type))
            self.db_conn.commit()
            self.load_courses()
            self.logger.info(f"添加课程: {name}")
        except Exception as e:
            self.logger.error(f"添加课程错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"添加课程失败: {str(e)}")

    def edit_course(self, course_id):
        """编辑课程"""
        QMessageBox.information(self, "提示", "编辑课程功能开发中")

    def add_class(self):
        """添加班级"""
        name, ok = QInputDialog.getText(self, "添加班级", "请输入班级名称:")
        if not ok or not name:
            return

        grade, ok = QInputDialog.getText(self, "添加班级", "请输入年级:")
        if not ok:
            grade = ""

        major, ok = QInputDialog.getText(self, "添加班级", "请输入专业:")
        if not ok:
            major = ""

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           INSERT INTO classes (class_name, grade, major)
                           VALUES (?, ?, ?)
                           """, (name, grade, major))
            self.db_conn.commit()
            self.load_classes()
            self.logger.info(f"添加班级: {name}")
        except Exception as e:
            self.logger.error(f"添加班级错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"添加班级失败: {str(e)}")

    def edit_class(self, class_id):
        """编辑班级"""
        QMessageBox.information(self, "提示", "编辑班级功能开发中")