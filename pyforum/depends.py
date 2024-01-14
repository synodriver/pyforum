"""
全局的依赖
"""
from typing import AsyncGenerator, List, Optional, cast

from fastapi import Depends, HTTPException
from fastapi.requests import Request
from redis.asyncio import Redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.exceptions import RedirectException
from pyforum.models import Thread, ThreadAuth, UserGroupLink, UserItemLink


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


async def get_groups(
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_user_or_jump),
) -> List[int]:
    links: List[UserGroupLink] = (
        await session.exec(
            select(UserGroupLink).where(UserGroupLink.user_id == user_id)
        )
    ).all()
    return [link.group_id for link in links]


async def check_admin_or_raise(group_ids: List[int] = Depends(get_groups)):
    if 2 not in group_ids:
        raise HTTPException(status_code=403, detail="unauthorized")


async def check_user_auth_for_threads(
    session: AsyncSession, threads: List[Thread], user_id: Optional[int] = None
) -> List[Thread]:
    invalid_threads: List[int] = []
    if user_id is not None:
        for thread in threads:
            await session.refresh(thread, ["id", "title", "description", "auths"])

            itemlinks: List[UserItemLink] = (
                await session.exec(
                    select(UserItemLink).where(UserItemLink.user_id == user_id)
                )
            ).all()
            for auth in thread.auths:  # 里面的每一项必须满足
                for itemlink in itemlinks:
                    if (
                        itemlink.item_id == auth.item_id
                        and itemlink.count >= auth.count
                    ):
                        break
                else:
                    # auth.item_id auth.count 这项不满足 要么没有要么数量不够
                    invalid_threads.append(thread.id)
                    break
    else:
        for thread in threads:
            await session.refresh(thread, ["id", "title", "description", "auths"])
            for auth in thread.auths:  # 里面的每一项必须满足
                if auth.count > 0:  # 因为用户没登录，认为啥也没有
                    invalid_threads.append(thread.id)
                    break
    return [thread for thread in threads if thread.id not in invalid_threads]
