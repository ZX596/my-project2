"""
用户认证系统主程序
"""
import os
import sys
import socket
import subprocess
import time
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired  # 添加导入

from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from werkzeug.utils import secure_filename
import bcrypt

from database import db, DatabaseManager, User, File, Certificate
from user_import import UserImportManager
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from urllib.parse import quote
from flask import jsonify
from datetime import datetime

# ==================== 主要修改部分开始 ====================

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# ============ 修改数据库配置 ============
# 原来的 MySQL 配置：
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:40%Zhengxue111@localhost/user_auth_system'

# 改为 SQLite 配置：
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "user_auth_system.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==================== 主要修改部分结束 ====================

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

# 创建上传文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 表单类
class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('学号/工号', validators=[DataRequired(), Length(min=8, max=13)])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    """注册表单"""
    username = StringField('学号/工号', validators=[DataRequired(), Length(min=8, max=13)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired()])
    name = StringField('真实姓名', validators=[DataRequired()])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    role = SelectField('角色', choices=[
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员')
    ], validators=[DataRequired()])
    submit = SubmitField('注册')
    
    def validate_username(self, field):
        """验证用户名格式和唯一性"""
        username = field.data.strip()
        role = self.role.data
        
        # 格式验证
        if not DatabaseManager.validate_username_format(username, role):
            if role == 'student':
                raise ValidationError('学号必须是13位数字')
            else:
                raise ValidationError('工号必须是8位数字')
        
        # 唯一性检查
        if DatabaseManager.check_username_exists(username):
            raise ValidationError('该学号/工号已存在')
    
    def validate_confirm_password(self, field):
        """验证两次输入的密码是否一致"""
        if field.data != self.password.data:
            raise ValidationError('两次输入的密码不一致')

