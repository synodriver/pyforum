"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

envfile = str(Path(__file__).parent.parent.resolve() / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=envfile, env_file_encoding="utf-8")
    site_name: Optional[str] = Field("Pyforum", description="站点名字，用于发送email验证")
    timezone_offset: Optional[int] = Field(8, description="本地时间与 UTC 的时差，默认东八区")

    redis_dsn: RedisDsn = Field(
        "redis://localhost:6379/1",
        validation_alias=AliasChoices("service_redis_dsn", "redis_url"),
    )
    sqlite: Optional[str] = Field(None, description="可选的sqlite存储")
    pg_dsn: Optional[PostgresDsn] = Field(None, description="可选的postgresql存储")
    captcha_ttl: Optional[int] = Field(600, description="验证码超时时间")
    captcha_num: Optional[int] = Field(4, description="验证码位数")

    email_fromaddr: Optional[str] = Field("Pyforum", description="发送email时自己是谁")
    email_token_num: Optional[int] = Field(4, description="email验证码位数")
    email_token_ttl: Optional[int] = Field(600, description="email验证码超时时间")
    email_smtp_server: Optional[str] = Field(None, description="邮件服务器 用于发送邮件")
    email_smtp_username: Optional[str] = Field(None, description="用于发送邮件的用户名")
    email_smtp_password: Optional[str] = Field(None, description="用于发送邮件的密码")
    email_smtp_port: Optional[int] = Field(465, description="邮件服务器端口")

    session_prefix: Optional[str] = Field(
        "starsessions:", description="在redis中session的前缀"
    )

    debug: Optional[bool] = Field(False, description="开启后sqlmodel将会debug，启用debug的路由")
    use_captcha: Optional[bool] = Field(True, description="是否开启captcha")

    @model_validator(mode="after")
    def check_db(self) -> "Settings":
        if self.pg_dsn is None and self.sqlite is None:
            raise ValueError("one of sqlite or pg_dsn must be set")
        return self


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
