"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserLogin(BaseModel):
    name: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=50)
    password: str = Field(..., max_length=50, description="明文密码")
    captcha: Optional[str] = Field("", max_length=20, description="验证答案")

    @model_validator(mode="after")
    def check_name_or_email(self) -> "UserLogin":
        if self.name is None and self.email is None:
            raise ValueError("must provide either name or email")
        return self


class UserRegister(BaseModel):
    name: str = Field(..., max_length=20)
    password: str = Field(..., max_length=50, description="未hash的")
    captcha: Optional[str] = Field("", max_length=20, description="验证答案")
    email_code: str = Field(..., max_length=20, description="发到邮箱的验证码")


class UserResetPasswordEmail(BaseModel):
    """
    忘记密码 重置 验证邮箱
    """

    name: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=50)

    @model_validator(mode="after")
    def check_name_email(self) -> "UserResetPasswordEmail":
        if self.name is None and self.email is None:
            raise ValueError("one of name or email must be set")
        return self


class UserResetPassword(BaseModel):
    """
    忘记密码 重置
    """

    new_password: str = Field(..., max_length=50, description="未hash的")
    email_code: str = Field(..., max_length=20, description="发到邮箱的验证码")


class UserSetProfile(BaseModel):
    """可以只修改一部分 因此全部是可选字段"""

    name: Optional[str] = Field(None, max_length=20, description="修改名字")
    age: Optional[int] = Field(None, gt=0, lt=200)
    # email: Optional[EmailStr] = Field(None, description="修改邮箱，需要重新验证") # 从cookie拿
    password: Optional[str] = Field(None, max_length=50, description="修改密码，未hash的")
    logo: Optional[str] = Field(None)
    sign: Optional[str] = Field(None, max_length=100, description="签名")
    email_code: Optional[str] = Field(None, max_length=20, description="发到邮箱的验证码")


class UserGetProfile(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    id: int = Field(..., description="uid")  # serialization_alias="user_id")
    name: str = Field(..., max_length=20)
    age: Optional[int] = Field(None, gt=0, lt=200)
    email: Optional[EmailStr] = Field(None, max_length=50)
    logo: Optional[str] = Field(None)
    sign: Optional[str] = Field(None, max_length=100, description="签名")
