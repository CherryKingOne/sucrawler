from __future__ import annotations

import os
import signal
import subprocess
from subprocess import Popen
from typing import Optional

from loguru import logger

from sucrawler.browser.exceptions import (
    BrowserLaunchError,
    BrowserNotFoundError,
    PortNotAvailableError,
)
from sucrawler.browser.launcher.base import BaseBrowserLauncher
from sucrawler.browser.launcher.path_detector import PathDetector
from sucrawler.browser.types import BrowserInfo, LaunchOptions


class ChromeLauncher(BaseBrowserLauncher):
    def __init__(self) -> None:
        super().__init__()
        self._path_detector = PathDetector()

    def detect_browsers(self) -> list[BrowserInfo]:
        return self._path_detector.detect_all()

    def launch(self, options: LaunchOptions) -> Popen:
        if not os.path.isfile(options.browser_path):
            raise BrowserNotFoundError(f"Browser not found at: {options.browser_path}")

        args = self._build_args(options)

        logger.info(f"[ChromeLauncher] Launching browser: {options.browser_path}")
        logger.debug(f"[ChromeLauncher] Debug port: {options.debug_port}")
        logger.debug(f"[ChromeLauncher] Headless: {options.headless}")

        try:
            if self.system == "Windows":
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )

            self._process = process
            return process

        except OSError as e:
            raise BrowserLaunchError(f"Failed to launch browser: {e}") from e

    def cleanup(self) -> None:
        if not self._process:
            return

        process = self._process

        if process.poll() is not None:
            logger.info("[ChromeLauncher] Browser process already exited")
            self._process = None
            return

        logger.info("[ChromeLauncher] Closing browser process...")

        try:
            if self.system == "Windows":
                self._cleanup_windows(process)
            else:
                self._cleanup_unix(process)

            logger.info("[ChromeLauncher] Browser process closed")
        except OSError as e:
            logger.warning(f"[ChromeLauncher] Error closing browser process: {e}")
        finally:
            self._process = None

    def _cleanup_windows(self, process: Popen) -> None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("[ChromeLauncher] Terminate timeout, force killing")
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="ignore",
            )
            process.wait(timeout=5)

    def _cleanup_unix(self, process: Popen) -> None:
        try:
            pgid = os.getpgid(process.pid)
        except ProcessLookupError:
            logger.info("[ChromeLauncher] Process group not found")
            return

        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("[ChromeLauncher] SIGTERM timeout, sending SIGKILL")
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)

    def _build_args(self, options: LaunchOptions) -> list[str]:
        args: list[str] = [
            options.browser_path,
            f"--remote-debugging-port={options.debug_port}",
            "--remote-debugging-address=0.0.0.0",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--exclude-switches=enable-automation",
            "--disable-infobars",
        ]

        if options.headless:
            args.extend(["--headless=new", "--disable-gpu"])
        else:
            args.append("--start-maximized")

        if options.user_data_dir:
            args.append(f"--user-data-dir={options.user_data_dir}")

        if options.user_agent:
            args.append(f"--user-agent={options.user_agent}")

        if options.proxy:
            args.append(f"--proxy-server={options.proxy}")

        if options.args:
            args.extend(options.args)

        return args
