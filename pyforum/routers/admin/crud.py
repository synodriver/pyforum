# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2024 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from typing import List, Literal, Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.models import Group, Item, Thread, User, UserGroupLink, UserItemLink
from pyforum.routers.admin.models import PatchUser, Search
from pyforum.utils import pwd_context


async def get_user_groups(
    session: AsyncSession, group_id: Optional[int] = None, name: Optional[str] = None
) -> List[Group]:
    if group_id is not None:
        group = (await session.exec(select(Group).where(Group.id == group_id))).all()
    elif name is not None:
        group = (await session.exec(select(Group).where(Group.name == name))).all()
    else:
        # 全部group
        group = (await session.exec(select(Group))).all()
    return group


async def del_user_groups(session: AsyncSession, group_id: int):
    group = (await session.exec(select(Group).where(Group.id == group_id))).one()
    await session.delete(group)
    await session.commit()
    # 让NoResultFound抛出


async def add_user_group(session: AsyncSession, name: str, description: str):
    try:
        group = (await session.exec(select(Group).where(Group.name == name))).one()
        raise HTTPException(status_code=409, detail=f"group {name} already exists")
    except NoResultFound:
        group = Group(name=name, description=description)
        session.add(group)
        await session.commit()


async def patch_user_group(
    session: AsyncSession,
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    group: Group = (await session.exec(select(Group).where(Group.id == id))).one()
    if name is not None:
        group_count = (
            await session.exec(
                func.count(
                    select(Group.id).where(and_(Group.id != id, Group.name == name))
                )
            )
        ).one()[0]
        if group_count:
            raise HTTPException(status_code=409, detail=f"group {name} already exists")
        group.name = name
    if description is not None:
        group.description = description
    session.add(group)
    await session.commit()


async def add_user(session: AsyncSession, name: str, email: str, password: str):
    """
    其他的等用户自己登录了自己改
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
    user: User = User(name=name, email=email, password=pwd_context.hash(password))
    session.add(user)
    await session.commit()


async def del_user(session: AsyncSession, id: int):
    user = (await session.exec(select(User).where(User.id == id))).one()
    await session.delete(user)
    await session.commit()


async def get_user(
    session: AsyncSession, id: Optional[int] = None, name: Optional[str] = None
):
    if id is None and name is None:
        raise HTTPException(status_code=404, detail="one of id or name is required")
    user = None
    if id is not None:
        user = (await session.exec(select(User).where(User.id == id))).one()
    elif name is not None:
        user = (await session.exec(select(User).where(User.name == name))).one()
    if user is not None:
        return user


async def patch_user(session: AsyncSession, body: PatchUser):  # todo 判断重名
    user = (await session.exec(select(User).where(User.id == body.id))).one()
    if body.name is not None:
        user_count = (
            await session.exec(
                func.count(
                    select(User.id).where(
                        and_(User.name == body.name, User.id != body.id)
                    )
                )
            )
        ).one()[
            0
        ]  # 是否有重名的
        if user_count:
            raise HTTPException(
                status_code=409, detail=f"user {body.name} already exists"
            )
        user.name = body.name
    if body.email is not None:
        user_count = (
            await session.exec(
                func.count(
                    select(User.id).where(
                        and_(User.email == body.email, User.id != body.id)
                    )
                )
            )
        ).one()[
            0
        ]  # 是否有重email的
        if user_count:
            raise HTTPException(status_code=409, detail="email already exists")
        user.email = body.email
    if body.password is not None:
        user.password = pwd_context.hash(body.password)
    if body.logo is not None:
        user.logo = body.logo
    if body.sign is not None:
        user.sign = body.sign
    if body.activate is not None:
        user.activate = body.activated
    session.add(user)
    await session.commit()


async def search_user_or_group(
    session: AsyncSession,
    type: Literal["user", "group"],
    op: Literal["and", "or"],
    body: Search,
):
    if op == "and":
        op_ = and_
    elif op == "or":
        op_ = or_
    query = []
    if type == "user":
        if body.name is not None:
            query.append(User.name.like(f"%{body.name}%"))
        if body.email is not None:
            query.append(User.email.like(f"%{body.email}%"))
        if body.age is not None:
            query.append(User.age == body.age)
        if body.sign is not None:
            query.append(User.sign.like(f"%{body.sign}%"))

        users = (await session.exec(select(User).where(op_(*query)))).all()
        return users
    elif type == "group":
        if body.name is not None:
            query.append(Group.name.like(f"%{body.name}%"))
        if body.description is not None:
            query.append(Group.description.like(f"%{body.description}%"))
        groups = (await session.exec(select(Group).where(op_(*query)))).all()
        return groups


async def user_add_group(session: AsyncSession, user_id: int, group_id: int):
    try:
        (await session.exec(select(User).where(User.id == user_id))).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"user {user_id} not found")
    try:
        (await session.exec(select(Group).where(Group.id == group_id))).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"group {group_id} not found")
    try:
        link = UserGroupLink(user_id=user_id, group_id=group_id)
        session.add(link)
        await session.commit()
    except IntegrityError:
        # 已经是这个组的成员了
        raise HTTPException(
            status_code=409, detail=f"user {user_id} is already in group {group_id}"
        )


async def user_del_group(session: AsyncSession, user_id: int, group_id: int):
    link = (
        await session.exec(
            select(UserGroupLink).where(
                and_(
                    UserGroupLink.user_id == user_id, UserGroupLink.group_id == group_id
                )
            )
        )
    ).one()
    await session.delete(link)
    await session.commit()


async def user_get_group(
    session: AsyncSession,
    user_id: int,
) -> List[int]:
    links: List[UserGroupLink] = (
        await session.exec(
            select(UserGroupLink).where(UserGroupLink.user_id == user_id)
        )
    ).all()
    return [link.group_id for link in links]


async def add_item_class(session: AsyncSession, name: str, description: str):
    item_count = (
        await session.exec(func.count(select(Item.id).where(Item.name == name)))
    ).one()[0]
    if item_count:
        raise HTTPException(status_code=409, detail=f"item {name} already exists")
    item = Item(name=name, description=description)
    session.add(item)
    await session.commit()


async def del_item_class(session: AsyncSession, id: int, deluser: bool = False) -> None:
    item = (await session.exec(select(Item).where(Item.id == id))).one()
    await session.delete(item)
    await session.commit()
    if deluser:
        links = (
            await session.exec(select(UserItemLink).where(UserItemLink.item_id == id))
        ).all()
        for link in links:
            await session.delete(link)
        await session.commit()


async def get_item_class(session: AsyncSession, id: Optional[int] = None):
    if id is not None:
        items = (await session.exec(select(Item).where(Item.id == id))).all()
    else:
        items = (await session.exec(select(Item))).all()
    return items


async def patch_item_class(
    session: AsyncSession,
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    item = (await session.exec(select(Item).where(Item.id == id))).one()
    if name is not None:
        item_count = (
            await session.exec(
                func.count(
                    select(Item.id).where(and_(Item.id != id, Item.name == name))
                )
            )
        ).one()[0]
        if item_count:
            raise HTTPException(status_code=409, detail=f"item {name} already exists")
        item.name = name
    if description is not None:
        item.description = description
    session.add(item)
    await session.commit()


async def user_add_item(
    session: AsyncSession, user_id: int, item_id: int, count: Optional[int] = 1
):
    try:
        (await session.exec(select(User).where(User.id == user_id))).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"user {user_id} not found")
    try:
        (await session.exec(select(Item).where((Item.id == item_id)))).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"item {item_id} not found")

    try:
        link: UserItemLink = (
            await session.exec(
                select(UserItemLink).where(
                    and_(
                        UserItemLink.user_id == user_id, UserItemLink.item_id == item_id
                    )
                )
            )
        ).one()
        link.count += count
    except NoResultFound:  # 之前没有拥有过
        link = UserItemLink(user_id=user_id, item_id=item_id, count=count)
    session.add(link)
    await session.commit()


async def user_del_item(
    session: AsyncSession, user_id: int, item_id: int, count: Optional[int] = 1
):
    try:
        (await session.exec(select(User).where(User.id == user_id))).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"user {user_id} not found")
    try:
        (await session.exec(select(Item).where((Item.id == item_id)))).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"item {item_id} not found")

    try:
        link: UserItemLink = (
            await session.exec(
                select(UserItemLink).where(
                    and_(
                        UserItemLink.user_id == user_id, UserItemLink.item_id == item_id
                    )
                )
            )
        ).one()
        link.count -= count  # 允许减成负数
        session.add(link)
        await session.commit()
    except NoResultFound:
        return


async def user_get_item(session: AsyncSession, user_id: int) -> list:
    ret = []
    links = (
        await session.exec(select(UserItemLink).where(UserItemLink.user_id == user_id))
    ).all()
    # await session.ref
    for link in links:
        await session.refresh(link, ["count", "item"])
        d = link.item.model_dump()
        d["count"] = link.count
        ret.append(d)
    return ret


async def add_thread(session: AsyncSession, name: str, description: str):
    try:
        thread = (await session.exec(select(Thread).where(Thread.name == name))).one()
        raise HTTPException(status_code=409, detail=f"thread {name} already exists")
    except NoResultFound:
        thread = Thread(name=name, description=description)
        session.add(thread)
        await session.commit()


async def del_thread(session: AsyncSession, id: int) -> None:
    thread = (await session.exec(select(Thread).where(Thread.id == id))).one()
    await session.delete(thread)
    await session.commit()


async def get_thread(
    session: AsyncSession, id: Optional[int] = None, name: Optional[str] = None
) -> List[Thread]:
    if id is not None:
        threads = (await session.exec(select(Thread).where(Thread.id == id))).all()
    elif name is not None:
        threads = (await session.exec(select(Thread).where(Thread.name == name))).all()
    else:
        # 全部group
        threads = (await session.exec(select(Thread))).all()
    return threads


async def patch_thread(
    session: AsyncSession,
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    thread: Thread = (await session.exec(select(Thread).where(Thread.id == id))).one()
    if name is not None:
        thread_count = (
            await session.exec(
                func.count(
                    select(Thread.id).where(and_(Thread.id != id, Thread.name == name))
                )
            )
        ).one()[0]
        if thread_count:
            raise HTTPException(status_code=409, detail=f"thread {name} already exists")
        thread.name = name
    if description is not None:
        thread.description = description
    session.add(thread)
    await session.commit()
