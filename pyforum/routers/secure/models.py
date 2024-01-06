"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from pydantic import BaseModel, EmailStr, Field


class RequestSendEmail(BaseModel):
    email: EmailStr = Field(..., description="要发送到的邮箱")
