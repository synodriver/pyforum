# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2024 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from typing import Optional, Sequence

from pydantic import BaseModel, Field


class AddViewAddress(BaseModel):
    name: str = Field(..., description="")
    position: Sequence[float, float] = Field(..., description="")
    description: str = Field(..., description="")


class PatchViewAddress(BaseModel):
    id: int = Field(..., description="")
    name: Optional[str] = Field(None, description="")
    position: Optional[Sequence[float, float]] = Field(None, description="")
    description: Optional[str] = Field(None, description="")
