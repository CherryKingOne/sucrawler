from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from sucrawler.browser.exceptions import BrowserNotFoundError
from sucrawler.browser.launcher.chrome_launcher import ChromeLauncher
from sucrawler.browser.types import LaunchOptions


class TestChromeLauncher:
    def test_init(self):
        launcher = ChromeLauncher()
        assert launcher.process is None

    def test_detect_browsers(self):
        launcher = ChromeLauncher()
        result = launcher.detect_browsers()
        assert isinstance(result, list)

    def test_find_available_port(self):
        launcher = ChromeLauncher()
        port = launcher.find_available_port(start_port=19222)
        assert port >= 19222
        assert isinstance(port, int)

    def test_find_available_port_occupied(self):
        launcher = ChromeLauncher()
        servers = []
        try:
            for _ in range(5):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("localhost", 0))
                s.listen(1)
                servers.append(s)

            ports = [s.getsockname()[1] for s in servers]
            start_port = min(ports)
            result = launcher.find_available_port(start_port=start_port, max_attempts=100)
            assert result not in ports or result > max(ports)
        finally:
            for s in servers:
                s.close()

    def test_launch_nonexistent_browser(self):
        launcher = ChromeLauncher()
        options = LaunchOptions(
            browser_path="/nonexistent/path/to/chrome",
            debug_port=9222,
        )
        with pytest.raises(BrowserNotFoundError):
            launcher.launch(options)

    @patch("subprocess.Popen")
    @patch("os.path.isfile")
    def test_launch_success(self, mock_isfile, mock_popen):
        mock_isfile.return_value = True
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        launcher = ChromeLauncher()
        launcher.system = "Linux"

        options = LaunchOptions(
            browser_path="/usr/bin/google-chrome",
            debug_port=9222,
            headless=True,
            user_data_dir="/tmp/test",
        )
        process = launcher.launch(options)

        assert process == mock_process
        assert launcher.process == mock_process
        mock_popen.assert_called_once()

        call_args = mock_popen.call_args[0][0]
        assert "--remote-debugging-port=9222" in call_args
        assert "--headless=new" in call_args
        assert "--user-data-dir=/tmp/test" in call_args

    @patch("subprocess.Popen")
    @patch("os.path.isfile")
    def test_build_args_with_proxy(self, mock_isfile, mock_popen):
        mock_isfile.return_value = True
        mock_popen.return_value = MagicMock()

        launcher = ChromeLauncher()
        launcher.system = "Linux"

        options = LaunchOptions(
            browser_path="/usr/bin/google-chrome",
            debug_port=9222,
            proxy="http://proxy:8080",
        )
        launcher.launch(options)

        call_args = mock_popen.call_args[0][0]
        assert "--proxy-server=http://proxy:8080" in call_args

    @patch("subprocess.Popen")
    @patch("os.path.isfile")
    def test_build_args_with_user_agent(self, mock_isfile, mock_popen):
        mock_isfile.return_value = True
        mock_popen.return_value = MagicMock()

        launcher = ChromeLauncher()
        launcher.system = "Linux"

        options = LaunchOptions(
            browser_path="/usr/bin/google-chrome",
            debug_port=9222,
            user_agent="TestAgent/1.0",
        )
        launcher.launch(options)

        call_args = mock_popen.call_args[0][0]
        assert "--user-agent=TestAgent/1.0" in call_args

    def test_cleanup_no_process(self):
        launcher = ChromeLauncher()
        launcher.cleanup()

    @patch("os.killpg")
    @patch("os.getpgid")
    def test_cleanup_with_process(self, mock_getpgid, mock_killpg):
        launcher = ChromeLauncher()
        launcher.system = "Linux"

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_process.wait.return_value = 0
        mock_getpgid.return_value = 12345

        launcher._process = mock_process
        launcher.cleanup()

        assert launcher.process is None
        mock_killpg.assert_called()

    def test_get_browser_info_chrome(self):
        launcher = ChromeLauncher()
        info = launcher.get_browser_info("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        assert info.type == "chrome"
        assert "Chrome" in info.name

    def test_get_browser_info_edge(self):
        launcher = ChromeLauncher()
        info = launcher.get_browser_info("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")
        assert info.type == "edge"
        assert "Edge" in info.name

    def test_get_browser_info_chromium(self):
        launcher = ChromeLauncher()
        info = launcher.get_browser_info("/usr/bin/chromium")
        assert info.type == "chromium"
        assert "Chromium" in info.name
