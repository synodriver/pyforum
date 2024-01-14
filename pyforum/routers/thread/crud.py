# -*- coding: utf-8 -*-
from typing import List, Optional, Union

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.depends import check_user_auth_for_threads
from pyforum.models import Thread, ThreadAuth


async def get_threads(
    session: AsyncSession, user_id: Optional[int] = None, id: Optional[int] = None
) -> List[Thread]:
    """

    :param session:
    :param user_id: None就是没登录
    :param id: thread_id
    :return:
    """
    # todo 对不同的user限制返回的内容
    if id is not None:
        threads: list = (
            await session.exec(select(Thread).where(Thread.id == id))
        ).all()
    else:
        threads: list = (await session.exec(select(Thread))).all()
    threads = await check_user_auth_for_threads(session, threads, user_id)
    return threads
