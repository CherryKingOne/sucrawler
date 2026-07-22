from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from typing import Any

from loguru import logger


class QRCodeUtils:
    """二维码工具类。

    提供二维码提取、解码、显示等通用功能。
    """

    BASE64_IMAGE_PATTERN = re.compile(
        r"data:image/(png|jpeg|jpg|gif|webp);base64,(.+)", re.IGNORECASE
    )

    @staticmethod
    def extract_base64_from_data_url(data_url: str) -> bytes | None:
        """从 data URL 中提取图片的二进制数据。

        Args:
            data_url: data URL 格式的图片字符串

        Returns:
            图片二进制数据，格式无效则返回 None
        """
        match = QRCodeUtils.BASE64_IMAGE_PATTERN.match(data_url.strip())
        if not match:
            return None

        try:
            return base64.b64decode(match.group(2))
        except Exception as e:
            logger.warning(f"Failed to decode base64 image: {e}")
            return None

    @staticmethod
    def is_base64_image(src: str) -> bool:
        """判断是否为 base64 格式的图片。

        Args:
            src: 图片源字符串

        Returns:
            是否为 base64 图片
        """
        return bool(QRCodeUtils.BASE64_IMAGE_PATTERN.match(src.strip()))

    @staticmethod
    def save_qrcode_image(image_data: bytes, output_path: str | Path) -> Path:
        """保存二维码图片到文件。

        Args:
            image_data: 图片二进制数据
            output_path: 输出路径

        Returns:
            保存的文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(image_data)

        logger.info(f"QR code saved to {output_path}")
        return output_path

    @staticmethod
    def display_qrcode_terminal(image_data: bytes) -> str:
        """在终端中显示二维码（ASCII 格式占位符）。

        实际的二维码解析需要依赖额外的库（如 pyzbar），
        这里提供基础的图片信息输出。

        Args:
            image_data: 图片二进制数据

        Returns:
            二维码描述信息
        """
        size = len(image_data)
        return f"[QR Code Image] Size: {size} bytes"

    @staticmethod
    def show_qrcode_popup(image_data: bytes, title: str = "扫码登录") -> bool:
        """弹窗显示二维码图片。

        使用 PIL/Pillow 库显示图片窗口，如果 PIL 不可用则返回 False。

        Args:
            image_data: 图片二进制数据
            title: 窗口标题

        Returns:
            是否成功显示
        """
        try:
            from PIL import Image, ImageTk
            import tkinter as tk
        except ImportError:
            logger.warning("PIL/Pillow or tkinter not available, cannot show popup")
            return False

        try:
            image = Image.open(io.BytesIO(image_data))

            root = tk.Tk()
            root.title(title)

            photo = ImageTk.PhotoImage(image)
            label = tk.Label(root, image=photo)
            label.image = photo
            label.pack()

            label_info = tk.Label(root, text="请使用手机扫描二维码登录", font=("Arial", 12))
            label_info.pack(pady=10)

            root.update()
            root.after(500, root.destroy)
            root.mainloop()

            return True
        except Exception as e:
            logger.warning(f"Failed to show QR code popup: {e}")
            return False

    @staticmethod
    def extract_qrcode_from_img_src(src: str) -> bytes | None:
        """从 img 标签的 src 属性提取二维码图片数据。

        支持 base64 data URL 和普通 URL（需额外下载）。

        Args:
            src: img 标签的 src 属性

        Returns:
            图片二进制数据
        """
        if QRCodeUtils.is_base64_image(src):
            return QRCodeUtils.extract_base64_from_data_url(src)

        if src.startswith("http://") or src.startswith("https://"):
            logger.info(f"QR code is remote URL: {src}, need download")
            return None

        logger.warning(f"Unsupported image src format: {src[:50]}...")
        return None

    @staticmethod
    def generate_qrcode_data_url(content: str) -> str | None:
        """生成二维码的 data URL。

        需要安装 qrcode 库。

        Args:
            content: 二维码内容

        Returns:
            data URL 格式的图片字符串
        """
        try:
            import qrcode
        except ImportError:
            logger.warning("qrcode library not available")
            return None

        try:
            img = qrcode.make(content)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            base64_data = base64.b64encode(buf.read()).decode("ascii")
            return f"data:image/png;base64,{base64_data}"
        except Exception as e:
            logger.warning(f"Failed to generate QR code: {e}")
            return None
