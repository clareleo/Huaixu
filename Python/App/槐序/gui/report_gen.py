from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
import logging
from utils.excel_utils import export_grades_to_excel


class ReportGenerationWindow(QWidget):
    """报表生成窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("成绩报表")
        self.resize(900, 600)
        self.init_ui()
        self.load_courses()
        self.load_classes()

    def init_ui(self):
        layout = QVBoxLayout()

        # 筛选区域
        filter_layout = QHBoxLayout()

        self.course_combo = QComboBox()
        self.course_combo.currentIndexChanged.connect(self.generate_report)

        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.generate_report)

        self.term_combo = QComboBox()
        self.term_combo.addItems(["2023-2024-1", "2023-2024-2", "2022-2023-1", "2022-2023-2"])
        self.term_combo.currentIndexChanged.connect(self.generate_report)

        filter_layout.addWidget(QLabel("课程:"))
        filter_layout.addWidget(self.course_combo)
        filter_layout.addWidget(QLabel("班级:"))
        filter_layout.addWidget(self.class_combo)
        filter_layout.addWidget(QLabel("学期:"))
        filter_layout.addWidget(self.term_combo)
        layout.addLayout(filter_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("导出Excel")
        export_btn.clicked.connect(self.export_excel)

        print_btn = QPushButton("打印报表")
        print_btn.clicked.connect(self.print_report)

        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(print_btn)
        layout.addLayout(btn_layout)

        # 报表表格
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "学号", "姓名", "平时成绩", "期中成绩", "期末成绩",
            "总成绩", "等级", "排名"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.report_table)

        # 统计信息
        self.stats_label = QLabel("请选择课程、班级和学期生成报表")
        layout.addWidget(self.stats_label)

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

    def load_classes(self):
        """加载班级列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_id, class_name FROM classes ORDER BY class_name")
            classes = cursor.fetchall()

            self.class_combo.clear()
            self.class_combo.addItem("所有班级", None)

            for class_id, class_name in classes:
                self.class_combo.addItem(class_name, class_id)
        except Exception as e:
            self.logger.error(f"加载班级列表错误: {str(e)}")

    def generate_report(self):
        """生成成绩报表"""
        course_id = self.course_combo.currentData()
        class_id = self.class_combo.currentData()
        term = self.term_combo.currentText()

        if not course_id or not class_id:
            self.report_table.setRowCount(0)
            self.stats_label.setText("请选择具体的课程和班级")
            return

        try:
            cursor = self.db_conn.cursor()

            # 获取学生成绩数据
            query = """
                    SELECT s.student_id, \
                           s.name,
                           MAX(CASE WHEN sc.exam_type = '平时' THEN sc.score END) as daily_score,
                           MAX(CASE WHEN sc.exam_type = '期中' THEN sc.score END) as midterm_score,
                           MAX(CASE WHEN sc.exam_type = '期末' THEN sc.score END) as final_score
                    FROM students s
                             LEFT JOIN scores sc ON s.student_id = sc.student_id
                        AND sc.course_id = ? AND sc.term = ?
                    WHERE s.class_id = ?
                    GROUP BY s.student_id, s.name
                    ORDER BY s.student_id \
                    """

            cursor.execute(query, (course_id, term, class_id))
            students = cursor.fetchall()

            # 计算总成绩和排名
            student_scores = []
            for student in students:
                daily = student[2] or 0
                midterm = student[3] or 0
                final = student[4] or 0
                classroom = student[5] or 0

                # 计算总成绩 (权重: 平时20% + 期中30% + 期末40% + 课堂10%)
                total_score = daily * 0.2 + midterm * 0.3 + final * 0.4 + classroom * 0.1

                # 确定等级
                if total_score >= 90:
                    grade = "优秀"
                elif total_score >= 80:
                    grade = "良好"
                elif total_score >= 70:
                    grade = "中等"
                elif total_score >= 60:
                    grade = "及格"
                else:
                    grade = "不及格"

                student_scores.append((*student, total_score, grade))

            # 按总成绩排序确定排名
            student_scores.sort(key=lambda x: x[5], reverse=True)
            ranked_students = []
            for i, student in enumerate(student_scores):
                ranked_students.append((*student, i + 1))

                # 在查询中添加课堂成绩
                query = """
                        SELECT s.student_id,
                               s.name,
                               MAX(CASE WHEN sc.exam_type = '平时' THEN sc.score END) as daily_score,
                               MAX(CASE WHEN sc.exam_type = '期中' THEN sc.score END) as midterm_score,
                               MAX(CASE WHEN sc.exam_type = '期末' THEN sc.score END) as final_score,
                               COALESCE(SUM(cs.score), 0)                             as classroom_score -- 添加课堂成绩
                        FROM students s
                                 LEFT JOIN scores sc ON s.student_id = sc.student_id
                            AND sc.course_id = ? AND sc.term = ?
                                 LEFT JOIN classroom_scores cs ON s.student_id = cs.student_id
                            AND cs.activity_id IN (SELECT activity_id \
                                                   FROM classroom_activities \
                                                   WHERE course_id = ? \
                                                     AND term = ?)
                        WHERE s.class_id = ?
                        GROUP BY s.student_id, s.name
                        ORDER BY s.student_id \
                        """

                cursor.execute(query, (course_id, term, course_id, term, class_id))
                students = cursor.fetchall()

            # 显示报表
            self.report_table.setRowCount(len(ranked_students))
            for row, student in enumerate(ranked_students):
                for col in range(8):  # 8列数据
                    value = student[col] if col < 6 else student[col]
                    self.report_table.setItem(row, col, QTableWidgetItem(str(value or "")))

            # 计算统计信息
            total_scores = [s[5] for s in ranked_students if s[5] > 0]
            if total_scores:
                avg_score = sum(total_scores) / len(total_scores)
                max_score = max(total_scores)
                min_score = min(total_scores)
                pass_count = sum(1 for s in total_scores if s >= 60)
                pass_rate = (pass_count / len(total_scores)) * 100

                stats_text = (
                    f"统计信息: 平均分 {avg_score:.1f} | "
                    f"最高分 {max_score:.1f} | "
                    f"最低分 {min_score:.1f} | "
                    f"及格率 {pass_rate:.1f}% | "
                    f"学生总数 {len(ranked_students)}"
                )
                self.stats_label.setText(stats_text)
            else:
                self.stats_label.setText("暂无成绩数据")

        except Exception as e:
            self.logger.error(f"生成报表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成报表失败: {str(e)}")

    def export_excel(self):
        """导出Excel报表"""
        course_name = self.course_combo.currentText()
        class_name = self.class_combo.currentText()
        term = self.term_combo.currentText()

        if not course_name or not class_name:
            QMessageBox.warning(self, "提示", "请先选择课程和班级")
            return

        try:
            # 获取表格数据
            data = []
            headers = []

            # 获取表头
            for col in range(self.report_table.columnCount()):
                headers.append(self.report_table.horizontalHeaderItem(col).text())

            # 获取数据
            for row in range(self.report_table.rowCount()):
                row_data = []
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # 导出到Excel
            filename = f"{course_name}_{class_name}_{term}_成绩报表.xlsx"
            export_grades_to_excel(headers, data, filename)

            QMessageBox.information(self, "成功", f"报表已导出到: {filename}")
            self.logger.info(f"导出报表: {filename}")

        except Exception as e:
            self.logger.error(f"导出Excel错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出Excel失败: {str(e)}")

    def print_report(self):
        """打印报表"""
        QMessageBox.information(self, "提示", "打印功能开发中")