from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QHeaderView, QDialog, QLineEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt
import logging


class GradeManagementWindow(QWidget):
    """成绩管理窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("成绩管理")
        self.resize(800, 600)
        self.init_ui()
        self.load_courses()
        self.load_classes()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 过滤区域
        filter_layout = QHBoxLayout()

        self.course_combo = QComboBox()
        self.course_combo.currentIndexChanged.connect(self.load_grades)

        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.load_grades)

        # 移除了学期下拉框
        filter_layout.addWidget(QLabel("课程:"))
        filter_layout.addWidget(self.course_combo)
        filter_layout.addWidget(QLabel("班级:"))
        filter_layout.addWidget(self.class_combo)
        layout.addLayout(filter_layout)

        # 操作按钮区域
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("录入成绩")
        add_btn.clicked.connect(self.add_grades)

        edit_btn = QPushButton("修改成绩")
        edit_btn.clicked.connect(self.edit_grades)

        import_btn = QPushButton("导入成绩")
        import_btn.clicked.connect(self.import_grades)

        export_btn = QPushButton("导出成绩")
        export_btn.clicked.connect(self.export_grades)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

        # 成绩表格
        self.grade_table = QTableWidget()
        self.grade_table.setColumnCount(4)
        self.grade_table.setHorizontalHeaderLabels([
            "学号", "姓名", "成绩", "操作"
        ])
        self.grade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.grade_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.grade_table)

        # 统计信息区域
        self.stats_label = QLabel("统计信息: 请选择课程和班级")
        layout.addWidget(self.stats_label)

        self.setLayout(layout)

    def edit_grade(self, row):
        """编辑单个成绩"""
        student_id = self.grade_table.item(row, 0).text()
        student_name = self.grade_table.item(row, 1).text()
        current_score_text = self.grade_table.item(row, 2).text()

        course_id = self.course_combo.currentData()

        current_score = None
        if current_score_text:
            try:
                current_score = float(current_score_text)
            except ValueError:
                pass

        dialog = GradeEditDialog(
            self.db_conn, student_id, student_name, course_id, current_score
        )

        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    cursor = self.db_conn.cursor()

                    # 检查是否已有成绩记录
                    cursor.execute("""
                                   SELECT score_id
                                   FROM scores
                                   WHERE student_id = ?
                                     AND course_id = ?
                                     AND exam_type = ?
                                   """, (student_id, course_id, data['exam_type']))

                    existing = cursor.fetchone()

                    if existing:
                        # 更新成绩
                        cursor.execute("""
                                       UPDATE scores
                                       SET score = ?
                                       WHERE score_id = ?
                                       """, (data['score'], existing[0]))
                    else:
                        # 插入新成绩
                        cursor.execute("""
                                       INSERT INTO scores (student_id, course_id, score, exam_type)
                                       VALUES (?, ?, ?, ?)
                                       """, (student_id, course_id, data['score'], data['exam_type']))

                    self.db_conn.commit()
                    self.load_grades()
                    self.logger.info(f"更新成绩: {student_id} - {data['score']}")

                except Exception as e:
                    self.logger.error(f"更新成绩错误: {str(e)}")
                    QMessageBox.critical(self, "错误", f"更新成绩失败: {str(e)}")
            else:
                QMessageBox.warning(self, "输入错误", "请输入有效的成绩(0-100)")

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
            QMessageBox.critical(self, "错误", f"加载班级列表失败: {str(e)}")

    def load_grades(self):
        """加载成绩数据"""
        course_id = self.course_combo.currentData()
        class_id = self.class_combo.currentData()

        if not course_id or not class_id:
            self.grade_table.setRowCount(0)
            self.stats_label.setText("请选择具体的课程和班级")
            return

        try:
            cursor = self.db_conn.cursor()

            # 查询学生和成绩
            query = """
                    SELECT s.student_id, s.name, sc.score
                    FROM students s
                             LEFT JOIN scores sc ON s.student_id = sc.student_id
                        AND sc.course_id = ?
                    WHERE s.class_id = ?
                    ORDER BY s.student_id \
                    """
            cursor.execute(query, (course_id, class_id))
            grades = cursor.fetchall()

            self.grade_table.setRowCount(len(grades))
            for row, (student_id, name, score) in enumerate(grades):
                self.grade_table.setItem(row, 0, QTableWidgetItem(student_id))
                self.grade_table.setItem(row, 1, QTableWidgetItem(name))
                self.grade_table.setItem(row, 2, QTableWidgetItem(str(score) if score else ""))

                # 操作按钮
                edit_btn = QPushButton("编辑")
                edit_btn.clicked.connect(lambda _, r=row: self.edit_grade(r))
                self.grade_table.setCellWidget(row, 3, edit_btn)

            # 计算统计信息
            cursor.execute("""
                           SELECT AVG(score),
                                  MAX(score),
                                  MIN(score),
                                  COUNT(CASE WHEN score >= 60 THEN 1 END) * 100.0 / COUNT(*)
                           FROM scores
                           WHERE course_id = ?
                             AND student_id IN (SELECT student_id
                                                FROM students
                                                WHERE class_id = ?)
                           """, (course_id, class_id))
            stats = cursor.fetchone()

            avg, max_, min_, pass_rate = stats
            stats_text = (
                f"统计信息: 平均分 {avg:.1f} | "
                f"最高分 {max_ or '无'} | "
                f"最低分 {min_ or '无'} | "
                f"及格率 {pass_rate or 0:.1f}%"
            )
            self.stats_label.setText(stats_text)

        except Exception as e:
            self.logger.error(f"加载成绩错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载成绩失败: {str(e)}")

    def add_grades(self):
        """批量录入成绩"""
        course_id = self.course_combo.currentData()
        class_id = self.class_combo.currentData()

        if not course_id or not class_id:
            QMessageBox.warning(self, "提示", "请先选择课程和班级")
            return

        QMessageBox.information(self, "提示", "批量录入成绩功能开发中")

    def edit_grade(self, row):
        """编辑单个成绩"""
        student_id = self.grade_table.item(row, 0).text()
        student_name = self.grade_table.item(row, 1).text()
        current_score = self.grade_table.item(row, 2).text()

        QMessageBox.information(
            self, "提示",
            f"编辑 {student_name}({student_id}) 的成绩\n当前成绩: {current_score}\n功能开发中"
        )

    def edit_grades(self):
        """编辑成绩"""
        QMessageBox.information(self, "提示", "编辑成绩功能开发中")

    def import_grades(self):
        """导入成绩"""
        QMessageBox.information(self, "提示", "导入成绩功能开发中")

    def export_grades(self):
        """导出成绩"""
        QMessageBox.information(self, "提示", "导出成绩功能开发中")


class GradeEditDialog(QDialog):
    """成绩编辑对话框"""

    def __init__(self, db_conn, student_id, student_name, course_id, current_score=None):
        super().__init__()
        self.db_conn = db_conn
        self.student_id = student_id
        self.course_id = course_id
        self.current_score = current_score

        self.setWindowTitle(f"编辑成绩 - {student_name}")
        self.resize(300, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 学生信息
        info_label = QLabel(f"学生: {self.student_id} - {self.student_name}")
        layout.addWidget(info_label)

        # 成绩输入
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("成绩:"))

        self.score_input = QLineEdit()
        self.score_input.setPlaceholderText("0-100")
        if self.current_score is not None:
            self.score_input.setText(str(self.current_score))
        score_layout.addWidget(self.score_input)

        layout.addLayout(score_layout)

        # 考试类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("考试类型:"))

        self.type_combo = QComboBox()
        self.type_combo.addItems(["期末", "期中", "平时", "作业"])
        type_layout.addWidget(self.type_combo)

        layout.addLayout(type_layout)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        """获取成绩数据"""
        try:
            score = float(self.score_input.text().strip())
            if score < 0 or score > 100:
                return None
            return {
                'score': score,
                'exam_type': self.type_combo.currentText()
            }
        except ValueError:
            return None