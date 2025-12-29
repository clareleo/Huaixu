import sys
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont, QIcon
from database.db_conn import create_connection
from database.db_init import initialize_database
from gui.startup_window import StartupWindow
from gui.login_window import LoginWindow
from gui.main_window import MainWindow

logger = logging.getLogger(__name__)


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.db_conn = None
        self.current_window = None  # 当前显示的窗口对象
        self.setup_app()
        self.show_startup_window()

    def setup_app(self):
        self.app.setQuitOnLastWindowClosed(True)
        self.app.setWindowIcon(QIcon('img/icon.png'))
        font = QFont("Microsoft YaHei", 15)
        self.app.setFont(font)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('grade_system.log'),
                logging.StreamHandler()
            ]
        )
        logger.info("[MainApp] 应用程序初始化完成")

    def show_startup_window(self):
        try:
            DB_FILE = 'grade_management.db'
            self.db_conn = create_connection(DB_FILE)
            if not self.db_conn:
                raise Exception("无法连接到数据库")
            logger.info(f"[MainApp] 数据库连接对象类型: {type(self.db_conn)}")
            initialize_database(self.db_conn)
            logger.info("[MainApp] 数据库初始化/连接成功")

            self.current_window = StartupWindow(self.db_conn)
            # 确保在显示窗口之前连接信号
            self.current_window.loading_completed.connect(self._on_startup_loaded)
            self.current_window.show()

        except Exception as e:
            logger.exception("[MainApp] 启动窗口显示失败")
            QMessageBox.critical(None, "启动错误", f"无法启动系统: {str(e)}")
            sys.exit(1)

    def _on_startup_loaded(self):
        logger.debug("启动页加载完成，即将显示登录窗口")
        logger.info("DEBUG: _on_startup_loaded 被调用")
        self._switch_to_window(LoginWindow(self.db_conn))

    def show_login_window(self):
        """显示登录窗口（保持兼容，但推荐统一用 _switch_to_window）"""
        logger.info("[MainApp] 准备显示登录窗口")
        self._switch_to_window(LoginWindow(self.db_conn))  # ✅ 必须调用这个！！！

    def show_main_window(self, user_id, role):
        logger.info(f"[MainApp] 准备显示主窗口，用户ID: {user_id}, 角色: {role}")
        self._switch_to_window(MainWindow(self.db_conn, user_id, role))

    def _on_logout_requested(self):
        print("[DEBUG] _on_logout_requested called")  # 添加调试输出
        logger.info("[MainApp] 收到登出请求，返回登录页")
        self.show_login_window()  # 返回登录窗口

    def _switch_to_window(self, new_window):
        if self.current_window:
            self.current_window.close()
            self.current_window.deleteLater()
            self.current_window = None

        self.current_window = new_window
        self.current_window.show()

        if isinstance(new_window, LoginWindow):
            new_window.db_conn = self.db_conn
            logger.info(f"[MainApp] 传递给 LoginWindow 的 db_conn 类型: {type(new_window.db_conn)}")
            new_window.login_success.connect(self._on_login_success)
            logger.info("[MainApp] 已连接登录成功信号")

        elif isinstance(new_window, MainWindow):
            logger.info(f"[MainApp] 准备连接 MainWindow 信号, 实例ID: {id(new_window)}")
            connection_result = new_window.logout_requested.connect(self._on_logout_requested)
            logger.info(f"[MainApp] 信号连接结果: {connection_result}")
            logger.info("[MainApp] 已连接登出信号")

    def _on_login_success(self, user_id, role):
        logger.info(f"[MainApp] 用户登录成功，ID: {user_id}, 角色: {role}")
        self.show_main_window(user_id, role)

    def run(self):
        sys.exit(self.app.exec_())