from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.schemas.schemas import JournalCreate, JournalUpdate, ResponseModel
from app.services.user_service import user_service
from app.services.journal_service import journal_service


router = APIRouter(prefix="/journal", tags=["手帐"])


async def get_current_user(
    x_session_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户"""
    if not x_session_id:
        raise HTTPException(status_code=401, detail="缺少 Session ID")
    
    user = await user_service.get_user_by_session(db, x_session_id)
    if not user:
        raise HTTPException(status_code=401, detail="无效的 Session ID")
    
    return user


@router.post("")
async def create_entry(
    request: JournalCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建手帐记录"""
    entry = await journal_service.create_entry(
        db=db,
        user_id=user.id,
        content=request.content,
        entry_type=request.entry_type,
        tags=request.tags,
        mood_score=request.mood_score
    )
    
    return ResponseModel(
        data={
            "id": entry.id,
            "content": entry.content,
            "entry_type": entry.entry_type,
            "tags": entry.tags,
            "mood_score": entry.mood_score,
            "created_at": entry.created_at.isoformat() if entry.created_at else None
        }
    )


@router.get("")
async def get_entries(
    entry_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取手帐记录列表"""
    entries, total = await journal_service.get_entries(
        db=db,
        user_id=user.id,
        entry_type=entry_type,
        date_from=date_from,
        date_to=date_to,
        tag=tag,
        page=page,
        page_size=page_size
    )
    
    return ResponseModel(
        data={
            "items": [
                {
                    "id": e.id,
                    "content": e.content,
                    "entry_type": e.entry_type,
                    "tags": e.tags,
                    "mood_score": e.mood_score,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in entries
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/{entry_id}")
async def get_entry(
    entry_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单条记录"""
    entry = await journal_service.get_entry(db, entry_id, user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return ResponseModel(
        data={
            "id": entry.id,
            "content": entry.content,
            "entry_type": entry.entry_type,
            "tags": entry.tags,
            "mood_score": entry.mood_score,
            "created_at": entry.created_at.isoformat() if entry.created_at else None
        }
    )


@router.put("/{entry_id}")
async def update_entry(
    entry_id: int,
    request: JournalUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新记录"""
    entry = await journal_service.update_entry(
        db=db,
        entry_id=entry_id,
        user_id=user.id,
        content=request.content,
        tags=request.tags,
        mood_score=request.mood_score
    )
    if not entry:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return ResponseModel(
        message="更新成功",
        data={
            "id": entry.id,
            "content": entry.content,
            "tags": entry.tags,
            "mood_score": entry.mood_score
        }
    )


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除记录"""
    success = await journal_service.delete_entry(db, entry_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return ResponseModel(message="删除成功")


@router.get("/stats/summary")
async def get_stats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取统计信息"""
    stats = await journal_service.get_stats(db, user.id)
    
    return ResponseModel(data=stats)