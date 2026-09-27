"""
OCR 服务模块
"""
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import io
from PIL import Image

from config.settings import settings


class OCRService:
    """OCR 服务类"""

    def __init__(self):
        self.base_url = settings.OCR_BASE_URL
        self.timeout = settings.OCR_TIMEOUT

    def process_image(self, image_path: Path) -> Optional[str]:
        """
        处理图片 OCR

        Args:
            image_path: 图片路径

        Returns:
            OCR 结果文本
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/ocr",
                    files=files,
                    timeout=self.timeout
                )

            if response.status_code == 200:
                result = response.json()
                return result.get('markdown', '')
            else:
                print(f"OCR 请求失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"OCR 处理错误: {e}")
            return None

    def process_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        处理 PDF OCR

        Args:
            pdf_path: PDF 路径

        Returns:
            OCR 结果文本
        """
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/ocr",
                    files=files,
                    timeout=self.timeout
                )

            if response.status_code == 200:
                result = response.json()
                return result.get('markdown', '')
            else:
                print(f"OCR 请求失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"OCR 处理错误: {e}")
            return None

    def health_check(self) -> bool:
        """
        检查 OCR 服务健康状态

        Returns:
            服务是否健康
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10
            )
            return response.status_code == 200
        except:
            return False