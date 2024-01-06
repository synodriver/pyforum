# -*- coding: utf-8 -*-
"""
Copyright (c) 2008-2024 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from unittest import IsolatedAsyncioTestCase
from urllib.parse import urljoin

from httpx import AsyncClient
from redis.asyncio import Redis


class TestApi(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.url = "http://127.0.0.1:8000/api/v1/"
        self.redis = Redis.from_url("redis://192.168.0.5:6379/10")
        # keys = await self.redis.keys("email:*")
        # for key in keys:
        #     await self.redis.delete(key)
        # keys = await self.redis.keys("captcha:*")
        # for key in keys:
        #     await self.redis.delete(key)

    async def asyncTearDown(self):
        pass

    async def test_signup_without_check(self):
        async with AsyncClient() as client:
            resp = await client.post(
                urljoin(self.url, "user/signup"),
                json={
                    "name": "test",
                    "email": "abc@gmail.com",
                    "password": "<PASSWORD>",
                    "captcha": "",
                    "email_code": "",
                },
            )
            self.assertEqual(resp.status_code, 403, f"{resp.text}")

    async def test_signup_wrong_email_format(self):
        async with AsyncClient() as client:
            resp = await client.post(
                urljoin(self.url, "user/signup"),
                json={
                    "name": "test",
                    "email": "abcail.com",
                    "password": "<PASSWORD>",
                    "captcha": "",
                    "email_code": "",
                },
            )
            self.assertEqual(resp.status_code, 422, f"{resp.text}")


if __name__ == "__main__":
    import unittest

    unittest.main()
