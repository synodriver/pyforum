"""
管理endpoint
"""
from typing import Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.depends import get_db_session
from pyforum.routers.admin.crud import (
    add_user,
    add_user_group,
    del_user,
    del_user_groups,
    get_user,
    get_user_groups,
    patch_user,
    patch_user_group,
    search_user_or_group,
)
from pyforum.routers.admin.models import (
    AddGroup,
    AddUser,
    PatchGroup,
    PatchUser,
    Search,
)

router = APIRouter(
    prefix="/api/v1/admin", tags=["admin"], dependencies=[]
)  # todo check admin


@router.get(
    "/user_group",
    description="查询用户组",
    response_class=ORJSONResponse,
    summary="如果id和name都没有则返回全部",
)
async def _(
    session: AsyncSession = Depends(get_db_session),
    id: Optional[int] = Query(None, description="group_id"),
    name: Optional[str] = Query(None, description="group_name"),
):
    groups = await get_user_groups(session, id, name)
    return {"msg": "ok", "groups": [g.model_dump() for g in groups]}


@router.post("/user_group", description="添加用户组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: AddGroup = Body(...)
):
    await add_user_group(session, body.name, body.description)
    return {"msg": "ok"}


@router.delete("/user_group", description="删除用户组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    id: int = Query(..., description="group_id"),
):
    await del_user_groups(session, id)
    return {"msg": "ok"}


@router.patch("/user_group", description="修改用户组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: PatchGroup = Body(...)
):
    await patch_user_group(session, body.id, body.name, body.description)
    return {"msg": "ok"}


@router.post("/user", description="新增用户", response_class=ORJSONResponse)
async def _(session: AsyncSession = Depends(get_db_session), body: AddUser = Body(...)):
    await add_user(session, body.name, body.email, body.password)
    return {"msg": "ok"}


@router.delete("/user", description="删除用户", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    id: int = Query(..., description="user_id"),
):
    await del_user(session, id)
    return {"msg": "ok"}


@router.get("/user", description="查询用户", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    id: Optional[int] = Query(None, description="user_id"),
    name: Optional[str] = Query(None, description="user name"),
):
    user = await get_user(session, id, name)
    return {
        "msg": "ok",
        "user": user.model_dump(exclude=["password"], exclude_none=True),
    }


@router.patch("/user", description="修改用户", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: PatchUser = Body(...)
):
    await patch_user(session, body)
    return {"msg": "ok"}


@router.post("/search", description="搜索用户或用户组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    type: Literal["user", "group"] = Query(..., description="查询类型"),
    op: Literal["and", "or"] = Query(..., description="操作类型"),
    body: Search = Body(...),
):
    data = await search_user_or_group(session, type, op, body)
    return {
        "msg": "ok",
        "data": [d.model_dump(exclude_none=True, exclude=["password"]) for d in data],
    }
