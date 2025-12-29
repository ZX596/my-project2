"""
用户批量导入模块
处理Excel文件导入用户信息
"""
import pandas as pd
import json
import traceback
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from flask import current_app
from database import db, DatabaseManager, User
import bcrypt

class UserImportManager:
    """用户导入管理器"""
    
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    @staticmethod
    def allowed_file(filename):
        """检查文件扩展名"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in UserImportManager.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_user_data(row, index):
        """验证单行用户数据"""
        errors = []
        
        # 必填字段检查
        required_fields = ['username', 'name', 'role']
        for field in required_fields:
            if pd.isna(row.get(field, '')) or str(row[field]).strip() == '':
                errors.append(f"{field}不能为空")
        
        if errors:
            return False, errors
        
        username = str(row['username']).strip()
        name = str(row['name']).strip()
        role = str(row['role']).strip().lower()
        email = str(row['email']).strip() if not pd.isna(row.get('email', '')) else ''
        
        # 角色验证
        if role not in ['student', 'teacher', 'admin']:
            errors.append(f"角色必须是student、teacher或admin，当前为: {role}")
        
        # 用户名格式验证
        if not DatabaseManager.validate_username_format(username, role):
            if role == 'student':
                errors.append("学号必须是13位数字")
            else:
                errors.append("工号必须是8位数字")
        
        # 用户名唯一性检查
        if DatabaseManager.check_username_exists(username):
            errors.append("用户名已存在")
        
        # 邮箱格式验证（可选）
        if email and '@' not in email:
            errors.append("邮箱格式不正确")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def process_excel_file(filepath):
        """处理Excel文件"""
        try:
            # 读取Excel文件
            df = pd.read_excel(filepath, dtype=str)
            
            # 检查必要的列
            required_columns = ['username', 'name', 'role']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f"缺少必要的列: {', '.join(missing_columns)}",
                    'data': None
                }
            
            # 处理数据
            processed_data = []
            for idx, row in df.iterrows():
                # 转换为字典并处理NaN值
                row_data = row.to_dict()
                row_data = {k: ('' if pd.isna(v) else str(v).strip()) for k, v in row_data.items()}
                
                # 验证数据
                is_valid, errors = UserImportManager.validate_user_data(row_data, idx + 2)
                
                processed_data.append({
                    'row_number': idx + 2,  # Excel行号（从2开始）
                    'data': row_data,
                    'is_valid': is_valid,
                    'errors': errors,
                    'status': 'pending',  # pending, success, failed, duplicate
                    'message': ''
                })
            
            return {
                'success': True,
                'message': '文件解析成功',
                'data': processed_data,
                'total_records': len(processed_data)
            }
            
        except Exception as e:
            current_app.logger.error(f"处理Excel文件失败: {str(e)}")
            return {
                'success': False,
                'message': f"处理Excel文件失败: {str(e)}",
                'data': None
            }
    
    @staticmethod
    def import_users(data, import_by):
        """导入用户数据"""
        success_count = 0
        failed_count = 0
        duplicate_count = 0
        detailed_report = []
        
        for item in data:
            row_number = item['row_number']
            row_data = item['data']
            
            # 如果数据无效，记录失败
            if not item['is_valid']:
                item['status'] = 'failed'
                item['message'] = '; '.join(item['errors'])
                failed_count += 1
                detailed_report.append(item.copy())
                continue
            
            username = row_data['username']
            name = row_data['name']
            role = row_data['role'].lower()
            email = row_data.get('email', '') or f"{username}@edu.cn"
            
            # 再次检查用户名是否已存在
            if DatabaseManager.check_username_exists(username):
                item['status'] = 'duplicate'
                item['message'] = '用户名已存在'
                duplicate_count += 1
                detailed_report.append(item.copy())
                continue
            
            try:
                # 创建用户（默认密码为123456）
                default_password = '123456'
                hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
                
                user = User(
                    username=username,
                    password=hashed_password.decode('utf-8'),
                    name=name,
                    email=email,
                    role=role
                )
                
                db.session.add(user)
                
                item['status'] = 'success'
                item['message'] = '导入成功'
                success_count += 1
                detailed_report.append(item.copy())
                
            except Exception as e:
                db.session.rollback()
                item['status'] = 'failed'
                item['message'] = f"数据库错误: {str(e)}"
                failed_count += 1
                detailed_report.append(item.copy())
        
        # 提交所有更改
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"提交数据库更改失败: {str(e)}")
            return {
                'success': False,
                'message': f"提交数据库更改失败: {str(e)}",
                'success_count': 0,
                'failed_count': len(data),
                'duplicate_count': 0,
                'detailed_report': detailed_report
            }
        
        # 保存导入日志
        try:
            DatabaseManager.save_import_log(
                filename='import.xlsx',
                import_by=import_by,
                total_records=len(data),
                success_count=success_count,
                failed_count=failed_count,
                duplicate_count=duplicate_count,
                report_data=detailed_report
            )
        except Exception as e:
            current_app.logger.error(f"保存导入日志失败: {str(e)}")
        
        return {
            'success': True,
            'message': f'导入完成。成功: {success_count}, 失败: {failed_count}, 重复: {duplicate_count}',
            'success_count': success_count,
            'failed_count': failed_count,
            'duplicate_count': duplicate_count,
            'detailed_report': detailed_report
        }
    
    @staticmethod
    def generate_import_template():
        """生成导入模板"""
        template_data = [
            {
                'username': '2023000000016',
                'name': '测试学生',
                'email': 'test_student@edu.cn',
                'role': 'student'
            },
            {
                'username': '20000006',
                'name': '测试教师',
                'email': 'test_teacher@edu.cn',
                'role': 'teacher'
            },
            {
                'username': '10000003',
                'name': '测试管理员',
                'email': 'test_admin@edu.cn',
                'role': 'admin'
            }
        ]
        
        df = pd.DataFrame(template_data)
        return df
    
    @staticmethod
    def save_uploaded_file(file):
        """保存上传的文件"""
        if file and UserImportManager.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            return filepath
        
        return None