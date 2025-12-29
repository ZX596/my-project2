"""
管理员面板模块
管理员可查看所有用户提交的数据，并可导出为CSV和Excel格式
"""
from form_handler import get_all_submissions, get_all_drafts, get_deadline, is_before_deadline
from data_export import export_to_csv, export_to_excel, export_to_json

def view_all_submissions():
    """
    管理员查看所有用户提交的数据
    
    Returns:
        dict: 所有提交记录，格式为 {user_id: {data: {...}, status: "submitted", ...}}
    """
    return get_all_submissions()

def view_all_drafts():
    """
    管理员查看所有草稿
    
    Returns:
        dict: 所有草稿记录
    """
    return get_all_drafts()

def get_submission_stats():
    """
    获取提交统计信息
    
    Returns:
        dict: 统计信息
    """
    submissions = get_all_submissions()
    drafts = get_all_drafts()
    
    return {
        "total_submitted": len(submissions),
        "total_drafts": len(drafts),
        "deadline": get_deadline(),
        "is_before_deadline": is_before_deadline()
    }

def export_submissions_csv(include_extra_fields=True):
    """
    管理员导出数据为CSV
    
    Args:
        include_extra_fields: 是否包含额外字段
    
    Returns:
        str: 导出文件路径
    """
    return export_to_csv(include_extra_fields=include_extra_fields)

def export_submissions_excel(include_extra_fields=True):
    """
    管理员导出数据为Excel
    
    Args:
        include_extra_fields: 是否包含额外字段
    
    Returns:
        str: 导出文件路径
    """
    return export_to_excel(include_extra_fields=include_extra_fields)

def export_submissions_json():
    """
    管理员导出数据为JSON
    
    Returns:
        str: 导出文件路径
    """
    return export_to_json()

if __name__ == "__main__":
    # 示例：打印所有提交数据
    print("=" * 50)
    print("管理员面板 - 查看所有提交数据")
    print("=" * 50)
    
    all_data = view_all_submissions()
    stats = get_submission_stats()
    
    print(f"\n统计信息:")
    print(f"  已提交记录数: {stats['total_submitted']}")
    print(f"  草稿记录数: {stats['total_drafts']}")
    print(f"  截止时间: {stats['deadline']}")
    print(f"  是否在截止时间前: {'是' if stats['is_before_deadline'] else '否'}")
    
    print(f"\n所有提交数据 ({len(all_data)} 条):")
    print("-" * 50)
    for user_id, record in all_data.items():
        print(f"\n用户ID: {user_id}")
        print(f"提交时间: {record.get('timestamp', record.get('submitted_at', 'N/A'))}")
        print("数据:")
        data = record.get("data", {})
        for field, value in data.items():
            print(f"  {field}: {value}")
    
    # 导出
    print("\n" + "=" * 50)
    print("导出数据")
    print("=" * 50)
    print(f"CSV导出路径: {export_submissions_csv()}")
    print(f"Excel导出路径: {export_submissions_excel()}")
    print(f"JSON导出路径: {export_submissions_json()}")
