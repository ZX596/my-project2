import requests
import json
import os

class GLM4VAPI:
    def __init__(self, config_path="api_config.json"):
        # Load API configuration
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as config_file:
                    self.config = json.load(config_file)
            else:
                # 使用默认配置
                self.config = {
                    "api_key": os.getenv("GLM4V_API_KEY", ""),
                    "api_url": os.getenv("GLM4V_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
                }
            
            self.api_key = self.config.get("api_key", "")
            self.api_url = self.config.get("api_url", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
            
            # 如果没有配置API密钥，使用模拟模式
            if not self.api_key or self.api_key == "your_api_key_here":
                self.use_mock = True
            else:
                self.use_mock = False
        except Exception as e:
            print(f"加载API配置失败: {e}")
            self.use_mock = True
            self.api_key = ""
            self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def call_api(self, image_base64, prompt):
        """
        Calls the GLM-4V API with the given image and prompt.

        :param image_base64: Base64-encoded image string
        :param prompt: Prompt for information extraction
        :return: Parsed JSON response or error message
        """
        # 如果使用模拟模式，返回模拟数据
        if self.use_mock:
            return self._mock_response()
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体（智谱AI GLM-4V API格式）
        payload = {
            "model": "glm-4v-plus",  # 或 "glm-4v"
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取返回内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                # 尝试解析JSON
                try:
                    return json.loads(content)
                except:
                    return {"content": content, "raw_response": result}
            else:
                return result
                
        except requests.exceptions.Timeout:
            return {"error": "API请求超时，请检查网络连接或稍后重试"}
        except requests.exceptions.ConnectionError as e:
            return {"error": f"无法连接到API服务器: {str(e)}。请检查网络连接或API配置是否正确"}
        except requests.exceptions.HTTPError as e:
            return {"error": f"API请求失败 (HTTP {response.status_code}): {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"API请求异常: {str(e)}"}
        except Exception as e:
            return {"error": f"未知错误: {str(e)}"}
    
    def _mock_response(self):
        """返回模拟响应，用于测试或API不可用时"""
        return {
            "content": """{
    "学院": "计算机学院",
    "竞赛项目": "全国大学生电子商务创新创意及创业挑战赛",
    "学号": "",
    "学生姓名": "",
    "获奖类别": "国家级",
    "获奖等级": "一等奖",
    "竞赛类型": "A类",
    "主办单位": "教育部",
    "获奖时间": "2024-01-01",
    "指导教师": ""
}""",
            "note": "这是模拟数据，请配置真实的API密钥以使用实际功能"
        }

# Example usage
if __name__ == "__main__":
    api = GLM4VAPI()
    example_image = "<base64_encoded_image>"  # Replace with actual Base64 string
    example_prompt = "Extract certificate details"
    result = api.call_api(example_image, example_prompt)
    print(json.dumps(result, indent=4))