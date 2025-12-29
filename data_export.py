"""
数据导出模块 - 从数据库导出证书信息
支持CSV和Excel格式导出
"""
import csv
import os
from datetime import datetime
import pandas as pd
from database import db, Certificate, DatabaseManager

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# 字段映射（数据库字段 -> 导出字段名）
FIELD_MAPPING = {
    'department': '学生所在学院',
    'competition_name': '竞赛项目',
    'student_id': '学号',
    'student_name': '学生姓名',
    'award_category': '获奖类别',
    'award_level': '获奖等级',
    'competition_type': '竞赛类型',
    'organizer': '主办单位',
    'award_date': '获奖时间',
    'advisor': '指导教师',
    'submitter_role': '提交者角色',
    'submitter_id': '提交者ID',
    'created_at': '创建时间',
    'submitted_at': '提交时间',
    'extraction_method': '识别方式',
    'extraction_confidence': '识别置信度'
}

EXPORT_FIELDS = [
    '学生所在学院', '竞赛项目', '学号', '学生姓名', '获奖类别',
    '获奖等级', '竞赛类型', '主办单位', '获奖时间', '指导教师',
    '提交者角色', '创建时间', '提交时间', '识别方式', '识别置信度'
]

def export_to_csv(status='submitted', include_extra_fields=True):
    """
    导出为CSV格式
    
    Args:
        status: 导出状态（'submitted'或'draft'或'all'）
        include_extra_fields: 是否包含额外字段（提交者、时间等）
    
    Returns:
        str: 导出文件路径
    """
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Zhengxue111@localhost/user_auth_system'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # 获取证书数据
        if status == 'all':
            certs = Certificate.query.all()
        else:
            certs = Certificate.query.filter_by(status=status).all()
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"certificates_export_{status}_{timestamp}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # 准备字段
        if include_extra_fields:
            fieldnames = EXPORT_FIELDS
        else:
            fieldnames = EXPORT_FIELDS[:10]  # 只包含基本信息
        
        # 写入CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for cert in certs:
                cert_dict = cert.to_dict()
                row = {}
                
                for db_field, export_field in FIELD_MAPPING.items():
                    if export_field in fieldnames:
                        value = cert_dict.get(db_field, '')
                        # 格式化日期
                        if 'date' in db_field or 'time' in db_field:
                            if value:
                                if isinstance(value, str):
                                    row[export_field] = value
                                else:
                                    row[export_field] = value
                            else:
                                row[export_field] = ''
                        else:
                            row[export_field] = str(value) if value else ''
                
                writer.writerow(row)
        
        return filepath

def export_to_excel(status='submitted', include_extra_fields=True):
    """
    导出为Excel格式
    
    Args:
        status: 导出状态（'submitted'或'draft'或'all'）
        include_extra_fields: 是否包含额外字段
    
    Returns:
        str: 导出文件路径
    """
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Zhengxue111@localhost/user_auth_system'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # 获取证书数据
        if status == 'all':
            certs = Certificate.query.all()
        else:
            certs = Certificate.query.filter_by(status=status).all()
        
        # 准备数据
        data = []
        for cert in certs:
            cert_dict = cert.to_dict()
            row = {}
            
            # 准备字段
            if include_extra_fields:
                fields_to_export = EXPORT_FIELDS
            else:
                fields_to_export = EXPORT_FIELDS[:10]
            
            for db_field, export_field in FIELD_MAPPING.items():
                if export_field in fields_to_export:
                    value = cert_dict.get(db_field, '')
                    # 格式化日期
                    if 'date' in db_field or 'time' in db_field:
                        row[export_field] = value if value else ''
                    else:
                        row[export_field] = str(value) if value else ''
            
            data.append(row)
        
        # 创建DataFrame
        df = pd.DataFrame(data, columns=fields_to_export if include_extra_fields else EXPORT_FIELDS[:10])
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"certificates_export_{status}_{timestamp}.xlsx"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # 导出到Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        return filepath

def export_to_json(status='submitted'):
    """
    导出为JSON格式
    
    Args:
        status: 导出状态
    
    Returns:
        str: 导出文件路径
    """
    from flask import Flask
    import json
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Zhengxue111@localhost/user_auth_system'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # 获取证书数据
        if status == 'all':
            certs = Certificate.query.all()
        else:
            certs = Certificate.query.filter_by(status=status).all()
        
        # 转换为字典列表
        data = [cert.to_dict() for cert in certs]
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"certificates_export_{status}_{timestamp}.json"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        # 写入JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath

if __name__ == "__main__":
    print("CSV导出路径:", export_to_csv())
    print("Excel导出路径:", export_to_excel())
    print("JSON导出路径:", export_to_json())
