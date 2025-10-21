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

        assign_course_to_class_btn = QPushButton("分配课程到班级")
        assign_course_to_class_btn.clicked.connect(self.assign_course_to_class)

        assign_student_to_class_btn = QPushButton("分配学生到班级")
        assign_student_to_class_btn.clicked.connect(self.assign_student_to_class)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(assign_course_to_class_btn)
        btn_layout.addWidget(assign_student_to_class_btn)
        layout.addLayout(btn_layout)

        # 课程表格
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["ID", "课程名称", "学分", "类型", "描述"])
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.course_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.course_table)

        # 学生-班级-课程关系表格
        self.relationship_table = QTableWidget()
        self.relationship_table.setColumnCount(4)
        self.relationship_table.setHorizontalHeaderLabels(["学生ID", "学生姓名", "班级ID", "课程ID"])
        self.relationship_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.relationship_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.relationship_table)

        self.setLayout(layout)

    def assign_course_to_class(self):
        dialog = AssignCourseToClassDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            self.load_courses()
            self.load_relationships()

    def assign_student_to_class(self):
        dialog = AssignStudentToClassDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            self.load_relationships()

    def load_relationships(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT s.id, s.name, c.id, co.id
                           FROM students s
                                    JOIN student_classes sc ON s.id = sc.student_id
                                    JOIN classes c ON sc.class_id = c.id
                                    JOIN class_courses cc ON c.id = cc.class_id
                                    JOIN courses co ON cc.course_id = co.id
                           """)
            relationships = cursor.fetchall()

            self.relationship_table.setRowCount(len(relationships))
            for row, relationship in enumerate(relationships):
                for col in range(4):
                    self.relationship_table.setItem(row, col, QTableWidgetItem(str(relationship[col])))
        except Exception as e:
            self.logger.error(f"加载学生-班级-课程关系错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载学生-班级-课程关系失败: {str(e)}")



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

class AssignCourseToClassDialog(QDialog):
    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.class_combo = QComboBox()
        self.load_classes()
        layout.addRow("选择班级:", self.class_combo)

        self.course_combo = QComboBox()
        self.load_courses()
        layout.addRow("选择课程:", self.course_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_classes(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM classes")
            classes = cursor.fetchall()
            for class_id, class_name in classes:
                self.class_combo.addItem(class_name, class_id)
        except Exception as e:
            logging.error(f"加载班级错误: {str(e)}")

    def load_courses(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM courses")
            courses = cursor.fetchall()
            for course_id, course_name in courses:
                self.course_combo.addItem(course_name, course_id)
        except Exception as e:
            logging.error(f"加载课程错误: {str(e)}")

    def accept(self):
        class_id = self.class_combo.currentData()
        course_id = self.course_combo.currentData()
        if class_id and course_id:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("INSERT INTO class_courses (class_id, course_id) VALUES (?, ?)", (class_id, course_id))
                self.db_conn.commit()
                super().accept()
            except Exception as e:
                logging.error(f"分配课程到班级错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"分配课程到班级失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "请选择班级和课程")

class AssignStudentToClassDialog(QDialog):
    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.class_combo = QComboBox()
        self.load_classes()
        layout.addRow("选择班级:", self.class_combo)

        self.student_combo = QComboBox()
        self.load_students()
        layout.addRow("选择学生:", self.student_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_classes(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM classes")
            classes = cursor.fetchall()
            for class_id, class_name in classes:
                self.class_combo.addItem(class_name, class_id)
        except Exception as e:
            logging.error(f"加载班级错误: {str(e)}")

    def load_students(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT id, name FROM students")
            students = cursor.fetchall()
            for student_id, student_name in students:
                self.student_combo.addItem(student_name, student_id)
        except Exception as e:
            logging.error(f"加载学生错误: {str(e)}")

    def accept(self):
        class_id = self.class_combo.currentData()
        student_id = self.student_combo.currentData()
        if class_id and student_id:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("INSERT INTO student_classes (student_id, class_id) VALUES (?, ?)", (student_id, class_id))
                self.db_conn.commit()
                super().accept()
            except Exception as e:
                logging.error(f"分配学生到班级错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"分配学生到班级失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "请选择班级和学生")
