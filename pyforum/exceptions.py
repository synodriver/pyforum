"""
自定义异常
"""


class RedirectException(Exception):
    def __init__(self, status_code: int = 307, url: str = "/"):
        self.status_code = status_code
        self.url = url
