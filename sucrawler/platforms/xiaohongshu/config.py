from __future__ import annotations

from pydantic import BaseModel, Field


class XHSConfig(BaseModel):
    base_url: str = "https://www.xiaohongshu.com"
    api_url: str = "https://edith.xiaohongshu.com/api/sns/web/v1"
    rate_limit: float = 1.0
    cookie: str = ""
    sign_key: str = ""
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
