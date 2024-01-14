# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2024 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class AddGroup(BaseModel):
    name: str = Field(..., max_length=20)
    description: str = Field(..., max_length=200)


class PatchGroup(BaseModel):
    id: int = Field(...)
    name: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=200)

    # @model_validator(mode="after")
    # def check_self(self) -> "PatchGroup":
    #     if self.id is None:
    #         raise ValueError("id must be set")
    #     return self


class AddUser(BaseModel):
    name: str = Field(..., max_length=20)
    email: str = Field(..., max_length=50)
    password: str = Field(..., max_length=50)


class PatchUser(BaseModel):
    id: int = Field(...)
    name: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=50)
    logo: Optional[str] = Field(None)
    sign: Optional[str] = Field(None, max_length=100)
    activated: Optional[bool] = Field(None)


class Search(BaseModel):
    name: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    age: Optional[int] = Field(None)
    sign: Optional[str] = Field(None, max_length=100)


class UserAddGroup(BaseModel):
    user_id: int = Field(...)
    group_id: int = Field(...)


UserDelGroup = UserAddGroup


class UserDelCookie(BaseModel):
    id: int = Field(...)


class AddItemClass(BaseModel):
    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=200)


class DelItemClass(BaseModel):
    id: int = Field(...)
    delete_user: Optional[bool] = Field(False, description="是否在删除物品类的时候把用户拥有的该类物品也一起删了")


class PatchItemClass(BaseModel):
    id: int = Field(...)
    name: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=200)


class UserAddItem(BaseModel):
    user_id: int = Field(...)
    item_id: int = Field(...)
    count: Optional[int] = Field(1)


UserDelItem = UserAddItem


class AddThread(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=200)


class PatchThread(BaseModel):
    id: int = Field(...)
    name: Optional[str] = Field(..., max_length=200)
    description: Optional[str] = Field(..., max_length=200)
