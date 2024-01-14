# -*- coding: utf-8 -*-
"""
帖子板块相关
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.depends import get_db_session, get_user
from pyforum.routers.thread.crud import get_threads

router = APIRouter(prefix="/api/v1/thread", tags=["thread"])


@router.get("/", description="查看有那些版块", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_user),
    id: Optional[int] = Query(None, description="thread_id"),
):
    threads = await get_threads(session, user_id, id)
    return {
        "msg": "ok",
        "threads": [
            thread.model_dump(exclude_none=True, exclude={"auths"})
            for thread in threads
        ],
    }
