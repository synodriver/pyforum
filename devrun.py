"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

from pyforum import app

kw = {"accesslog": "-", "loglevel": "DEBUG"}
config = Config.from_mapping(kw)
config.bind = "0.0.0.0:8000"

asyncio.run(serve(app, config))
