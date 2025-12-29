import logging
import threading
import time

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QLabel, QStatusBar, QMenuBar, QMenu, QAction,
    QMessageBox, QFrame, QHBoxLayout, QToolButton, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from gui.course_class_mgmt import CourseClassManagementDialog
from numpy.ma.bench import timer


class MainWindow(QMainWindow):
    """主窗口"""
    logout_requested = pyqtSignal()  # 退出登录信号

    def __init__(self, db_conn, user_id, user_role):
        super().__init__()
        self.db_conn = db_conn
        self.user_id = user_id
        self.user_role = user_role
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle(f"槐序 - HuaiXu - {self.get_role_display(user_role)}")
        self.resize(1440, 900)

        self.select_user()

        self.init_ui()

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
                background: #f0f0f0; color: black; 
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

        self.create_menubar()
        self.create_toolbar()
        self.create_central_tabs()
        self.create_statusbar()

    def show_course_class_management(self):
        try:
            self.course_class_dialog = CourseClassManagementDialog(self.db_conn)
            self.course_class_dialog.exec_()
        except Exception as e:
            self.logger.error(f"打开课程与班级关联管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开课程与班级关联管理: {str(e)}")

    def create_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("📁 文件")

        logout_action = QAction("🚪 退出登录", self)
        logout_action.triggered.connect(self.logout)  # 绑定退出登录
        logout_action.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogCloseButton')))
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ 退出系统", self)
        exit_action.triggered.connect(self.close)
        exit_action.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogCancelButton')))
        file_menu.addAction(exit_action)

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

            course_class_action = QAction("📚 班级关联课程", self)
            course_class_action.triggered.connect(self.show_course_class_management)
            manage_menu.addAction(course_class_action)

        report_menu = menubar.addMenu("📈 报表")

        stats_action = QAction("📋 成绩统计", self)
        stats_action.triggered.connect(self.show_statistics)
        report_menu.addAction(stats_action)

        export_action = QAction("💾 导出数据", self)
        export_action.triggered.connect(self.export_data)
        report_menu.addAction(export_action)

    def create_toolbar(self):
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
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")

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

        self.setCentralWidget(self.tab_widget)

        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)

        welcome_label = QLabel("🏠 欢迎使用槐序 - HuaiXu")
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

        # 添加按钮框
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f0f8ff, stop:1 #e6f3ff);
                border: 2px solid #b0d4f1;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        button_layout = QGridLayout(button_frame)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(20, 20, 20, 20)

        # 创建按钮
        buttons = [
            ("📅 日程安排", self.show_calendar),
            ("📝 点我", self.show_notes),
            ("📊 数据分析", self.show_data_analysis),
            ("⚙️ 系统设置", self.show_settings),
            ("📞 联系我们", self.show_contact),
            ("🌐 网站链接", self.show_links),
            ("🔍 搜索功能", self.show_search),
        ]

        # 布局按钮 (4列2行)
        for i, (text, func) in enumerate(buttons):
            row = i // 4
            col = i % 4
            btn = QToolButton()
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setMinimumSize(120, 80)
            btn.setMaximumSize(150, 100)
            btn.setStyleSheet("""
                QToolButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f0f0f0);
                    border: 1px solid #b0d4f1;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 12px;
                    color: #333;
                }
                QToolButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #e3f2fd, stop:1 #bbdefb);
                    border: 1px solid #90caf9;
                }
                QToolButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #bbdefb, stop:1 #90caf9);
                }
            """)
            btn.clicked.connect(func)
            button_layout.addWidget(btn, row, col)

        welcome_layout.addStretch()
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(subtitle_label)
        welcome_layout.addWidget(button_frame)  # 添加按钮框
        welcome_layout.addStretch()

        self.tab_widget.addTab(welcome_widget, "首页")

    def create_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            f"✅ 欢迎使用槐序 - HuaiXu | 当前用户: {self.get_role_display(self.user_role)} | 角色: {self.user_role}")

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
        from gui.student_mgmt import StudentManagementWindow
        try:
            self.student_window = StudentManagementWindow(self.db_conn)
            self.student_window.show()
        except Exception as e:
            self.logger.error(f"打开学生管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开学生管理: {str(e)}")

    def show_grade_management(self):
        from gui.grade_mgmt import GradeManagementWindow
        try:
            self.grade_window = GradeManagementWindow(self.db_conn)
            self.grade_window.show()
        except Exception as e:
            self.logger.error(f"打开成绩管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开成绩管理: {str(e)}")

    def show_assignment_management(self):
        from gui.assignment_mgmt import AssignmentManagementWindow
        try:
            self.assignment_window = AssignmentManagementWindow(self.db_conn)
            self.assignment_window.show()
        except Exception as e:
            self.logger.error(f"打开作业管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开作业管理: {str(e)}")

    def show_statistics(self):
        QMessageBox.information(self, "提示", "📊 统计报表功能开发中...",
                                QMessageBox.Ok, QMessageBox.Ok)

    def export_data(self):
        QMessageBox.information(self, "提示", "💾 数据导出功能开发中...",
                                QMessageBox.Ok, QMessageBox.Ok)

    def logout(self):
        logging.info("用户点击退出登录，发送退出信号")
        self.logout_requested.emit()  # 发送退出登录信号

    def closeEvent(self, event):
        self.logger.info("主窗口关闭")
        # self.logout_requested.disconnect()  # 断开信号避免野指针
        # ？不是为什么我断开个信号会导致堆栈溢出
        super().closeEvent(event)

    def show_settings(self):
        from gui.settings_window import SettingsWindow
        try:
            self.settings_window = SettingsWindow(self.db_conn)
            self.settings_window.show()
        except Exception as e:
            self.logger.error(f"打开系统设置错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开系统设置: {str(e)}")

    def show_reports(self):
        from gui.report_gen import ReportGenerationWindow
        try:
            self.report_window = ReportGenerationWindow(self.db_conn)
            self.report_window.show()
        except Exception as e:
            self.logger.error(f"打开报表生成错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开报表生成: {str(e)}")

    def show_classroom_management(self):
        from gui.classroom_mgmt import ClassroomManagementWindow
        try:
            self.classroom_window = ClassroomManagementWindow(self.db_conn)
            self.classroom_window.show()
        except Exception as e:
            self.logger.error(f"打开课堂管理窗口错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开课堂管理: {str(e)}")

    def select_user(self):
        """每15秒检查用户状态的线程函数"""

        def user_check_loop():
            while getattr(self, '_running', True):  # 使用标志控制循环
                logging.info("当前用户为：%s", self.get_role_display(self.user_role))
                logging.info("当前用户ID为：%s", self.user_id)
                logging.info("运行正常，显示为主窗口")
                time.sleep(15)  # 每15秒检查一次

        # 创建并启动线程
        self.user_check_thread = threading.Thread(target=user_check_loop, daemon=True)
        self._running = True  # 设置运行标志
        self.user_check_thread.start()

    def show_calendar(self):
        msg = QMessageBox()
        msg.setWindowTitle("日程安排")
        msg.setText("📅 日程安排功能开发中...")
        msg.setFont(QFont("Microsoft YaHei", 14))
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        msg.exec_()

    def show_notes(self):
        msg = QMessageBox()
        msg.setWindowTitle("点我")
        msg.setText("📝 这我不知道写什么..........")
        msg.setFont(QFont("Microsoft YaHei", 14))
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        msg.exec_()

    def show_data_analysis(self):
        msg = QMessageBox()
        msg.setWindowTitle("数据分析")
        msg.setText("📊 数据分析功能开发中...")
        msg.setFont(QFont("Microsoft YaHei", 14))
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        msg.exec_()

    def show_contact(self):
        msg = QMessageBox()
        msg.setWindowTitle("联系我们")
        msg.setText("📞 联系我们功能开发中...")
        msg.setFont(QFont("Microsoft YaHei", 14))
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        msg.exec_()

    def show_links(self):
        msg = QMessageBox()
        msg.setWindowTitle("网站链接")
        msg.setText("🌐 网站链接功能开发中...")
        msg.setFont(QFont("Microsoft YaHei", 14))
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        msg.exec_()

    def show_search(self):
        msg = QMessageBox()
        msg.setWindowTitle("搜索功能")
        msg.setText("🔍 搜索功能开发中...")
        msg.setFont(QFont("Microsoft YaHei", 14))
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        msg.exec_()




