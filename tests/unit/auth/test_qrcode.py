from __future__ import annotations

import base64
from pathlib import Path

import pytest

from sucrawler.auth.qrcode import QRCodeUtils


class TestQRCodeUtils:
    @pytest.fixture
    def sample_png_bytes(self) -> bytes:
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    @pytest.fixture
    def sample_data_url(self, sample_png_bytes: bytes) -> str:
        b64 = base64.b64encode(sample_png_bytes).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def test_is_base64_image_valid_png(self, sample_data_url: str):
        assert QRCodeUtils.is_base64_image(sample_data_url) is True

    def test_is_base64_image_valid_jpeg(self):
        data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD/2wBDAA=="
        assert QRCodeUtils.is_base64_image(data_url) is True

    def test_is_base64_image_invalid(self):
        assert QRCodeUtils.is_base64_image("https://example.com/qr.png") is False
        assert QRCodeUtils.is_base64_image("not a data url") is False
        assert QRCodeUtils.is_base64_image("") is False

    def test_extract_base64_from_data_url(self, sample_data_url: str, sample_png_bytes: bytes):
        result = QRCodeUtils.extract_base64_from_data_url(sample_data_url)
        assert result is not None
        assert result == sample_png_bytes

    def test_extract_base64_from_data_url_invalid(self):
        result = QRCodeUtils.extract_base64_from_data_url("not a data url")
        assert result is None

    def test_save_qrcode_image(self, sample_png_bytes: bytes, tmp_path: Path):
        output_path = tmp_path / "qrcode.png"
        result = QRCodeUtils.save_qrcode_image(sample_png_bytes, output_path)
        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == sample_png_bytes

    def test_save_qrcode_image_nested_dir(self, sample_png_bytes: bytes, tmp_path: Path):
        output_path = tmp_path / "nested" / "dir" / "qrcode.png"
        result = QRCodeUtils.save_qrcode_image(sample_png_bytes, output_path)
        assert result.exists()

    def test_display_qrcode_terminal(self, sample_png_bytes: bytes):
        result = QRCodeUtils.display_qrcode_terminal(sample_png_bytes)
        assert "QR Code Image" in result
        assert str(len(sample_png_bytes)) in result

    def test_extract_qrcode_from_img_src_base64(self, sample_data_url: str, sample_png_bytes: bytes):
        result = QRCodeUtils.extract_qrcode_from_img_src(sample_data_url)
        assert result == sample_png_bytes

    def test_extract_qrcode_from_img_src_remote_url(self):
        result = QRCodeUtils.extract_qrcode_from_img_src("https://example.com/qr.png")
        assert result is None

    def test_extract_qrcode_from_img_src_invalid(self):
        result = QRCodeUtils.extract_qrcode_from_img_src("invalid")
        assert result is None

    def test_show_qrcode_popup_no_pil(self, sample_png_bytes: bytes, monkeypatch: pytest.MonkeyPatch):
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name in ("PIL", "PIL.Image", "PIL.ImageTk"):
                raise ImportError("No module named 'PIL'")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        result = QRCodeUtils.show_qrcode_popup(sample_png_bytes)
        assert result is False

    def test_generate_qrcode_data_url_no_lib(self, monkeypatch: pytest.MonkeyPatch):
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "qrcode":
                raise ImportError("No module named 'qrcode'")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        result = QRCodeUtils.generate_qrcode_data_url("test")
        assert result is None

    def test_is_base64_image_case_insensitive(self):
        data_url = "DATA:IMAGE/PNG;BASE64,abc="
        assert QRCodeUtils.is_base64_image(data_url) is True
