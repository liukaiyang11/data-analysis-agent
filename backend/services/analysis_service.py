"""
数据分析服务模块
"""
from typing import Dict, Any, Optional
import json
from pathlib import Path

from core.analysis.data_analyzer import DataAnalyzer
from config.settings import settings


class AnalysisService:
    """数据分析服务类"""

    def __init__(self):
        self.data_analyzer = DataAnalyzer() if DataAnalyzer else None

    def analyze_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        分析文本数据

        Args:
            text: 待分析文本

        Returns:
            分析结果
        """
        if not self.data_analyzer:
            print("数据分析器未初始化")
            return None

        try:
            result = self.data_analyzer.analyze(text)
            return result
        except Exception as e:
            print(f"数据分析错误: {e}")
            return None

    def analyze_from_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        从文件分析数据

        Args:
            file_path: 文件路径

        Returns:
            分析结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.analyze_text(text)
        except Exception as e:
            print(f"文件读取错误: {e}")
            return None

    def save_analysis_result(self, result: Dict[str, Any], output_path: Path) -> bool:
        """
        保存分析结果

        Args:
            result: 分析结果
            output_path: 输出路径

        Returns:
            是否保存成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存结果错误: {e}")
            return False