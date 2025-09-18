"""课程管理"""
# gui/course_mgmt.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QHeaderView, QInputDialog, QDialog,
    QFormLayout, QDialogButtonBox, QLineEdit, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
import logging


class CourseManagementWindow(QWidget):
    """课程管理窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("课程管理")
        self.resize(800, 600)
        self.init_ui()
        self.load_courses()

    def init_ui(self):
        layout = QVBoxLayout()

        # 操作按钮
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("添加课程")
        add_btn.clicked.connect(self.add_course)

        edit_btn = QPushButton("编辑课程")
        edit_btn.clicked.connect(self.edit_course)

        delete_btn = QPushButton("删除课程")
        delete_btn.clicked.connect(self.delete_course)

        assign_btn = QPushButton("分配课程到班级")
        assign_btn.clicked.connect(self.assign_course_to_class)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(assign_btn)
        layout.addLayout(btn_layout)

        # 课程表格
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["ID", "课程名称", "学分", "类型", "描述"])
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.course_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.course_table)

        self.setLayout(layout)

    def load_courses(self):
        """加载课程列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM courses ORDER BY course_name")
            courses = cursor.fetchall()

            self.course_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col in range(5):
                    self.course_table.setItem(row, col, QTableWidgetItem(str(course[col])))
        except Exception as e:
            self.logger.error(f"加载课程列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载课程列表失败: {str(e)}")

    def add_course(self):
        """添加新课程"""
        dialog = CourseEditDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            self.load_courses()

    # 其他方法实现...
