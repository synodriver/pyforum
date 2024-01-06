"""
用户相关的endpoint
"""
import secrets
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.config import settings
from pyforum.depends import get_db_session, get_redis, get_user, get_user_or_jump
from pyforum.routers.user.crud import (
    get_user_by_email,
    get_user_by_name,
    handle_get_sign,
    handle_getprofile,
    handle_setprofile,
    handle_sign,
    handle_signup,
    reset_user_password,
    verify_password_login,
)
from pyforum.routers.user.models import (
    UserLogin,
    UserRegister,
    UserResetPassword,
    UserResetPasswordEmail,
    UserSetProfile,
)
from pyforum.utils import ensure_str, generate_token, send_email

router = APIRouter(prefix="/api/v1/user", tags=["user"])


@router.post("/login", description="用户登录,返回200的正常，其余的detail字段是错误信息")
async def login(
    request: Request,
    body: UserLogin = Body(),
    user_id: int = Depends(get_user),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
):
    if user_id is not None:
        return ORJSONResponse(status_code=403, content={"msg": "already login"})
    if settings.use_captcha:

        async def check_captcha():
            if captcha_id := request.session.get("captcha_id", None):
                if real_answer := await redis.get(f"captcha:{captcha_id}"):
                    if ensure_str(real_answer).upper() != body.captcha.upper():
                        raise HTTPException(status_code=403, detail="wrong captcha")
                else:
                    raise HTTPException(
                        status_code=403, detail="captcha time out. get a new one"
                    )
            else:
                raise HTTPException(status_code=403, detail="need get captcha first")

        await check_captcha()
    if (
        uid := await verify_password_login(
            session, request, body.password, body.name, body.email
        )
    ) == False:
        raise HTTPException(status_code=403, detail="wrong username or password")
    request.session.update({"user_id": uid})
    request.session.pop("captcha_id", None)  # 登录完成之后不需要captcha_id了
    return ORJSONResponse(status_code=200, content={"msg": "ok"})


@router.post("/logout", response_class=ORJSONResponse, description="用户退出登录")
async def logout(request: Request, user_id: int = Depends(get_user_or_jump)):
    request.session.clear()
    return {"id": user_id, "msg": "ok"}


@router.post("/signup", description="用户注册")
async def signup(
    request: Request,
    body: UserRegister = Body(),
    user_id: Optional[int] = Depends(get_user),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
):
    if user_id is not None:
        raise HTTPException(status_code=403, detail="already login")

    async def check_email():
        if email_id := request.session.get("email_id", None):
            current_email = await redis.get(f"email:pending:{email_id}")
            if not current_email:
                raise HTTPException(status_code=403, detail="email verify time out")
            if email_code := await redis.get(f"email:answer:{email_id}"):
                if ensure_str(email_code) != body.email_code:
                    raise HTTPException(status_code=403, detail="wrong email verify")
            else:
                raise HTTPException(status_code=403, detail="email verify time out")
            return ensure_str(current_email)
        else:
            raise HTTPException(status_code=403, detail="need to receive email first")

    current_email = await check_email()
    request.session.pop("email_id", None)
    if settings.use_captcha:

        async def check_captcha():
            if captcha_id := request.session.get("captcha_id", None):
                if real_answer := await redis.get(f"captcha:{captcha_id}"):
                    if ensure_str(real_answer).upper() != body.captcha.upper():
                        raise HTTPException(status_code=403, detail="wrong captcha")
                else:
                    raise HTTPException(
                        status_code=403, detail="captcha time out. get a new one"
                    )
            else:
                raise HTTPException(status_code=403, detail="need get captcha first")

        await check_captcha()
        request.session.pop("captcha_id", None)
    await handle_signup(session, body.name, current_email, body.password)

    return ORJSONResponse(status_code=200, content={"msg": "ok"})  # todo test


