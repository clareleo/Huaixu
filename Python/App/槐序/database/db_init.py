import logging
from PyQt5.QtWidgets import QMessageBox

# 数据库表创建SQL语句
CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
        real_name TEXT,
        email TEXT
    )""",

    """CREATE TABLE IF NOT EXISTS classes (
        class_id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        grade TEXT,
        major TEXT,
        description TEXT
    )""",

    """CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT CHECK(gender IN ('男', '女', '其他')),
        birth_date TEXT,
        class_id INTEGER,
        admission_date TEXT,
        contact TEXT,
        FOREIGN KEY (class_id) REFERENCES classes(class_id)
    )""",

    """CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        credit REAL,
        course_type TEXT CHECK(course_type IN ('必修', '选修')),
        description TEXT
    )""",

    """CREATE TABLE IF NOT EXISTS course_class (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        term TEXT NOT NULL,
        teacher_id INTEGER,
        FOREIGN KEY (course_id) REFERENCES courses(course_id),
        FOREIGN KEY (class_id) REFERENCES classes(class_id),
        FOREIGN KEY (teacher_id) REFERENCES users(user_id),
        UNIQUE(course_id, class_id, term)
    )""",

    """CREATE TABLE IF NOT EXISTS scores (
        score_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        course_id INTEGER NOT NULL,
        score REAL CHECK(score >= 0 AND score <= 100),
        term TEXT NOT NULL,
        exam_type TEXT DEFAULT '期末',
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id),
        UNIQUE(student_id, course_id, term, exam_type)
    )""",

    """CREATE TABLE IF NOT EXISTS assignment_folders (
        folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_path TEXT NOT NULL UNIQUE,
        course_id INTEGER NOT NULL,
        term TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )""",

    """CREATE TABLE IF NOT EXISTS assignment_submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        folder_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        submit_time TEXT,
        status TEXT CHECK(status IN ('未提交', '已提交', '已批改')),
        score REAL,
        feedback TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (folder_id) REFERENCES assignment_folders(folder_id),
        UNIQUE(student_id, folder_id)
    )""",

    """CREATE TABLE IF NOT EXISTS evaluations (
        eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        eval_type TEXT NOT NULL,
        eval_content TEXT,
        score REAL,
        term TEXT,
        evaluator_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (evaluator_id) REFERENCES users(user_id)
    )""",

    # 课堂活动表
    """CREATE TABLE IF NOT EXISTS classroom_activities (
        activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        term TEXT NOT NULL,
        activity_date DATE NOT NULL,
        activity_type TEXT NOT NULL,
        description TEXT,
        max_score REAL DEFAULT 0,
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )""",

    # 课堂活动评分表
    """CREATE TABLE IF NOT EXISTS classroom_scores (
        score_id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER NOT NULL,
        student_id TEXT NOT NULL,
        score REAL DEFAULT 0,
        comment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (activity_id) REFERENCES classroom_activities(activity_id),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )"""
]

# 初始数据插入SQL
INITIAL_DATA = [
    """INSERT OR IGNORE INTO users (username, password, role, real_name)
       VALUES ('admin', 'admin123', 'admin', '系统管理员')""",

    """INSERT OR IGNORE INTO classes (class_name, grade, major)
       VALUES ('计算机1班', '2023', '计算机科学与技术')"""
]

def initialize_database(conn):
    """初始化数据库表结构"""
    try:
        cursor = conn.cursor()

        # 创建表
        for create_table_sql in CREATE_TABLES:
            cursor.execute(create_table_sql)

        # 插入初始数据
        for insert_sql in INITIAL_DATA:
            cursor.execute(insert_sql)

        conn.commit()
        return True
    except Exception as e:
        QMessageBox.critical(
            None,
            "数据库错误",
            f"初始化数据库时出错:\n{str(e)}"
        )
        logging.error(f"数据库初始化错误: {str(e)}")
        return False