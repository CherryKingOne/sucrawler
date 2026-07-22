from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LoginType(str, Enum):
    """登录方式。"""

    QRCODE = "qrcode"
    PHONE = "phone"
    COOKIE = "cookie"


class LoginStatus(str, Enum):
    """登录状态。"""

    LOGGED_OUT = "logged_out"
    LOGGING_IN = "logging_in"
    LOGGED_IN = "logged_in"
    EXPIRED = "expired"


class CredentialInfo(BaseModel):
    """凭证信息。"""

    platform: str
    login_type: LoginType
    status: LoginStatus = LoginStatus.LOGGED_OUT
    cookies: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None
    extra: dict = Field(default_factory=dict)

    def is_valid(self) -> bool:
        """检查凭证是否有效。"""
        if self.status != LoginStatus.LOGGED_IN:
            return False
        if self.expires_at and self.expires_at < datetime.now():
            return False
        return True
