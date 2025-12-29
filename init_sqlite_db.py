import sqlite3
import os

def init_sqlite_database():
    # 创建或连接 SQLite 数据库
    db_path = "user_auth_system.db"
    
    # 删除现有数据库（仅用于初始化）
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 创建 users 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(20) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        name VARCHAR(50) NOT NULL,
        email VARCHAR(100),
        role VARCHAR(20) CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. 创建 files 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name VARCHAR(255),
        filename VARCHAR(255) NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_type VARCHAR(50) NOT NULL,
        file_size INTEGER NOT NULL,
        upload_time DATETIME,
        description TEXT,
        status VARCHAR(20),
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 3. 创建 certificates 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS certificates (
        cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        submitter_id INTEGER NOT NULL,
        submitter_role VARCHAR(20) CHECK(submitter_role IN ('student', 'teacher')),
        student_id VARCHAR(13) NOT NULL,
        student_name VARCHAR(50) NOT NULL,
        department VARCHAR(100),
        competition_name VARCHAR(200),
        award_category VARCHAR(50),
        award_level VARCHAR(50),
        competition_type VARCHAR(20),
        organizer VARCHAR(200),
        award_date DATE,
        advisor VARCHAR(50) NOT NULL,
        file_id INTEGER,
        file_path VARCHAR(500),
        extraction_method VARCHAR(50),
        extraction_confidence DECIMAL(5, 2),
        status VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        submitted_at TIMESTAMP,
        FOREIGN KEY (submitter_id) REFERENCES users (id),
        FOREIGN KEY (file_id) REFERENCES files (id)
    )
    ''')
    
    # 4. 创建 permissions 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL UNIQUE,
        code VARCHAR(50) NOT NULL UNIQUE,
        description VARCHAR(255)
    )
    ''')
    
    # 5. 创建 role_permissions 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS role_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role VARCHAR(20) NOT NULL,
        permission_code VARCHAR(50) NOT NULL,
        FOREIGN KEY (permission_code) REFERENCES permissions (code)
    )
    ''')
    
    # 6. 创建 system_config 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_config (
        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key VARCHAR(100) NOT NULL UNIQUE,
        config_value TEXT,
        description VARCHAR(255),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER,
        FOREIGN KEY (updated_by) REFERENCES users (id)
    )
    ''')
    
    # 7. 创建 import_logs 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS import_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename VARCHAR(255) NOT NULL,
        import_by VARCHAR(20) NOT NULL,
        total_records INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        duplicate_count INTEGER DEFAULT 0,
        report_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_certificates_submitter ON certificates (submitter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_certificates_student ON certificates (student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_certificates_status ON certificates (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_user ON files (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_import_logs_import_by ON import_logs (import_by)')
    
    conn.commit()
    
    # 插入初始化数据
    insert_initial_data(cursor, conn)
    
    conn.close()
    print(f"SQLite 数据库初始化完成: {db_path}")

def insert_initial_data(cursor, conn):
    # 插入用户数据（密码改为加密后的，这里使用123456的bcrypt加密）
    users_data = [
        ('00000000', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '超级管理员', 'superadmin@edu.cn', 'admin'),
        ('10000001', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '系统管理员', 'sysadmin@edu.cn', 'admin'),
        ('10000002', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '数据管理员', 'datadmin@edu.cn', 'admin'),
        ('20000001', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '张教授', 'zhang@edu.cn', 'teacher'),
        ('20000002', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '李教授', 'li@edu.cn', 'teacher'),
        ('20000003', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '王老师', 'wang@edu.cn', 'teacher'),
        ('20000004', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '赵老师', 'zhao@edu.cn', 'teacher'),
        ('20000005', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '刘教授', 'liu@edu.cn', 'teacher'),
        ('2023000000001', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '张诗玉', 'zhangsan@edu.cn', 'student'),
        ('2023000000002', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '李黎', 'lisi@edu.cn', 'student'),
        ('2023000000003', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '王之涵', 'wangwu@edu.cn', 'student'),
        ('2023000000004', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '赵天海', 'zhaoliu@edu.cn', 'student'),
        ('2023000000005', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '钱仲怀', 'qianqi@edu.cn', 'student'),
        ('2023000000006', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '孙则诚', 'sunba@edu.cn', 'student'),
        ('2023000000007', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '周梦诗', 'zhoujiu@edu.cn', 'student'),
        ('2023000000008', '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e', '吴十', 'wushi@edu.cn', 'student'),
        ('2023000000010', '$2b$12$Wmp6SHDR8MUUI/Nn5fry9Ohz5aiG8WOEVOLqSrXfdKQwpx7BMWOSS', '薯条', 'stp@email.com', 'student')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO users (username, password, name, email, role)
    VALUES (?, ?, ?, ?, ?)
    ''', users_data)
    
    # 插入权限数据
    permissions_data = [
        ('用户管理', 'user_manage', '管理用户信息'),
        ('批量导入', 'batch_import', '批量导入用户'),
        ('查看所有用户', 'view_all_users', '查看所有用户信息'),
        ('修改个人信息', 'edit_profile', '修改自己的个人信息'),
        ('查看个人成绩', 'view_grades', '学生查看成绩'),
        ('管理成绩', 'manage_grades', '教师管理成绩'),
        ('系统设置', 'system_settings', '管理系统设置'),
        ('查看日志', 'view_logs', '查看系统日志'),
        ('导出数据', 'export_data', '导出用户数据')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO permissions (name, code, description)
    VALUES (?, ?, ?)
    ''', permissions_data)
    
    # 插入角色权限数据
    role_perms_data = [
        ('admin', 'user_manage'),
        ('admin', 'batch_import'),
        ('admin', 'view_all_users'),
        ('admin', 'edit_profile'),
        ('admin', 'system_settings'),
        ('admin', 'view_logs'),
        ('admin', 'export_data'),
        ('teacher', 'view_all_users'),
        ('teacher', 'edit_profile'),
        ('teacher', 'manage_grades'),
        ('teacher', 'export_data'),
        ('student', 'edit_profile'),
        ('student', 'view_grades')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO role_permissions (role, permission_code)
    VALUES (?, ?)
    ''', role_perms_data)
    
    # 插入系统配置数据
    config_data = [
        ('submission_deadline', '2025-12-30 23:59:59', '证书提交截止时间', None),
        ('default_extraction_api', 'glm4v', '默认信息提取API', None),
        ('max_file_size_mb', '10', '最大文件大小（MB）', None)
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO system_config (config_key, config_value, description, updated_by)
    VALUES (?, ?, ?, ?)
    ''', config_data)
    
    conn.commit()

if __name__ == "__main__":
    init_sqlite_database()