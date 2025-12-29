"""
数据库操作模块
处理数据库连接和基本操作
"""
import json
import bcrypt
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
#新增1
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, comment='学号/工号')
    password = db.Column(db.String(255), nullable=False, comment='加密后的密码')
    name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    email = db.Column(db.String(100), comment='邮箱')
    # ============ 修改：将 ENUM 改为 String ============
    role = db.Column(db.String(20), nullable=False, default='student')  # 原来是 ENUM
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
            
    def __repr__(self):
        return f'<User {self.username} - {self.name}>'
    
    def check_password(self, password):
        """验证密码"""
        try:
            # 先尝试正常的bcrypt验证
            return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            # 如果bcrypt验证失败，检查是否是特定的已知哈希
            known_hash = '$2b$12$5TCM9Bv38stmssJqvfWPDO.FsfGRdUP.YNQPwWfFOQ5mNNzJS2K.e'  # 123456的加密
            # 方法1：如果是已知的预置哈希且密码是"123456"
            if self.password == known_hash and password == "123456":
                print(f"调试: 使用预置哈希验证用户 {self.username}")
                return True
            # 方法2：如果是其他情况，尝试直接比较明文（仅用于紧急情况）
            if len(self.password) < 30 and password == self.password:
                print(f"警告: 用户 {self.username} 的密码可能是明文")
                return True
            # 方法3：如果是新注册的用户，密码哈希应该是正确的
            # 如果是老用户（导入的或预置的），允许用"123456"登录
            if password == "123456":
                print(f"提示: 尝试用默认密码验证用户 {self.username}")
                # 这里可以自动修复密码哈希
                self.fix_password_hash(password)
                return True
            return False

    # flask_login 所需属性和方法
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        # 可根据实际业务逻辑调整
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def fix_password_hash(self, password):
        """修复密码哈希"""
        try:
            # 生成正确的bcrypt哈希
            new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # 更新数据库（需要数据库会话）
            self.password = new_hash
            db.session.commit()
            print(f"已修复用户 {self.username} 的密码哈希")
        except Exception as e:
            print(f"修复密码哈希失败: {e}")

    def get_permissions(self):
        """获取用户权限"""
        return Permission.get_role_permissions(self.role)
    
    def has_permission(self, permission_code):
        """检查是否有指定权限"""
        permissions = self.get_permissions()
        return permission_code in permissions

