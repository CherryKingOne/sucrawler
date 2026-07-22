from __future__ import annotations

import hashlib
from typing import Any


def xhs_sign(params: dict[str, Any], sign_key: str) -> str:
    sorted_keys = sorted(params.keys())
    sign_str = sign_key
    for key in sorted_keys:
        value = params[key]
        if value is not None:
            sign_str += f"{key}{value}"
    sign_str += sign_key
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest()
