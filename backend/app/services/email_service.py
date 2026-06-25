"""
邮件验证码服务

生产环境：通过 Resend API 发送验证码邮件
开发环境：无 Resend API Key 时打印验证码到控制台
"""
import random
import time
import httpx
from typing import Dict, Optional

from app.core.config import settings


# 内存存储验证码 {email: {code, expires_at, verified}}
_verification_store: Dict[str, dict] = {}


def generate_code() -> str:
    """生成 6 位数字验证码"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def store_code(email: str) -> str:
    """生成验证码并存储，5 分钟有效，返回验证码"""
    code = generate_code()
    _verification_store[email] = {
        "code": code,
        "expires_at": time.time() + 300,  # 5 分钟
        "verified": False
    }
    return code


def verify_code(email: str, code: str) -> bool:
    """
    校验验证码

    Returns:
        True — 验证成功，标记为已验证
        False — 验证失败（过期、不存在或不匹配）
    """
    entry = _verification_store.get(email)
    if not entry:
        return False
    if time.time() > entry["expires_at"]:
        del _verification_store[email]
        return False
    if entry["code"] != code:
        return False

    entry["verified"] = True
    return True


def is_verified(email: str) -> bool:
    """检查邮箱是否已通过验证"""
    entry = _verification_store.get(email)
    if not entry:
        return False
    return entry.get("verified", False)


def cleanup_expired():
    """清理过期的验证码"""
    now = time.time()
    expired = [e for e, v in _verification_store.items() if v["expires_at"] < now]
    for e in expired:
        del _verification_store[e]


async def send_verification_email(email: str, code: str) -> bool:
    """
    发送验证码邮件

    优先使用 Resend API，失败或未配置时自动降级到控制台输出
    """
    if settings.resend_api_key:
        success = await _send_via_resend(email, code)
        if success:
            return True
        print("[Email] Resend 发送失败，降级到控制台模式")

    # 开发模式/降级：打印到控制台
    print(f"\n{'='*50}")
    print(f"📧 验证码邮件")
    print(f"收件人: {email}")
    print(f"验证码: {code}")
    print(f"有效期: 5 分钟")
    print(f"{'='*50}\n")
    return True


async def _send_via_resend(email: str, code: str) -> bool:
    """通过 Resend API 发送邮件"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": settings.resend_from,
                    "to": email,
                    "subject": "星尘 AI — 邮箱验证码",
                    "html": f"""<div style="max-width:480px;margin:0 auto;padding:32px;font-family:Arial,sans-serif">
<h2 style="color:#0ea5e9">✨ 星尘 AI 邮箱验证</h2>
<p>你的验证码是：</p>
<h1 style="font-size:36px;letter-spacing:8px;color:#333;text-align:center;padding:16px;background:#f0f9ff;border-radius:8px">{code}</h1>
<p>有效期 5 分钟，请尽快完成验证。</p>
<p style="color:#999;font-size:12px;margin-top:32px">如果这不是你的操作，请忽略此邮件。</p>
</div>"""
                },
                timeout=15.0
            )
            if response.status_code != 200:
                print(f"[Resend] 发送失败 status={response.status_code}: {response.text}")
            return response.status_code == 200
    except Exception as e:
        print(f"[Resend] 发送异常: {e}")
        return False
