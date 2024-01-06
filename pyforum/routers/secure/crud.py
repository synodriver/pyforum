"""
各种逻辑
"""
import random
from io import BytesIO
from typing import Tuple

from captcha.image import ImageCaptcha

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
