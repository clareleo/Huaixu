from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox,
    QHeaderView, QDialog, QComboBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
import logging

class CourseClassManagementDialog(QDialog):
    """课程与班级关联管理对话框"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("课程与班级关联管理")
        self.resize(800, 600)
        self.init_ui()
        self.load_course_class_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # 表格显示课程与班级关联
        self.course_class_table = QTableWidget()
        self.course_class_table.setColumnCount(4)
        self.course_class_table.setHorizontalHeaderLabels(["课程ID", "课程名称", "班级ID", "班级名称"])
        self.course_class_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.course_class_table)

        # 按钮区域
        btn_layout = QHBoxLayout()
        add_association_btn = QPushButton("添加关联")
        add_association_btn.clicked.connect(self.add_association)
        remove_association_btn = QPushButton("删除关联")
        remove_association_btn.clicked.connect(self.remove_association)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(add_association_btn)
        btn_layout.addWidget(remove_association_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_course_class_data(self):
        """加载课程与班级关联数据"""
        try:
            cursor = self.db_conn.cursor()
            # 查询所有课程与班级的关联
            cursor.execute("""
                SELECT c.course_id, c.course_name, cl.class_id, cl.class_name
                FROM courses c
                JOIN course_class cc ON c.course_id = cc.course_id
                JOIN classes cl ON cc.class_id = cl.class_id
                ORDER BY c.course_id, cl.class_id
            """)
            data = cursor.fetchall()
            self.course_class_table.setRowCount(len(data))
            for row, (course_id, course_name, class_id, class_name) in enumerate(data):
                self.course_class_table.setItem(row, 0, QTableWidgetItem(str(course_id)))
                self.course_class_table.setItem(row, 1, QTableWidgetItem(course_name))
                self.course_class_table.setItem(row, 2, QTableWidgetItem(str(class_id)))
                self.course_class_table.setItem(row, 3, QTableWidgetItem(class_name))
        except Exception as e:
            self.logger.error(f"加载课程与班级关联数据错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载课程与班级关联数据失败: {str(e)}")

    def add_association(self):
        """添加课程与班级关联"""
        # 创建一个对话框来选择课程和班级
        dialog = AddAssociationDialog(self.db_conn)
        if dialog.exec_() == QDialog.Accepted:
            course_id = dialog.get_selected_course_id()
            class_id = dialog.get_selected_class_id()
            if course_id and class_id:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("""
                        INSERT OR IGNORE INTO course_class (course_id, class_id)
                        VALUES (?, ?)
                    """, (course_id, class_id))
                    self.db_conn.commit()
                    self.load_course_class_data()  # 刷新表格
                    self.logger.info(f"添加关联: 课程ID {course_id}, 班级ID {class_id}")
                    QMessageBox.information(self, "成功", f"已关联课程ID {course_id} 与 班级ID {class_id}")
                except Exception as e:
                    self.logger.error(f"添加关联错误: {str(e)}")
                    QMessageBox.critical(self, "错误", f"添加关联失败: {str(e)}")

    def remove_association(self):
        """删除选中的课程与班级关联"""
        selected = self.course_class_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的关联")
            return
        # 假设选中的行包含课程ID和班级ID在第0和第2列
        row = selected[0].row()
        course_id_item = self.course_class_table.item(row, 0)
        class_id_item = self.course_class_table.item(row, 2)
        if not course_id_item or not class_id_item:
            QMessageBox.warning(self, "提示", "无法获取选中的关联信息")
            return
        course_id = int(course_id_item.text())
        class_id = int(class_id_item.text())
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除课程ID {course_id} 与 班级ID {class_id} 的关联吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    DELETE FROM course_class
                    WHERE course_id = ? AND class_id = ?
                """, (course_id, class_id))
                self.db_conn.commit()
                self.load_course_class_data()  # 刷新表格
                self.logger.info(f"删除关联: 课程ID {course_id}, 班级ID {class_id}")
                QMessageBox.information(self, "成功", f"已删除课程ID {course_id} 与 班级ID {class_id} 的关联")
            except Exception as e:
                self.logger.error(f"删除关联错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除关联失败: {str(e)}")

class AddAssociationDialog(QDialog):
    """添加课程与班级关联的对话框"""

    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.selected_course_id = None
        self.selected_class_id = None
        self.setWindowTitle("添加课程与班级关联")
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 课程选择
        course_layout = QHBoxLayout()
        course_layout.addWidget(QLabel("课程:"))
        self.course_combo = QComboBox()
        self.load_courses()
        course_layout.addWidget(self.course_combo)
        layout.addLayout(course_layout)

        # 班级选择
        class_layout = QHBoxLayout()
        class_layout.addWidget(QLabel("班级:"))
        self.class_combo = QComboBox()
        self.load_classes()
        class_layout.addWidget(self.class_combo)
        layout.addLayout(class_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.accept_association)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_courses(self):
        """加载课程列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
            courses = cursor.fetchall()
            self.course_combo.addItem("选择课程", None)
            for course_id, course_name in courses:
                self.course_combo.addItem(course_name, course_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载课程列表失败: {str(e)}")

    def load_classes(self):
        """加载班级列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT class_id, class_name FROM classes ORDER BY class_name")
            classes = cursor.fetchall()
            self.class_combo.addItem("选择班级", None)
            for class_id, class_name in classes:
                self.class_combo.addItem(class_name, class_id)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载班级列表失败: {str(e)}")

    def accept_association(self):
        """确认添加关联"""
        self.selected_course_id = self.course_combo.currentData()
        self.selected_class_id = self.class_combo.currentData()
        if not self.selected_course_id:
            QMessageBox.warning(self, "提示", "请选择一个课程！")
            return
        if not self.selected_class_id:
            QMessageBox.warning(self, "提示", "请选择一个班级！")
            return
        self.accept()

    def get_selected_course_id(self):
        return self.selected_course_id

    def get_selected_class_id(self):
        return self.selected_class_id