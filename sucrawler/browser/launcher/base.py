from __future__ import annotations

import platform
import socket
from abc import ABC, abstractmethod
from subprocess import Popen
from typing import Optional

from loguru import logger

from sucrawler.browser.types import BrowserInfo, BrowserType, LaunchOptions


class BaseBrowserLauncher(ABC):
    def __init__(self) -> None:
        self.system: str = platform.system()
        self._process: Optional[Popen] = None

    @property
    def process(self) -> Optional[Popen]:
        return self._process

    @abstractmethod
    def detect_browsers(self) -> list[BrowserInfo]: ...

    @abstractmethod
    def launch(self, options: LaunchOptions) -> Popen: ...

    @abstractmethod
    def cleanup(self) -> None: ...

    def find_available_port(self, start_port: int = 9222, max_attempts: int = 100) -> int:
        port = start_port
        for _ in range(max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    logger.debug(f"[BrowserLauncher] Found available port: {port}")
                    return port
            except OSError:
                port += 1

        msg = f"Cannot find available port, tried {start_port} to {port - 1}"
        raise RuntimeError(msg)

    def wait_until_ready(self, debug_port: int, timeout: int = 30) -> bool:
        import time

        logger.info(f"[BrowserLauncher] Waiting for browser on port {debug_port}...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(("localhost", debug_port))
                    if result == 0:
                        logger.info(f"[BrowserLauncher] Browser ready on port {debug_port}")
                        return True
            except OSError:
                pass

            time.sleep(0.5)

        logger.error(f"[BrowserLauncher] Browser not ready within {timeout}s")
        return False

    def get_browser_info(self, browser_path: str) -> BrowserInfo:
        import subprocess

        path_lower = browser_path.lower()
        if "chrome" in path_lower and "edge" not in path_lower:
            name = "Google Chrome"
            browser_type: BrowserType = "chrome"
        elif "edge" in path_lower or "msedge" in path_lower:
            name = "Microsoft Edge"
            browser_type = "edge"
        elif "chromium" in path_lower:
            name = "Chromium"
            browser_type = "chromium"
        else:
            name = "Unknown Browser"
            browser_type = "chrome"

        try:
            result = subprocess.run(
                [browser_path, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            version = result.stdout.strip() if result.stdout else "Unknown Version"
        except (subprocess.SubprocessError, OSError):
            version = "Unknown Version"

        return BrowserInfo(name=name, version=version, path=browser_path, type=browser_type)