class ImportForm(FlaskForm):
    """导入表单"""
    file = FileField('Excel文件', validators=[FileRequired()])
    submit = SubmitField('导入')

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        
        user = DatabaseManager.get_user_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('用户名或密码错误！', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = DatabaseManager.create_user(
                username=form.username.data.strip(),
                password=form.password.data,
                name=form.name.data.strip(),
                email=form.email.data.strip(),
                role=form.role.data
            )
            
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'注册失败: {str(e)}', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录。', 'info')
    return redirect(url_for('index'))


# 注意：User类需实现如下属性/方法以兼容Flask-Login：
# @property
# def is_active(self):
#     return True
# @property
# def is_authenticated(self):
#     return True
# @property
# def is_anonymous(self):
#     return False
# def get_id(self):
#     return str(self.id)

@app.route('/admin/import', methods=['GET', 'POST'])
@login_required
def admin_import():
    """批量导入页面"""
    # 权限检查
    if not current_user.has_permission('batch_import'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ImportForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        if file and UserImportManager.allowed_file(file.filename):
            try:
                # 保存文件
                filepath = UserImportManager.save_uploaded_file(file)
                
                # 处理Excel文件
                result = UserImportManager.process_excel_file(filepath)
                
                if not result['success']:
                    flash(result['message'], 'danger')
                    return render_template('import.html', form=form)
                
                # 导入用户
                import_result = UserImportManager.import_users(
                    data=result['data'],
                    import_by=current_user.username
                )
                
                if import_result['success']:
                    flash(import_result['message'], 'success')
                    
                    # 保存详细报告到session供下载
                    session['import_report'] = import_result['detailed_report']
                    session['import_summary'] = {
                        'success': import_result['success_count'],
                        'failed': import_result['failed_count'],
                        'duplicate': import_result['duplicate_count'],
                        'total': result['total_records']
                    }
                    
                    return redirect(url_for('import_report'))
                else:
                    flash(import_result['message'], 'danger')
                    
            except Exception as e:
                flash(f'导入失败: {str(e)}', 'danger')
        else:
            flash('请上传Excel文件（.xlsx或.xls格式）', 'danger')
    
    return render_template('import.html', form=form)

@app.route('/admin/import/template')
@login_required
def download_template():
    """下载导入模板"""
    # 权限检查
    if not current_user.has_permission('batch_import'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    df = UserImportManager.generate_import_template()
    
    # 保存到临时文件
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'import_template.xlsx')
    df.to_excel(template_path, index=False)
    
    # 发送文件
    from flask import send_file
    return send_file(template_path, 
                    as_attachment=True, 
                    download_name='用户导入模板.xlsx')

@app.route('/admin/import/report')
@login_required
def import_report():
    """导入报告页面"""
    # 权限检查
    if not current_user.has_permission('batch_import'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    report = session.get('import_report', [])
    summary = session.get('import_summary', {})
    
    return render_template('import_report.html', 
                         report=report, 
                         summary=summary)

@app.route('/admin/users')
@login_required
def user_management():
    """用户管理页面"""
    # 权限检查
    if not current_user.has_permission('user_manage'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    users = DatabaseManager.get_all_users()
    return render_template('user_management.html', users=users)

@app.route('/admin/logs')
@login_required
def import_logs():
    """导入日志页面"""
    # 权限检查
    if not current_user.has_permission('view_logs'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    logs = DatabaseManager.get_import_logs()
    return render_template('import_logs.html', logs=logs)

@app.route('/profile')
@login_required
def profile():
    """个人资料页面"""
    return render_template('profile.html', user=current_user)

@app.route('/api/check_username/<username>/<role>')
def check_username(username, role):
    """检查用户名API"""
    # 格式验证
    is_valid_format = DatabaseManager.validate_username_format(username, role)
    
    # 唯一性检查
    exists = DatabaseManager.check_username_exists(username)
    
    return jsonify({
        'valid_format': is_valid_format,
        'exists': exists,
        'valid': is_valid_format and not exists
    })

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# 模板过滤器
@app.template_filter('role_name')
def role_name_filter(role):
    """角色名称过滤器"""
    role_names = {
        'student': '学生',
        'teacher': '教师',
        'admin': '管理员'
    }
    return role_names.get(role, role)

@app.template_filter('status_color')
def status_color_filter(status):
    """状态颜色过滤器"""
    colors = {
        'success': 'success',
        'failed': 'danger',
        'duplicate': 'warning',
        'pending': 'secondary'
    }
    return colors.get(status, 'secondary')




#新增


# 导入新模块
from file_validator import FileValidator
from file_upload import FileUploadManager
import os

# 更新应用配置
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 创建新的表单类
class FileUploadForm(FlaskForm):
    """文件上传表单"""
    file = FileField('选择文件', validators=[
        FileRequired(message='请选择要上传的文件')
    ])
    description = StringField('文件描述', validators=[
        Length(max=500, message='描述不能超过500个字符')
    ])
    submit = SubmitField('上传')

# 添加新的路由
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """文件上传页面"""
    form = FileUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        description = form.description.data
        
        # 验证文件类型
        if not FileValidator.allowed_file(file.filename):
            flash('不支持的文件类型。只允许上传PDF、JPG、PNG、JPEG格式。', 'danger')
            return render_template('upload.html', form=form)
        
        # 保存文件
        file_record, errors = FileUploadManager.save_uploaded_file(
            file, current_user.id, description
        )
        
        if file_record:
            flash(f'文件"{file_record.original_filename}"上传成功！', 'success')
            return redirect(url_for('my_files'))
        else:
            for error in errors:
                flash(error, 'danger')
    
    return render_template('upload.html', form=form)

@app.route('/files')
@login_required
def my_files():
    """我的文件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    files_pagination = DatabaseManager.get_user_files(current_user.id, page, per_page)
    
    # 获取文件统计
    stats = FileUploadManager.get_user_files_summary(current_user.id)
    
    return render_template('files_list.html', 
                         files=files_pagination.items,
                         pagination=files_pagination,
                         stats=stats)

@app.route('/file/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """删除文件"""
    success, message = FileUploadManager.delete_file(file_id, current_user.id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('my_files'))

@app.route('/file/download/<int:file_id>')
@login_required
def download_file(file_id):
    """下载文件"""
    from flask import send_file
    
    file_path, error = FileUploadManager.get_file_path(file_id, current_user.id)
    
    if error:
        flash(error, 'danger')
        return redirect(url_for('my_files'))
    
    file_record = DatabaseManager.get_file_by_id(file_id, current_user.id)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_record.original_filename
    )


def _get_serializer():
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='file-share')


def _is_port_open(host, port, timeout=0.5):
    try:
        port = int(port)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _start_streamlit_if_needed(streamlit_addr, timeout=20):
    """如果 streamlit 地址的端口不可用，则在后台启动 Streamlit，并等待直到可用或超时。

    返回 True 表示端口可用（已运行或已成功启动），False 表示超时或启动失败。
    """
    parsed = urlparse(streamlit_addr)
    host = parsed.hostname or '127.0.0.1'
    port = parsed.port or 8501

    if _is_port_open(host, port):
        return True

    # 尝试在项目目录启动 Streamlit
    preview_script = os.path.join(os.path.dirname(__file__), 'preview_demo.py')
    cmd = [sys.executable, '-m', 'streamlit', 'run', preview_script, f'--server.address={host}', f'--server.port={port}']
    try:
        # 启动子进程，不等待其结束
        subprocess.Popen(cmd, cwd=os.path.dirname(__file__), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return False

    # 等待端口就绪
    waited = 0.0
    interval = 0.5
    while waited < timeout:
        if _is_port_open(host, port):
            return True
        time.sleep(interval)
        waited += interval

    return False


@app.route('/streamlit/status')
def streamlit_status():
    """返回 Streamlit 服务状态（是否可用）"""
    streamlit_addr = os.environ.get('STREAMLIT_HOST', 'http://127.0.0.1:8501')
    parsed = urlparse(streamlit_addr)
    host = parsed.hostname or '127.0.0.1'
    port = parsed.port or 8501
    ready = _is_port_open(host, port)
    return jsonify({'ready': ready, 'streamlit_addr': streamlit_addr})


@app.route('/file/shared/<token>')
def shared_file(token):
    """通过 token 分享文件（无需登录），token 有时间限制。"""
    s = _get_serializer()
    try:
        data = s.loads(token, max_age=300)  # 5分钟
        file_id = int(data.get('file_id'))
    except SignatureExpired:
        return '链接已过期', 410
    except (BadSignature, Exception):
        return '无效的链接', 400

    # 直接从数据库中查找文件记录，不需要用户上下文
    file_record = DatabaseManager.get_file_by_id(file_id)
    if not file_record:
        return '文件不存在', 404

    # 返回文件，不作为 attachment 以便内联展示
    from flask import send_file
    if not os.path.exists(file_record.file_path):
        return '文件不存在', 404

    return send_file(file_record.file_path, as_attachment=False, mimetype=file_record.file_type)


@app.route('/file/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    """为前端（Flask）生成跳转到 Streamlit 的链接，使用短期 token 分享文件。
    用户点击后会被重定向到本机 Streamlit，query 参数为 file_url。
    """
    # 检查是否有草稿证书关联此文件
    cert_id = request.args.get('cert_id', None)
    
    # 权限检查：只能预览自己的文件或有管理权限
    file_record = DatabaseManager.get_file_by_id(file_id, current_user.id)
    if not file_record:
        # 若不是本人，检查管理员权限
        if not current_user.has_permission('manage_all_files'):
            flash('无权预览该文件', 'danger')
            return redirect(url_for('my_files'))
        # 管理员查找不限定用户
        file_record = DatabaseManager.get_file_by_id(file_id)
        if not file_record:
            flash('文件不存在', 'danger')
            return redirect(url_for('my_files'))

    s = _get_serializer()
    token = s.dumps({'file_id': file_id})

    # 构建可以被 Streamlit 访问的共享 URL
    shared_url = url_for('shared_file', token=token, _external=True)

    # 将用户重定向到 Streamlit，本接口会在需要时自动尝试后台启动 Streamlit
    streamlit_addr = os.environ.get('STREAMLIT_HOST', 'http://127.0.0.1:8501')

    # 将共享链接保存到 session
    session['last_shared_file_url'] = shared_url

    parsed = urlparse(streamlit_addr)
    host = parsed.hostname or '127.0.0.1'
    port = parsed.port or 8501

    # 确定提交者角色
    submitter_role = current_user.role if current_user.role in ['student', 'teacher'] else 'student'

    # 构建跳转URL
    params = f"file_url={quote(shared_url, safe='')}&file_id={file_id}&user_id={current_user.id}&role={submitter_role}"
    if cert_id:
        params += f"&cert_id={cert_id}"

    # 如果 Streamlit 已经运行，直接带参数跳转
    if _is_port_open(host, port):
        target = f"{streamlit_addr}/?{params}"
        return redirect(target)

    # 否则在后台启动 Streamlit（非阻塞）并展示等待页面，页面会轮询 /streamlit/status
    # 使用新的证书处理应用
    preview_script = os.path.join(os.path.dirname(__file__), 'certificate_processor.py')
    cmd = [sys.executable, '-m', 'streamlit', 'run', preview_script, f'--server.address={host}', f'--server.port={port}']
    try:
        subprocess.Popen(cmd, cwd=os.path.dirname(__file__), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # 启动失败则回退到直接跳转（可能会失败）
        target = f"{streamlit_addr}/?{params}"
        return redirect(target)

    return render_template('streamlit_wait.html', streamlit_addr=streamlit_addr, shared_url=shared_url)

@app.route('/file/view/<int:file_id>')
@login_required
def view_file(file_id):
    """查看文件详情"""
    file_record = DatabaseManager.get_file_by_id(file_id, current_user.id)
    
    if not file_record:
        flash('文件不存在或无权访问', 'danger')
        return redirect(url_for('my_files'))
    
    # 检查文件是否存在
    if not os.path.exists(file_record.file_path):
        flash('文件不存在或已被删除', 'danger')
        return redirect(url_for('my_files'))
    
    return render_template('file_detail.html', file=file_record)

# 更新仪表板路由，添加文件统计
@app.route('/dashboard')
@login_required
def dashboard():
    """仪表板"""
    permissions = current_user.get_permissions()
    
    # 获取用户文件统计
    stats = FileUploadManager.get_user_files_summary(current_user.id)
    
    # 获取用户证书统计
    from database import Certificate
    cert_stats = {
        'total_submitted': Certificate.query.filter_by(submitter_id=current_user.id, status='submitted').count(),
        'total_draft': Certificate.query.filter_by(submitter_id=current_user.id, status='draft').count(),
        'total': Certificate.query.filter_by(submitter_id=current_user.id).count()
    }
    
    return render_template('dashboard.html', 
                         user=current_user, 
                         permissions=permissions,
                         stats=stats,
                         cert_stats=cert_stats)

# 管理员查看所有文件
@app.route('/admin/all-files')
@login_required
def admin_all_files():
    """管理员查看所有文件"""
    if not current_user.has_permission('manage_all_files'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取所有文件（分页）
    files = File.query.filter_by(status='active') \
                     .order_by(File.upload_time.desc()) \
                     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_files.html', files=files)

# 证书相关路由
@app.route('/certificates')
@login_required
def my_certificates():
    """我的证书列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None)
    per_page = 10
    
    certificates = DatabaseManager.get_user_certificates(
        current_user.id, 
        status=status, 
        page=page, 
        per_page=per_page
    )
    
    return render_template('certificates_list.html', 
                         certificates=certificates.items,
                         pagination=certificates,
                         status=status)

@app.route('/certificate/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    """查看证书详情"""
    cert = DatabaseManager.get_certificate_by_id(cert_id, current_user.id)
    
    if not cert:
        # 管理员可以查看所有证书
        if current_user.has_permission('view_all_users'):
            cert = DatabaseManager.get_certificate_by_id(cert_id)
        else:
            flash('证书不存在或无权访问', 'danger')
            return redirect(url_for('my_certificates'))
    
    return render_template('certificate_detail.html', certificate=cert)

@app.route('/certificate/<int:cert_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_certificate(cert_id):
    """编辑证书（仅草稿状态）"""
    cert = DatabaseManager.get_certificate_by_id(cert_id, current_user.id)
    
    if not cert:
        flash('证书不存在或无权修改', 'danger')
        return redirect(url_for('my_certificates'))
    
    if cert.status == 'submitted':
        flash('已提交的证书不能修改', 'danger')
        return redirect(url_for('view_certificate', cert_id=cert_id))
    
    if request.method == 'POST':
        # 处理表单提交
        form_data = {
            'student_id': request.form.get('student_id'),
            'student_name': request.form.get('student_name'),
            'department': request.form.get('department'),
            'competition_name': request.form.get('competition_name'),
            'award_category': request.form.get('award_category'),
            'award_level': request.form.get('award_level'),
            'competition_type': request.form.get('competition_type'),
            'organizer': request.form.get('organizer'),
            'advisor': request.form.get('advisor'),
        }
        
        # 处理日期
        award_date_str = request.form.get('award_date')
        if award_date_str:
            try:
                form_data['award_date'] = datetime.strptime(award_date_str, '%Y-%m-%d').date()
            except:
                form_data['award_date'] = None
        else:
            form_data['award_date'] = None
        
        success, message = DatabaseManager.update_certificate(cert_id, current_user.id, **form_data)
        
        if success:
            flash('更新成功', 'success')
            return redirect(url_for('view_certificate', cert_id=cert_id))
        else:
            flash(message, 'danger')
    
    return render_template('certificate_edit.html', certificate=cert)

@app.route('/certificate/<int:cert_id>/submit', methods=['POST'])
@login_required
def submit_certificate(cert_id):
    """提交证书"""
    success, message = DatabaseManager.submit_certificate(cert_id, current_user.id)
    
    if success:
        flash('提交成功', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('view_certificate', cert_id=cert_id))

# 管理员证书管理
@app.route('/admin/certificates')
@login_required
def admin_certificates():
    """管理员查看所有证书"""
    if not current_user.has_permission('view_all_users'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None)
    submitter_role = request.args.get('role', None)
    per_page = 20
    
    certificates = DatabaseManager.get_all_certificates(
        status=status,
        submitter_role=submitter_role,
        page=page,
        per_page=per_page
    )
    
    # 统计信息
    total_submitted = Certificate.query.filter_by(status='submitted').count()
    total_draft = Certificate.query.filter_by(status='draft').count()
    total_student = Certificate.query.filter_by(submitter_role='student', status='submitted').count()
    total_teacher = Certificate.query.filter_by(submitter_role='teacher', status='submitted').count()
    
    stats = {
        'total_submitted': total_submitted,
        'total_draft': total_draft,
        'total_student': total_student,
        'total_teacher': total_teacher
    }
    
    return render_template('admin_certificates.html',
                         certificates=certificates.items,
                         pagination=certificates,
                         status=status,
                         submitter_role=submitter_role,
                         stats=stats)

@app.route('/admin/certificates/export')
@login_required
def admin_export_certificates():
    """管理员导出证书数据"""
    if not current_user.has_permission('export_data'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    export_format = request.args.get('format', 'excel')  # excel, csv, json
    status = request.args.get('status', 'submitted')  # submitted, draft, all
    include_extra = request.args.get('extra', 'true') == 'true'
    
    try:
        from data_export import export_to_excel, export_to_csv, export_to_json
        
        if export_format == 'excel':
            filepath = export_to_excel(status=status, include_extra_fields=include_extra)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            download_name = f'证书导出_{status}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        elif export_format == 'csv':
            filepath = export_to_csv(status=status, include_extra_fields=include_extra)
            mimetype = 'text/csv'
            download_name = f'证书导出_{status}_{datetime.now().strftime("%Y%m%d")}.csv'
        elif export_format == 'json':
            filepath = export_to_json(status=status)
            mimetype = 'application/json'
            download_name = f'证书导出_{status}_{datetime.now().strftime("%Y%m%d")}.json'
        else:
            flash('不支持的导出格式', 'danger')
            return redirect(url_for('admin_certificates'))
        
        from flask import send_file
        return send_file(
            filepath,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
    except Exception as e:
        flash(f'导出失败: {str(e)}', 'danger')
        return redirect(url_for('admin_certificates'))

@app.route('/admin/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    """系统配置管理"""
    if not current_user.has_permission('system_settings'):
        flash('您没有权限访问此页面。', 'danger')
        return redirect(url_for('dashboard'))
    
    from database import SystemConfig
    
    if request.method == 'POST':
        # 更新截止时间
        deadline = request.form.get('deadline')
        if deadline:
            try:
                # 验证日期格式
                datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
                SystemConfig.set_config(
                    'submission_deadline',
                    deadline,
                    '证书提交截止时间',
                    current_user.id
                )
                flash('截止时间更新成功', 'success')
            except ValueError:
                flash('日期格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式', 'danger')
        
        # 更新默认API
        default_api = request.form.get('default_api')
        if default_api:
            SystemConfig.set_config(
                'default_extraction_api',
                default_api,
                '默认信息提取API',
                current_user.id
            )
            flash('默认API更新成功', 'success')
        
        return redirect(url_for('admin_config'))
    
    # 获取当前配置
    deadline = SystemConfig.get_config('submission_deadline', '2025-12-30 23:59:59')
    default_api = SystemConfig.get_config('default_extraction_api', 'glm4v')
    
    return render_template('admin_config.html',
                         deadline=deadline,
                         default_api=default_api)

if __name__ == '__main__':
    with app.app_context():
        # ============ 修改数据库初始化 ============
        try:
            # 先检查数据库文件是否存在
            db_file = os.path.join(basedir, "user_auth_system.db")
            if not os.path.exists(db_file):
                print("初始化数据库...")
                from init_sqlite_db import init_sqlite_database
                init_sqlite_database()
            
            # 创建所有表（如果不存在）
            db.create_all()
            print("数据库初始化完成")
        except Exception as e:
            print(f"数据库初始化错误: {e}")
            # 继续运行，让用户界面仍然可以访问
    
    app.run(debug=True, port=5000)

