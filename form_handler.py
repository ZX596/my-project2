"""
表单处理模块 - 使用JSON文件存储
实现草稿保存和批量提交功能
"""
import json
import os
from datetime import datetime

DATA_DIR = "form_data"
DRAFT_FILE = os.path.join(DATA_DIR, "drafts.json")
SUBMIT_FILE = os.path.join(DATA_DIR, "submitted.json")
DEADLINE = "2025-12-30 18:31:00"  # 截止时间

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path):
    """加载JSON文件"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_json(path, data):
    """保存JSON文件"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"保存文件失败: {e}")
        return False

def is_before_deadline():
    """检查是否在截止时间之前"""
    try:
        now = datetime.now()
        deadline = datetime.strptime(DEADLINE, "%Y-%m-%d %H:%M:%S")
        return now <= deadline
    except Exception as e:
        print(f"检查截止时间失败: {e}")
        return True  # 默认允许提交

def save_draft(user_id, form_data):
    """
    保存草稿到drafts.json
    
    Args:
        user_id: 用户ID（学号）
        form_data: 表单数据字典
    
    Returns:
        tuple: (success, message)
    """
    try:
        drafts = load_json(DRAFT_FILE)
        
        # 保存草稿数据
        drafts[user_id] = {
            "data": form_data,
            "status": "draft",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().isoformat()
        }
        
        if save_json(DRAFT_FILE, drafts):
            return True, "草稿保存成功"
        else:
            return False, "保存草稿失败"
    except Exception as e:
        return False, f"保存草稿时出错: {str(e)}"

def submit_form(user_id, form_data):
    """
    批量提交表单到submitted.json
    提交后数据不可修改
    
    Args:
        user_id: 用户ID（学号）
        form_data: 表单数据字典
    
    Returns:
        tuple: (success, message)
    """
    # 检查截止时间
    if not is_before_deadline():
        deadline_str = DEADLINE
        return False, f"已超过截止时间 ({deadline_str})，无法提交。"
    
    try:
        submitted = load_json(SUBMIT_FILE)
        
        # 检查是否已提交
        if user_id in submitted:
            return False, "您已经提交过，无法重复提交。"
        
        # 验证必填字段
        required_fields = ["学号", "学生姓名", "指导教师"]
        missing_fields = [field for field in required_fields if not form_data.get(field, "").strip()]
        if missing_fields:
            return False, f"必填字段不能为空: {', '.join(missing_fields)}"
        
        # 验证学号格式
        student_id = form_data.get("学号", "").strip()
        if student_id and len(student_id) != 13:
            return False, "学号必须是13位数字"
        
        # 保存提交数据
        submitted[user_id] = {
            "data": form_data,
            "status": "submitted",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "submitted_at": datetime.now().isoformat()
        }
        
        # 删除对应的草稿
        drafts = load_json(DRAFT_FILE)
        if user_id in drafts:
            del drafts[user_id]
            save_json(DRAFT_FILE, drafts)
        
        if save_json(SUBMIT_FILE, submitted):
            return True, "提交成功！数据已保存，无法修改。"
        else:
            return False, "提交失败"
    except Exception as e:
        return False, f"提交时出错: {str(e)}"

def get_user_draft(user_id):
    """
    获取用户的草稿
    
    Args:
        user_id: 用户ID（学号）
    
    Returns:
        dict: 草稿数据，如果没有则返回None
    """
    try:
        drafts = load_json(DRAFT_FILE)
        draft = drafts.get(user_id)
        if draft:
            return draft.get("data", {})
        return None
    except Exception as e:
        print(f"获取草稿时出错: {str(e)}")
        return None

def get_user_submission(user_id):
    """
    获取用户的提交记录
    
    Args:
        user_id: 用户ID（学号）
    
    Returns:
        dict: 提交数据，如果没有则返回None
    """
    try:
        submitted = load_json(SUBMIT_FILE)
        submission = submitted.get(user_id)
        if submission:
            return submission.get("data", {})
        return None
    except Exception as e:
        print(f"获取提交记录时出错: {str(e)}")
        return None

def get_all_submissions():
    """
    获取所有提交记录（管理员功能）
    
    Returns:
        dict: 所有提交记录，格式为 {user_id: {data: {...}, status: "submitted", ...}}
    """
    try:
        return load_json(SUBMIT_FILE)
    except Exception as e:
        print(f"获取所有提交记录时出错: {str(e)}")
        return {}

def get_all_drafts():
    """
    获取所有草稿（管理员功能）
    
    Returns:
        dict: 所有草稿记录
    """
    try:
        return load_json(DRAFT_FILE)
    except Exception as e:
        print(f"获取所有草稿时出错: {str(e)}")
        return {}

def get_deadline():
    """获取截止时间"""
    return DEADLINE

def get_deadline_datetime():
    """获取截止时间（datetime对象）"""
    try:
        return datetime.strptime(DEADLINE, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.strptime("2025-12-30 18:31:00", "%Y-%m-%d %H:%M:%S")
