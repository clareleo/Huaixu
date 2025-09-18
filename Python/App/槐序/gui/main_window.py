from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QLabel, QStatusBar, QMenuBar, QMenu, QAction,
    QMessageBox, QFrame, QHBoxLayout, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor


class MainWindow(QMainWindow):
    """主窗口"""
    logout_requested = pyqtSignal()

    def __init__(self, db_conn, user_id, user_role):
        super().__init__()
        self.db_conn = db_conn
        self.user_id = user_id
        self.user_role = user_role
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle(f"4+X成绩管理系统 - {self.get_role_display(user_role)}")
        self.resize(1440, 900)

        # 设置窗口图标（如果有图标文件的话）
        # self.setWindowIcon(QIcon('icons/app_icon.png'))

        self.init_ui()
        self.setup_for_role()

    def get_role_display(self, role):
        """获取角色显示名称"""
        role_map = {
            'admin': '管理员',
            'teacher': '教师',
            'student': '学生'
        }
        return role_map.get(role, role)

    def init_ui(self):
        """初始化界面 - 美化版"""
        # 设置主窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #c3cfe2);
            }
            QMenuBar {
                background: white;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                padding: 5px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 5px;
            }
            QMenuBar::item:selected {
                background: #e3f2fd;
            }
            QMenuBar::item:pressed {
                background: #bbdefb;
            }
            QMenu {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background: #e3f2fd;
            }
            QMenu::item:disabled {
                color: #999;
            }
            QStatusBar {
                background: white;
                border: 1px solid #e0e0e0;
                border-top: none;
                padding: 5px 10px;
            }
            QStatusBar::item {
                border: none;
            }
        """)

        # 创建菜单栏
        self.create_menubar()

        # 创建工具栏
        self.create_toolbar()

        # 创建主选项卡
        self.create_central_tabs()

        # 创建状态栏
        self.create_statusbar()

    def setup_for_role(self):
        self.create_menubar()
        self.create_toolbar()
        self.create_central_tabs()
        self.create_statusbar()

    def create_menubar(self):
        """创建菜单栏 - 美化版"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("📁 文件")

        logout_action = QAction("🚪 退出登录", self)
        logout_action.triggered.connect(self.logout)
        logout_action.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogCloseButton')))
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ 退出系统", self)
        exit_action.triggered.connect(self.close)
        exit_action.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogCancelButton')))
        file_menu.addAction(exit_action)

        # 管理菜单 (管理员和教师可见)
        if self.user_role in ['admin', 'teacher']:
            manage_menu = menubar.addMenu("⚙️ 管理")

            student_action = QAction("👥 学生管理", self)
            student_action.triggered.connect(self.show_student_management)
            manage_menu.addAction(student_action)

            grade_action = QAction("📊 成绩管理", self)
            grade_action.triggered.connect(self.show_grade_management)
            manage_menu.addAction(grade_action)

            assignment_action = QAction("📝 作业管理", self)
            assignment_action.triggered.connect(self.show_assignment_management)
            manage_menu.addAction(assignment_action)

            classroom_action = QAction("🏫 课堂管理", self)
            classroom_action.triggered.connect(self.show_classroom_management)
            manage_menu.addAction(classroom_action)

        # 报表菜单
        report_menu = menubar.addMenu("📈 报表")

        stats_action = QAction("📋 成绩统计", self)
        stats_action.triggered.connect(self.show_statistics)
        report_menu.addAction(stats_action)

        export_action = QAction("💾 导出数据", self)
        export_action.triggered.connect(self.export_data)
        report_menu.addAction(export_action)

    def create_toolbar(self):
        """创建工具栏 - 美化版"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background: white;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 8px;
                margin: 2px;
            }
            QToolButton:hover {
                background: #e3f2fd;
                border: 1px solid #bbdefb;
            }
        """)

    def create_central_tabs(self):
        """创建中心选项卡 - 美化版"""
        # 创建主选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")

        # 设置选项卡样式
        self.tab_widget.setStyleSheet("""
            #mainTabWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                margin: 10px;
            }
            #mainTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background: white;
            }
            #mainTabWidget::tab-bar {
                alignment: left;
            }
            #mainTabWidget QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
                font-weight: 500;
            }
            #mainTabWidget QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #2196F3;
                color: #2196F3;
                font-weight: bold;
            }
            #mainTabWidget QTabBar::tab:!selected {
                color: #666;
            }
        """)

        # 设置中心部件
        self.setCentralWidget(self.tab_widget)

        # 添加欢迎标签页（临时）
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)

        welcome_label = QLabel("🏠 欢迎使用4+X成绩管理系统")
        welcome_label.setObjectName("welcomeLabel")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            #welcomeLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 50px;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ebf3fd, stop:1 #ddeef7);
                border-radius: 15px;
                border: 2px solid #b8daff;
            }
        """)

        subtitle_label = QLabel(f"当前用户角色: {self.get_role_display(self.user_role)} | 用户ID: {self.user_id}")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            #subtitleLabel {
                font-size: 14px;
                color: #666;
                margin: 20px;
            }
        """)

        welcome_layout.addStretch()
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(subtitle_label)
        welcome_layout.addStretch()

        self.tab_widget.addTab(welcome_widget, "首页")

    def create_statusbar(self):
        """创建状态栏 - 美化版"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            f"✅ 欢迎使用4+X成绩管理系统 | 当前用户: {self.get_role_display(self.user_role)} | 角色: {self.user_role}",
            5000)

        # 设置状态栏样式
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 1px solid #e0e0e0;
                border-top: none;
                color: #333;
                font-weight: 500;
            }
        """)

    def create_statusbar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            f"✅ 欢迎使用4+X成绩管理系统 | 当前用户: {self.get_role_display(self.user_role)} | 角色: {self.user_role}")

        # 美化状态栏
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: white;
                border: 1px solid #e0e0e0;
                border-top: none;
                color: #333333;
                font-weight: 500;
                padding: 5px 10px;
            }
        """)

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
        QMessageBox.information(self, "提示", "📊 统计报表功能开发中...",
                                QMessageBox.Ok, QMessageBox.Ok)

    def export_data(self):
        """导出数据"""
        QMessageBox.information(self, "提示", "💾 数据导出功能开发中...",
                                QMessageBox.Ok, QMessageBox.Ok)

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

    def show_classroom_management(self):
        """显示课堂管理界面"""
        from gui.classroom_mgmt import ClassroomManagementWindow
        try:
            self.classroom_window = ClassroomManagementWindow(self.db_conn)
            self.classroom_window.show()
        except Exception as e:
            self.logger.error(f"打开课堂管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开课堂管理: {str(e)}")