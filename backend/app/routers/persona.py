from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.schemas.schemas import ResponseModel, PersonaSwitch
from app.services.user_service import user_service
from app.services.persona_service import persona_service


router = APIRouter(prefix="/personas", tags=["人格"])


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


@router.get("")
async def get_personas(db: AsyncSession = Depends(get_db)):
    """获取所有人格列表"""
    personas = await persona_service.get_all_personas(db)
    
    # 修复：data 必须是字典，不能是列表
    return ResponseModel(
        data={
            "items": [
                {
                    "id": p.id,
                    "name": p.name,
                    "avatar": p.avatar,
                    "description": p.description,
                    "is_default": p.is_default,
                    "traits": p.config_json
                }
                for p in personas
            ]
        }
    )


@router.get("/current")
async def get_current_persona(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前人格"""
    persona = await persona_service.get_persona_by_id(
        db, user.current_persona_id
    )
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")
    
    return ResponseModel(
        data={
            "id": persona.id,
            "name": persona.name,
            "avatar": persona.avatar,
            "system_prompt": persona.system_prompt
        }
    )


@router.post("/switch")
async def switch_persona(
    request: PersonaSwitch,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """切换人格"""
    success = await persona_service.switch_persona(
        db, user.id, request.persona_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="人格不存在")
    
    persona = await persona_service.get_persona_by_id(db, request.persona_id)
    
    return ResponseModel(
        message=f"已切换到人格：{persona.name}",
        data={
            "current_persona_id": persona.id,
            "persona_name": persona.name
        }
    )


@router.get("/{persona_id}")
async def get_persona_detail(
    persona_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取人格详情"""
    persona = await persona_service.get_persona_by_id(db, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")
    
    return ResponseModel(
        data={
            "id": persona.id,
            "name": persona.name,
            "avatar": persona.avatar,
            "description": persona.description,
            "system_prompt": persona.system_prompt,
            "traits": persona.config_json
        }
    )