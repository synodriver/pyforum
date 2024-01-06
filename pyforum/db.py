# -*- coding: utf-8 -*-
"""
各种数据库连接
"""
import os
from contextlib import asynccontextmanager

from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import create_async_engine

from pyforum.config import settings

gallib = None
redis = None

if os.name == "nt":
    HOST = "192.168.0.5"  # local mysql5.7 server
else:
    HOST = "127.0.0.1"


@asynccontextmanager
async def lifespan(app):
    global gallib
    global redis
    redis = await from_url(str(settings.redis_dsn))
    gallib = create_async_engine(
        settings.sqlite or settings.pg_dsn, echo=settings.debug
    )
    yield {"redis": redis, "sqla": gallib}  # request.state
    await redis.close()