# 设置属性，例如头像 邮箱更改
@router.post("/profile")
async def set_profile(
    request: Request,
    body: UserSetProfile = Body(...),
    user_id: int = Depends(get_user_or_jump),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
):
    async def check_email():
        if email_id := request.session.get("email_id", None):
            current_email = await redis.get(f"email:pending:{email_id}")
            if not current_email:
                return ""
                # raise HTTPException(status_code=403, detail="email verify time out")
            if email_code := await redis.get(f"email:answer:{email_id}"):  # answer
                if ensure_str(email_code) != body.email_code:
                    return ""
            else:
                return ""
            return ensure_str(current_email)
        else:
            return ""

    current_email = await check_email()
    if current_email:
        request.session.pop("email_id", None)
    await handle_setprofile(session, user_id, body, current_email)
    return ORJSONResponse(status_code=200, content={"msg": "ok"})  # todo logo


@router.get("/profile", response_class=ORJSONResponse)
async def get_profile(
    user_id: int = Depends(get_user_or_jump),
    session: AsyncSession = Depends(get_db_session),
):
    return await handle_getprofile(session, user_id)


@router.post("/sign", description="签到")
async def hande_sign_(
    user_id: int = Depends(get_user_or_jump),
    session: AsyncSession = Depends(get_db_session),
    year: Optional[int] = Query(None, description="年份，用于补签"),
    month: Optional[int] = Query(None, description="月份，用于补签"),
    day: Optional[int] = Query(None, description="日期，用于补签"),
):
    await handle_sign(session, user_id, year, month, day)
    return ORJSONResponse(status_code=200, content={"msg": "ok"})


@router.get("/sign", description="查看签到")
async def get_sign(
    user_id: int = Depends(get_user_or_jump),
    session: AsyncSession = Depends(get_db_session),
    year: Optional[int] = Query(None, description="年份，用于补签"),
    month: Optional[int] = Query(None, description="月份，用于补签"),
):
    sign_data = await handle_get_sign(session, user_id, year, month)
    return ORJSONResponse(status_code=200, content={"msg": "ok", "sign": sign_data})


# 验证用户是否拥有对已知邮箱的控制权
email_template = """
您好，你正在进行{}的密码恢复。

您的验证码为: {}

验证码 {}秒内有效，如果不是本人操作，请忽略。"""


@router.post("/reset-password-email", description="重置密码时发送邮件")
async def handle_reset_password_sendemail(
    request: Request,
    body: UserResetPasswordEmail = Body(...),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    user_id: int = Depends(get_user),
):
    if user_id is not None:
        return ORJSONResponse(status_code=403, content={"msg": "already login"})
    if body.name is not None:
        user = await get_user_by_name(session, body.name)
    else:
        user = await get_user_by_email(session, body.email)
    # 不要告诉用户这个user是否存在
    if user is not None:
        email_id: str = secrets.token_hex(16)
        request.session.update({"email_id": email_id})
        token = generate_token(settings.email_token_num)
        await redis.set(f"email:answer:{email_id}", token, ex=settings.email_token_ttl)
        # 记录下当前正在验证的是哪个用户，免得用户收到验证码后换了另一个用户
        await redis.set(
            f"email:pendinguser:{email_id}", user.id, ex=settings.email_token_ttl
        )
        await send_email(
            settings.email_fromaddr,
            user.email,
            email_template.format(settings.site_name, token, settings.email_token_ttl),
            settings.email_smtp_server,
            settings.email_smtp_username,
            settings.email_smtp_password,
            settings.email_smtp_port,
        )
    return ORJSONResponse(
        status_code=200, content={"msg": "recovery code has been send to your email"}
    )
    # todo 两者返回消耗时间不一样，是否会被计时攻击？


@router.post("/reset-password", description="忘记密码")
async def handle_reset_password(
    request: Request,
    body: UserResetPassword = Body(...),
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
):
    async def check_email():
        if email_id := request.session.get("email_id", None):
            current_user = await redis.get(f"email:pendinguser:{email_id}")
            if not current_user:
                return 0
                # raise HTTPException(status_code=403, detail="email verify time out")
            if email_code := await redis.get(f"email:answer:{email_id}"):  # answer
                if ensure_str(email_code) != body.email_code:
                    return 0
            else:
                return 0
            return int(current_user)
        else:
            return 0

    current_user: int = await check_email()
    if current_user:
        request.session.pop("email_id", None)
        await reset_user_password(session, current_user, body.new_password)
    return ORJSONResponse(status_code=200, content={"msg": "ok"})
