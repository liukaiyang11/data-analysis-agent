"""
应用配置设置
"""
import os
from pathlib import Path
from typing import Optional

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 环境变量加载
from dotenv import load_dotenv
load_dotenv()

class Settings:
    """应用配置类"""

    # 应用基础配置
    APP_NAME: str = "Data Analysis API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 服务器配置
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8708"))  # 改为8708，和app.py一致

    # 文件上传配置
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024)))  # 100MB
    ALLOWED_EXTENSIONS: set = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}

    # OCR 服务配置
    OCR_BASE_URL: str = os.getenv("OCR_SERVICE_URL", "http://localhost:8707")
    OCR_TIMEOUT: int = int(os.getenv("OCR_TIMEOUT", "300"))

    # 数据分析配置
    TOKENIZER_PATH: str = os.getenv(
        "QWEN_TOKENIZER_PATH",
        "./03_DataAnalysis_main/backend/external/tokenizers/Qwen-tokenizer"
    )
    CHUNK_SIZE: int = int(os.getenv("ANALYSIS_CHUNK_SIZE", "1500"))
    MAX_WORKERS: int = int(os.getenv("ANALYSIS_MAX_WORKERS", "10"))

    # LLM API 配置（数据分析）
    API_KEY: str = os.getenv("ANALYSIS_API_KEY", "sk-e3ffb45ef5b")
    API_BASE: str = os.getenv("ANALYSIS_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME: str = os.getenv("ANALYSIS_MODEL_NAME", "qwen3-max")
    
    # 可视化 LLM API 配置
    VISUALIZER_API_KEY: str = os.getenv("VISUALIZER_API_KEY", API_KEY)  # 默认使用分析配置
    VISUALIZER_API_BASE: str = os.getenv("VISUALIZER_API_BASE", API_BASE)
    VISUALIZER_MODEL_NAME: str = os.getenv("VISUALIZER_MODEL_NAME", MODEL_NAME)

    # 路径配置
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    LOGS_DIR: Path = BASE_DIR / "logs"
    STATIC_DIR: Path = BASE_DIR / "static"

    # 创建必要的目录
    @classmethod
    def create_directories(cls):
        """创建必要的目录"""
        for directory in [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.LOGS_DIR, cls.STATIC_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> bool:
        """验证配置"""
        if not cls.API_KEY:
            print("WARNING: API_KEY 未设置")
            return False

        if not os.path.exists(cls.TOKENIZER_PATH):
            print(f"WARNING: TOKENIZER_PATH 不存在: {cls.TOKENIZER_PATH}")
            return False

        return True

# 全局设置实例
settings = Settings()

# 初始化时创建目录
settings.create_directories()