class Permission(db.Model):
    """权限模型"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, comment='权限名称')
    code = db.Column(db.String(50), unique=True, nullable=False, comment='权限代码')
    description = db.Column(db.String(255), comment='权限描述')
    
    @staticmethod
    def get_role_permissions(role):
        """获取角色权限"""
        from sqlalchemy import text
        # 对于 SQLite，使用原生查询
        query = text("""
            SELECT p.code 
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_code = p.code
            WHERE rp.role = :role
        """)
        try:
            result = db.session.execute(query, {'role': role})
            return [row[0] for row in result]
        except:
            # 如果查询失败，返回默认权限
            default_permissions = {
                'admin': ['user_manage', 'batch_import', 'view_all_users', 'edit_profile', 
                         'system_settings', 'view_logs', 'export_data'],
                'teacher': ['view_all_users', 'edit_profile', 'manage_grades', 'export_data'],
                'student': ['edit_profile', 'view_grades']
            }
            return default_permissions.get(role, [])

class ImportLog(db.Model):
    """导入日志模型"""
    __tablename__ = 'import_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    import_by = db.Column(db.String(20), nullable=False, comment='导入者用户名')
    total_records = db.Column(db.Integer, default=0, comment='总记录数')
    success_count = db.Column(db.Integer, default=0, comment='成功数')
    failed_count = db.Column(db.Integer, default=0, comment='失败数')
    duplicate_count = db.Column(db.Integer, default=0, comment='重复数')
    report_data = db.Column(db.Text, comment='JSON格式的报告数据')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    
    def get_report_data(self):
        """获取报告数据"""
        if self.report_data:
            return json.loads(self.report_data)
        return {}

class File(db.Model):
    """文件模型"""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # 存储的唯一文件名
    original_filename = db.Column(db.String(255), nullable=False)  # 原始文件名
    file_path = db.Column(db.String(500), nullable=False)  # 文件存储路径
    file_type = db.Column(db.String(50), nullable=False)  # 文件类型: pdf, jpg, png, jpeg
    file_size = db.Column(db.Integer, nullable=False)  # 文件大小(字节)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)  # 文件描述
    status = db.Column(db.String(20), default='active')  # 文件状态
    
    # 外键关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('files', lazy=True))
    
    def __repr__(self):
        return f'<File {self.original_filename}>'
    
    def format_size(self):
        """格式化文件大小显示"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def get_file_info(self):
        """获取文件信息字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'formatted_size': self.format_size(),
            'upload_time': self.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': self.description,
            'user_id': self.user_id
        }

class Certificate(db.Model):
    """证书信息模型"""
    __tablename__ = 'certificates'
    
    cert_id = db.Column(db.Integer, primary_key=True, comment='证书ID')
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='提交者user_id')
    # ============ 修改：将 ENUM 改为 String ============
    submitter_role = db.Column(db.String(20), nullable=False, comment='提交者角色')  # 原来是 ENUM
    student_id = db.Column(db.String(13), nullable=False, comment='学号（13位）')
    student_name = db.Column(db.String(50), nullable=False, comment='学生姓名')
    department = db.Column(db.String(100), comment='学生所在学院')
    competition_name = db.Column(db.String(200), comment='竞赛项目')
    award_category = db.Column(db.String(50), comment='获奖类别（国家级、省级）')
    award_level = db.Column(db.String(50), comment='获奖等级')
    competition_type = db.Column(db.String(20), comment='竞赛类型（A类、B类）')
    organizer = db.Column(db.String(200), comment='主办单位')
    award_date = db.Column(db.Date, comment='获奖时间')
    advisor = db.Column(db.String(50), nullable=False, comment='指导教师')
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), comment='关联文件ID')
    file_path = db.Column(db.String(500), comment='证书文件路径')
    extraction_method = db.Column(db.String(50), comment='识别方式')
    extraction_confidence = db.Column(db.Numeric(5, 2), comment='识别置信度')
    # ============ 修改：将 ENUM 改为 String ============
    status = db.Column(db.String(20), nullable=False, default='draft', comment='状态')  # 原来是 ENUM
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    submitted_at = db.Column(db.TIMESTAMP, comment='提交时间')
    
    # 关系
    submitter = db.relationship('User', backref=db.backref('certificates', lazy=True))
    file = db.relationship('File', backref=db.backref('certificates', lazy=True))
    
    def __repr__(self):
        return f'<Certificate {self.cert_id} - {self.student_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'cert_id': self.cert_id,
            'submitter_id': self.submitter_id,
            'submitter_role': self.submitter_role,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'department': self.department,
            'competition_name': self.competition_name,
            'award_category': self.award_category,
            'award_level': self.award_level,
            'competition_type': self.competition_type,
            'organizer': self.organizer,
            'award_date': self.award_date.strftime('%Y-%m-%d') if self.award_date else None,
            'advisor': self.advisor,
            'file_id': self.file_id,
            'file_path': self.file_path,
            'extraction_method': self.extraction_method,
            'extraction_confidence': float(self.extraction_confidence) if self.extraction_confidence else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None
        }

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_config'
    
    config_id = db.Column(db.Integer, primary_key=True, comment='配置ID')
    config_key = db.Column(db.String(100), unique=True, nullable=False, comment='配置键')
    config_value = db.Column(db.Text, comment='配置值')
    description = db.Column(db.String(255), comment='配置说明')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='更新者user_id')
    
    # 关系
    updater = db.relationship('User', backref=db.backref('config_updates', lazy=True))
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key} = {self.config_value}>'
    
    @staticmethod
    def get_config(key, default=None):
        """获取配置值"""
        config = SystemConfig.query.filter_by(config_key=key).first()
        return config.config_value if config else default
    
    @staticmethod
    def set_config(key, value, description=None, updated_by=None):
        """设置配置值"""
        config = SystemConfig.query.filter_by(config_key=key).first()
        if config:
            config.config_value = value
            if description:
                config.description = description
            if updated_by:
                config.updated_by = updated_by
        else:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                description=description,
                updated_by=updated_by
            )
            db.session.add(config)
        db.session.commit()
        return config

class RolePermission(db.Model):
    """角色权限关联模型"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, comment='角色名称')
    permission_code = db.Column(db.String(50), nullable=False, comment='权限代码')
    
    def __repr__(self):
        return f'<RolePermission {self.role} - {self.permission_code}>'

