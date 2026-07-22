from __future__ import annotations

import re


def extract_user_id_from_url(url: str) -> str | None:
    cleaned = url.strip().strip('"').strip("'")

    patterns = [
        r"bilibili\.com/(\d+)",
        r"space\.bilibili\.com/(\d+)",
        r"xiaohongshu\.com/user/profile/([a-zA-Z0-9]+)",
        r"xiaohongshu\.com/user/([a-zA-Z0-9]+)",
        r"/profile/([a-zA-Z0-9]+)",
        r"/user/([a-zA-Z0-9]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return match.group(1)
    return None


def detect_platform_from_url(url: str) -> str | None:
    cleaned = url.strip().strip('"').strip("'").lower()

    if "bilibili.com" in cleaned:
        return "bilibili"
    if "xiaohongshu.com" in cleaned or "xhslink.com" in cleaned:
        return "xiaohongshu"
    return None
