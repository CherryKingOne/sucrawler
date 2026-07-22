"""认证模块。

统一的登录认证框架，支持多平台、多登录方式。
"""
from .base import BaseAuthenticator
from .credential_store import CredentialStore
from .exceptions import (
    AuthError,
    InvalidCredentialError,
    LoginFailedError,
    LoginTimeoutError,
    QRCodeExpiredError,
)
from .qrcode import QRCodeUtils
from .types import CredentialInfo, LoginStatus, LoginType

__all__ = [
    "BaseAuthenticator",
    "CredentialStore",
    "QRCodeUtils",
    "LoginType",
    "LoginStatus",
    "CredentialInfo",
    "AuthError",
    "LoginFailedError",
    "LoginTimeoutError",
    "QRCodeExpiredError",
    "InvalidCredentialError",
]
