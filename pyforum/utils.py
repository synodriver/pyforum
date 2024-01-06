# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
import asyncio
import random
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from io import BytesIO
from typing import Tuple

import aiosmtplib
from captcha.image import ImageCaptcha
from passlib.context import CryptContext

from pyforum.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def ensure_str(data):
    if isinstance(data, str):
        return data
    elif isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8")
    else:
        return str(data)


async def send_email(
    fromaddr: str,
    to: str,
    content: str,
    smtp_server: str,
    username: str,
    password: str,
    port: int = 465,
):
    if settings.debug:
        print(content)
    else:
        msg = MIMEText(content, "plain", "utf-8")
        msg["From"] = fromaddr
        msg["To"] = to
        msg["Subject"] = "验证消息"
        async with aiosmtplib.SMTP(
            hostname=smtp_server,
            port=port,
            use_tls=True,
            username=username,
            password=password,
        ) as smtp:
            await smtp.send_message(msg)


image = ImageCaptcha()
seed = "1234567890abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_captcha(num: int) -> Tuple[BytesIO, str]:
    captcha_str = "".join(random.choice(seed) for _ in range(num))
    image = ImageCaptcha().generate_image(captcha_str)
    buffer = BytesIO()
    image.save(buffer, "jpeg")
    buffer.seek(0, 0)
    return buffer, captcha_str


def generate_token(num: int) -> str:
    return "".join(random.choice(seed) for _ in range(num))
