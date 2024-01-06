"""
全局的依赖
"""
from typing import AsyncGenerator, Optional, cast

from fastapi.requests import Request
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.exceptions import RedirectException


async def get_user_or_jump(request: Request) -> int:
    """没登陆就跳转，通过查询redis中的session"""
    uid = request.session.get("user_id", None)
    if uid is not None:  # fixme 为什么会得到True？
        return uid
    else:
        raise RedirectException(307, "/")


async def get_user(request: Request) -> Optional[int]:
    return request.session.get("user_id", None)


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(request.state.sqla) as session:
        yield session


def get_redis(request: Request) -> Redis:
    return cast(Redis, request.state.redis)
