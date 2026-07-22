from __future__ import annotations

from pydantic import BaseModel, Field


class BiliConfig(BaseModel):
    base_url: str = "https://www.bilibili.com"
    api_url: str = "https://api.bilibili.com"
    rate_limit: float = 1.0
    cookie: str = ""
    sessdata: str = ""
    bili_jct: str = ""
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
