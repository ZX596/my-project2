"""
证书信息提取服务
整合GLM4V API进行证书信息智能识别
"""
import json
import re
from datetime import datetime
from glm4v_api import GLM4VAPI
from info_extractor import extract_certificate_info

class CertificateExtractor:
    """证书信息提取器"""
    
    def __init__(self, config_path="api_config.json"):
        """初始化提取器"""
        self.api = GLM4VAPI(config_path)
        self.prompt = """请从这张竞赛证书图片中提取以下信息，并以JSON格式返回：
{
    "学院": "学生所在学院",
    "竞赛项目": "竞赛项目名称",
    "学号": "13位学号",
    "学生姓名": "学生姓名",
    "获奖类别": "国家级或省级",
    "获奖等级": "一等奖、二等奖、三等奖、金奖、银奖、铜奖或优秀奖",
    "竞赛类型": "A类或B类",
    "主办单位": "主办单位名称",
    "获奖时间": "YYYY-MM-DD格式的日期",
    "指导教师": "指导教师姓名"
}

如果某个字段无法识别，请返回空字符串。请确保返回的是有效的JSON格式。"""
    
    def extract_from_image_base64(self, image_base64):
        """
        从Base64编码的图片中提取证书信息
        
        Args:
            image_base64: Base64编码的图片字符串
            
        Returns:
            dict: 提取的信息字典，包含success字段和data字段
        """
        try:
            # 调用GLM4V API
            response = self.api.call_api(image_base64, self.prompt)
            
            # 检查是否有错误
            if 'error' in response:
                error_msg = response['error']
                # 提供更友好的错误提示
                if 'getaddrinfo failed' in error_msg or 'NameResolutionError' in error_msg:
                    error_msg = "无法连接到API服务器。请检查：\n1. 网络连接是否正常\n2. API配置是否正确（api_config.json）\n3. 是否配置了有效的API密钥"
                elif 'timeout' in error_msg.lower():
                    error_msg = "API请求超时，请稍后重试或检查网络连接"
                
                return {
                    'success': False,
                    'error': error_msg,
                    'data': {},
                    'is_mock': False
                }
            
            # 检查是否是模拟响应
            is_mock = response.get('note') is not None
            
            # 尝试从响应中提取JSON
            extracted_data = self._parse_api_response(response)
            
            # 验证和清理数据
            cleaned_data = self._clean_extracted_data(extracted_data)
            
            return {
                'success': True,
                'data': cleaned_data,
                'extraction_method': 'glm4v',
                'confidence': self._calculate_confidence(cleaned_data),
                'is_mock': is_mock,
                'note': '这是模拟数据，请配置真实的API密钥' if is_mock else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'提取失败: {str(e)}',
                'data': {},
                'is_mock': False
            }
    
    def _parse_api_response(self, response):
        """解析API响应，提取JSON数据"""
        # 如果响应直接是字典且包含所需字段
        if isinstance(response, dict):
            # 检查是否包含所需字段
            required_fields = ['学院', '竞赛项目', '学号', '学生姓名', '获奖类别', 
                             '获奖等级', '竞赛类型', '主办单位', '获奖时间', '指导教师']
            if any(field in response for field in required_fields):
                return response
            
            # 检查是否有content或text字段包含JSON
            content = response.get('content', response.get('text', response.get('message', '')))
            if isinstance(content, str):
                # 如果content是JSON字符串，尝试解析
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    pass
                # 否则尝试从文本中提取JSON
                return self._extract_json_from_text(content)
            
            # 检查choices字段（OpenAI格式）
            if 'choices' in response and len(response['choices']) > 0:
                message = response['choices'][0].get('message', {})
                content = message.get('content', '')
                if content:
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, dict):
                            return parsed
                    except:
                        return self._extract_json_from_text(content)
        
        # 如果是字符串，尝试提取JSON
        if isinstance(response, str):
            return self._extract_json_from_text(response)
        
        # 默认返回空字典
        return {}
    
    def _extract_json_from_text(self, text):
        """从文本中提取JSON"""
        # 尝试找到JSON对象
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # 如果找不到JSON，尝试使用info_extractor
        return extract_certificate_info({'text': text})
    
    def _clean_extracted_data(self, data):
        """清理和验证提取的数据"""
        cleaned = {
            'department': data.get('学院', '').strip(),
            'competition_name': data.get('竞赛项目', '').strip(),
            'student_id': data.get('学号', '').strip(),
            'student_name': data.get('学生姓名', '').strip(),
            'award_category': data.get('获奖类别', '').strip(),
            'award_level': data.get('获奖等级', '').strip(),
            'competition_type': data.get('竞赛类型', '').strip(),
            'organizer': data.get('主办单位', '').strip(),
            'award_date': self._parse_date(data.get('获奖时间', '').strip()),
            'advisor': data.get('指导教师', '').strip()
        }
        
        # 验证学号格式
        if cleaned['student_id']:
            # 移除非数字字符
            cleaned['student_id'] = re.sub(r'\D', '', cleaned['student_id'])
            if len(cleaned['student_id']) != 13:
                cleaned['student_id'] = ''  # 如果格式不正确，清空
        
        return cleaned
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return None
        
        # 尝试多种日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y年%m月%d日',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y-%m',
            '%Y年%m月'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        # 尝试提取年份
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            try:
                return datetime(int(year_match.group(1)), 1, 1).date()
            except:
                pass
        
        return None
    
    def _calculate_confidence(self, data):
        """计算提取置信度"""
        # 统计非空字段数量
        non_empty_count = sum(1 for v in data.values() if v)
        total_fields = len(data)
        
        # 基础置信度
        confidence = (non_empty_count / total_fields) * 100
        
        # 如果关键字段存在，提高置信度
        key_fields = ['student_id', 'student_name', 'competition_name']
        if all(data.get(f) for f in key_fields):
            confidence = min(confidence + 10, 100)
        
        return round(confidence, 2)

