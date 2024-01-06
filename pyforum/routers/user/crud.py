# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import HTTPException
from fastapi.requests import Request
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import noload, selectinload
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.config import settings
from pyforum.models import Sign, User
from pyforum.routers.user.models import UserGetProfile, UserSetProfile
from pyforum.utils import pwd_context


async def verify_password_login(
    session: AsyncSession,
    request: Request,
    password: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
) -> Union[bool, int]:
    user: Optional[User] = None
    try:
        if username is not None:
            user = (
                await session.exec(
                    select(User).where(
                        and_(User.name == username, User.activated == True)
                    )
                )
            ).one()
        elif email is not None:
            user = (
                await session.exec(
                    select(User).where(
                        and_(User.email == email, User.activated == True)
                    )
                )
            ).one()
    except NoResultFound:
        return False  # 查无此人
    if not user.activated:
        return False  # 已经注销了
    if not pwd_context.verify(password, user.password):
        return False  # 密码不对
    # 只有登录才会检查，因此此处更新last_login
    user.last_login = datetime.now(
        tz=timezone(timedelta(hours=settings.timezone_offset))
    )
    user.last_ip = request.client.host
    session.add(user)
    await session.commit()
    await session.refresh(user)  # ["link", "id"]
    return user.id


async def handle_signup(session: AsyncSession, name: str, email: str, password: str):
    """
    处理注册
    :param session:
    :param name:
    :param email:
    :param password:
    :return:
    """
    user_count = (
        await session.exec(
            func.count(
                select(User.id).where(or_(User.name == name, User.email == email))
            )
        )
    ).one()[0]
    if user_count:
        raise HTTPException(status_code=409, detail="user name or email already exists")
    session.add(User(name=name, email=email, password=pwd_context.hash(password)))
    await session.commit()


async def handle_setprofile(
    session: AsyncSession, user_id: int, body: UserSetProfile, email: str
):
    user: User = (await session.exec(select(User).where(User.id == user_id))).one()
    if body.name is not None:
        user_count = (
            await session.exec(
                func.count(
                    select(User.id).where(
                        and_(User.name == body.name, User.id != user_id)
                    )
                )
            )
        ).one()[
            0
        ]  # 是否有重名的
        if user_count:
            raise HTTPException(status_code=409, detail="user name already exists")
        user.name = body.name
    if email:
        user_count = (
            await session.exec(
                func.count(
                    select(User.id).where(and_(User.email == email, User.id != user_id))
                )
            )
        ).one()[
            0
        ]  # 是否有重email的
        if user_count:
            raise HTTPException(status_code=409, detail="email already exists")
        user.email = email
    if body.password is not None:
        user.password = pwd_context.hash(body.password)
    if body.logo is not None:
        user.logo = body.logo
    if body.sign is not None:
        user.sign = body.sign
    session.add(user)
    await session.commit()


async def handle_getprofile(session: AsyncSession, user_id: int):
    user: User = (await session.exec(select(User).where(User.id == user_id))).one()
    return UserGetProfile.model_validate(user.model_dump(exclude_none=True)).model_dump(
        exclude_none=True
    )


async def get_user_by_name(session: AsyncSession, name: str):
    user: User = (
        await session.exec(select(User).where(User.name == name))
    ).one_or_none()
    return user


async def get_user_by_email(session: AsyncSession, email: str):
    user: User = (
        await session.exec(select(User).where(User.email == email))
    ).one_or_none()
    return user


async def reset_user_password(session: AsyncSession, user_id: int, new_password: str):
    user: User = (await session.exec(select(User).where(User.id == user_id))).one()
    user.password = pwd_context.hash(new_password)
    session.add(user)
    await session.commit()


async def handle_sign(
    session: AsyncSession,
    user_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
):
    """
    签到逻辑
    :param session:
    :param user_id:
    :return:
    """
    if year is not None and month is not None and day is not None:
        now = datetime(year=year, month=month, day=day)
    else:
        now = datetime.now(tz=timezone(timedelta(hours=settings.timezone_offset)))
    try:
        sign: Sign = (
            await session.exec(
                select(Sign).where(
                    and_(
                        Sign.user_id == user_id,
                        Sign.year == now.year,
                        Sign.month == now.month,
                    )
                )
            )
        ).one()
    except NoResultFound:  # 本月第一次
        sign: Sign = Sign(user_id=user_id, year=now.year, month=now.month)
    sign.set_sign(now.day)
    session.add(sign)
    await session.commit()


async def handle_get_sign(
    session: AsyncSession,
    user_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    """
    查看签到数据
    :param month:
    :param year:
    :param session:
    :param user_id:
    :return:
    """
    if year is not None and month is not None:
        now = datetime(year=year, month=month, day=1)
        if now > datetime.now(tz=timezone(timedelta(hours=settings.timezone_offset))):
            raise HTTPException(
                status_code=403, detail="can't get sign data of future"
            )  # 不能查看未来的签到数据
    else:
        now = datetime.now(tz=timezone(timedelta(hours=settings.timezone_offset)))
    try:
        sign: Sign = (
            await session.exec(
                select(Sign).where(
                    and_(
                        Sign.user_id == user_id,
                        Sign.year == now.year,
                        Sign.month == now.month,
                    )
                )
            )
        ).one()
    except NoResultFound:  # 本月第一次 todo 用户乱查看未来的数据岂不是数据库爆炸 因此非特权用户不得查看
        sign: Sign = Sign(user_id=user_id, year=now.year, month=now.month)
        session.add(sign)
        await session.commit()
        await session.refresh(sign)
    return sign.to_list()
