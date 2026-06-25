"""
长期记忆摘要服务

- 从对话历史中提取关键信息
- 合并旧记忆与新信息
- 注入到对话上下文中
"""
import json
import re
from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.memory import MemorySummary
from app.models.models import Message, Conversation
from app.services.deepseek_service import deepseek_service


# 触发摘要的新消息阈值
SUMMARIZE_THRESHOLD = 15

# 摘要生成 Prompt
SUMMARIZE_PROMPT = """你需要从对话历史中提取关于用户的关键信息，生成记忆摘要。

## 已有记忆
{previous_memory}

## 新的对话内容
{new_messages}

## 输出格式
请以 JSON 格式输出，包含以下字段（如果某类没有信息，写"暂无"）：
{{
  "basic_info": "用户的职业、年龄、兴趣、生活状态等信息",
  "preferences": "用户喜欢什么、讨厌什么、习惯偏好等",
  "recent_status": "用户近期的情绪状态、发生的重要事件",
  "plans": "用户提到的约定、计划、目标等"
}}

## 要求
1. 只提取事实性信息，不要加入推测
2. 将新旧记忆合并，避免重复
3. 每条信息尽量简洁（1-2 句话）
4. 只输出 JSON，不要有其他内容"""


class MemoryService:
    """记忆摘要服务"""

    @staticmethod
    async def get_latest(db: AsyncSession, user_id: int) -> Optional[MemorySummary]:
        """获取用户最新的记忆摘要"""
        result = await db.execute(
            select(MemorySummary)
            .where(MemorySummary.user_id == user_id)
            .order_by(desc(MemorySummary.updated_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def should_summarize(db: AsyncSession, user_id: int) -> bool:
        """检查是否需要生成新摘要"""
        # 统计用户总消息数
        result = await db.execute(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
            .where(Message.role.in_(["user", "assistant"]))
        )
        total_messages = result.scalar() or 0

        if total_messages == 0:
            return False

        # 获取上次摘要
        latest = await MemoryService.get_latest(db, user_id)
        if not latest:
            return total_messages >= SUMMARIZE_THRESHOLD

        return (total_messages - (latest.message_count or 0)) >= SUMMARIZE_THRESHOLD

    @staticmethod
    async def generate_summary(db: AsyncSession, user_id: int) -> Optional[MemorySummary]:
        """
        生成／更新记忆摘要

        1. 获取旧摘要 + 新增消息
        2. 调用 DeepSeek 生成合并摘要
        3. 存入数据库
        """
        # 获取旧摘要
        latest = await MemoryService.get_latest(db, user_id)
        previous_memory = latest.content_json if latest else "暂无"
        last_msg_id = latest.last_message_id if latest else 0

        # 获取自上次摘要以来的新消息
        result = await db.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
            .where(Message.id > last_msg_id)
            .where(Message.role.in_(["user", "assistant"]))
            .order_by(Message.created_at)
            .limit(50)  # 最多取 50 条新消息
        )
        new_messages = result.scalars().all()

        if not new_messages:
            return latest

        # 格式化新消息
        formatted = []
        for msg in new_messages:
            role_label = "用户" if msg.role == "user" else "AI"
            formatted.append(f"{role_label}：{msg.content}")
        new_content = "\n".join(formatted)

        # 统计总消息数
        total_result = await db.execute(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
            .where(Message.role.in_(["user", "assistant"]))
        )
        total_messages = total_result.scalar() or 0

        # 调用 DeepSeek 生成摘要
        prompt = SUMMARIZE_PROMPT.format(
            previous_memory=previous_memory,
            new_messages=new_content
        )

        try:
            # 使用非流式方式调用 DeepSeek
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.deepseek_api_url,
                    headers={
                        "Authorization": f"Bearer {settings.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "temperature": 0.3,
                        "max_tokens": 1000
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result_data = response.json()
                raw_output = result_data["choices"][0]["message"]["content"].strip()

            # 尝试解析 JSON
            content_json = MemoryService._parse_json_output(raw_output)

            # 存入数据库
            summary = MemorySummary(
                user_id=user_id,
                content_json=content_json,
                last_message_id=new_messages[-1].id,
                message_count=total_messages
            )
            db.add(summary)
            await db.commit()
            await db.refresh(summary)
            return summary

        except Exception as e:
            print(f"[Memory] 生成摘要失败: {e}")
            await db.rollback()
            return None

    @staticmethod
    def _parse_json_output(raw: str) -> str:
        """从 DeepSeek 输出中提取 JSON"""
        # 尝试直接解析
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 块
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        if match:
            try:
                parsed = json.loads(match.group(1))
                return json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

        # 回退：直接存原始文本
        return json.dumps({"raw": raw}, ensure_ascii=False)

    @staticmethod
    def format_memory_context(summary: Optional[MemorySummary]) -> str:
        """将记忆摘要格式化为 system prompt 片段"""
        if not summary:
            return ""

        try:
            data = json.loads(summary.content_json)
        except json.JSONDecodeError:
            return ""

        parts = ["\n## 关于用户的记忆（请结合以下信息与用户交流）"]

        labels = {
            "basic_info": "基本信息",
            "preferences": "偏好习惯",
            "recent_status": "近期状态",
            "plans": "重要约定"
        }

        for key, label in labels.items():
            value = data.get(key, "")
            if value and value != "暂无" and value != "无":
                parts.append(f"- {label}：{value}")

        if len(parts) == 1:
            return ""

        return "\n".join(parts)


# 全局实例
memory_service = MemoryService()
