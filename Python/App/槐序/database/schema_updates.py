"""
数据库表结构定义 - 学生成绩4+X管理
"""

# 专业表
CREATE_MAJORS_TABLE = """
CREATE TABLE IF NOT EXISTS majors (
    major_id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_name TEXT NOT NULL UNIQUE,
    description TEXT
);
"""

# 专业课程关联表
CREATE_MAJOR_COURSES_TABLE = """
CREATE TABLE IF NOT EXISTS major_courses (
    major_id INTEGER,
    course_id INTEGER,
    PRIMARY KEY (major_id, course_id),
    FOREIGN KEY (major_id) REFERENCES majors(major_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
"""

# 班级专业关联表
CREATE_CLASS_MAJORS_TABLE = """
CREATE TABLE IF NOT EXISTS class_majors (
    class_id INTEGER,
    major_id INTEGER,
    PRIMARY KEY (class_id, major_id),
    FOREIGN KEY (class_id) REFERENCES classes(class_id),
    FOREIGN KEY (major_id) REFERENCES majors(major_id)
);
"""

# 成绩表（4+X管理）
CREATE_SCORES_TABLE = """
CREATE TABLE IF NOT EXISTS scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    major_id INTEGER,
    course_id INTEGER,
    regular_score REAL,      -- 平时成绩
    final_score REAL,        -- 期末成绩
    total_score REAL,        -- 总成绩（自动计算）
    credits REAL,            -- 学分
    exam_date DATE DEFAULT CURRENT_DATE,
    teacher_id TEXT,
    remark TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (major_id) REFERENCES majors(major_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
"""

# 插入默认专业数据
INSERT_DEFAULT_MAJORS = """
INSERT OR IGNORE INTO majors (major_id, major_name, description) VALUES
(1, '计算机应用技术', 'Computer Application Technology');
"""

# 创建表的SQL语句列表
ALL_TABLES = [
    CREATE_MAJORS_TABLE,
    CREATE_MAJOR_COURSES_TABLE,
    CREATE_CLASS_MAJORS_TABLE,
    CREATE_SCORES_TABLE,
    INSERT_DEFAULT_MAJORS
]

def create_score_management_tables(db_conn):
    """创建成绩管理相关的表"""
    cursor = db_conn.cursor()
    for sql in ALL_TABLES:
        cursor.execute(sql)
    db_conn.commit()