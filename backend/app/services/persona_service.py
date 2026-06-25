from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from app.models.models import Persona, User


class PersonaService:
    """人格服务"""
    
    # MVP 预设人格
    DEFAULT_PERSONAS = [
        {
            "id": 1,
            "name": "星尘",
            "avatar": "/assets/avatars/stardust.png",
            "system_prompt": """你是星尘，一个温柔体贴的AI伙伴。你的特点是：
- 善于倾听，不轻易打断用户
- 会用温暖的话语安慰和鼓励用户
- 会记住用户的喜好和经历
- 说话语气柔和，像一位知心朋友
- 适当使用emoji让对话更生动
请用中文回复，保持温柔体贴的语气。""",
            "description": "温柔体贴的知心伙伴",
            "is_default": True,
            "config_json": '{"warmth": 0.9, "humor": 0.3, "formality": 0.2}'
        },
        {
            "id": 2,
            "name": "北辰",
            "avatar": "/assets/avatars/beichen.png",
            "system_prompt": """你是北辰，一个理性冷静的AI顾问。你的特点是：
- 分析问题条理清晰，给出结构化建议
- 不煽情，不废话，直击问题核心
- 善于从多个角度分析利弊
- 说话简洁有力，像一位靠谱的导师
请用中文回复，保持理性客观的语气。""",
            "description": "理性冷静的AI顾问",
            "is_default": False,
            "config_json": '{"warmth": 0.3, "humor": 0.2, "formality": 0.9}'
        },
        {
            "id": 3,
            "name": "阿星",
            "avatar": "/assets/avatars/axing.png",
            "system_prompt": """你是阿星，一个嘴贱但靠谱的AI损友。你的特点是：
- 说话幽默风趣，经常使用网络流行语
- 会善意地调侃用户，但绝不越界
- 用户遇到困难时，虽然嘴上说"真拿你没办法"，但会认真帮忙
- 像认识多年的死党，聊天轻松无压力
请用中文回复，保持幽默随性的语气。""",
            "description": "嘴贱但靠谱的AI损友",
            "is_default": False,
            "config_json": '{"warmth": 0.6, "humor": 0.95, "formality": 0.1}'
        }
    ]
    
    @staticmethod
    async def init_default_personas(db: AsyncSession):
        """初始化默认人格"""
        for persona_data in PersonaService.DEFAULT_PERSONAS:
            result = await db.execute(
                select(Persona).where(Persona.id == persona_data["id"])
            )
            if not result.scalar_one_or_none():
                persona = Persona(**persona_data)
                db.add(persona)
        await db.commit()
    
    @staticmethod
    async def get_all_personas(db: AsyncSession) -> List[Persona]:
        """获取所有人格"""
        result = await db.execute(select(Persona))
        return result.scalars().all()
    
    @staticmethod
    async def get_persona_by_id(db: AsyncSession, persona_id: int) -> Optional[Persona]:
        """通过 ID 获取人格"""
        result = await db.execute(
            select(Persona).where(Persona.id == persona_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_default_persona(db: AsyncSession) -> Optional[Persona]:
        """获取默认人格"""
        result = await db.execute(
            select(Persona).where(Persona.is_default == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def switch_persona(db: AsyncSession, user_id: int, persona_id: int) -> bool:
        """切换用户当前人格"""
        persona = await PersonaService.get_persona_by_id(db, persona_id)
        if not persona:
            return False

        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(current_persona_id=persona_id)
        )
        await db.commit()
        return True

    @staticmethod
    async def get_user_personas(db: AsyncSession, user_id: Optional[int] = None) -> List[Persona]:
        """获取可用人格：系统人格 + 该用户的定制人格（未登录只看系统人格）"""
        if user_id is None:
            result = await db.execute(
                select(Persona).where(Persona.is_system == True).order_by(Persona.id)
            )
        else:
            result = await db.execute(
                select(Persona).where(
                    (Persona.is_system == True) |
                    ((Persona.is_system == False) & (Persona.user_id == user_id))
                ).order_by(Persona.is_system.desc(), Persona.id)
            )
        return result.scalars().all()

    @staticmethod
    async def create_custom_persona(
        db: AsyncSession,
        user_id: int,
        name: str,
        description: str,
        system_prompt: str,
        config_json: Optional[str] = None
    ) -> Persona:
        """创建用户定制人格"""
        persona = Persona(
            name=name,
            description=description,
            system_prompt=system_prompt,
            config_json=config_json,
            is_system=False,
            is_default=False,
            user_id=user_id
        )
        db.add(persona)
        await db.commit()
        await db.refresh(persona)
        return persona

    @staticmethod
    async def update_custom_persona(
        db: AsyncSession,
        persona_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Optional[Persona]:
        """更新用户定制人格"""
        persona = await PersonaService.get_persona_by_id(db, persona_id)
        if not persona or persona.user_id != user_id:
            return None

        if name: persona.name = name
        if description: persona.description = description
        if system_prompt: persona.system_prompt = system_prompt

        await db.commit()
        await db.refresh(persona)
        return persona

    @staticmethod
    async def delete_custom_persona(db: AsyncSession, persona_id: int, user_id: int) -> bool:
        """删除用户定制人格"""
        persona = await PersonaService.get_persona_by_id(db, persona_id)
        if not persona or persona.user_id != user_id:
            return False

        # 如果用户当前使用这个人格，切回默认
        user = await db.get(User, user_id)
        if user and user.current_persona_id == persona_id:
            default_p = await PersonaService.get_default_persona(db)
            if default_p:
                user.current_persona_id = default_p.id

        await db.delete(persona)
        await db.commit()
        return True

    @staticmethod
    async def generate_persona_from_description(description: str) -> dict:
        """通过 DeepSeek 根据用户描述生成人格配置"""
        import httpx
        from app.core.config import settings

        prompt = f"""根据以下描述，生成一个完整的 AI 角色设定。

用户描述：{description}

请严格输出 JSON 格式（不要有其他文字）：
{{
  "name": "角色名（2-4个中文字）",
  "description": "一句话概括角色特点",
  "system_prompt": "完整的系统提示词，200-400字，包括：性格特点、说话语气、行为准则、与用户互动的方式",
  "traits": {{"warmth": 0.0-1.0, "humor": 0.0-1.0, "formality": 0.0-1.0}}
}}"""

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.deepseek_api_url,
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False, "temperature": 0.8, "max_tokens": 1500},
                timeout=60.0
            )
            resp.raise_for_status()
            result = resp.json()
            raw = result["choices"][0]["message"]["content"].strip()

        # 解析 JSON
        import json, re
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if m:
                return json.loads(m.group(1))
            return {"name": "自定义", "description": description[:50], "system_prompt": raw, "traits": {}}

    @staticmethod
    async def generate_persona_from_text(text: str, description: str = "") -> dict:
        """分析上传文件的文本内容，提取人物性格生成人格"""
        import httpx
        from app.core.config import settings

        text_sample = text[:4000]  # 截取前 4000 字分析
        extra = f"\n用户额外要求：{description}" if description else ""

        prompt = f"""分析以下文本中的人物性格特征，生成一个 AI 角色设定。{extra}

文本内容（前 4000 字）：
---
{text_sample}
---

请严格输出 JSON 格式（不要有其他文字）：
{{
  "name": "角色名（2-4个中文字）",
  "description": "一句话概括角色特点",
  "system_prompt": "完整的系统提示词，200-400字，模仿文本中人物的性格和说话风格",
  "traits": {{"warmth": 0.0-1.0, "humor": 0.0-1.0, "formality": 0.0-1.0}}
}}"""

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.deepseek_api_url,
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False, "temperature": 0.7, "max_tokens": 1500},
                timeout=60.0
            )
            resp.raise_for_status()
            result = resp.json()
            raw = result["choices"][0]["message"]["content"].strip()

        import json, re
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if m:
                return json.loads(m.group(1))
            return {"name": "自定义", "description": "从文件生成", "system_prompt": raw, "traits": {}}


# 全局实例
persona_service = PersonaService()