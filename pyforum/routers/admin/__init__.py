"""
管理endpoint
"""
import gc
from typing import List, Literal, Optional

import orjson
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.config import settings
from pyforum.depends import check_admin_or_raise, get_db_session, get_groups, get_redis
from pyforum.routers.admin.crud import (
    add_item_class,
    add_user,
    add_user_group,
    del_item_class,
    del_user,
    del_user_groups,
    get_item_class,
    get_user,
    get_user_groups,
    patch_item_class,
    patch_user,
    patch_user_group,
    search_user_or_group,
    user_add_group,
    user_add_item,
    user_del_group,
    user_del_item,
    user_get_group,
    user_get_item,
)
from pyforum.routers.admin.models import (
    AddGroup,
    AddItemClass,
    AddUser,
    DelItemClass,
    PatchGroup,
    PatchItemClass,
    PatchUser,
    Search,
    UserAddGroup,
    UserAddItem,
    UserDelCookie,
    UserDelGroup,
    UserDelItem,
)

router = APIRouter(
    prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(check_admin_or_raise)]
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


@router.post("/user/group", description="添加用户所属的组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: UserAddGroup = Body(...)
):
    await user_add_group(session, body.user_id, body.group_id)
    return {"msg": "ok"}


@router.get("/user/group", description="获取用户所属的组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    id: int = Query(..., description=""),
):
    groups = await user_get_group(session, id)
    return {"msg": "ok", "groups": groups}


@router.delete("/user/group", description="删除用户所属的组", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: UserDelGroup = Body(...)
):
    await user_del_group(session, body.user_id, body.group_id)
    return {"msg": "ok"}


@router.delete("/user/cookie", description="让指定用户的登录失效", response_class=ORJSONResponse)
async def _(redis: Redis = Depends(get_redis), body: UserDelCookie = Body(...)):
    find = []
    async for key in redis.scan_iter(settings.session_prefix + "*", 10):
        cookie = await redis.get(key)
        cookie_dict = orjson.loads(cookie)
        if cookie_dict["user_id"] == body.id:
            find.append(key)
    await redis.delete(*find)
    return {"msg": "ok"}


@router.delete("/cookie", description="让全部访客的登录失效", response_class=ORJSONResponse)
async def _(redis: Redis = Depends(get_redis)):
    find = []
    async for key in redis.scan_iter(settings.session_prefix + "*", 10):
        cookie = await redis.get(key)
        cookie_dict = orjson.loads(cookie)
        if "user_id" not in cookie_dict:
            find.append(key)
    await redis.delete(*find)
    return {"msg": "ok"}


@router.post("/item", description="增加一种物品", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: AddItemClass = Body(...)
):
    await add_item_class(session, body.name, body.description)
    return {"msg": "ok"}


@router.delete("/item", description="删除一种物品", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: DelItemClass = Body(...)
):
    await del_item_class(session, body.id, body.delete_user)
    return {"msg": "ok"}


@router.get("/item", description="查看全部物品种类", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session),
    id: Optional[int] = Query(None, description="item_id"),
):
    items = await get_item_class(session, id)
    return {"msg": "ok", "items": [i.model_dump() for i in items]}


@router.patch("/item", description="修改物品类", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: PatchItemClass = Body(...)
):
    await patch_item_class(session, body.id, body.name, body.description)
    return {"msg": "ok"}


@router.post("/user/item", description="给用户发物品", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: UserAddItem = Body(...)
):
    await user_add_item(session, body.user_id, body.item_id, body.count)
    return {"msg": "ok"}


@router.delete("/user/item", description="给用户删除物品", response_class=ORJSONResponse)
async def _(
    session: AsyncSession = Depends(get_db_session), body: UserDelItem = Body(...)
):
    await user_del_item(session, body.user_id, body.item_id, body.count)
    return {"msg": "ok"}


@router.get("/user/item", description="查看用户有哪些物品", response_class=ORJSONResponse)
async def _(session: AsyncSession = Depends(get_db_session), id: int = Query(...)):
    items = await user_get_item(session, id)
    return {"msg": "ok", "items": items}


#### thread帖子相关


@router.post("/gc", description="垃圾回收 降低内存占用", response_class=ORJSONResponse)
async def _():
    gc.collect()
    return {"msg": "ok"}
