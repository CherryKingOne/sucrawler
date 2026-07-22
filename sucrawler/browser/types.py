from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BrowserType = Literal["chrome", "edge", "chromium"]
BrowserMode = Literal["standard", "cdp"]
LoginType = Literal["qrcode", "phone", "cookie"]


class BrowserConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    mode: BrowserMode = "standard"
    browser_type: BrowserType = "chrome"
    cdp_connect_existing: bool = False
    debug_port: int = 9222
    custom_browser_path: str = ""
    headless: bool = False
    user_data_dir: str = ""
    save_login_state: bool = True
    launch_timeout: int = 60
    auto_close: bool = True
    stealth_script_path: str = ""
    user_agent: str = ""
    viewport_width: int = 1920
    viewport_height: int = 1080
    proxy: str = ""
    auto_login: bool = True
    login_type: LoginType = "qrcode"
    credential_dir: str = ""
    login_timeout: int = 300
    save_credentials: bool = True


class BrowserInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    version: str
    path: str
    type: BrowserType


class LaunchOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    browser_path: str
    debug_port: int
    headless: bool = False
    user_data_dir: str | None = None
    user_agent: str | None = None
    proxy: str | None = None
    args: list[str] = Field(default_factory=list)
