# -*- coding: utf-8 -*-
"""
巡礼
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.depends import get_db_session, get_redis, get_user, get_user_or_jump
from pyforum.routers.view.crud import (
    add_viewaddress,
    get_viewaddress,
    patch_viewaddress,
)
from pyforum.routers.view.models import AddViewAddress, PatchViewAddress

router = APIRouter(prefix="/api/v1/view", tags=["admin"])


@router.get("/", description="查看有哪些地点")
async def _(
    session: AsyncSession = Depends(get_db_session),
    name: Optional[str] = Query(None, description=""),
    offset: Optional[int] = Query(0),
    limit: Optional[int] = Query(10),
):
    if limit > 20:
        raise HTTPException(403, "limit is too large")
    data = await get_viewaddress(session, name, offset, limit)
    return {"msg": "ok", "address": [i.dump() for i in data]}


@router.post("/", description="添加地点")
async def _(
    session: AsyncSession = Depends(get_db_session),
    uid: int = Depends(get_user_or_jump),
    body: AddViewAddress = Body(...),
):
    await add_viewaddress(session, body.name, uid, body.position, body.description)
    return {"msg": "ok"}


@router.patch("/", description="修改地点")
async def _(
    session: AsyncSession = Depends(get_db_session),
    uid: int = Depends(get_user_or_jump),
    body: PatchViewAddress = Body(...),
):
    await patch_viewaddress(
        session, body.id, body.name, body.position, body.description
    )
    return {"msg": "ok"}
