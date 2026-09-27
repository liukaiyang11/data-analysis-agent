"""
PDF 报告导出器
将 HTML 可视化报告转换为 PDF 格式
"""
import os
import tempfile
from typing import Dict, Any
from datetime import datetime
from weasyprint import HTML, CSS


class PDFExporter:
    """PDF 报告导出器"""

    def __init__(self, output_dir: str = "/tmp/reports"):
        """
        初始化 PDF 导出器

        Args:
            output_dir: PDF 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def html_to_pdf(
        self,
        html_content: str,
        output_filename: str = None,
        title: str = "数据分析报告",
        add_header_footer: bool = True
    ) -> str:
        """
        将 HTML 转换为 PDF

        Args:
            html_content: HTML 内容字符串
            output_filename: 输出文件名（不含路径），如果为 None 则自动生成
            title: 报告标题
            add_header_footer: 是否添加页眉页脚

        Returns:
            生成的 PDF 文件路径
        """
        # 生成文件名
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"report_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        # 处理 HTML 内容，确保可以正确渲染
        processed_html = self._process_html_for_pdf(html_content, title, add_header_footer)

        # 使用 WeasyPrint 将 HTML 转换为 PDF
        HTML(string=processed_html).write_pdf(
            output_path,
            stylesheets=[CSS(string=self._get_pdf_styles())]
        )

        print(f"✅ PDF 已生成: {output_path}")
        return output_path

    def _process_html_for_pdf(self, html_content: str, title: str, add_header_footer: bool) -> str:
        """
        处理 HTML 内容以适配 PDF 输出

        Args:
            html_content: 原始 HTML 内容
            title: 报告标题
            add_header_footer: 是否添加页眉页脚

        Returns:
            处理后的 HTML 内容
        """
        # 如果 HTML 不包含完整的文档结构，包装它
        if not html_content.strip().lower().startswith('<!doctype') and not html_content.strip().lower().startswith('<html'):
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    {html_content}
</body>
</html>
"""

        # 移除交互式脚本（PDF 不支持 JavaScript）
        # 保留图表的渲染结果（如果已经转换为图片）
        # 这里简化处理，实际可能需要预先将 ECharts 转为静态图片

        # 如果需要页眉页脚
        if add_header_footer:
            header_footer_html = f"""
<style>
    @page {{
        @top-center {{
            content: "{title}";
            font-size: 10pt;
            color: #666;
        }}
        @bottom-center {{
            content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
            font-size: 9pt;
            color: #999;
        }}
        @bottom-right {{
            content: "生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}";
            font-size: 8pt;
            color: #999;
        }}
    }}
</style>
"""
            # 在 </head> 前插入页眉页脚样式
            html_content = html_content.replace('</head>', f'{header_footer_html}</head>')

        return html_content

    def _get_pdf_styles(self) -> str:
        """
        获取 PDF 专用样式

        Returns:
            CSS 样式字符串
        """
        return """
        @page {
            size: A4;
            margin: 2cm 1.5cm;
        }

        body {
            font-family: "Noto Sans CJK SC", "Source Han Sans", "Microsoft YaHei", sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #333;
        }

        h1 {
            font-size: 18pt;
            color: #2c3e50;
            margin-top: 0;
            page-break-after: avoid;
        }

        h2 {
            font-size: 14pt;
            color: #34495e;
            margin-top: 1.5em;
            page-break-after: avoid;
        }

        h3 {
            font-size: 12pt;
            color: #7f8c8d;
            margin-top: 1em;
            page-break-after: avoid;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }

        .page-break {
            page-break-after: always;
        }

        img {
            max-width: 100%;
            height: auto;
        }

        /* 确保图表容器不会被分页 */
        .chart, .panel, .visualization {
            page-break-inside: avoid;
        }
        """

    def generate_summary_pdf(
        self,
        analyzed_data: Dict[str, Any],
        visualization_html: str,
        user_query: str,
        summary: str,
        title: str,
        output_filename: str = None
    ) -> str:
        """
        生成包含摘要和数据表格的完整 PDF 报告（不包含 JavaScript 图表）

        Args:
            analyzed_data: 分析后的数据
            visualization_html: 可视化 HTML 内容（会被忽略，因为包含 JS）
            user_query: 用户问题
            summary: 分析摘要
            title: 报告标题
            output_filename: 输出文件名

        Returns:
            生成的 PDF 文件路径
        """
        # 从结构化数据中提取关键信息
        data_tables_html = self._extract_data_tables(analyzed_data)

        # 构建完整的报告 HTML
        report_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        .cover {{
            text-align: center;
            padding: 100px 50px;
            page-break-after: always;
        }}
        .cover h1 {{
            font-size: 32pt;
            color: #2c3e50;
            margin-bottom: 20px;
        }}
        .cover .subtitle {{
            font-size: 14pt;
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .summary-section {{
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            page-break-inside: avoid;
        }}
        .summary-section h2 {{
            margin-top: 0;
        }}
        .query-section {{
            margin: 20px 0;
            padding: 15px;
            background-color: #e8f4f8;
            border-radius: 5px;
            page-break-inside: avoid;
        }}
        .data-section {{
            margin: 20px 0;
        }}
        .key-points {{
            background-color: #fff9e6;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .key-points ul {{
            margin: 10px 0;
            padding-left: 25px;
        }}
    </style>
</head>
<body>
    <!-- 封面 -->
    <div class="cover">
        <h1>{title}</h1>
        <p class="subtitle">生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
    </div>

    <!-- 问题描述 -->
    <div class="query-section">
        <h2>📋 分析需求</h2>
        <p>{user_query}</p>
    </div>

    <!-- 摘要 -->
    <div class="summary-section">
        <h2>📊 分析摘要</h2>
        <p>{summary}</p>
    </div>

    <!-- 分页 -->
    <div class="page-break"></div>

    <!-- 数据详情 -->
    <div class="data-section">
        <h2>📈 数据详情</h2>
        {data_tables_html}
    </div>

</body>
</html>
"""

        return self.html_to_pdf(
            html_content=report_html,
            output_filename=output_filename,
            title=title,
            add_header_footer=True
        )

    def _extract_data_tables(self, analyzed_data: Dict[str, Any]) -> str:
        """
        从结构化数据中提取表格和关键点

        Args:
            analyzed_data: 分析后的数据

        Returns:
            HTML 格式的数据表格
        """
        html_parts = []

        chunks = analyzed_data.get("analyzed_chunks", [])

        for i, chunk in enumerate(chunks, 1):
            if "analysis" not in chunk:
                continue

            analysis = chunk["analysis"]
            header_path = chunk.get("metadata", {}).get("header_path", f"章节 {i}")

            # 添加章节标题
            html_parts.append(f'<h3>{header_path}</h3>')

            # 添加摘要
            summary = analysis.get("summary", "")
            if summary:
                html_parts.append(f'<p><strong>摘要：</strong>{summary}</p>')

            # 添加关键点
            key_points = analysis.get("key_points", [])
            if key_points:
                html_parts.append('<div class="key-points">')
                html_parts.append('<strong>关键要点：</strong>')
                html_parts.append('<ul>')
                for point in key_points:
                    html_parts.append(f'<li>{point}</li>')
                html_parts.append('</ul>')
                html_parts.append('</div>')

            # 添加数据表格
            tables = analysis.get("tables", [])
            for table in tables:
                table_title = table.get("title", "数据表格")
                headers = table.get("headers", [])
                rows = table.get("rows", [])
                note = table.get("note", "")

                html_parts.append(f'<h4>{table_title}</h4>')
                html_parts.append('<table>')

                # 表头
                if headers:
                    html_parts.append('<tr>')
                    for header in headers:
                        html_parts.append(f'<th>{header}</th>')
                    html_parts.append('</tr>')

                # 数据行
                for row in rows:
                    html_parts.append('<tr>')
                    for cell in row:
                        html_parts.append(f'<td>{cell}</td>')
                    html_parts.append('</tr>')

                html_parts.append('</table>')

                # 表格注释
                if note:
                    html_parts.append(f'<p style="font-size: 0.9em; color: #666; font-style: italic;">注：{note}</p>')

            html_parts.append('<hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">')

        return '\n'.join(html_parts) if html_parts else '<p>暂无详细数据</p>'


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 测试 PDF 导出
    exporter = PDFExporter()

    test_html = """
    <h1>测试报告</h1>
    <p>这是一个测试报告，包含中文内容。</p>
    <h2>数据表格</h2>
    <table>
        <tr>
            <th>项目</th>
            <th>数值</th>
        </tr>
        <tr>
            <td>收入</td>
            <td>1000万</td>
        </tr>
        <tr>
            <td>支出</td>
            <td>800万</td>
        </tr>
    </table>
    """

    pdf_path = exporter.html_to_pdf(
        html_content=test_html,
        title="测试数据分析报告"
    )

    print(f"PDF 文件已生成: {pdf_path}")
