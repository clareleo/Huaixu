# gui/student_score_mgmt.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QComboBox, QLabel,
    QMessageBox, QHeaderView, QDialog, QLineEdit, QDialogButtonBox,
    QTabWidget, QFormLayout, QFileDialog
)
from PyQt5.QtCore import Qt
import logging

# 尝试导入必要的库，如果失败则显示警告
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas未安装，Excel导入功能将不可用")

try:
    # 尝试导入openpyxl用于处理.xlsx文件
    import openpyxl

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    # 尝试导入xlrd用于处理.xls文件
    import xlrd

    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False


# 检查是否可以导入Excel支持
def check_excel_support():
    """检查Excel支持是否可用"""
    if not PANDAS_AVAILABLE:
        return False

    # 检查是否至少有一个Excel引擎可用
    # pandas 1.2.0+ 默认使用openpyxl处理.xlsx，使用xlrd处理.xls
    # 但xlrd 2.0+ 不再支持.xlsx，只支持.xls
    return True  # pandas本身支持Excel，但需要额外的引擎


class StudentScoreManagementWindow(QWidget):
    """学生成绩4+X管理窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)
        self._loading = False  # 防止递归加载标志

        self.setWindowTitle("学生成绩4+X管理")
        self.resize(1200, 800)
        self.init_ui()
        self.load_majors()
        self.load_courses()
        self.load_classes()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 创建选项卡
        tab_widget = QTabWidget()

        # 成绩管理选项卡
        self.score_tab = self.create_score_tab()
        tab_widget.addTab(self.score_tab, "成绩管理")

        # 专业课程管理选项卡
        self.major_course_tab = self.create_major_course_tab()
        tab_widget.addTab(self.major_course_tab, "专业课程管理")

        # 班级专业管理选项卡
        self.class_major_tab = self.create_class_major_tab()
        tab_widget.addTab(self.class_major_tab, "班级专业管理")

        layout.addWidget(tab_widget)
        self.setLayout(layout)

    def create_score_tab(self):
        """创建成绩管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 过滤区域
        filter_layout = QHBoxLayout()

        self.major_combo = QComboBox()
        self.major_combo.currentIndexChanged.connect(self.on_filter_changed)

        self.course_combo = QComboBox()
        self.course_combo.currentIndexChanged.connect(self.on_filter_changed)

        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_filter_changed)

        filter_layout.addWidget(QLabel("专业:"))
        filter_layout.addWidget(self.major_combo)
        filter_layout.addWidget(QLabel("课程:"))
        filter_layout.addWidget(self.course_combo)
        filter_layout.addWidget(QLabel("班级:"))
        filter_layout.addWidget(self.class_combo)
        layout.addLayout(filter_layout)

        # 操作按钮区域
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("录入成绩")
        add_btn.clicked.connect(self.add_score)

        edit_btn = QPushButton("修改成绩")
        edit_btn.clicked.connect(self.edit_score)

        delete_btn = QPushButton("删除成绩")
        delete_btn.clicked.connect(self.delete_score)

        # 只有Excel支持可用时才显示Excel导入按钮
        excel_available = check_excel_support()
        self.import_btn = QPushButton("Excel导入成绩")
        if excel_available:
            self.import_btn.clicked.connect(self.import_scores_from_excel)
        else:
            self.import_btn.setEnabled(False)
            self.import_btn.setToolTip("需要安装依赖: pip install pandas openpyxl")
        btn_layout.addWidget(self.import_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_scores)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        # 成绩表格
        self.score_table = QTableWidget()
        self.score_table.setColumnCount(8)
        self.score_table.setHorizontalHeaderLabels([
            "学号", "姓名", "专业", "课程", "平时成绩", "期末成绩", "总成绩", "学分"
        ])
        self.score_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.score_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.score_table)

        # 统计信息区域
        self.stats_label = QLabel("统计信息: 请选择专业、课程和班级")
        layout.addWidget(self.stats_label)

        widget.setLayout(layout)
        return widget

    def create_major_course_tab(self):
        """创建专业课程管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 操作按钮
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("添加专业课程关联")
        add_btn.clicked.connect(self.add_major_course)

        delete_btn = QPushButton("删除专业课程关联")
        delete_btn.clicked.connect(self.delete_major_course)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_major_courses)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        # 专业课程表格
        self.major_course_table = QTableWidget()
        self.major_course_table.setColumnCount(4)
        self.major_course_table.setHorizontalHeaderLabels([
            "专业ID", "专业名称", "课程ID", "课程名称"
        ])
        self.major_course_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.major_course_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.major_course_table)

        self.load_major_courses()
        widget.setLayout(layout)
        return widget

    def create_class_major_tab(self):
        """创建班级专业管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 操作按钮
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("添加班级专业关联")
        add_btn.clicked.connect(self.add_class_major)

        delete_btn = QPushButton("删除班级专业关联")
        delete_btn.clicked.connect(self.delete_class_major)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_class_majors)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        # 班级专业表格
        self.class_major_table = QTableWidget()
        self.class_major_table.setColumnCount(4)
        self.class_major_table.setHorizontalHeaderLabels([
            "班级ID", "班级名称", "专业ID", "专业名称"
        ])
        self.class_major_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.class_major_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.class_major_table)

        self.load_class_majors()
        widget.setLayout(layout)
        return widget

    def on_filter_changed(self):
        """过滤条件改变时的处理"""
        if not self._loading:
            self.load_scores()

    def load_majors(self):
        """加载专业列表"""
        try:
            self._loading = True
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT major_id, major_name FROM majors ORDER BY major_name")
            majors = cursor.fetchall()

            # 更新所有专业下拉框
            for combo in [self.major_combo]:
                combo.clear()
                combo.addItem("所有专业", None)
                for major_id, major_name in majors:
                    combo.addItem(major_name, major_id)
        except Exception as e:
            self.logger.error(f"加载专业列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载专业列表失败: {str(e)}")
        finally:
            self._loading = False

    def load_courses(self):
        """加载课程列表"""
        try:
            self._loading = True
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
            courses = cursor.fetchall()

            # 更新所有课程下拉框
            for combo in [self.course_combo]:
                combo.clear()
                combo.addItem("所有课程", None)
                for course_id, course_name in courses:
                    combo.addItem(course_name, course_id)
        except Exception as e:
            self.logger.error(f"加载课程列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载课程列表失败: {str(e)}")
        finally:
            self._loading = False

    def load_classes(self):
        """加载班级列表"""
        try:
            self._loading = True
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_id, class_name FROM classes ORDER BY class_name")
            classes = cursor.fetchall()

            # 更新所有班级下拉框
            for combo in [self.class_combo]:
                combo.clear()
                combo.addItem("所有班级", None)
                for class_id, class_name in classes:
                    combo.addItem(class_name, class_id)
        except Exception as e:
            self.logger.error(f"加载班级列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载班级列表失败: {str(e)}")
        finally:
            self._loading = False

    def load_scores(self):
        """加载成绩数据"""
        if self._loading:
            return  # 防止递归调用

        self._loading = True
        try:
            major_id = self.major_combo.currentData()
            course_id = self.course_combo.currentData()
            class_id = self.class_combo.currentData()

            cursor = self.db_conn.cursor()

            # 如果选择了班级但没有选择课程，显示该班级所有学生的基础信息
            if class_id and not course_id:
                query = """
                        SELECT s.student_id, \
                               s.name,
                               CASE WHEN m.major_name IS NOT NULL THEN m.major_name ELSE '未分配专业' END,
                               '未选课程',
                               sc.regular_score, \
                               sc.final_score, \
                               sc.total_score, \
                               sc.credits
                        FROM students s
                                 LEFT JOIN scores sc ON s.student_id = sc.student_id
                                 LEFT JOIN majors m ON sc.major_id = m.major_id
                        WHERE s.class_id = ?
                        ORDER BY s.student_id \
                        """
                params = [class_id]
            else:
                query = """
                        SELECT s.student_id, \
                               s.name, \
                               m.major_name, \
                               c.course_name,
                               sc.regular_score, \
                               sc.final_score, \
                               sc.total_score, \
                               sc.credits
                        FROM scores sc
                                 JOIN students s ON sc.student_id = s.student_id
                                 LEFT JOIN majors m ON sc.major_id = m.major_id
                                 LEFT JOIN courses c ON sc.course_id = c.course_id
                        WHERE 1 = 1 \
                        """
                params = []

                if major_id:
                    query += " AND sc.major_id = ?"
                    params.append(major_id)

                if course_id:
                    query += " AND sc.course_id = ?"
                    params.append(course_id)

                if class_id:
                    query += " AND s.class_id = ?"
                    params.append(class_id)

                query += " ORDER BY s.student_id"

            cursor.execute(query, params)
            scores = cursor.fetchall()

            self.score_table.setRowCount(len(scores))
            for row, score in enumerate(scores):
                for col in range(8):
                    item = QTableWidgetItem(str(score[col]) if score[col] is not None else "")
                    self.score_table.setItem(row, col, item)

            # 计算统计信息
            if scores:
                total_scores = [s[6] for s in scores if s[6] is not None and s[6] != '']  # 总成绩
                if total_scores:
                    total_scores = [float(s) for s in total_scores if s != '']
                    if total_scores:
                        avg_score = sum(total_scores) / len(total_scores)
                        max_score = max(total_scores)
                        min_score = min(total_scores)
                        pass_count = sum(1 for s in total_scores if s >= 60)
                        pass_rate = (pass_count / len(total_scores)) * 100 if total_scores else 0

                        stats_text = (
                            f"统计信息: 平均分 {avg_score:.1f} | "
                            f"最高分 {max_score} | "
                            f"最低分 {min_score} | "
                            f"及格率 {pass_rate:.1f}%"
                        )
                        self.stats_label.setText(stats_text)
                    else:
                        self.stats_label.setText("统计信息: 无有效成绩数据")
                else:
                    self.stats_label.setText("统计信息: 无有效成绩数据")
            else:
                self.stats_label.setText("统计信息: 无数据")

        except Exception as e:
            self.logger.error(f"加载成绩错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载成绩失败: {str(e)}")
        finally:
            self._loading = False

    def import_scores_from_excel(self):
        """从Excel导入成绩"""
        excel_available = check_excel_support()
        if not excel_available:
            msg = "缺少Excel支持库，无法导入Excel文件\n\n"
            msg += "请安装以下依赖:\n"
            msg += "pip install pandas openpyxl\n\n"
            msg += "注意:\n"
            msg += "- openpyxl: 用于处理.xlsx文件\n"
            msg += "- xlrd (可选): 用于处理.xls文件"
            QMessageBox.warning(self, "警告", msg)
            return

        # 首先检查是否选择了班级和课程
        class_id = self.class_combo.currentData()
        course_id = self.course_combo.currentData()

        if not class_id:
            QMessageBox.warning(self, "提示", "请先选择班级")
            return

        if not course_id:
            QMessageBox.warning(self, "提示", "请先选择课程")
            return

        # 选择Excel文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择成绩Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls)"
        )

        if not file_path:
            return  # 用户取消了选择

        try:
            # 读取Excel文件
            try:
                # 检查文件扩展名并相应处理
                if file_path.lower().endswith('.xlsx'):
                    if not OPENPYXL_AVAILABLE:
                        QMessageBox.critical(self, "错误",
                                             "缺少openpyxl库，无法处理.xlsx文件\n请运行: pip install openpyxl")
                        return
                    df = pd.read_excel(file_path, engine='openpyxl')
                elif file_path.lower().endswith('.xls'):
                    if not XLRD_AVAILABLE:
                        QMessageBox.critical(self, "错误", "缺少xlrd库，无法处理.xls文件\n请运行: pip install xlrd")
                        return
                    df = pd.read_excel(file_path, engine='xlrd')
                else:
                    QMessageBox.critical(self, "错误", "不支持的文件格式，请选择.xlsx或.xls文件")
                    return
            except Exception as e:
                QMessageBox.critical(self, "错误",
                                     f"读取Excel文件失败: {str(e)}\n\n请确保文件格式正确且未被其他程序占用")
                return

            # 验证Excel格式
            required_columns = ['学号', '姓名', '平时成绩', '期末成绩', '学分']
            if not all(col in df.columns for col in required_columns):
                QMessageBox.critical(self, "错误", f"Excel文件格式不正确，必须包含以下列: {', '.join(required_columns)}")
                return

            # 获取专业ID（从课程或班级关联中获取）
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT cm.major_id
                           FROM class_majors cm
                           WHERE cm.class_id = ?
                           """, (class_id,))
            result = cursor.fetchone()
            major_id = result[0] if result else None

            if not major_id:
                QMessageBox.warning(self, "提示", "请先设置班级与专业的关联关系")
                return

            # 处理数据并插入数据库
            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    student_id = str(row['学号']).strip()
                    if not student_id:
                        continue  # 跳过空行

                    regular_score = float(row['平时成绩']) if pd.notna(row['平时成绩']) else None
                    final_score = float(row['期末成绩']) if pd.notna(row['期末成绩']) else None
                    credits = float(row['学分']) if pd.notna(row['学分']) else None

                    # 计算总成绩（平时50% + 期末50%）
                    total_score = None
                    if regular_score is not None and final_score is not None:
                        total_score = regular_score * 0.5 + final_score * 0.5

                    # 检查学生是否存在
                    cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
                    if not cursor.fetchone():
                        errors.append(f"第{index + 2}行: 学生 {student_id} 不存在")
                        error_count += 1
                        continue

                    # 检查成绩是否已存在，如果存在则更新
                    cursor.execute("""
                                   SELECT score_id
                                   FROM scores
                                   WHERE student_id = ?
                                     AND course_id = ?
                                   """, (student_id, course_id))

                    existing_score = cursor.fetchone()
                    if existing_score:
                        # 更新现有成绩
                        cursor.execute("""
                                       UPDATE scores
                                       SET regular_score = ?,
                                           final_score   = ?,
                                           total_score   = ?,
                                           credits       = ?,
                                           major_id      = ?
                                       WHERE student_id = ?
                                         AND course_id = ?
                                       """, (regular_score, final_score, total_score, credits, major_id,
                                             student_id, course_id))
                    else:
                        # 插入新成绩
                        cursor.execute("""
                                       INSERT INTO scores
                                       (student_id, major_id, course_id, regular_score, final_score, total_score,
                                        credits)
                                       VALUES (?, ?, ?, ?, ?, ?, ?)
                                       """, (student_id, major_id, course_id, regular_score, final_score, total_score,
                                             credits))

                    success_count += 1

                except ValueError as ve:
                    errors.append(f"第{index + 2}行: 数据格式错误 - {str(ve)}")
                    error_count += 1
                except Exception as e:
                    errors.append(f"第{index + 2}行: 处理错误 - {str(e)}")
                    error_count += 1

            self.db_conn.commit()
            self.load_scores()  # 刷新表格

            # 显示结果
            result_msg = f"导入完成！\n成功: {success_count} 条\n失败: {error_count} 条"
            if errors:
                result_msg += "\n\n错误详情:\n" + "\n".join(errors[:10])  # 只显示前10个错误
                if len(errors) > 10:
                    result_msg += f"\n... 还有 {len(errors) - 10} 个错误"

            QMessageBox.information(self, "导入结果", result_msg)
            self.logger.info(f"从Excel导入 {success_count} 条成绩记录，{error_count} 条失败")

        except Exception as e:
            self.db_conn.rollback()
            self.logger.error(f"导入Excel成绩错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"导入Excel成绩失败: {str(e)}")

    def add_score(self):
        """添加成绩"""
        dialog = ScoreEditDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                                   INSERT INTO scores
                                   (student_id, major_id, course_id, regular_score, final_score, total_score, credits)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)
                                   """, (
                                       data['student_id'], data['major_id'], data['course_id'],
                                       data['regular_score'], data['final_score'], data['total_score'], data['credits']
                                   ))
                    self.db_conn.commit()
                    self.load_scores()
                    self.logger.info(f"添加成绩: {data['student_id']}")
                    QMessageBox.information(self, "成功", "成绩添加成功")
                except Exception as e:
                    self.logger.error(f"添加成绩错误: {str(e)}")
                    QMessageBox.critical(self, "错误", f"添加成绩失败: {str(e)}")
            else:
                QMessageBox.warning(self, "输入错误", "请填写完整且有效的成绩信息")

    def edit_score(self):
        """编辑成绩"""
        selected = self.score_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的成绩记录")
            return

        row = selected[0].row()
        student_id = self.score_table.item(row, 0).text()
        course_name = self.score_table.item(row, 3).text()

        # 获取课程ID
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT course_id FROM courses WHERE course_name = ?", (course_name,))
            result = cursor.fetchone()
            if result:
                course_id = result[0]
            else:
                QMessageBox.critical(self, "错误", "无法获取课程ID")
                return
        except Exception as e:
            self.logger.error(f"获取课程ID错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"获取课程ID失败: {str(e)}")
            return

        dialog = ScoreEditDialog(self.db_conn, student_id, course_id)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                                   UPDATE scores
                                   SET regular_score = ?,
                                       final_score   = ?,
                                       total_score   = ?,
                                       credits       = ?
                                   WHERE student_id = ?
                                     AND course_id = ?
                                   """, (
                                       data['regular_score'], data['final_score'], data['total_score'],
                                       data['credits'], data['student_id'], data['course_id']
                                   ))
                    self.db_conn.commit()
                    self.load_scores()
                    self.logger.info(f"更新成绩: {data['student_id']}")
                    QMessageBox.information(self, "成功", "成绩更新成功")
                except Exception as e:
                    self.logger.error(f"更新成绩错误: {str(e)}")
                    QMessageBox.critical(self, "错误", f"更新成绩失败: {str(e)}")
            else:
                QMessageBox.warning(self, "输入错误", "请填写完整且有效的成绩信息")

    def delete_score(self):
        """删除成绩"""
        selected = self.score_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的成绩记录")
            return

        row = selected[0].row()
        student_id = self.score_table.item(row, 0).text()
        course_name = self.score_table.item(row, 3).text()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {student_id} 的 {course_name} 成绩吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM scores WHERE student_id = ? AND course_id = ?",
                               (student_id, course_name))
                self.db_conn.commit()
                self.load_scores()
                self.logger.info(f"删除成绩: {student_id}")
                QMessageBox.information(self, "成功", "成绩删除成功")
            except Exception as e:
                self.logger.error(f"删除成绩错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除成绩失败: {str(e)}")

    def load_major_courses(self):
        """加载专业课程关联数据"""
        try:
            self._loading = True
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT m.major_id, m.major_name, c.course_id, c.course_name
                           FROM major_courses mc
                                    JOIN majors m ON mc.major_id = m.major_id
                                    JOIN courses c ON mc.course_id = c.course_id
                           ORDER BY m.major_name, c.course_name
                           """)
            major_courses = cursor.fetchall()

            self.major_course_table.setRowCount(len(major_courses))
            for row, mc in enumerate(major_courses):
                for col in range(4):
                    item = QTableWidgetItem(str(mc[col]))
                    self.major_course_table.setItem(row, col, item)
        except Exception as e:
            self.logger.error(f"加载专业课程关联错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载专业课程关联失败: {str(e)}")
        finally:
            self._loading = False

    def add_major_course(self):
        """添加专业课程关联"""
        dialog = MajorCourseEditDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                                   INSERT INTO major_courses (major_id, course_id)
                                   VALUES (?, ?)
                                   """, (data['major_id'], data['course_id']))
                    self.db_conn.commit()
                    self.load_major_courses()
                    self.logger.info(f"添加专业课程关联: {data['major_id']} - {data['course_id']}")
                    QMessageBox.information(self, "成功", "专业课程关联添加成功")
                except Exception as e:
                    self.logger.error(f"添加专业课程关联错误: {str(e)}")
                    QMessageBox.critical(self, "错误", f"添加专业课程关联失败: {str(e)}")
            else:
                QMessageBox.warning(self, "输入错误", "请选择专业和课程")

    def delete_major_course(self):
        """删除专业课程关联"""
        selected = self.major_course_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的专业课程关联")
            return

        row = selected[0].row()
        major_id = self.major_course_table.item(row, 0).text()
        course_id = self.major_course_table.item(row, 2).text()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除专业ID {major_id} 与课程ID {course_id} 的关联吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM major_courses WHERE major_id = ? AND course_id = ?",
                               (major_id, course_id))
                self.db_conn.commit()
                self.load_major_courses()
                self.logger.info(f"删除专业课程关联: {major_id} - {course_id}")
                QMessageBox.information(self, "成功", "专业课程关联删除成功")
            except Exception as e:
                self.logger.error(f"删除专业课程关联错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除专业课程关联失败: {str(e)}")

    def load_class_majors(self):
        """加载班级专业关联数据"""
        try:
            self._loading = True
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT cl.class_id, cl.class_name, m.major_id, m.major_name
                           FROM class_majors cm
                                    JOIN classes cl ON cm.class_id = cl.class_id
                                    JOIN majors m ON cm.major_id = m.major_id
                           ORDER BY cl.class_name, m.major_name
                           """)
            class_majors = cursor.fetchall()

            self.class_major_table.setRowCount(len(class_majors))
            for row, cm in enumerate(class_majors):
                for col in range(4):
                    item = QTableWidgetItem(str(cm[col]))
                    self.class_major_table.setItem(row, col, item)
        except Exception as e:
            self.logger.error(f"加载班级专业关联错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载班级专业关联失败: {str(e)}")
        finally:
            self._loading = False

    def add_class_major(self):
        """添加班级专业关联"""
        dialog = ClassMajorEditDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                                   INSERT INTO class_majors (class_id, major_id)
                                   VALUES (?, ?)
                                   """, (data['class_id'], data['major_id']))
                    self.db_conn.commit()
                    self.load_class_majors()
                    self.logger.info(f"添加班级专业关联: {data['class_id']} - {data['major_id']}")
                    QMessageBox.information(self, "成功", "班级专业关联添加成功")
                except Exception as e:
                    self.logger.error(f"添加班级专业关联错误: {str(e)}")
                    QMessageBox.critical(self, "错误", f"添加班级专业关联失败: {str(e)}")
            else:
                QMessageBox.warning(self, "输入错误", "请选择班级和专业")

    def delete_class_major(self):
        """删除班级专业关联"""
        selected = self.class_major_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的班级专业关联")
            return

        row = selected[0].row()
        class_id = self.class_major_table.item(row, 0).text()
        major_id = self.class_major_table.item(row, 2).text()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除班级ID {class_id} 与专业ID {major_id} 的关联吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM class_majors WHERE class_id = ? AND major_id = ?",
                               (class_id, major_id))
                self.db_conn.commit()
                self.load_class_majors()
                self.logger.info(f"删除班级专业关联: {class_id} - {major_id}")
                QMessageBox.information(self, "成功", "班级专业关联删除成功")
            except Exception as e:
                self.logger.error(f"删除班级专业关联错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除班级专业关联失败: {str(e)}")


class ScoreEditDialog(QDialog):
    """成绩编辑对话框"""

    def __init__(self, db_conn, student_id=None, course_id=None):
        super().__init__()
        self.db_conn = db_conn
        self.student_id = student_id
        self.course_id = course_id

        self.setWindowTitle("编辑成绩" if student_id else "添加成绩")
        self.resize(400, 300)
        self.init_ui()
        if student_id and course_id:
            self.load_existing_data()

    def init_ui(self):
        layout = QFormLayout()

        # 学生选择
        self.student_combo = QComboBox()
        self.load_students()
        layout.addRow("学生:", self.student_combo)

        # 专业选择
        self.major_combo = QComboBox()
        self.load_majors()
        layout.addRow("专业:", self.major_combo)

        # 课程选择
        self.course_combo = QComboBox()
        self.load_courses()
        layout.addRow("课程:", self.course_combo)

        # 平时成绩
        self.regular_score_input = QLineEdit()
        self.regular_score_input.setPlaceholderText("0-100")
        layout.addRow("平时成绩:", self.regular_score_input)

        # 期末成绩
        self.final_score_input = QLineEdit()
        self.final_score_input.setPlaceholderText("0-100")
        layout.addRow("期末成绩:", self.final_score_input)

        # 学分
        self.credits_input = QLineEdit()
        self.credits_input.setPlaceholderText("如: 3.0")
        layout.addRow("学分:", self.credits_input)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_students(self):
        """加载学生列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT student_id, name FROM students ORDER BY student_id")
            students = cursor.fetchall()
            for student_id, name in students:
                self.student_combo.addItem(f"{student_id} - {name}", student_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载学生列表失败: {str(e)}")

    def load_majors(self):
        """加载专业列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT major_id, major_name FROM majors ORDER BY major_name")
            majors = cursor.fetchall()
            for major_id, major_name in majors:
                self.major_combo.addItem(major_name, major_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载专业列表失败: {str(e)}")

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

    def load_existing_data(self):
        """加载现有成绩数据"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT s.student_id,
                                  m.major_id,
                                  c.course_id,
                                  sc.regular_score,
                                  sc.final_score,
                                  sc.credits
                           FROM scores sc
                                    JOIN students s ON sc.student_id = s.student_id
                                    JOIN majors m ON sc.major_id = m.major_id
                                    JOIN courses c ON sc.course_id = c.course_id
                           WHERE s.student_id = ?
                             AND c.course_id = ?
                           """, (self.student_id, self.course_id))
            result = cursor.fetchone()

            if result:
                student_id, major_id, course_id, regular_score, final_score, credits = result
                # 设置学生选择
                for i in range(self.student_combo.count()):
                    if self.student_combo.itemData(i) == student_id:
                        self.student_combo.setCurrentIndex(i)
                        break
                # 设置专业选择
                for i in range(self.major_combo.count()):
                    if self.major_combo.itemData(i) == major_id:
                        self.major_combo.setCurrentIndex(i)
                        break
                # 设置课程选择
                for i in range(self.course_combo.count()):
                    if self.course_combo.itemData(i) == course_id:
                        self.course_combo.setCurrentIndex(i)
                        break
                # 设置成绩
                self.regular_score_input.setText(str(regular_score) if regular_score else "")
                self.final_score_input.setText(str(final_score) if final_score else "")
                self.credits_input.setText(str(credits) if credits else "")
        except Exception as e:
            self.logger.error(f"加载现有成绩数据错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载现有成绩数据失败: {str(e)}")

    def get_data(self):
        """获取表单数据"""
        try:
            student_id = self.student_combo.currentData()
            major_id = self.major_combo.currentData()
            course_id = self.course_combo.currentData()

            regular_score = float(
                self.regular_score_input.text().strip()) if self.regular_score_input.text().strip() else None
            final_score = float(
                self.final_score_input.text().strip()) if self.final_score_input.text().strip() else None
            credits = float(self.credits_input.text().strip()) if self.credits_input.text().strip() else None

            # 计算总成绩
            total_score = None
            if regular_score is not None and final_score is not None:
                total_score = regular_score * 0.5 + final_score * 0.5  # 平时50%，期末50%

            return {
                'student_id': student_id,
                'major_id': major_id,
                'course_id': course_id,
                'regular_score': regular_score,
                'final_score': final_score,
                'total_score': total_score,
                'credits': credits
            }
        except ValueError:
            return None


class MajorCourseEditDialog(QDialog):
    """专业课程关联编辑对话框"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn

        self.setWindowTitle("添加专业课程关联")
        self.resize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # 专业选择
        self.major_combo = QComboBox()
        self.load_majors()
        layout.addRow("专业:", self.major_combo)

        # 课程选择
        self.course_combo = QComboBox()
        self.load_courses()
        layout.addRow("课程:", self.course_combo)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_majors(self):
        """加载专业列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT major_id, major_name FROM majors ORDER BY major_name")
            majors = cursor.fetchall()
            for major_id, major_name in majors:
                self.major_combo.addItem(major_name, major_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载专业列表失败: {str(e)}")

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
        major_id = self.major_combo.currentData()
        course_id = self.course_combo.currentData()
        if major_id and course_id:
            return {
                'major_id': major_id,
                'course_id': course_id
            }
        return None


class ClassMajorEditDialog(QDialog):
    """班级专业关联编辑对话框"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn

        self.setWindowTitle("添加班级专业关联")
        self.resize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # 班级选择
        self.class_combo = QComboBox()
        self.load_classes()
        layout.addRow("班级:", self.class_combo)

        # 专业选择
        self.major_combo = QComboBox()
        self.load_majors()
        layout.addRow("专业:", self.major_combo)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def load_classes(self):
        """加载班级列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_id, class_name FROM classes ORDER BY class_name")
            classes = cursor.fetchall()
            for class_id, class_name in classes:
                self.class_combo.addItem(class_name, class_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载班级列表失败: {str(e)}")

    def load_majors(self):
        """加载专业列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT major_id, major_name FROM majors ORDER BY major_name")
            majors = cursor.fetchall()
            for major_id, major_name in majors:
                self.major_combo.addItem(major_name, major_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载专业列表失败: {str(e)}")

    def get_data(self):
        """获取表单数据"""
        class_id = self.class_combo.currentData()
        major_id = self.major_combo.currentData()
        if class_id and major_id:
            return {
                'class_id': class_id,
                'major_id': major_id
            }
        return None



