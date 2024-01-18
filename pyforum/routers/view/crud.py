# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.models import ViewAddress


async def get_viewaddress(
    session: AsyncSession,
    name: Optional[str] = None,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10,
) -> List[ViewAddress]:
    if name is not None:
        addrs = (
            await session.exec(
                select(ViewAddress)
                .where(ViewAddress.name.like(f"%{name}%"))
                .offset(offset)
                .limit(limit)
            )
        ).all()
    else:
        addrs = (
            await session.exec(select(ViewAddress).offset(offset).limit(limit))
        ).all()
    return addrs


async def add_viewaddress(
    session: AsyncSession, name: str, uid: int, position: tuple, des: str
):
    try:
        (await session.exec(select(ViewAddress).where(ViewAddress.name == name))).one()
        raise HTTPException(status_code=409, detail=f"address {name} already exists")
    except NoResultFound:
        addr = ViewAddress(
            name=name,
            author_id=uid,
            position=f"POINT({position[0]} {position[1]})",
            description=des,
        )
        session.add(addr)
        await session.commit()


# async def search_viewaddress(session: AsyncSession, name: str) -> List[ViewAddress]:
#     addrs = (
#         await session.exec(
#             select(ViewAddress).where(ViewAddress.name.like(f"%{name}%"))
#         )
#     ).all()
#     return addrs
async def patch_viewaddress(
    session: AsyncSession,
    id: int,
    name: Optional[str] = None,
    position: Optional[tuple] = None,
    des: Optional[str] = None,
):
    addr: ViewAddress = (
        await session.exec(select(ViewAddress).where(ViewAddress.id == id))
    ).one()
    if name is not None:
        addr.name = name
    if position is not None:
        addr.pos = position
    if des is not None:
        addr.description = des
    session.add(addr)
    await session.commit()
