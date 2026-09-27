"""
可视化服务模块
"""
from typing import Dict, Any, Optional
from pathlib import Path

from core.visualization.generator import ReportGenerator
from core.visualization.exporter import PDFExporter
from config.settings import settings


class VisualizationService:
    """可视化服务类"""

    def __init__(self):
        self.report_generator = ReportGenerator() if ReportGenerator else None
        self.pdf_exporter = PDFExporter() if PDFExporter else None

    def generate_html_report(
        self,
        analysis_data: Dict[str, Any],
        user_question: str = ""
    ) -> Optional[str]:
        """
        生成 HTML 报告

        Args:
            analysis_data: 分析数据
            user_question: 用户问题

        Returns:
            HTML 报告内容
        """
        if not self.report_generator:
            print("报告生成器未初始化")
            return None

        try:
            html_report = self.report_generator.generate_report(
                analysis_data, user_question
            )
            return html_report.html if hasattr(html_report, 'html') else str(html_report)
        except Exception as e:
            print(f"HTML 报告生成错误: {e}")
            return None

    def export_to_pdf(
        self,
        analysis_data: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        导出为 PDF

        Args:
            analysis_data: 分析数据
            output_path: 输出路径

        Returns:
            是否导出成功
        """
        if not self.pdf_exporter:
            print("PDF 导出器未初始化")
            return False

        try:
            success = self.pdf_exporter.export_pdf(analysis_data, str(output_path))
            return success
        except Exception as e:
            print(f"PDF 导出错误: {e}")
            return False

    def save_html_report(self, html_content: str, output_path: Path) -> bool:
        """
        保存 HTML 报告

        Args:
            html_content: HTML 内容
            output_path: 输出路径

        Returns:
            是否保存成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"HTML 保存错误: {e}")
            return False