from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QLabel, QMessageBox, QHeaderView, QInputDialog, QDialog, QFormLayout, QDateEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDate
import logging


class StudentManagementWindow(QWidget):
    """学生管理窗口"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("学生管理")
        self.resize(800, 600)
        self.init_ui()
        self.load_students()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 搜索和过滤区域
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索学生姓名或学号...")
        self.search_input.textChanged.connect(self.load_students)

        self.class_filter = QComboBox()
        self.class_filter.addItem("所有班级", None)
        self.load_classes()
        self.class_filter.currentIndexChanged.connect(self.load_students)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.class_filter)
        layout.addLayout(search_layout)

        # 操作按钮区域
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("添加学生")
        add_btn.clicked.connect(self.add_student)

        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_student)

        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_student)

        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_students)

        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_students)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

        # 学生表格
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(6)
        self.student_table.setHorizontalHeaderLabels([
            "学号", "姓名", "性别", "班级", "入学日期", "联系方式"
        ])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.student_table)

        self.setLayout(layout)

    def add_student(self):
        """添加学生"""
        dialog = StudentEditDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()

            if not data['student_id']:
                QMessageBox.warning(self, "提示", "学号不能为空")
                return

            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                               INSERT INTO students
                               (student_id, name, gender, birth_date, class_id, admission_date, contact)
                               VALUES (?, ?, ?, ?, ?, ?, ?)
                               """, (
                                   data['student_id'], data['name'], data['gender'],
                                   data['birth_date'], data['class_id'], data['admission_date'],
                                   data['contact']
                               ))
                self.db_conn.commit()
                self.load_students()
                self.logger.info(f"添加学生: {data['student_id']}")
            except Exception as e:
                self.logger.error(f"添加学生错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加学生失败: {str(e)}")

    def edit_student(self):
        """编辑学生信息"""
        selected = self.student_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的学生")
            return

        student_id = self.student_table.item(selected[0].row(), 0).text()

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                           SELECT student_id, name, gender, birth_date, class_id, admission_date, contact
                           FROM students
                           WHERE student_id = ?
                           """, (student_id,))
            student_data = cursor.fetchone()

            if student_data:
                data_dict = {
                    'student_id': student_data[0],
                    'name': student_data[1],
                    'gender': student_data[2],
                    'birth_date': student_data[3],
                    'class_id': student_data[4],
                    'admission_date': student_data[5],
                    'contact': student_data[6]
                }

                dialog = StudentEditDialog(self.db_conn, data_dict)
                if dialog.exec_() == QDialog.Accepted:
                    new_data = dialog.get_data()

                    cursor.execute("""
                                   UPDATE students
                                   SET name           = ?,
                                       gender         = ?,
                                       birth_date     = ?,
                                       class_id       = ?,
                                       admission_date = ?,
                                       contact        = ?
                                   WHERE student_id = ?
                                   """, (
                                       new_data['name'], new_data['gender'], new_data['birth_date'],
                                       new_data['class_id'], new_data['admission_date'], new_data['contact'],
                                       student_id
                                   ))
                    self.db_conn.commit()
                    self.load_students()
                    self.logger.info(f"更新学生: {student_id}")
        except Exception as e:
            self.logger.error(f"编辑学生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"编辑学生失败: {str(e)}")

    def load_classes(self):
        """加载班级列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_id, class_name FROM classes ORDER BY class_name")
            classes = cursor.fetchall()

            for class_id, class_name in classes:
                self.class_filter.addItem(class_name, class_id)
        except Exception as e:
            self.logger.error(f"加载班级列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载班级列表失败: {str(e)}")

    def load_students(self):
        """加载学生列表"""
        search_text = self.search_input.text().strip()
        class_id = self.class_filter.currentData()

        try:
            cursor = self.db_conn.cursor()

            query = """
                    SELECT s.student_id, \
                           s.name, \
                           s.gender,
                           c.class_name, \
                           s.admission_date, \
                           s.contact
                    FROM students s
                             LEFT JOIN classes c ON s.class_id = c.class_id
                    WHERE 1 = 1 \
                    """
            params = []

            if search_text:
                query += " AND (s.name LIKE ? OR s.student_id LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%"])

            if class_id:
                query += " AND s.class_id = ?"
                params.append(class_id)

            query += " ORDER BY s.student_id"

            cursor.execute(query, params)
            students = cursor.fetchall()

            self.student_table.setRowCount(len(students))
            for row, student in enumerate(students):
                for col in range(6):
                    self.student_table.setItem(row, col, QTableWidgetItem(str(student[col] or "")))
        except Exception as e:
            self.logger.error(f"加载学生列表错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载学生列表失败: {str(e)}")

    def add_student(self):
        """添加学生"""
        # 这里应该弹出一个对话框收集学生信息
        # 简化示例，使用输入对话框
        student_id, ok = QInputDialog.getText(
            self, "添加学生", "请输入学号:"
        )

        if ok and student_id:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "INSERT INTO students (student_id, name) VALUES (?, ?)",
                    (student_id, "新学生")
                )
                self.db_conn.commit()
                self.load_students()
                self.logger.info(f"添加学生: {student_id}")
            except Exception as e:
                self.logger.error(f"添加学生错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加学生失败: {str(e)}")

    def edit_student(self):
        """编辑学生信息"""
        selected = self.student_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的学生")
            return

        student_id = self.student_table.item(selected[0].row(), 0).text()
        QMessageBox.information(self, "提示", f"编辑学生 {student_id} 功能开发中")

    def delete_student(self):
        """删除学生"""
        selected = self.student_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的学生")
            return

        student_id = self.student_table.item(selected[0].row(), 0).text()
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除学生 {student_id} 吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(
                    "DELETE FROM students WHERE student_id = ?",
                    (student_id,)
                )
                self.db_conn.commit()
                self.load_students()
                self.logger.info(f"删除学生: {student_id}")
            except Exception as e:
                self.logger.error(f"删除学生错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除学生失败: {str(e)}")

    def import_students(self):
        """导入学生数据"""
        QMessageBox.information(self, "提示", "导入学生功能开发中")

    def export_students(self):
        """导出学生数据"""
        QMessageBox.information(self, "提示", "导出学生功能开发中")


