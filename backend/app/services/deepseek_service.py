import httpx
import json
from typing import AsyncGenerator, List, Dict
from app.core.config import settings


class DeepSeekService:
    """DeepSeek API 服务"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_url = settings.deepseek_api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None
    ) -> AsyncGenerator[str, None]:
        """
        流式对话，返回 SSE 格式的内容片段
        
        Args:
            messages: 对话历史 [{role, content}, ...]
            system_prompt: 系统提示词
        
        Yields:
            内容片段字符串
        """
        # 构建请求体
        request_messages = []
        if system_prompt:
            request_messages.append({
                "role": "system",
                "content": system_prompt
            })
        request_messages.extend(messages)
        
        payload = {
            "model": "deepseek-chat",
            "messages": request_messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉 "data: " 前缀
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
    
    async def generate_title(self, user_message: str, ai_response: str) -> str:
        """
        根据对话生成标题
        
        Args:
            user_message: 用户第一条消息
            ai_response: AI 第一条回复
        
        Returns:
            标题字符串
        """
        prompt = f"""请根据以下对话，生成一个简短的标题（不超过10个字）。
标题要能概括对话主题。

用户：{user_message}
AI：{ai_response}

标题："""
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.5,
            "max_tokens": 20
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            title = result["choices"][0]["message"]["content"].strip()
            # 清理标题，去掉引号等
            title = title.strip('"''"').strip()
            return title[:20]  # 限制长度


# 全局实例
deepseek_service = DeepSeekService()