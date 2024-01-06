"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, RedirectResponse
from sqlalchemy.exc import NoResultFound
from starlette.responses import JSONResponse
from starsessions import SessionAutoloadMiddleware, SessionMiddleware
from starsessions.stores.redis import RedisStore

from pyforum.config import settings
from pyforum.db import lifespan
from pyforum.exceptions import RedirectException
from pyforum.routers import secure, user

app = FastAPI(
    title=settings.site_name, description="论坛后端", version="0.0.1", lifespan=lifespan
)

app.include_router(user.router)
app.include_router(secure.router)

#### 加session中间件
from starsessions.serializers import Serializer


class ORJsonSerializer(Serializer):
    def serialize(self, data: Any) -> bytes:
        return orjson.dumps(data)

    def deserialize(self, data: bytes):
        if not data:
            return {}
        return orjson.loads(data)  # type: ignore[no-any-return]


app.add_middleware(SessionAutoloadMiddleware)
app.add_middleware(
    SessionMiddleware,
    store=RedisStore(url=str(settings.redis_dsn), prefix=settings.session_prefix),
    lifetime=3600 * 24 * 180,  # cookie有效期半年,如果登录会延长
    rolling=True,
    serializer=ORJsonSerializer(),
)


# 后端处理时间，debug only
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(RedirectException)
async def redirect_exception_handler(request, exc: RedirectException):
    return RedirectResponse(exc.url, exc.status_code)


@app.exception_handler(NoResultFound)
async def _(request, exc: NoResultFound):
    return ORJSONResponse(status_code=404, content={"msg": "not found"})


# monkey patch
import orjson
from starlette import requests

requests.json = orjson
from fastapi import exception_handlers
from fastapi.responses import ORJSONResponse

exception_handlers.JSONResponse = ORJSONResponse
