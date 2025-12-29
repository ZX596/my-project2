"""
文件验证模块
"""
import os
from werkzeug.utils import secure_filename
from flask import current_app

class FileValidator:
    """文件验证器"""
    
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }
    
    # 最大文件大小：10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    @classmethod
    def allowed_file(cls, filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def validate_file(cls, file):
        """验证文件"""
        errors = []
        
        # 检查文件是否存在
        if not file or file.filename == '':
            errors.append('请选择要上传的文件')
            return False, errors
        
        # 检查文件名安全性
        filename = secure_filename(file.filename)
        if not filename:
            errors.append('文件名无效或包含不支持的字符')
            return False, errors
        
        # 检查文件类型
        if not cls.allowed_file(filename):
            allowed = ', '.join(cls.ALLOWED_EXTENSIONS.keys())
            errors.append(f'不支持的文件类型。只允许: {allowed}')
            return False, errors
        
        # 检查文件大小
        try:
            # 保存文件指针位置
            current_position = file.tell()
            
            # 移动到文件末尾获取大小
            file.seek(0, 2)
            file_size = file.tell()
            
            # 重置文件指针
            file.seek(current_position)
            
            if file_size > cls.MAX_FILE_SIZE:
                size_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
                errors.append(f'文件过大。最大允许 {size_mb}MB')
                return False, errors
            
            if file_size == 0:
                errors.append('文件为空')
                return False, errors
                
        except Exception as e:
            errors.append(f'文件大小检查失败: {str(e)}')
            return False, errors
        
        return True, errors
    
    @classmethod
    def get_file_type(cls, filename):
        """获取文件MIME类型"""
        ext = filename.rsplit('.', 1)[1].lower()
        return cls.ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
    
    @classmethod
    def get_file_extension(cls, filename):
        """获取文件扩展名"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''