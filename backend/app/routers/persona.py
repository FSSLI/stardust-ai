from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_user_optional
from app.schemas.schemas import ResponseModel, PersonaSwitch
from app.services.persona_service import persona_service
from app.services.file_parser import extract_text


router = APIRouter(prefix="/personas", tags=["人格"])


@router.get("")
async def get_personas(
    user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取可用人格列表（系统 + 用户定制）"""
    personas = await persona_service.get_user_personas(db, user.id if user else None)

    return ResponseModel(
        data={
            "items": [
                {
                    "id": p.id,
                    "name": p.name,
                    "avatar": p.avatar,
                    "description": p.description,
                    "is_default": p.is_default,
                    "is_system": p.is_system,
                    "user_id": p.user_id,
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
    persona = await persona_service.get_persona_by_id(db, user.current_persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在")

    return ResponseModel(
        data={
            "id": persona.id,
            "name": persona.name,
            "avatar": persona.avatar,
            "description": persona.description,
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
    success = await persona_service.switch_persona(db, user.id, request.persona_id)
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
            "is_system": persona.is_system,
            "traits": persona.config_json
        }
    )


# ========== 定制人格 API ==========

@router.post("/custom")
async def create_custom_persona(
    description: str = Form(..., min_length=2, max_length=1000),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    通过文字描述创建定制人格

    用户描述 → DeepSeek 生成完整人格配置 → 存入数据库
    """
    if not user.email:
        raise HTTPException(status_code=403, detail="匿名用户不能创建定制人格，请先注册")

    # AI 生成人格
    config = await persona_service.generate_persona_from_description(description)

    persona = await persona_service.create_custom_persona(
        db=db,
        user_id=user.id,
        name=config.get("name", "自定义"),
        description=config.get("description", ""),
        system_prompt=config.get("system_prompt", ""),
        config_json=json.dumps(config.get("traits", {}), ensure_ascii=False)
    )

    return ResponseModel(
        message="人格创建成功",
        data={
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "is_system": False
        }
    )


@router.post("/custom/upload")
async def create_persona_from_file(
    file: UploadFile = File(...),
    description: str = Form(""),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文件（txt/docx/pdf）分析文本 → AI 提取人物性格 → 创建人格
    """
    if not user.email:
        raise HTTPException(status_code=403, detail="匿名用户不能创建定制人格，请先注册")

    # 检查文件类型
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("txt", "docx", "pdf"):
        raise HTTPException(status_code=400, detail="仅支持 txt / docx / pdf 格式")

    # 读取文件内容
    content = await file.read()
    text = extract_text(filename, content)
    if not text or len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="无法提取文本或文本太短（至少 10 个字符）")

    # AI 分析生成人格
    config = await persona_service.generate_persona_from_text(text, description)

    persona = await persona_service.create_custom_persona(
        db=db,
        user_id=user.id,
        name=config.get("name", "自定义"),
        description=config.get("description", "从文件生成"),
        system_prompt=config.get("system_prompt", ""),
        config_json=json.dumps(config.get("traits", {}), ensure_ascii=False)
    )

    return ResponseModel(
        message="人格创建成功",
        data={
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "is_system": False
        }
    )


@router.put("/custom/{persona_id}")
async def update_custom_persona(
    persona_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """编辑定制人格"""
    persona = await persona_service.update_custom_persona(
        db, persona_id, user.id, name, description, system_prompt
    )
    if not persona:
        raise HTTPException(status_code=404, detail="人格不存在或无权编辑")

    return ResponseModel(message="更新成功")


@router.delete("/custom/{persona_id}")
async def delete_custom_persona(
    persona_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除定制人格"""
    success = await persona_service.delete_custom_persona(db, persona_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="人格不存在或无权删除")

    return ResponseModel(message="已删除")
