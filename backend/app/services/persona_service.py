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
        # 检查人格是否存在
        persona = await PersonaService.get_persona_by_id(db, persona_id)
        if not persona:
            return False
        
        # 更新用户当前人格
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(current_persona_id=persona_id)
        )
        await db.commit()
        return True


# 全局实例
persona_service = PersonaService()