from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import create_access_token, get_current_user
from app.schemas.schemas import ResponseModel, RegisterRequest, LoginRequest, SendCodeRequest
from app.services.user_service import user_service
from app.services.email_service import store_code, send_verification_email, verify_code, cleanup_expired


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/anonymous")
async def create_anonymous_user(db: AsyncSession = Depends(get_db)):
    """
    创建匿名用户

    返回 session_id，用于后续所有请求的 X-Session-Id 头
    """
    session_id = user_service.generate_session_id()
    user = await user_service.get_or_create_user(db, session_id)

    return ResponseModel(
        data={
            "session_id": user.session_id,
            "user_id": user.id,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )


@router.post("/send-code")
async def send_code(request: SendCodeRequest):
    """
    发送邮箱验证码（5 分钟有效）

    生产环境通过 Resend 发送，开发环境打印到控制台
    """
    cleanup_expired()

    # 检查是否已注册
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        existing = await user_service.get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    code = store_code(request.email)
    success = await send_verification_email(request.email, code)
    if not success:
        raise HTTPException(status_code=500, detail="验证码发送失败，请稍后重试")

    return ResponseModel(message="验证码已发送")


@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    邮箱注册（需要邮件验证码）

    返回 JWT token + 用户信息
    """
    # 校验验证码
    if not verify_code(request.email, request.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    user, error = await user_service.register_user(db, request.email, request.password)
    if error:
        raise HTTPException(status_code=400, detail=error)

    token = create_access_token(user.id, user.email)

    return ResponseModel(
        message="注册成功",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "current_persona_id": user.current_persona_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    )


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    邮箱登录

    返回 JWT token + 用户信息
    """
    user, error = await user_service.login_user(db, request.email, request.password)
    if error:
        raise HTTPException(status_code=401, detail=error)

    token = create_access_token(user.id, user.email)

    return ResponseModel(
        message="登录成功",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "current_persona_id": user.current_persona_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    )


@router.get("/me")
async def get_me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    获取当前用户信息（需要 JWT 或 Session ID）
    """
    return ResponseModel(
        data={
            "id": user.id,
            "email": user.email,
            "session_id": user.session_id,
            "current_persona_id": user.current_persona_id,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )


@router.post("/logout")
async def logout(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    退出登录

    匿名用户：级联删除所有数据（对话、消息、手帐、用户）
    注册用户：仅返回成功，数据保留
    """
    is_anonymous = not user.email

    if is_anonymous:
        await user_service.delete_anonymous_user(db, user.id)
        return ResponseModel(message="已退出，匿名数据已清除")
    else:
        return ResponseModel(message="已退出")
