from __future__ import annotations


def cookies_list_to_string(cookies: list[dict]) -> str:
    """Cookie 列表转 Cookie header 字符串。

    Args:
        cookies: Cookie 列表，每项包含 name 和 value

    Returns:
        Cookie header 字符串，格式: name1=value1; name2=value2
    """
    parts = []
    for cookie in cookies:
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        if name:
            parts.append(f"{name}={value}")
    return "; ".join(parts)


def string_to_cookies_list(
    cookie_str: str,
    domain: str = "",
    path: str = "/",
) -> list[dict]:
    """Cookie 字符串转 Cookie 列表。

    Args:
        cookie_str: Cookie header 字符串
        domain: 默认域名
        path: 默认路径

    Returns:
        Cookie 列表
    """
    cookies: list[dict] = []
    if not cookie_str:
        return cookies

    for part in cookie_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue

        name, value = part.split("=", 1)
        cookie = {
            "name": name.strip(),
            "value": value.strip(),
            "domain": domain,
            "path": path,
        }
        cookies.append(cookie)

    return cookies


def cookies_list_to_dict(cookies: list[dict]) -> dict[str, str]:
    """Cookie 列表转字典。

    Args:
        cookies: Cookie 列表

    Returns:
        {name: value} 字典
    """
    result: dict[str, str] = {}
    for cookie in cookies:
        name = cookie.get("name", "")
        value = cookie.get("value", "")
        if name:
            result[name] = value
    return result


def dict_to_cookies_list(
    cookie_dict: dict[str, str],
    domain: str = "",
    path: str = "/",
) -> list[dict]:
    """字典转 Cookie 列表。

    Args:
        cookie_dict: {name: value} 字典
        domain: 默认域名
        path: 默认路径

    Returns:
        Cookie 列表
    """
    cookies: list[dict] = []
    for name, value in cookie_dict.items():
        cookies.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": path,
        })
    return cookies


def filter_cookies_by_domain(
    cookies: list[dict],
    domain: str,
) -> list[dict]:
    """按域名过滤 Cookie。

    Args:
        cookies: Cookie 列表
        domain: 目标域名

    Returns:
        匹配的 Cookie 列表
    """
    result: list[dict] = []
    for cookie in cookies:
        cookie_domain = cookie.get("domain", "")
        if not cookie_domain:
            continue
        if cookie_domain == domain or cookie_domain.startswith(".") and domain.endswith(cookie_domain[1:]):
            result.append(cookie)
    return result


def merge_cookies(*cookie_lists: list[dict]) -> list[dict]:
    """合并多个 Cookie 列表，后者覆盖前者。

    Args:
        *cookie_lists: 多个 Cookie 列表

    Returns:
        合并后的 Cookie 列表
    """
    merged: dict[str, dict] = {}
    for cookie_list in cookie_lists:
        for cookie in cookie_list:
            key = f"{cookie.get('domain', '')}:{cookie.get('path', '/')}:{cookie.get('name', '')}"
            merged[key] = cookie
    return list(merged.values())
