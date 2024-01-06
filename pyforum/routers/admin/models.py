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
