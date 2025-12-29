import json

def extract_certificate_info(api_response):
    """
    Extracts required fields from the API response.

    :param api_response: JSON response from the API
    :return: Dictionary containing extracted fields
    """
    fields = [
        "学院", "竞赛项目", "学号", "学生姓名", "获奖类别",
        "获奖等级", "竞赛类型", "主办单位", "获奖时间", "指导教师"
    ]

    extracted_info = {}
    for field in fields:
        extracted_info[field] = api_response.get(field, "字段缺失")

    return extracted_info

# Example usage
if __name__ == "__main__":
    # Simulated API response
    api_response = {
        "学院": "计算机学院",
        "竞赛项目": "程序设计大赛",
        "学号": "20251234",
        "学生姓名": "张三",
        "获奖类别": "个人赛",
        "获奖等级": "一等奖",
        "竞赛类型": "国家级",
        "主办单位": "教育部",
        "获奖时间": "2025-12-01",
        "指导教师": "李老师"
    }

    extracted_info = extract_certificate_info(api_response)
    print(json.dumps(extracted_info, indent=4, ensure_ascii=False))