class StudentEditDialog(QDialog):
    """学生信息编辑对话框"""

    def __init__(self, db_conn, student_data=None):
        super().__init__()
        self.db_conn = db_conn
        self.student_data = student_data
        self.setWindowTitle("编辑学生信息" if student_data else "添加学生")
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # 学号
        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("请输入学号")
        layout.addRow("学号:", self.student_id_input)

        # 姓名
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入姓名")
        layout.addRow("姓名:", self.name_input)

        # 性别
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女", "其他"])
        layout.addRow("性别:", self.gender_combo)

        # 出生日期
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate(2000, 1, 1))
        layout.addRow("出生日期:", self.birth_date_edit)

        # 班级选择
        self.class_combo = QComboBox()
        self.load_classes()
        layout.addRow("班级:", self.class_combo)

        # 入学日期
        self.admission_date_edit = QDateEdit()
        self.admission_date_edit.setCalendarPopup(True)
        self.admission_date_edit.setDate(QDate.currentDate())
        layout.addRow("入学日期:", self.admission_date_edit)

        # 联系方式
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("请输入联系方式")
        layout.addRow("联系方式:", self.contact_input)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

        # 如果是编辑模式，填充数据
        if self.student_data:
            self.fill_data()

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

    def fill_data(self):
        """填充学生数据"""
        if self.student_data:
            self.student_id_input.setText(self.student_data.get('student_id', ''))
            self.name_input.setText(self.student_data.get('name', ''))

            # 设置性别
            gender = self.student_data.get('gender', '')
            if gender:
                index = self.gender_combo.findText(gender)
                if index >= 0:
                    self.gender_combo.setCurrentIndex(index)

            # 设置出生日期
            birth_date = self.student_data.get('birth_date')
            if birth_date:
                try:
                    date = QDate.fromString(birth_date, 'yyyy-MM-dd')
                    self.birth_date_edit.setDate(date)
                except:
                    pass

            # 设置班级
            class_id = self.student_data.get('class_id')
            if class_id:
                for i in range(self.class_combo.count()):
                    if self.class_combo.itemData(i) == class_id:
                        self.class_combo.setCurrentIndex(i)
                        break

            # 设置入学日期
            admission_date = self.student_data.get('admission_date')
            if admission_date:
                try:
                    date = QDate.fromString(admission_date, 'yyyy-MM-dd')
                    self.admission_date_edit.setDate(date)
                except:
                    pass

            self.contact_input.setText(self.student_data.get('contact', ''))

    def get_data(self):
        """获取表单数据"""
        return {
            'student_id': self.student_id_input.text().strip(),
            'name': self.name_input.text().strip(),
            'gender': self.gender_combo.currentText(),
            'birth_date': self.birth_date_edit.date().toString('yyyy-MM-dd'),
            'class_id': self.class_combo.currentData(),
            'admission_date': self.admission_date_edit.date().toString('yyyy-MM-dd'),
            'contact': self.contact_input.text().strip()
        }