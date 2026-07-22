from __future__ import annotations

import os
import platform
from typing import Optional

from loguru import logger

from sucrawler.browser.types import BrowserInfo, BrowserType


class PathDetector:
    def __init__(self) -> None:
        self.system: str = platform.system()

    def detect_all(self) -> list[BrowserInfo]:
        paths = self._get_candidate_paths()
        results: list[BrowserInfo] = []

        for path in paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                info = self._build_info(path)
                if info:
                    results.append(info)
                    logger.debug(f"[PathDetector] Found browser: {info.name} at {path}")

        logger.info(f"[PathDetector] Found {len(results)} browser(s)")
        return results

    def find_first(self, browser_type: Optional[BrowserType] = None) -> Optional[BrowserInfo]:
        browsers = self.detect_all()
        if not browser_type:
            return browsers[0] if browsers else None
        for b in browsers:
            if b.type == browser_type:
                return b
        return None

    def _get_candidate_paths(self) -> list[str]:
        if self.system == "Windows":
            return self._windows_paths()
        if self.system == "Darwin":
            return self._macos_paths()
        return self._linux_paths()

    def _windows_paths(self) -> list[str]:
        return [
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Beta\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Dev\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome SxS\Application\chrome.exe"),
        ]

    def _macos_paths(self) -> list[str]:
        return [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
            "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta",
            "/Applications/Microsoft Edge Dev.app/Contents/MacOS/Microsoft Edge Dev",
            "/Applications/Microsoft Edge Canary.app/Contents/MacOS/Microsoft Edge Canary",
        ]

    def _linux_paths(self) -> list[str]:
        return [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome-beta",
            "/usr/bin/google-chrome-unstable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable",
            "/usr/bin/microsoft-edge-beta",
            "/usr/bin/microsoft-edge-dev",
        ]

    def _build_info(self, path: str) -> Optional[BrowserInfo]:
        import subprocess

        path_lower = path.lower()
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
            return None

        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            version = result.stdout.strip() if result.stdout else "Unknown Version"
        except (subprocess.SubprocessError, OSError):
            version = "Unknown Version"

        return BrowserInfo(name=name, version=version, path=path, type=browser_type)
