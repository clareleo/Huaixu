from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QLabel, QStatusBar, QMenuBar, QMenu, QAction,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging


class MainWindow(QMainWindow):
    """主窗口"""
    logout_requested = pyqtSignal()

    def __init__(self, db_conn, user_id, user_role):
        super().__init__()
        self.db_conn = db_conn
        self.user_id = user_id
        self.user_role = user_role
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("4+X成绩管理系统")
        self.resize(1024, 768)
        self.init_ui()

        # 根据用户角色设置界面
        self.setup_for_role()

    def init_ui(self):
        """初始化界面"""
        # 创建菜单栏
        self.create_menubar()

        # 创建工具栏
        self.create_toolbar()

        # 创建主选项卡
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"欢迎使用4+X成绩管理系统 | 当前用户: {self.user_role}")

    def create_menubar(self):
        """创建菜单栏"""
        menubar = QMenuBar(self)

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        logout_action = QAction("退出登录", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)

        exit_action = QAction("退出系统", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 管理菜单 (管理员和教师可见)
        if self.user_role in ['admin', 'teacher']:
            manage_menu = menubar.addMenu("管理")

            student_action = QAction("学生管理", self)
            student_action.triggered.connect(self.show_student_management)
            manage_menu.addAction(student_action)

            grade_action = QAction("成绩管理", self)
            grade_action.triggered.connect(self.show_grade_management)
            manage_menu.addAction(grade_action)

            assignment_action = QAction("作业管理", self)
            assignment_action.triggered.connect(self.show_assignment_management)
            manage_menu.addAction(assignment_action)

        # 报表菜单
        report_menu = menubar.addMenu("报表")

        stats_action = QAction("成绩统计", self)
        stats_action.triggered.connect(self.show_statistics)
        report_menu.addAction(stats_action)

        export_action = QAction("导出数据", self)
        export_action.triggered.connect(self.export_data)
        report_menu.addAction(export_action)

        self.setMenuBar(menubar)

    def create_toolbar(self):
        """创建工具栏"""
        pass  # 可根据需要添加常用功能按钮

    def setup_for_role(self):
        """根据用户角色设置界面"""
        if self.user_role == 'student':
            # 学生角色隐藏管理功能
            pass
        elif self.user_role == 'teacher':
            # 教师角色特定设置
            pass
        elif self.user_role == 'admin':
            # 管理员角色特定设置
            pass

    def show_student_management(self):
        """显示学生管理界面"""
        from gui.student_mgmt import StudentManagementWindow
        try:
            self.student_window = StudentManagementWindow(self.db_conn)
            self.student_window.show()
        except Exception as e:
            self.logger.error(f"打开学生管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开学生管理: {str(e)}")

    def show_grade_management(self):
        """显示成绩管理界面"""
        from gui.grade_mgmt import GradeManagementWindow
        try:
            self.grade_window = GradeManagementWindow(self.db_conn)
            self.grade_window.show()
        except Exception as e:
            self.logger.error(f"打开成绩管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开成绩管理: {str(e)}")

    def show_assignment_management(self):
        """显示作业管理界面"""
        from gui.assignment_mgmt import AssignmentManagementWindow
        try:
            self.assignment_window = AssignmentManagementWindow(self.db_conn)
            self.assignment_window.show()
        except Exception as e:
            self.logger.error(f"打开作业管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开作业管理: {str(e)}")

    def show_statistics(self):
        """显示统计报表"""
        # 待实现
        QMessageBox.information(self, "提示", "统计报表功能开发中")

    def export_data(self):
        """导出数据"""
        # 待实现
        QMessageBox.information(self, "提示", "数据导出功能开发中")

    def logout(self):
        """退出登录"""
        self.logger.info(f"用户 {self.user_id} 退出登录")
        self.logout_requested.emit()
        self.close()

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.logger.info("主窗口关闭")
        event.accept()

    def show_settings(self):
        """显示系统设置"""
        from gui.settings_window import SettingsWindow
        try:
            self.settings_window = SettingsWindow(self.db_conn)
            self.settings_window.show()
        except Exception as e:
            self.logger.error(f"打开系统设置错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开系统设置: {str(e)}")

    def show_reports(self):
        """显示报表生成"""
        from gui.report_gen import ReportGenerationWindow
        try:
            self.report_window = ReportGenerationWindow(self.db_conn)
            self.report_window.show()
        except Exception as e:
            self.logger.error(f"打开报表生成错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开报表生成: {str(e)}")