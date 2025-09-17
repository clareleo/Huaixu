import sqlite3
from PyQt5.QtWidgets import QMessageBox

def create_connection(db_file):
    """创建数据库连接"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        QMessageBox.critical(
            None,
            "数据库错误",
            f"无法连接数据库 {db_file}:\n{str(e)}"
        )
    return conn

def close_connection(conn):
    """关闭数据库连接"""
    if conn:
        try:
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.warning(
                None,
                "数据库警告",
                f"关闭数据库连接时出错:\n{str(e)}"
            )