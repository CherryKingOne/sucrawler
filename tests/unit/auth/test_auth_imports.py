from __future__ import annotations


def test_auth_imports():
    from sucrawler.auth import (
        AuthError,
        BaseAuthenticator,
        CredentialInfo,
        InvalidCredentialError,
        LoginFailedError,
        LoginStatus,
        LoginTimeoutError,
        LoginType,
        QRCodeExpiredError,
    )

    assert BaseAuthenticator is not None
    assert LoginType is not None
    assert LoginStatus is not None
    assert CredentialInfo is not None
    assert AuthError is not None
    assert LoginFailedError is not None
    assert LoginTimeoutError is not None
    assert QRCodeExpiredError is not None
    assert InvalidCredentialError is not None
