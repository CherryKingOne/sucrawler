from __future__ import annotations

import platform
from unittest.mock import patch

import pytest

from sucrawler.browser.launcher.path_detector import PathDetector


class TestPathDetector:
    def test_init(self):
        detector = PathDetector()
        assert detector.system == platform.system()

    def test_detect_all_returns_list(self):
        detector = PathDetector()
        result = detector.detect_all()
        assert isinstance(result, list)

    def test_find_first_no_filter(self):
        detector = PathDetector()
        result = detector.find_first()
        assert result is None or result.__class__.__name__ == "BrowserInfo"

    def test_find_first_with_type(self):
        detector = PathDetector()
        result = detector.find_first(browser_type="chrome")
        assert result is None or result.type == "chrome"

    @patch("os.path.isfile")
    @patch("os.access")
    def test_detect_all_with_mock(self, mock_access, mock_isfile):
        mock_isfile.return_value = True
        mock_access.return_value = True

        detector = PathDetector()
        detector.system = "Darwin"

        with patch.object(detector, "_build_info") as mock_build:
            from sucrawler.browser.types import BrowserInfo

            mock_build.return_value = BrowserInfo(
                name="Google Chrome",
                version="120.0",
                path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                type="chrome",
            )
            result = detector.detect_all()
            assert len(result) > 0
            assert result[0].type == "chrome"

    def test_macos_paths(self):
        detector = PathDetector()
        detector.system = "Darwin"
        paths = detector._macos_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert any("Google Chrome" in p for p in paths)

    def test_linux_paths(self):
        detector = PathDetector()
        detector.system = "Linux"
        paths = detector._linux_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert any("chromium" in p for p in paths)

    def test_windows_paths(self):
        detector = PathDetector()
        detector.system = "Windows"
        paths = detector._windows_paths()
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert any("chrome.exe" in p for p in paths)
