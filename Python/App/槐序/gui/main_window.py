import logging
import threading
import time

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QLabel, QStatusBar, QMenuBar, QMenu, QAction,
    QMessageBox, QFrame, QHBoxLayout, QToolButton, QGridLayout, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QIcon, QDesktopServices


class MainWindow(QMainWindow):
    """主窗口"""
    logout_requested = pyqtSignal()  # 退出登录信号

    # 样式常量
    MESSAGE_BOX_STYLE = """
        QMessageBox {
            font-family: 'Microsoft YaHei';
            font-size: 14px;
        }
        QLabel {
            font-family: 'Microsoft YaHei';
            font-size: 14px;
        }
    """

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
        """初始化界面 """
        self.create_menubar()
        self.create_toolbar()
        self.create_central_tabs()
        self.create_statusbar()

    def _open_window(self, window_class, window_name, db_conn=None, use_exec=False, **kwargs):
        """
        通用窗口打开方法，统一错误处理

        Args:
            window_class: 窗口类
            window_name: 窗口名称（用于错误提示）
            db_conn: 数据库连接（可选，默认使用 self.db_conn）
            use_exec: 是否使用 exec_() 而不是 show()（用于对话框）
            **kwargs: 传递给窗口类的其他参数
        """
        try:
            if db_conn is None:
                db_conn = self.db_conn
            # 如果有额外参数，一起传递；否则只传递 db_conn
            if kwargs:
                window = window_class(db_conn, **kwargs)
            else:
                window = window_class(db_conn)

            # 根据窗口类型选择显示方式
            if use_exec or hasattr(window, 'exec_'):
                window.exec_()
            else:
                window.show()
            return window
        except Exception as e:
            self.logger.error(f"打开{window_name}窗口错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"无法打开{window_name}: {str(e)}")
            return None

    def show_course_class_management(self):
        """显示课程与班级关联管理窗口"""
        from gui.course_class_mgmt import CourseClassManagementDialog
        self.course_class_dialog = self._open_window(
            CourseClassManagementDialog,
            "课程与班级关联管理",
            use_exec=True
        )

    def create_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("📁 文件")

        logout_action = QAction("🚪 退出登录", self)
        logout_action.triggered.connect(self.logout)
        logout_action.setIcon(self.style().standardIcon(self.style().SP_DialogCloseButton))
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ 退出系统", self)
        exit_action.triggered.connect(self.close)
        exit_action.setIcon(self.style().standardIcon(self.style().SP_DialogCancelButton))
        file_menu.addAction(exit_action)

        if self.user_role in ['admin', 'teacher']:
            manage_menu = menubar.addMenu("⚙️ 管理")

            student_action = QAction("👥 学生管理", self)
            student_action.triggered.connect(self.show_student_management)
            manage_menu.addAction(student_action)

            grade_action = QAction("📊 成绩管理", self)
            grade_action.triggered.connect(self.show_grade_management)
            manage_menu.addAction(grade_action)

            score_4x_action = QAction("📊 4+X成绩管理", self)
            score_4x_action.triggered.connect(self.show_student_score_management)
            manage_menu.addAction(score_4x_action)

            edit_4x_action = QAction("📝 编辑4+X成绩模板", self)
            edit_4x_action.triggered.connect(self.open_score_editor)
            manage_menu.addAction(edit_4x_action)

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

    def show_student_score_management(self):
        """显示4+X成绩管理窗口"""
        from gui.student_score_mgmt import StudentScoreManagementWindow
        self.score_window = self._open_window(
            StudentScoreManagementWindow,
            "4+X成绩管理"
        )

    def open_score_editor(self):
        """打开4+X成绩编辑器"""
        from gui.score_editor_window import ScoreEditorWindow
        try:
            score_editor = ScoreEditorWindow(self.db_conn, self)
            score_editor.show()
        except Exception as e:
            self.logger.error(f"打开4+X成绩编辑器错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"无法打开4+X成绩编辑器: {str(e)}")

    def create_toolbar(self):
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background: rgba(255, 255, 255, 0.85);
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
                background: rgba(227, 242, 253, 0.8);
                border: 1px solid rgba(187, 222, 251, 0.8);
            }
        """)

    def create_central_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")

        self.tab_widget.setStyleSheet("""
            #mainTabWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                margin: 10px;
            }
            #mainTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.95);
            }
            #mainTabWidget QTabBar::tab {
                background: rgba(248, 249, 250, 0.9);
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
                background: rgba(235, 243, 253, 0.85);
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
                background: rgba(240, 248, 255, 0.85);
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
                        stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(240, 240, 240, 0.9));
                    border: 1px solid #b0d4f1;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 12px;
                    color: #333;
                }
                QToolButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(227, 242, 253, 0.9), stop:1 rgba(187, 222, 251, 0.9));
                    border: 1px solid #90caf9;
                }
                QToolButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(187, 222, 251, 0.9), stop:1 rgba(144, 202, 249, 0.9));
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
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #e0e0e0;
                border-top: none;
                color: #333333;
                font-weight: 500;
                padding: 5px 10px;
            }
        """)

    def show_student_management(self):
        """显示学生管理窗口"""
        from gui.student_mgmt import StudentManagementWindow
        self.student_window = self._open_window(
            StudentManagementWindow,
            "学生管理"
        )

    def show_grade_management(self):
        """显示成绩管理窗口"""
        from gui.grade_mgmt import GradeManagementWindow
        self.grade_window = self._open_window(
            GradeManagementWindow,
            "成绩管理"
        )

    def show_assignment_management(self):
        """显示作业管理窗口"""
        from gui.assignment_mgmt import AssignmentManagementWindow
        self.assignment_window = self._open_window(
            AssignmentManagementWindow,
            "作业管理"
        )

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
        """窗口关闭事件处理"""
        self.logger.info("主窗口关闭")
        self._running = False  # 停止用户检查线程
        super().closeEvent(event)

    def show_settings(self):
        """显示系统设置窗口"""
        from gui.settings_window import SettingsWindow
        self.settings_window = self._open_window(
            SettingsWindow,
            "系统设置"
        )

    def show_reports(self):
        """显示报表生成窗口"""
        from gui.report_gen import ReportGenerationWindow
        self.report_window = self._open_window(
            ReportGenerationWindow,
            "报表生成"
        )

    def show_classroom_management(self):
        """显示课堂管理窗口"""
        from gui.classroom_mgmt import ClassroomManagementWindow
        self.classroom_window = self._open_window(
            ClassroomManagementWindow,
            "课堂管理"
        )

    def select_user(self):
        """每15秒检查用户状态的线程函数"""

        def user_check_loop():
            while getattr(self, '_running', True):  # 使用标志控制循环
                logging.info("当前用户为：%s", self.get_role_display(self.user_role))
                logging.info("当前用户ID为：%s", self.user_id)
                logging.info("运行正常，显示为主窗口")
                time.sleep(60)  # 每60秒检查一次

        # 创建并启动线程
        self.user_check_thread = threading.Thread(target=user_check_loop, daemon=True)
        self._running = True  # 设置运行标志
        self.user_check_thread.start()

    def _show_info_message(self, title, text):
        """
        显示信息提示框的通用方法

        Args:
            title: 窗口标题
            text: 提示文本
        """
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setFont(QFont("Microsoft YaHei", 20))
        msg.setStyleSheet(self.MESSAGE_BOX_STYLE)
        msg.exec_()

    def show_calendar(self):
        """打开日程安排网站"""
        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择访问方式")
        dialog.setFixedSize(520, 260)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(22)

        # 提示标签
        label = QLabel("请选择要访问的网站：")
        label.setStyleSheet("font-size: 25px; font-weight: bold; margin-bottom: 14px;")
        layout.addWidget(label)

        # 内网按钮
        intranet_btn = QToolButton()
        intranet_btn.setText("🌐 校园内网\nhttps://nei.ytyz.org/")
        intranet_btn.setMinimumHeight(72)
        intranet_btn.setStyleSheet("""
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 181, 246, 0.9), stop:1 rgba(66, 165, 245, 0.9));
                border: 2px solid #42a5f5;
                border-radius: 8px;
                padding: 10px;
                font-size: 18px;
                color: white;
                font-weight: bold;
            }
            QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(66, 165, 245, 0.9), stop:1 rgba(25, 118, 210, 0.9));
                border: 2px solid #1976d2;
            }
        """)

        # 外网按钮
        internet_btn = QToolButton()
        internet_btn.setText("🌍 校园外网\nhttps://www.ytyz.org/")
        internet_btn.setMinimumHeight(72)
        internet_btn.setStyleSheet("""
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(129, 199, 132, 0.9), stop:1 rgba(102, 187, 106, 0.9));
                border: 2px solid #66bb6a;
                border-radius: 8px;
                padding: 10px;
                font-size: 18px;
                color: white;
                font-weight: bold;
            }
            QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(102, 187, 106, 0.9), stop:1 rgba(76, 175, 80, 0.9));
                border: 2px solid #4caf50;
            }
        """)

        # 按钮布局（左右排列）
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 8)
        button_layout.setSpacing(28)
        intranet_btn.setMinimumWidth(200)
        internet_btn.setMinimumWidth(200)
        button_layout.addStretch()
        button_layout.addWidget(intranet_btn)
        button_layout.addWidget(internet_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addSpacing(10)

        # 取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # 连接按钮信号
        def open_intranet():
            dialog.accept()
            url = QUrl("https://nei.ytyz.org/")
            QDesktopServices.openUrl(url)

        def open_internet():
            dialog.accept()
            url = QUrl("https://www.ytyz.org/")
            QDesktopServices.openUrl(url)

        intranet_btn.clicked.connect(open_intranet)
        internet_btn.clicked.connect(open_internet)

        # 显示对话框
        dialog.exec_()

    def show_notes(self):
        """显示点我功能提示"""
        self._show_info_message("点我", "📝 这我不知道写什么..........")

    def show_data_analysis(self):
        """显示数据分析功能提示"""
        self._show_info_message("数据分析", "📊 数据分析功能开发中...")

    def show_contact(self):
        """显示联系我们功能提示"""
        self._show_info_message("联系我们", "📞 联系我们功能开发中...")

    def show_links(self):
        """显示网站链接功能提示"""
        self._show_info_message("网站链接", "🌐 网站链接功能开发中...")

    def show_search(self):
        """显示搜索功能提示"""
        self._show_info_message("搜索功能", "🔍 搜索功能开发中...")