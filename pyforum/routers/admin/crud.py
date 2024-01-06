# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2024 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from typing import List, Literal, Optional

from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.models import Group, User
from pyforum.routers.admin import PatchUser, Search
from pyforum.utils import pwd_context


async def get_user_groups(
    session: AsyncSession, group_id: Optional[int] = None, name: Optional[str] = None
) -> List[Group]:
    group = []
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
    group_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    try:
        group = (await session.exec(select(Group).where(Group.name == name))).one()
        raise HTTPException(status_code=409, detail=f"group {name} already exists")
    except NoResultFound:
        group: Group = (
            await session.exec(select(Group).where(Group.id == group_id))
        ).one()
        if name is not None:
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


async def patch_user(session: AsyncSession, body: PatchUser):
    user = (await session.exec(select(User).where(User.id == body.id))).one()
    if body.name is not None:
        user.name = body.name
    if body.email is not None:
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
