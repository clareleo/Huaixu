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
    parser = argparse.ArgumentParser(description='4+X成绩管理系统')
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
    logger.info("启动4+X成绩管理系统")

    # 设置全局异常处理
    sys.excepthook = excepthook

    # 解析命令行参数
    args = parse_arguments()
    logger.info(f"命令行参数: {args}")

    # 初始化应用程序
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('img/icon.png'))

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

    # 创建数据库连接
    try:
        logger.info(f"连接数据库: {args.db}")
        db_conn = create_connection(args.db)
        if db_conn is None:
            logger.error("无法连接数据库")
            QMessageBox.critical(None, "错误", "无法连接数据库，程序将退出")
            return 1

        # 检查并初始化数据库表
        logger.info("初始化数据库表")
        if not initialize_database(db_conn):
            logger.error("数据库初始化失败")
            QMessageBox.critical(None, "错误", "数据库初始化失败，程序将退出")
            return 1
    except Exception as e:
        logger.exception("数据库初始化异常")
        QMessageBox.critical(None, "错误", f"数据库初始化异常: {str(e)}")
        return 1

    # 显示登录窗口
    try:
        logger.info("显示登录窗口")
        login_window = LoginWindow(db_conn)
        login_window.show()
    except Exception as e:
        logger.exception("无法启动登录窗口")
        QMessageBox.critical(None, "错误", f"无法启动登录窗口: {str(e)}")
        return 1

    # 执行应用程序
    logger.info("进入应用程序主循环")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()