"""
集成服务模块
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import uuid

from services.ocr_service import OCRService
from services.analysis_service import AnalysisService
from services.visualization_service import VisualizationService
from config.settings import settings


class IntegrationService:
    """集成服务类 - 协调各个服务完成完整流程"""

    def __init__(self):
        self.ocr_service = OCRService()
        self.analysis_service = AnalysisService()
        self.visualization_service = VisualizationService()

    def process_document(
        self,
        file_path: Path,
        user_question: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        处理文档的完整流程：OCR → 分析 → 可视化

        Args:
            file_path: 文件路径
            user_question: 用户问题

        Returns:
            处理结果
        """
        try:
            # 步骤1: OCR 识别
            print(f"开始 OCR 处理: {file_path}")
            ocr_result = self._process_ocr(file_path)
            if not ocr_result:
                return None

            # 步骤2: 数据分析
            print("开始数据分析...")
            analysis_result = self.analysis_service.analyze_text(ocr_result)
            if not analysis_result:
                return None

            # 步骤3: 生成可视化报告
            print("生成可视化报告...")
            html_report = self.visualization_service.generate_html_report(
                analysis_result, user_question
            )

            # 步骤4: 保存结果
            result_id = str(uuid.uuid4())
            saved_files = self._save_results(
                result_id, analysis_result, html_report
            )

            return {
                "result_id": result_id,
                "ocr_text": ocr_result,
                "analysis_data": analysis_result,
                "html_report": html_report,
                "saved_files": saved_files
            }

        except Exception as e:
            print(f"文档处理错误: {e}")
            return None

    def _process_ocr(self, file_path: Path) -> Optional[str]:
        """处理 OCR"""
        file_extension = file_path.suffix.lower()

        if file_extension == '.pdf':
            return self.ocr_service.process_pdf(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self.ocr_service.process_image(file_path)
        else:
            print(f"不支持的文件格式: {file_extension}")
            return None

    def _save_results(
        self,
        result_id: str,
        analysis_data: Dict[str, Any],
        html_report: Optional[str]
    ) -> Dict[str, str]:
        """保存处理结果"""
        saved_files = {}

        try:
            # 保存分析数据
            analysis_path = settings.OUTPUT_DIR / f"{result_id}_analysis.json"
            if self.analysis_service.save_analysis_result(analysis_data, analysis_path):
                saved_files["analysis"] = str(analysis_path)

            # 保存 HTML 报告
            if html_report:
                html_path = settings.OUTPUT_DIR / f"{result_id}_report.html"
                if self.visualization_service.save_html_report(html_report, html_path):
                    saved_files["html_report"] = str(html_path)

            # 导出 PDF 报告
            pdf_path = settings.OUTPUT_DIR / f"{result_id}_report.pdf"
            if self.visualization_service.export_to_pdf(analysis_data, pdf_path):
                saved_files["pdf_report"] = str(pdf_path)

        except Exception as e:
            print(f"保存结果错误: {e}")

        return saved_files

    def get_result_files(self, result_id: str) -> Optional[Dict[str, str]]:
        """获取结果文件路径"""
        try:
            files = {}
            base_name = f"{result_id}_"

            for file_path in settings.OUTPUT_DIR.glob(f"{base_name}*"):
                if file_path.suffix == '.json' and 'analysis' in file_path.name:
                    files['analysis'] = str(file_path)
                elif file_path.suffix == '.html':
                    files['html_report'] = str(file_path)
                elif file_path.suffix == '.pdf':
                    files['pdf_report'] = str(file_path)

            return files if files else None

        except Exception as e:
            print(f"获取结果文件错误: {e}")
            return None

    def health_check(self) -> Dict[str, bool]:
        """检查各个服务的健康状态"""
        return {
            "ocr_service": self.ocr_service.health_check(),
            "analysis_service": self.analysis_service is not None,
            "visualization_service": (
                self.visualization_service.report_generator is not None and
                self.visualization_service.pdf_exporter is not None
            )
        }