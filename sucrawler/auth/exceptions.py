from __future__ import annotations


class AuthError(Exception):
    """认证基异常。"""


class LoginFailedError(AuthError):
    """登录失败。"""


class LoginTimeoutError(AuthError):
    """登录超时。"""


class QRCodeExpiredError(AuthError):
    """二维码过期。"""


class InvalidCredentialError(AuthError):
    """凭证无效。"""
