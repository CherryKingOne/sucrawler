import base64
import hashlib
import hmac


def md5(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.md5(data).hexdigest()


def sha1(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha1(data).hexdigest()


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def base64_encode(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")


def base64_decode(data: str) -> bytes:
    return base64.b64decode(data)


def base64_decode_str(data: str) -> str:
    return base64_decode(data).decode("utf-8")


def hmac_sign(key: str | bytes, message: str | bytes, algorithm: str = "sha256") -> str:
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(message, str):
        message = message.encode("utf-8")
    if algorithm == "sha256":
        digest = hashlib.sha256
    elif algorithm == "sha1":
        digest = hashlib.sha1
    elif algorithm == "md5":
        digest = hashlib.md5
    else:
        msg = f"Unsupported algorithm: {algorithm}"
        raise ValueError(msg)
    return hmac.new(key, message, digest).hexdigest()
