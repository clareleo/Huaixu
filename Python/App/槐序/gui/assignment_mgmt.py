from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QHeaderView, QFileDialog, QInputDialog
)
from PyQt5.QtCore import Qt
import os
import logging
from utils.file_monitor import AssignmentFolderMonitor


class AssignmentManagementWindow(QWidget):
    """作业管理窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("作业管理")
        self.resize(1000, 700)
        self.init_ui()
        self.load_courses()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.course_combo = QComboBox()
        self.course_combo.currentIndexChanged.connect(self.load_assignments)

        add_folder_btn = QPushButton("添加作业文件夹")
        add_folder_btn.clicked.connect(self.add_assignment_folder)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_assignments)

        toolbar.addWidget(QLabel("课程:"))
        toolbar.addWidget(self.course_combo)
        toolbar.addWidget(add_folder_btn)
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # 作业文件夹表格
        self.folder_table = QTableWidget()
        self.folder_table.setColumnCount(4)
        self.folder_table.setHorizontalHeaderLabels(["ID", "课程", "文件夹路径", "操作"])
        self.folder_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.folder_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.folder_table)

        # 作业提交详情区域
        self.detail_label = QLabel("选择文件夹查看作业提交详情")
        layout.addWidget(self.detail_label)

        self.submission_table = QTableWidget()
        self.submission_table.setColumnCount(6)
        self.submission_table.setHorizontalHeaderLabels(["学号", "姓名", "文件", "状态", "分数", "操作"])
        self.submission_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.submission_table)

        self.setLayout(layout)

        # 连接信号
        self.folder_table.cellClicked.connect(self.show_folder_details)

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

    def load_assignments(self):
        """加载作业文件夹列表"""
        course_id = self.course_combo.currentData()

        try:
            cursor = self.db_conn.cursor()

            query = """
                    SELECT f.folder_id, c.course_name, f.folder_path
                    FROM assignment_folders f
                             JOIN courses c ON f.course_id = c.course_id
                    WHERE 1 = 1 \
                    """
            params = []

            if course_id:
                query += " AND f.course_id = ?"
                params.append(course_id)

            query += " ORDER BY c.course_name"

            cursor.execute(query, params)
            folders = cursor.fetchall()

            self.folder_table.setRowCount(len(folders))
            for row, folder in enumerate(folders):
                for col in range(3):
                    self.folder_table.setItem(row, col, QTableWidgetItem(str(folder[col])))

                # 添加查看按钮
                view_btn = QPushButton("查看")
                view_btn.clicked.connect(lambda _, f=folder: self.show_folder_details(f))
                self.folder_table.setCellWidget(row, 3, view_btn)
        except Exception as e:
            self.logger.error(f"加载作业文件夹错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载作业文件夹失败: {str(e)}")

    def add_assignment_folder(self):
        """添加作业文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择作业文件夹")
        if not folder_path:
            return

        course_id = self.course_combo.currentData()
        if not course_id:
            QMessageBox.warning(self, "提示", "请先选择课程")
            return

        description, ok = QInputDialog.getText(
            self, "作业描述", "请输入作业描述:"
        )

        if ok:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                               INSERT INTO assignment_folders
                                   (folder_path, course_id, description)
                               VALUES (?, ?, ?)
                               """, (folder_path, course_id, description))
                self.db_conn.commit()
                self.load_assignments()
                self.logger.info(f"添加作业文件夹: {folder_path}")
            except Exception as e:
                self.logger.error(f"添加作业文件夹错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加作业文件夹失败: {str(e)}")

    def show_folder_details(self, folder):
        """显示选定文件夹的作业提交详情"""
        folder_id, course_name, folder_path = folder
        self.detail_label.setText(f"作业详情 - {course_name}")

        try:
            # 获取该课程的学生列表
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT s.student_id, s.name
                           FROM students s
                                    JOIN classes c ON s.class_id = c.class_id
                                    JOIN course_class cc ON c.class_id = cc.class_id
                           WHERE cc.course_id = (SELECT course_id FROM assignment_folders WHERE folder_id = ?)
                           ORDER BY s.student_id
                           """, (folder_id,))
            students = cursor.fetchall()

            # 获取已有提交记录
            cursor.execute("""
                           SELECT student_id, file_name, status, score
                           FROM assignment_submissions
                           WHERE folder_id = ?
                           """, (folder_id,))
            submissions = {row[0]: row[1:] for row in cursor.fetchall()}

            # 检查文件夹中的文件
            monitor = AssignmentFolderMonitor(folder_path)
            current_files = monitor._get_current_files()

            self.submission_table.setRowCount(len(students))
            for row, (student_id, name) in enumerate(students):
                self.submission_table.setItem(row, 0, QTableWidgetItem(student_id))
                self.submission_table.setItem(row, 1, QTableWidgetItem(name))

                # 查找学生提交的文件
                student_files = [f for f in current_files if student_id in f]
                file_item = QTableWidgetItem(", ".join(student_files) if student_files else "未提交")
                self.submission_table.setItem(row, 2, file_item)

                # 状态和分数
                if student_id in submissions:
                    file_name, status, score = submissions[student_id]
                    self.submission_table.setItem(row, 3, QTableWidgetItem(status))
                    self.submission_table.setItem(row, 4, QTableWidgetItem(str(score) if score else ""))
                else:
                    self.submission_table.setItem(row, 3, QTableWidgetItem("未提交"))
                    self.submission_table.setItem(row, 4, QTableWidgetItem(""))

                # 操作按钮
                grade_btn = QPushButton("批改")
                grade_btn.clicked.connect(lambda _, s=student_id: self.grade_assignment(s, folder_id))
                self.submission_table.setCellWidget(row, 5, grade_btn)
        except Exception as e:
            self.logger.error(f"加载作业详情错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载作业详情失败: {str(e)}")

    def grade_assignment(self, student_id, folder_id):
        """批改作业"""
        # 这里应该弹出一个对话框让教师输入分数和反馈
        # 简化示例，使用输入对话框
        score, ok = QInputDialog.getDouble(
            self, "批改作业", "请输入分数 (0-100):",
            min=0, max=100, decimals=1
        )

        if ok:
            try:
                cursor = self.db_conn.cursor()

                # 检查是否已有记录
                cursor.execute("""
                               SELECT submission_id
                               FROM assignment_submissions
                               WHERE student_id = ?
                                 AND folder_id = ?
                               """, (student_id, folder_id))
                exists = cursor.fetchone()

                if exists:
                    # 更新记录
                    cursor.execute("""
                                   UPDATE assignment_submissions
                                   SET score  = ?,
                                       status = '已批改'
                                   WHERE submission_id = ?
                                   """, (score, exists[0]))
                else:
                    # 插入新记录
                    cursor.execute("""
                                   INSERT INTO assignment_submissions
                                       (student_id, folder_id, file_name, status, score)
                                   VALUES (?, ?, '手动录入', '已批改', ?)
                                   """, (student_id, folder_id, score))

                self.db_conn.commit()
                self.logger.info(f"批改作业: 学生 {student_id} 分数 {score}")

                # 刷新显示
                current_row = self.folder_table.currentRow()
                if current_row >= 0:
                    folder = [
                        self.folder_table.item(current_row, col).text() for col in range(3)
                    ]
                    self.show_folder_details(folder)
            except Exception as e:
                self.logger.error(f"批改作业错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"批改作业失败: {str(e)}")