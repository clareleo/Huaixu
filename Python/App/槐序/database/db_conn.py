import sqlite3
from PyQt5.QtWidgets import QMessageBox


def create_connection(db_file):
    """创建数据库连接"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")

        # 创建成绩管理相关的表
        create_score_management_tables(conn)

        return conn
    except sqlite3.Error as e:
        QMessageBox.critical(
            None,
            "数据库错误",
            f"无法连接数据库 {db_file}:\n{str(e)}"
        )
    return conn


def create_score_management_tables(db_conn):
    """创建成绩管理相关的表"""
    cursor = db_conn.cursor()

    # 专业表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS majors
                   (
                       major_id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       major_name
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       description
                       TEXT
                   );
                   """)

    # 专业课程关联表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS major_courses
                   (
                       major_id
                       INTEGER,
                       course_id
                       INTEGER,
                       PRIMARY
                       KEY
                   (
                       major_id,
                       course_id
                   ),
                       FOREIGN KEY
                   (
                       major_id
                   ) REFERENCES majors
                   (
                       major_id
                   ),
                       FOREIGN KEY
                   (
                       course_id
                   ) REFERENCES courses
                   (
                       course_id
                   )
                       );
                   """)

    # 班级专业关联表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS class_majors
                   (
                       class_id
                       INTEGER,
                       major_id
                       INTEGER,
                       PRIMARY
                       KEY
                   (
                       class_id,
                       major_id
                   ),
                       FOREIGN KEY
                   (
                       class_id
                   ) REFERENCES classes
                   (
                       class_id
                   ),
                       FOREIGN KEY
                   (
                       major_id
                   ) REFERENCES majors
                   (
                       major_id
                   )
                       );
                   """)

    # 成绩表（4+X管理）- 如果表已存在，添加缺失的字段
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS scores_new
                   (
                       score_id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       student_id
                       TEXT
                       NOT
                       NULL,
                       major_id
                       INTEGER,
                       course_id
                       INTEGER,
                       regular_score
                       REAL, -- 平时成绩
                       final_score
                       REAL, -- 期末成绩
                       total_score
                       REAL, -- 总成绩（自动计算）
                       credits
                       REAL, -- 学分
                       exam_date
                       DATE
                       DEFAULT
                       CURRENT_DATE,
                       teacher_id
                       TEXT,
                       remark
                       TEXT,
                       FOREIGN
                       KEY
                   (
                       student_id
                   ) REFERENCES students
                   (
                       student_id
                   ),
                       FOREIGN KEY
                   (
                       major_id
                   ) REFERENCES majors
                   (
                       major_id
                   ),
                       FOREIGN KEY
                   (
                       course_id
                   ) REFERENCES courses
                   (
                       course_id
                   )
                       );
                   """)

    # 检查现有表的列
    cursor.execute("PRAGMA table_info(scores)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    # 如果表不存在，直接创建
    if 'scores' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
        cursor.execute("""
                       CREATE TABLE scores
                       (
                           score_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                           student_id    TEXT NOT NULL,
                           major_id      INTEGER,
                           course_id     INTEGER,
                           regular_score REAL, -- 平时成绩
                           final_score   REAL, -- 期末成绩
                           total_score   REAL, -- 总成绩（自动计算）
                           credits       REAL, -- 学分
                           exam_date     DATE DEFAULT CURRENT_DATE,
                           teacher_id    TEXT,
                           remark        TEXT,
                           FOREIGN KEY (student_id) REFERENCES students (student_id),
                           FOREIGN KEY (major_id) REFERENCES majors (major_id),
                           FOREIGN KEY (course_id) REFERENCES courses (course_id)
                       );
                       """)
    else:
        # 如果表存在，添加缺失的字段
        if 'regular_score' not in existing_columns:
            cursor.execute("ALTER TABLE scores ADD COLUMN regular_score REAL")
        if 'final_score' not in existing_columns:
            cursor.execute("ALTER TABLE scores ADD COLUMN final_score REAL")
        if 'total_score' not in existing_columns:
            cursor.execute("ALTER TABLE scores ADD COLUMN total_score REAL")
        if 'credits' not in existing_columns:
            cursor.execute("ALTER TABLE scores ADD COLUMN credits REAL")
        if 'major_id' not in existing_columns:
            cursor.execute("ALTER TABLE scores ADD COLUMN major_id INTEGER")

    # 插入默认专业数据
    cursor.execute("""
                   INSERT
                   OR IGNORE INTO majors (major_id, major_name, description) VALUES
        (1, '计算机应用技术', 'Computer Application Technology');
                   """)

    db_conn.commit()


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