# -*- coding: utf-8 -*-
"""
数据库orm对象
"""
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import List, Optional

from bitarray import bitarray
from pydantic import FilePath
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, Relationship, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from pyforum.config import settings

tz = timezone(timedelta(hours=settings.timezone_offset))


class UserGroupLink(SQLModel, table=True):
    """
    用户-组 m-m
    """

    __tablename__ = "user_group_link"
    user_id: Optional[int] = Field(None, foreign_key="user.id", primary_key=True)
    group_id: Optional[int] = Field(None, foreign_key="group.id", primary_key=True)


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(None, primary_key=True)
    name: str = Field(...)
    age: Optional[int] = Field(None, gt=0, lt=200)
    email: Optional[str] = Field(None)
    password: str = Field(..., description="hashed password")
    logo: Optional[str] = Field(None, description="头像")
    sign: Optional[str] = Field(None, description="签名")
    create_time: datetime = Field(
        default_factory=partial(datetime.now, tz=tz), description="注册时间"
    )
    last_login: Optional[datetime] = Field(None, description="上次是什么时候登录的")
    last_ip: Optional[str] = Field(None, description="上次登录的ip")
    activated: Optional[bool] = Field(True, description="用户是否有效，反之已经注销")

    user_item_link: List["UserItemLink"] = Relationship(
        back_populates="user"
    )  # sa_relationship_kwargs={"lazy": "selectin"})
    groups: List["Group"] = Relationship(
        back_populates="users", link_model=UserGroupLink
    )


class Group(SQLModel, table=True):
    """
    用户组
    """

    __tablename__ = "group"
    id: Optional[int] = Field(None, primary_key=True)
    name: str = Field(...)
    description: Optional[str] = Field(None, description="本用户组的描述")
    users: List[User] = Relationship(back_populates="groups", link_model=UserGroupLink)


class Sign(SQLModel, table=True):
    """
    签到表 todo 这东西要加锁吗？
    """

    __tablename__ = "sign"
    id: Optional[int] = Field(None, primary_key=True)
    user_id: int = Field(..., description="那个用户", foreign_key="user.id")
    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份")
    data: Optional[int] = Field(
        0, description="一个4字节的int一共有32位，存储一个月至多31天的签到数据，对应的位如果是1就表示当天有签到"
    )

    def get_sign(self, day: int):
        """
        看看第几天有没有签到
        :param day: 1-31天
        :return:
        """
        a = bitarray(endian="little")
        a.frombytes(self.data.to_bytes(4, "little"))
        return a[day - 1]

    def set_sign(self, day: int):
        """
        设置第几天的签到
        :param day: 1-31天
        :return:
        """
        a = bitarray(endian="little")
        a.frombytes(self.data.to_bytes(4, "little"))
        a[day - 1] = 1
        self.data = int.from_bytes(a.tobytes(), "little")

    def unset_sign(self, day: int):
        """
        怎么还会有人要取消签到的……先写着吧
        :param day: 1-31天
        :return:
        """
        a = bitarray(endian="little")
        a.frombytes(self.data.to_bytes(4, "little"))
        a[day - 1] = 0
        self.data = int.from_bytes(a.tobytes(), "little")

    def to_list(self) -> list:
        a = bitarray(endian="little")
        a.frombytes(self.data.to_bytes(4, "little"))
        return a.tolist()


class Item(SQLModel, table=True):
    """
    用户拥有的物品（权限也是
    """

    __tablename__ = "item"
    id: Optional[int] = Field(None, primary_key=True)
    name: str = Field(...)
    description: Optional[str] = Field(None, description="对物品的描述")

    user_item_link: List["UserItemLink"] = Relationship(
        back_populates="item"
    )  # sa_relationship_kwargs={"lazy": "selectin"})
    auths: List["ThreadAuth"] = Relationship(back_populates="item")

class UserItemLink(SQLModel, table=True):
    """
    用户-物品多对多关系表
    """

    __tablename__ = "user_item_link"
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    item_id: Optional[int] = Field(
        default=None, foreign_key="item.id", primary_key=True
    )
    count: int = Field(default=1, description="物品数量")

    user: User = Relationship(
        back_populates="user_item_link"
    )  # sa_relationship_kwargs={"lazy": "selectin"})
    item: Item = Relationship(
        back_populates="user_item_link"
    )  # sa_relationship_kwargs={"lazy": "selectin"})


class Thread(SQLModel, table=True):
    """板块"""

    __tablename__ = "thread"
    id: Optional[int] = Field(None, primary_key=True)
    title: str = Field(...)
    description: str = Field(..., description="描述")

    auths: List["ThreadAuth"] = Relationship(back_populates="thread")


class ThreadAuth(SQLModel, table=True):
    """
    板块{thread_id}所需要的权限 为{item_id}>={count}
    """

    __tablename__ = "thread_auth"
    id: Optional[int] = Field(None, primary_key=True)
    thread_id: Optional[int] = Field(None, foreign_key="thread.id")
    item_id: int = Field(..., foreign_key="item.id")
    count: int = Field(default=0, description="")

    thread: Thread = Relationship(back_populates="auths")
    item: Item = Relationship(back_populates="auths")


async def init_db():
    sqlite_file_name = "data.db"
    sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"
    engine = create_async_engine(sqlite_url, echo=True)
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def test_query():
    from sqlmodel import func, select

    sqlite_file_name = "data.db"
    sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"
    engine = create_async_engine(sqlite_url, echo=True)
    async with AsyncSession(engine) as session:
        # users = (await session.exec(select(User).where(User.name.like("%sy%")))).all()
        users = (await session.exec(select(User).where(User.name == "1213213"))).all()
        print(users)


if __name__ == "__main__":
    import asyncio

    # asyncio.run(init_db())
    asyncio.run(test_query())
