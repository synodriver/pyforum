"""
安全相关 验证码等
"""
import secrets
from typing import cast

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import ORJSONResponse, StreamingResponse
from redis.asyncio import Redis
from starlette.templating import Jinja2Templates

from pyforum.config import settings
from pyforum.depends import get_redis
from pyforum.routers.secure.models import RequestSendEmail
from pyforum.utils import generate_captcha, generate_token, send_email

router = APIRouter(prefix="/api/v1/secure", tags=["secure"])


@router.get("/captcha")
async def captcha(request: Request, redis: Redis = Depends(get_redis)):
    captcha_id: str = secrets.token_hex(16)
    request.session.update({"captcha_id": captcha_id})
    image, answer = generate_captcha(settings.captcha_num)
    if settings.debug:
        print(answer)
    await redis.set(f"captcha:{captcha_id}", answer, ex=settings.captcha_ttl)
    return StreamingResponse(content=image, media_type="image/jpeg")


email_template = """
您好，你正在进行{}的邮箱验证。

您的验证码为: {}

验证码 {}秒内有效，如果不是本人操作，请忽略。"""


# 注册 换邮箱等实现不知道用户邮箱的情况，验证为止邮箱是否属于用户
@router.post("/email", description="发送邮件验证码", response_class=ORJSONResponse)
async def email(
    request: Request,
    email: RequestSendEmail = Body(...),
    redis: Redis = Depends(get_redis),
):
    email_id: str = secrets.token_hex(16)
    request.session.update({"email_id": email_id})
    token = generate_token(settings.email_token_num)
    await redis.set(f"email:answer:{email_id}", token, ex=settings.email_token_ttl)
    # 记录下当前正在验证的是哪个邮箱，免得用户收到验证码后换了另一个邮箱来注册
    await redis.set(
        f"email:pending:{email_id}", email.email, ex=settings.email_token_ttl
    )
    await send_email(
        settings.email_fromaddr,
        email.email,
        email_template.format(settings.site_name, token, settings.email_token_ttl),
        settings.email_smtp_server,
        settings.email_smtp_username,
        settings.email_smtp_password,
        settings.email_smtp_port,
    )
    return {"msg": "ok"}
