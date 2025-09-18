from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QHeaderView, QDateEdit, QLineEdit,
    QDoubleSpinBox, QDialog, QFormLayout, QDialogButtonBox,
    QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
import logging
from datetime import datetime


class ClassroomManagementWindow(QWidget):
    """课堂管理窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("课堂管理")
        self.resize(1000, 700)
        self.init_ui()
        self.load_courses()
        self.load_activities()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.course_combo = QComboBox()
        self.course_combo.currentIndexChanged.connect(self.load_activities)

        add_activity_btn = QPushButton("新建课堂活动")
        add_activity_btn.clicked.connect(self.add_classroom_activity)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_activities)

        toolbar.addWidget(QLabel("课程:"))
        toolbar.addWidget(self.course_combo)
        toolbar.addWidget(add_activity_btn)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # 课堂活动表格
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(5)
        self.activity_table.setHorizontalHeaderLabels(["ID", "课程", "日期", "活动类型", "操作"])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activity_table.cellClicked.connect(self.show_activity_details)
        layout.addWidget(self.activity_table)

        # 学生评分区域
        self.detail_label = QLabel("选择课堂活动查看学生评分")
        layout.addWidget(self.detail_label)

        self.score_table = QTableWidget()
        self.score_table.setColumnCount(5)
        self.score_table.setHorizontalHeaderLabels(["学号", "姓名", "分数", "评语", "操作"])
        self.score_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.score_table)

        self.setLayout(layout)

    def load_courses(self):
        """加载课程列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
            courses = cursor.fetchall()

            self.course_combo.clear()
            self.course_combo.addItem("所有课程", None)

            for course_id, course_name in courses:
                self.course_combo.addItem(course_name, course_id)
        except Exception as e:
            self.logger.error(f"加载课程列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载课程列表失败: {str(e)}")

    def load_activities(self):
        """加载课堂活动列表"""
        course_id = self.course_combo.currentData()

        try:
            cursor = self.db_conn.cursor()

            query = """
                    SELECT a.activity_id, \
                           c.course_name, \
                           a.activity_date,
                           a.activity_type
                    FROM classroom_activities a
                             JOIN courses c ON a.course_id = c.course_id
                    WHERE 1 = 1
                    """
            params = []

            if course_id:
                query += " AND a.course_id = ?"
                params.append(course_id)

            query += " ORDER BY a.activity_date DESC"

            cursor.execute(query, params)
            activities = cursor.fetchall()

            self.activity_table.setRowCount(len(activities))
            for row, activity in enumerate(activities):
                for col in range(4):
                    self.activity_table.setItem(row, col, QTableWidgetItem(str(activity[col])))

                # 添加评分按钮
                score_btn = QPushButton("学生评分")
                score_btn.clicked.connect(lambda _, a=activity: self.show_activity_details(a))
                self.activity_table.setCellWidget(row, 4, score_btn)
        except Exception as e:
            self.logger.error(f"加载课堂活动错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载课堂活动失败: {str(e)}")

    def add_classroom_activity(self):
        """新建课堂活动"""
        dialog = ClassroomActivityDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            self.load_activities()

    def show_activity_details(self, activity):
        """显示课堂活动的学生评分"""
        activity_id, course_name, activity_date, activity_type = activity
        self.detail_label.setText(f"课堂活动: {course_name} - {activity_type} ({activity_date})")

        try:
            # 获取该课程的学生列表
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT s.student_id, s.name
                           FROM students s
                                    JOIN classes c ON s.class_id = c.class_id
                                    JOIN course_class cc ON c.class_id = cc.class_id
                           WHERE cc.course_id = (SELECT course_id
                                                 FROM classroom_activities
                                                 WHERE activity_id = ?)
                           ORDER BY s.student_id
                           """, (activity_id,))
            students = cursor.fetchall()

            # 获取已有评分记录
            cursor.execute("""
                           SELECT student_id, score, comment
                           FROM classroom_scores
                           WHERE activity_id = ?
                           """, (activity_id,))
            scores = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

            self.score_table.setRowCount(len(students))
            for row, (student_id, name) in enumerate(students):
                self.score_table.setItem(row, 0, QTableWidgetItem(student_id))
                self.score_table.setItem(row, 1, QTableWidgetItem(name))

                # 分数和评语
                if student_id in scores:
                    score, comment = scores[student_id]
                    self.score_table.setItem(row, 2, QTableWidgetItem(str(score)))
                    self.score_table.setItem(row, 3, QTableWidgetItem(comment or ""))
                else:
                    self.score_table.setItem(row, 2, QTableWidgetItem("0"))
                    self.score_table.setItem(row, 3, QTableWidgetItem(""))

                # 操作按钮
                grade_btn = QPushButton("评分")
                grade_btn.clicked.connect(lambda _, s=student_id: self.grade_student(s, activity_id))
                self.score_table.setCellWidget(row, 4, grade_btn)

        except Exception as e:
            self.logger.error(f"加载课堂活动详情错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载课堂活动详情失败: {str(e)}")

    def grade_student(self, student_id, activity_id):
        """为学生评分"""
        dialog = StudentGradeDialog(self.db_conn, student_id, activity_id)
        if dialog.exec_() == QDialog.Accepted:
            self.show_activity_details([activity_id, "", "", ""])  # 刷新显示


class ClassroomActivityDialog(QDialog):
    """新建课堂活动对话框"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.setWindowTitle("新建课堂活动")
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # 课程选择
        self.course_combo = QComboBox()
        self.load_courses()
        layout.addRow("课程:", self.course_combo)

        # 活动日期
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        layout.addRow("活动日期:", self.date_edit)

        # 活动类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["回答问题", "小组讨论", "课堂测验", "演示汇报", "其他"])
        layout.addRow("活动类型:", self.type_combo)

        # 最大分数
        self.max_score_spin = QDoubleSpinBox()
        self.max_score_spin.setRange(0, 100)
        self.max_score_spin.setValue(10)
        self.max_score_spin.setSuffix("分")
        layout.addRow("最大分数:", self.max_score_spin)

        # 活动描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        layout.addRow("活动描述:", self.desc_edit)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_courses(self):
        """加载课程列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
            courses = cursor.fetchall()

            for course_id, course_name in courses:
                self.course_combo.addItem(course_name, course_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载课程列表失败: {str(e)}")

    def get_data(self):
        """获取表单数据"""
        return {
            'course_id': self.course_combo.currentData(),
            'activity_date': self.date_edit.date().toString("yyyy-MM-dd"),
            'activity_type': self.type_combo.currentText(),
            'max_score': self.max_score_spin.value(),
            'description': self.desc_edit.toPlainText()
        }


class StudentGradeDialog(QDialog):
    """学生评分对话框"""

    def __init__(self, db_conn, student_id, activity_id):
        super().__init__()
        self.db_conn = db_conn
        self.student_id = student_id
        self.activity_id = activity_id
        self.setWindowTitle("学生评分")
        self.resize(300, 200)
        self.init_ui()
        self.load_student_info()

    def init_ui(self):
        layout = QFormLayout()

        # 学生信息
        self.student_label = QLabel()
        layout.addRow("学生:", self.student_label)

        # 分数输入
        self.score_spin = QDoubleSpinBox()
        self.score_spin.setRange(0, 100)
        self.score_spin.setDecimals(1)
        layout.addRow("分数:", self.score_spin)

        # 活动信息
        self.activity_label = QLabel()
        layout.addRow("活动:", self.activity_label)

        # 评语
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(60)
        layout.addRow("评语:", self.comment_edit)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_grade)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_student_info(self):
        """加载学生和活动信息"""
        try:
            cursor = self.db_conn.cursor()

            # 获取学生信息
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (self.student_id,))
            student_name = cursor.fetchone()[0]
            self.student_label.setText(f"{self.student_id} - {student_name}")

            # 获取活动信息
            cursor.execute("""
                           SELECT a.activity_type, a.description, c.course_name
                           FROM classroom_activities a
                                    JOIN courses c ON a.course_id = c.course_id
                           WHERE a.activity_id = ?
                           """, (self.activity_id,))
            activity_type, description, course_name = cursor.fetchone()
            self.activity_label.setText(f"{course_name} - {activity_type}")

            # 加载已有评分
            cursor.execute("""
                           SELECT score, comment
                           FROM classroom_scores
                           WHERE activity_id = ?
                             AND student_id = ?
                           """, (self.activity_id, self.student_id))
            existing = cursor.fetchone()
            if existing:
                self.score_spin.setValue(existing[0])
                self.comment_edit.setPlainText(existing[1] or "")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载信息失败: {str(e)}")

    def save_grade(self):
        """保存评分"""
        try:
            score = self.score_spin.value()
            comment = self.comment_edit.toPlainText()

            cursor = self.db_conn.cursor()

            # 检查是否已有记录
            cursor.execute("""
                           SELECT score_id
                           FROM classroom_scores
                           WHERE activity_id = ?
                             AND student_id = ?
                           """, (self.activity_id, self.student_id))

            existing = cursor.fetchone()

            if existing:
                # 更新记录
                cursor.execute("""
                               UPDATE classroom_scores
                               SET score   = ?,
                                   comment = ?
                               WHERE score_id = ?
                               """, (score, comment, existing[0]))
            else:
                # 插入新记录
                cursor.execute("""
                               INSERT INTO classroom_scores (activity_id, student_id, score, comment)
                               VALUES (?, ?, ?, ?)
                               """, (self.activity_id, self.student_id, score, comment))

            self.db_conn.commit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存评分失败: {str(e)}")
            self.reject()