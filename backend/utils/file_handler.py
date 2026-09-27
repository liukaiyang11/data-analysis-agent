"""
文件处理工具模块
"""
import os
import tempfile
from pathlib import Path
from typing import List, Optional
import shutil

from config.settings import settings


class FileHandler:
    """文件处理类"""

    @staticmethod
    def validate_file(file_path: Path) -> bool:
        """
        验证文件

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        if not file_path.exists():
            return False

        if not file_path.is_file():
            return False

        # 检查文件大小
        file_size = file_path.stat().st_size
        if file_size > settings.MAX_FILE_SIZE:
            return False

        # 检查文件扩展名
        if file_path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
            return False

        return True

    @staticmethod
    def save_upload_file(upload_file, filename: Optional[str] = None) -> Path:
        """
        保存上传的文件

        Args:
            upload_file: 上传的文件
            filename: 文件名

        Returns:
            保存的文件路径
        """
        if not filename:
            filename = upload_file.filename

        # 创建安全的文件名
        safe_filename = FileHandler.get_safe_filename(filename)
        file_path = settings.UPLOAD_DIR / safe_filename

        # 确保上传目录存在
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return file_path

    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        获取安全的文件名

        Args:
            filename: 原始文件名

        Returns:
            安全的文件名
        """
        # 移除路径信息
        filename = os.path.basename(filename)

        # 移除危险字符
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        safe_filename = ''.join(c for c in filename if c in safe_chars)

        # 确保文件名不为空
        if not safe_filename:
            safe_filename = "upload"

        return safe_filename

    @staticmethod
    def create_temp_file(suffix: str = ".tmp") -> Path:
        """
        创建临时文件

        Args:
            suffix: 文件后缀

        Returns:
            临时文件路径
        """
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return Path(temp_path)

    @staticmethod
    def cleanup_temp_files(temp_dir: Path) -> None:
        """
        清理临时文件

        Args:
            temp_dir: 临时目录
        """
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """
        获取文件大小（MB）

        Args:
            file_path: 文件路径

        Returns:
            文件大小（MB）
        """
        if not file_path.exists():
            return 0.0

        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)

    @staticmethod
    def list_files_by_extension(directory: Path, extensions: List[str]) -> List[Path]:
        """
        按扩展名列出文件

        Args:
            directory: 目录路径
            extensions: 扩展名列表

        Returns:
            文件路径列表
        """
        files = []
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))
        return files