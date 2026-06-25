from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional, Dict
from app.models.models import JournalEntry


class JournalService:
    """手帐服务"""
    
    @staticmethod
    async def create_entry(
        db: AsyncSession,
        user_id: int,
        content: str,
        entry_type: str = "note",
        tags: List[str] = None,
        mood_score: Optional[int] = None
    ) -> JournalEntry:
        """创建记录"""
        tags_str = ",".join(tags) if tags else None
        
        entry = JournalEntry(
            user_id=user_id,
            content=content,
            entry_type=entry_type,
            tags=tags_str,
            mood_score=mood_score
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry
    
    @staticmethod
    async def get_entries(
        db: AsyncSession,
        user_id: int,
        entry_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[JournalEntry], int]:
        """获取记录列表"""
        query = select(JournalEntry).where(JournalEntry.user_id == user_id)
        
        # 类型筛选
        if entry_type:
            query = query.where(JournalEntry.entry_type == entry_type)
        
        # 日期筛选
        if date_from:
            query = query.where(JournalEntry.created_at >= date_from)
        if date_to:
            query = query.where(JournalEntry.created_at <= date_to)
        
        # 标签筛选
        if tag:
            query = query.where(JournalEntry.tags.contains(tag))
        
        # 总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # 分页
        result = await db.execute(
            query.order_by(desc(JournalEntry.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total
    
    @staticmethod
    async def get_entry(
        db: AsyncSession,
        entry_id: int,
        user_id: int
    ) -> Optional[JournalEntry]:
        """获取单条记录"""
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.id == entry_id)
            .where(JournalEntry.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_entry(
        db: AsyncSession,
        entry_id: int,
        user_id: int,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        mood_score: Optional[int] = None
    ) -> Optional[JournalEntry]:
        """更新记录"""
        entry = await JournalService.get_entry(db, entry_id, user_id)
        if not entry:
            return None
        
        if content is not None:
            entry.content = content
        if tags is not None:
            entry.tags = ",".join(tags)
        if mood_score is not None:
            entry.mood_score = mood_score
        
        await db.commit()
        await db.refresh(entry)
        return entry
    
    @staticmethod
    async def delete_entry(
        db: AsyncSession,
        entry_id: int,
        user_id: int
    ) -> bool:
        """删除记录"""
        entry = await JournalService.get_entry(db, entry_id, user_id)
        if not entry:
            return False
        
        await db.delete(entry)
        await db.commit()
        return True
    
    @staticmethod
    async def get_stats(db: AsyncSession, user_id: int) -> Dict:
        """获取统计信息"""
        # 总数
        total_result = await db.execute(
            select(func.count())
            .select_from(JournalEntry)
            .where(JournalEntry.user_id == user_id)
        )
        total = total_result.scalar()
        
        # 按类型统计
        type_result = await db.execute(
            select(JournalEntry.entry_type, func.count())
            .where(JournalEntry.user_id == user_id)
            .group_by(JournalEntry.entry_type)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        # 心情趋势（最近7天）
        mood_result = await db.execute(
            select(
                func.date(JournalEntry.created_at),
                func.avg(JournalEntry.mood_score)
            )
            .where(JournalEntry.user_id == user_id)
            .where(JournalEntry.mood_score.isnot(None))
            .group_by(func.date(JournalEntry.created_at))
            .order_by(func.date(JournalEntry.created_at))
            .limit(7)
        )
        mood_trend = [
            {"date": str(row[0]), "avg_mood": round(row[1], 1)}
            for row in mood_result.all()
        ]
        
        return {
            "total_entries": total,
            "by_type": by_type,
            "mood_trend": mood_trend
        }


# 全局实例
journal_service = JournalService()