class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def create_user(username, password, name, email, role):
        """创建用户"""
        # 验证角色有效性
        if role not in ['student', 'teacher', 'admin']:
            raise ValueError(f'无效的角色: {role}')
        
        # 加密密码
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = User(
            username=username,
            password=hashed_password.decode('utf-8'),
            name=name,
            email=email,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def check_username_exists(username):
        """检查用户名是否存在"""
        user = User.query.filter_by(username=username).first()
        return user is not None
    
    @staticmethod
    def validate_username_format(username, role):
        """验证用户名格式"""
        if role == 'student':
            return len(username) == 13 and username.isdigit()
        elif role in ['teacher', 'admin']:
            return len(username) == 8 and username.isdigit()
        return False
    
    @staticmethod
    def save_import_log(filename, import_by, total_records, success_count, 
                        failed_count, duplicate_count, report_data):
        """保存导入日志"""
        log = ImportLog(
            filename=filename,
            import_by=import_by,
            total_records=total_records,
            success_count=success_count,
            failed_count=failed_count,
            duplicate_count=duplicate_count,
            report_data=json.dumps(report_data, ensure_ascii=False)
        )
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_import_logs(limit=50):
        """获取导入日志"""
        return ImportLog.query.order_by(ImportLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_all_users():
        """获取所有用户"""
        return User.query.all()
    
    @staticmethod
    def get_users_by_role(role):
        """根据角色获取用户"""
        return User.query.filter_by(role=role).all()
    
    @staticmethod
    def add_file(user_id, filename, original_filename, file_path, file_type, file_size, description=None):
        """添加文件记录"""
        try:
            file = File(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                description=description
            )
            db.session.add(file)
            db.session.commit()
            return file, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def get_user_files(user_id, page=1, per_page=10):
        """获取用户的文件列表"""
        return File.query.filter_by(user_id=user_id, status='active') \
                         .order_by(File.upload_time.desc()) \
                         .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_file_by_id(file_id, user_id=None):
        """根据ID获取文件"""
        query = File.query.filter_by(id=file_id, status='active')
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.first()
    
    @staticmethod
    def delete_file(file_id, user_id):
        """删除文件记录"""
        try:
            file = File.query.filter_by(id=file_id, user_id=user_id).first()
            if not file:
                return False, "文件不存在或无权删除"
            
            file.status = 'deleted'
            db.session.commit()
            return True, "文件删除成功"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_file_stats(user_id):
        """获取用户文件统计信息"""
        total_files = File.query.filter_by(user_id=user_id, status='active').count()
        total_size = db.session.query(db.func.sum(File.file_size)) \
                               .filter_by(user_id=user_id, status='active').scalar() or 0
        recent_files = File.query.filter_by(user_id=user_id, status='active') \
                                 .order_by(File.upload_time.desc()) \
                                 .limit(5).all()
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'recent_files': recent_files
        }
    
    @staticmethod
    def create_certificate(submitter_id, submitter_role, student_id, student_name, 
                          advisor, file_id=None, file_path=None, **kwargs):
        """创建证书记录"""
        try:
            # 验证提交者角色
            if submitter_role not in ['student', 'teacher']:
                return None, f"无效的提交者角色: {submitter_role}"
            
            cert = Certificate(
                submitter_id=submitter_id,
                submitter_role=submitter_role,
                student_id=student_id,
                student_name=student_name,
                advisor=advisor,
                file_id=file_id,
                file_path=file_path,
                department=kwargs.get('department'),
                competition_name=kwargs.get('competition_name'),
                award_category=kwargs.get('award_category'),
                award_level=kwargs.get('award_level'),
                competition_type=kwargs.get('competition_type'),
                organizer=kwargs.get('organizer'),
                award_date=kwargs.get('award_date'),
                extraction_method=kwargs.get('extraction_method'),
                extraction_confidence=kwargs.get('extraction_confidence'),
                status=kwargs.get('status', 'draft')
            )
            db.session.add(cert)
            db.session.commit()
            return cert, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def update_certificate(cert_id, user_id, **kwargs):
        """更新证书记录"""
        try:
            cert = Certificate.query.filter_by(cert_id=cert_id, submitter_id=user_id).first()
            if not cert:
                return False, "证书不存在或无权修改"
            
            if cert.status == 'submitted':
                return False, "已提交的证书不能修改"
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(cert, key) and value is not None:
                    setattr(cert, key, value)
            
            db.session.commit()
            return True, "更新成功"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def submit_certificate(cert_id, user_id):
        """提交证书"""
        try:
            cert = Certificate.query.filter_by(cert_id=cert_id, submitter_id=user_id).first()
            if not cert:
                return False, "证书不存在或无权提交"
            
            if cert.status == 'submitted':
                return False, "证书已提交"
            
            # 验证必填字段
            if not cert.student_id or len(cert.student_id) != 13:
                return False, "学号必须是13位数字"
            if not cert.student_name:
                return False, "学生姓名不能为空"
            if not cert.advisor:
                return False, "指导教师不能为空"
            
            cert.status = 'submitted'
            cert.submitted_at = datetime.now()
            db.session.commit()
            return True, "提交成功"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_user_certificates(user_id, status=None, page=1, per_page=10):
        """获取用户的证书列表"""
        query = Certificate.query.filter_by(submitter_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Certificate.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_certificate_by_id(cert_id, user_id=None):
        """根据ID获取证书"""
        query = Certificate.query.filter_by(cert_id=cert_id)
        if user_id:
            query = query.filter_by(submitter_id=user_id)
        return query.first()
    
    @staticmethod
    def get_all_certificates(status=None, submitter_role=None, page=1, per_page=20):
        """获取所有证书（管理员功能）"""
        query = Certificate.query
        if status:
            query = query.filter_by(status=status)
        if submitter_role:
            query = query.filter_by(submitter_role=submitter_role)
        return query.order_by(Certificate.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_submission_deadline():
        """获取提交截止时间"""
        deadline_str = SystemConfig.get_config('submission_deadline', '2025-12-30 23:59:59')
        try:
            return datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.strptime('2025-12-30 23:59:59', '%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def is_before_deadline():
        """检查是否在截止时间之前"""
        deadline = DatabaseManager.get_submission_deadline()
        return datetime.now() <= deadline
    
    @staticmethod
    def init_database_data():
        """初始化数据库基础数据"""
        try:
            # 清空现有数据（可选）
            # db.session.query(RolePermission).delete()
            # db.session.query(Permission).delete()
            
            # 添加权限数据
            permissions = [
                {'name': '用户管理', 'code': 'user_manage', 'description': '管理用户信息'},
                {'name': '批量导入', 'code': 'batch_import', 'description': '批量导入用户'},
                {'name': '查看所有用户', 'code': 'view_all_users', 'description': '查看所有用户信息'},
                {'name': '修改个人信息', 'code': 'edit_profile', 'description': '修改自己的个人信息'},
                {'name': '查看个人成绩', 'code': 'view_grades', 'description': '学生查看成绩'},
                {'name': '管理成绩', 'code': 'manage_grades', 'description': '教师管理成绩'},
                {'name': '系统设置', 'code': 'system_settings', 'description': '管理系统设置'},
                {'name': '查看日志', 'code': 'view_logs', 'description': '查看系统日志'},
                {'name': '导出数据', 'code': 'export_data', 'description': '导出用户数据'},
            ]
            
            for perm_data in permissions:
                perm = Permission.query.filter_by(code=perm_data['code']).first()
                if not perm:
                    perm = Permission(**perm_data)
                    db.session.add(perm)
            
            # 添加角色权限关联
            role_permissions = [
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
                ('student', 'view_grades'),
            ]
            
            for role, perm_code in role_permissions:
                exists = RolePermission.query.filter_by(role=role, permission_code=perm_code).first()
                if not exists:
                    rp = RolePermission(role=role, permission_code=perm_code)
                    db.session.add(rp)
            
            db.session.commit()
            print("数据库基础数据初始化完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"数据库初始化失败: {e}")
