"""
文件上传处理模块
"""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from database import db, File
from file_validator import FileValidator

class FileUploadManager:
    """文件上传管理器"""
    
    @staticmethod
    def save_uploaded_file(file, user_id, description=None):
        """保存上传的文件并记录到数据库"""
        from database import DatabaseManager
        
        # 验证文件
        is_valid, errors = FileValidator.validate_file(file)
        if not is_valid:
            return None, errors
        
        try:
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            
            # 构建保存路径
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            user_folder = os.path.join(upload_folder, str(user_id))
            
            # 创建用户目录
            os.makedirs(user_folder, exist_ok=True)
            
            # 完整文件路径
            file_path = os.path.join(user_folder, unique_filename)
            
            # 保存文件
            file.save(file_path)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 获取文件类型
            file_type = FileValidator.get_file_type(original_filename)
            
            # 保存到数据库
            file_record, error = DatabaseManager.add_file(
                user_id=user_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                description=description
            )
            
            if error:
                # 如果数据库保存失败，删除物理文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                return None, [error]
            
            return file_record, []
            
        except Exception as e:
            current_app.logger.error(f"文件上传失败: {str(e)}")
            return None, [f"文件上传失败: {str(e)}"]
    
    @staticmethod
    def delete_file(file_id, user_id):
        """删除文件（物理文件和数据库记录）"""
        from database import DatabaseManager
        
        try:
            # 获取文件记录
            file_record = DatabaseManager.get_file_by_id(file_id, user_id)
            if not file_record:
                return False, "文件不存在或无权删除"
            
            # 删除物理文件
            if os.path.exists(file_record.file_path):
                try:
                    os.remove(file_record.file_path)
                except Exception as e:
                    current_app.logger.error(f"删除物理文件失败: {str(e)}")
            
            # 标记数据库记录为已删除
            success, message = DatabaseManager.delete_file(file_id, user_id)
            return success, message
            
        except Exception as e:
            current_app.logger.error(f"删除文件失败: {str(e)}")
            return False, f"删除文件失败: {str(e)}"
    
    @staticmethod
    def get_file_path(file_id, user_id):
        """获取文件路径"""
        from database import DatabaseManager
        
        file_record = DatabaseManager.get_file_by_id(file_id, user_id)
        if not file_record:
            return None, "文件不存在或无权访问"
        
        if not os.path.exists(file_record.file_path):
            return None, "文件不存在"
        
        return file_record.file_path, None
    
    @staticmethod
    def get_user_files_summary(user_id):
        """获取用户文件统计摘要"""
        from database import DatabaseManager
        
        stats = DatabaseManager.get_file_stats(user_id)
        
        # 格式化总大小
        total_size = stats['total_size']
        formatted_size = FileUploadManager.format_file_size(total_size)
        
        return {
            'total_files': stats['total_files'],
            'total_size': total_size,
            'formatted_total_size': formatted_size,
            'recent_files': stats['recent_files']
        }
    
    @staticmethod
    def format_file_size(size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.2f} {size_names[i]}"