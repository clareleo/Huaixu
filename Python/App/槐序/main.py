"""
这个bug修的我想死
"""

import sys
import argparse
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont, QIcon
from database.db_conn import create_connection
from database.db_init import initialize_database
from gui.login_window import LoginWindow
# 导入启动窗口
from gui.startup_window import StartupWindow


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('grade_system.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_stylesheet(path='resources/styles.qss'):
    """加载应用程序样式表"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"样式表文件未找到: {path}")
        return ""


def excepthook(exctype, value, tb):
    """全局异常处理钩子"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logging.critical(f"未捕获的异常: {error_msg}")
    QMessageBox.critical(None, "程序错误",
                         f"发生未捕获的异常:\n{error_msg}\n程序将退出。")
    sys.exit(1)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='HuaiXu')
    parser.add_argument('--db', default='grade_management.db',
                        help='指定数据库文件路径')
    parser.add_argument('--style', default='resources/styles.qss',
                        help='指定样式表文件路径')
    parser.add_argument('--test', action='store_true',
                        help='测试模式，不显示主界面')
    return parser.parse_args()


def main():
    # 设置日志
    logger = setup_logging()
    logger.info("启动 - HuaiXu槐序")

    # 设置全局异常处理
    sys.excepthook = excepthook

    # 解析命令行参数
    args = parse_arguments()
    logger.info(f"命令行参数: {args}")

    # 初始化应用程序
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('img/icon.png'))
    app.setQuitOnLastWindowClosed(False)  # 重要：禁止最后一个窗口关闭时自动退出程序

    # 设置默认字体
    font = QFont("Microsoft YaHei", 15)
    app.setFont(font)

    # 加载样式表
    stylesheet = load_stylesheet(args.style)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        logger.info("样式表加载成功")

    # 测试模式直接退出
    if args.test:
        logger.info("测试模式成功启动，退出")
        return 0

    try:
        # 先创建数据库连接（用于启动窗口和后续登录）
        db_conn = create_connection(args.db)
        if db_conn is None:
            logger.error("无法连接数据库")
            QMessageBox.critical(None, "错误", "无法连接数据库，程序将退出")
            return 1

        # 添加这行来初始化数据库表结构
        initialize_database(db_conn)
        logger.info("数据库初始化完成")

        # 创建并显示启动窗口，传入数据库文件路径
        startup_window = StartupWindow(args.db)
        startup_window.show()

        # 注意：启动窗口会处理加载完成后跳转到登录窗口的逻辑
        # 应用程序主循环会继续运行，直到所有窗口关闭
        sys.exit(app.exec_())

    except Exception as e:
        logger.exception("程序启动异常")
        QMessageBox.critical(None, "错误", f"程序启动时发生异常: {str(e)}")
        return 1


if __name__ == "__main__":
    main()