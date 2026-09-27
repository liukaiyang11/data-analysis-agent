#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前后端联调专用API服务
完整流程：OCR → 信息结构化 → 可视化报告 → 用户问答
"""
import os
import sys
import json
import time
import io
import requests
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入配置
from config.settings import settings

# 添加backwark目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "backwark"))

# 导入信息结构化和可视化模块
try:
    from core.analysis.data_analyzer import DataAnalyzer
    from core.visualization.visualizer import ReportGenerator
except ImportError as e:

    DataAnalyzer = None
    ReportGenerator = None
    PDFExporter = None

# -----------------------
# 配置
# -----------------------
app = FastAPI(
    title="前后端联调OCR API",
    version="1.0.0",
    description="专门用于前后端联调测试的OCR服务"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 从配置文件读取OCR服务地址
OCR_SERVICE_URL = f"{settings.OCR_BASE_URL}/ocr"
RESULTS_DIR = settings.OUTPUT_DIR / "ocr_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------
# 工具函数
# -----------------------
def call_real_ocr(file_path: str, enable_desc: bool = False) -> Dict[str, Any]:
    """调用真实的OCR服务"""
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"enable_description": "true" if enable_desc else "false"}

            resp = requests.post(OCR_SERVICE_URL, files=files, data=data, timeout=300)

        if resp.status_code == 200:
            result = resp.json()
            print(f"OCR成功! 页数: {result['page_count']}")
            return result
        else:
            print(f"OCR失败: {resp.status_code}")
            return {"error": f"OCR服务失败: {resp.text}", "status_code": resp.status_code}

    except Exception as e:
        print(f"OCR调用异常: {e}")
        return {"error": f"OCR服务调用异常: {str(e)}"}

def save_results(file_path: str, result: Dict[str, Any]) -> Dict[str, str]:
    """保存OCR结果到文件"""
    base_name = Path(file_path).stem

    # 保存JSON结果
    json_file = RESULTS_DIR / f"{base_name}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    # 保存Markdown结果
    if 'markdown' in result:
        md_file = RESULTS_DIR / f"{base_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(result['markdown'])

    return {
        "json_file": str(json_file),
        "md_file": str(RESULTS_DIR / f"{base_name}.md") if 'markdown' in result else None
    }


# -----------------------
# API 路由
# -----------------------
@app.get("/")
async def root():
    """API根路径"""
    return {
        "service": "DeepSeek-OCR API服务",
        "version": "1.0.0",
        "status": "running",
        "description": "调用真实的DeepSeek-OCR服务进行文档识别",
        "endpoints": {
            "ocr": "/ocr - OCR识别接口（调用真实OCR服务）",
            "status": "/status/{task_id} - 查询任务处理状态",
            "download": "/download/{filename} - 下载结果文件",
            "list_results": "/results - 查看处理结果列表",
            "health": "/health - 健康检查"
        },
        "ocr_service": OCR_SERVICE_URL
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "ocr_service": OCR_SERVICE_URL,
        "results_dir": str(RESULTS_DIR),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }

@app.post("/ocr")
async def ocr_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enable_description: bool = Form(True),
    user_query: str = Form('分析此文档并生成可视化报告')
):
    """
    主要的OCR接口 - 调用真实的DeepSeek-OCR服务

    参数:
        file: 上传的文件
        enable_description: 是否启用图片描述（默认True）
        user_query: 用户查询意图
    """
    try:
        # 读取上传的文件
        contents = await file.read()
        file_size = len(contents)

        # 检查文件大小限制
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(400, "文件大小超过100MB限制")

        # 保存上传的文件到临时位置
        temp_file = RESULTS_DIR / f"temp_{int(time.time())}_{file.filename}"
        with open(temp_file, "wb") as f:
            f.write(contents)

        # 生成任务ID
        task_id = f"task_{int(time.time())}_{Path(file.filename).stem}"

        # 立即创建初始状态文件，避免竞态条件
        status_file = RESULTS_DIR / f"status_{task_id}.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "processing",
                "current_step": "文件上传",
                "progress": 0,
                "message": "文件已接收，正在准备处理...",
                "task_id": task_id
            }, f, ensure_ascii=False)

        # 使用真实OCR服务进行异步处理
        background_tasks.add_task(process_real_ocr, str(temp_file), file.filename, enable_description, task_id, user_query)

        return JSONResponse({
            "task_id": task_id,
            "status": "processing",
            "message": "文件已接收，正在使用真实OCR服务处理...",
            "filename": file.filename,
            "enable_description": enable_description,
            "user_query": user_query
        })

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"处理失败: {str(e)}"
        print(f"{error_msg}")
        print(traceback.format_exc())
        raise HTTPException(500, error_msg)

def process_real_ocr(temp_file_path: str, original_filename: str, enable_description: bool, task_id: str, user_query: str = '分析此文档并生成可视化报告'):
    """后台处理真实OCR + 信息结构化"""
    try:
        status_file = RESULTS_DIR / f"status_{task_id}.json"

        # ==================== 步骤1: OCR识别 ====================
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "processing",
                "current_step": "OCR识别",
                "progress": 20,
                "message": "正在调用DeepSeek-OCR服务进行文字识别...",
                "task_id": task_id
            }, f, ensure_ascii=False)

        result = call_real_ocr(temp_file_path, enable_description)

        if 'error' in result:
            raise Exception(result.get('error', '未知错误'))

        # 获取markdown内容
        markdown_content = result.get("markdown", "")
        if not markdown_content or len(markdown_content) < 50:
            raise Exception("OCR识别结果为空或内容过短")

        print(f"OCR识别成功，内容长度: {len(markdown_content)} 字符")

        # ==================== 步骤2: 信息结构化 ====================
        analyzed_result = None
        if DataAnalyzer is not None:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "status": "processing",
                    "current_step": "信息结构化",
                    "progress": 50,
                    "message": "正在对OCR结果进行结构化分析...",
                    "task_id": task_id
                }, f, ensure_ascii=False)

            try:
                print(f"开始信息结构化分析...")
                analyzer = DataAnalyzer()
                analyzed_result = analyzer.analyze_ocr_json(result, use_concurrent=True)

                # 保存结构化结果
                analyzed_file = RESULTS_DIR / f"{task_id}_analyzed.json"
                with open(analyzed_file, 'w', encoding='utf-8') as f:
                    json.dump(analyzed_result, f, ensure_ascii=False, indent=2)

                print(f"信息结构化完成，分析了 {analyzed_result.get('total_chunks', 0)} 个块")
            except Exception as e:
                print(f"信息结构化失败: {e}")
                import traceback
                print(traceback.format_exc())

        # ==================== 步骤3: 保存结果 ====================
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "processing",
                "current_step": "保存结果",
                "progress": 80,
                "message": "正在保存处理结果...",
                "task_id": task_id
            }, f, ensure_ascii=False)

        # 添加文件信息
        result["file_info"] = {
            "original_name": original_filename,
            "temp_path": temp_file_path,
            "processing_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "user_query": user_query
        }

        # 保存OCR结果
        saved_files = save_results(temp_file_path, result)
        result["saved_files"] = saved_files

        # 添加结构化结果引用
        if analyzed_result:
            result["analyzed_file"] = str(RESULTS_DIR / f"{task_id}_analyzed.json")

        # ==================== 完成 ====================
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "completed",
                "current_step": "完成",
                "progress": 100,
                "message": "处理完成！可以开始提问了。",
                "result": result,
                "task_id": task_id,
                "has_analysis": analyzed_result is not None
            }, f, ensure_ascii=False)

        print(f"完整处理成功: {original_filename}")

        # 清理临时文件
        Path(temp_file_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"处理失败: {e}")
        import traceback
        print(traceback.format_exc())

        status_file = RESULTS_DIR / f"status_{task_id}.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "error",
                "current_step": "处理失败",
                "progress": 0,
                "message": f"处理异常: {str(e)}",
                "error": str(e),
                "task_id": task_id
            }, f, ensure_ascii=False)

@app.get("/results")
async def list_results():
    """查看处理结果列表"""
    try:
        results = []

        # 列出所有JSON结果文件
        for json_file in RESULTS_DIR.glob("*.json"):
            if json_file.name.startswith("status_"):
                continue  # 跳过状态文件

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                results.append({
                    "filename": json_file.name,
                    "original_name": data.get("file_name", "未知"),
                    "page_count": data.get("page_count", 0),
                    "status": data.get("status", "success"),
                    "mock_mode": data.get("mock_mode", False),
                    "size": json_file.stat().st_size,
                    "created_time": time.strftime('%Y-%m-%d %H:%M:%S',
                                                time.localtime(json_file.stat().st_ctime))
                })
            except:
                continue

        # 按创建时间排序
        results.sort(key=lambda x: x["created_time"], reverse=True)

        return JSONResponse({
            "total": len(results),
            "results": results,
            "results_dir": str(RESULTS_DIR)
        })

    except Exception as e:
        raise HTTPException(500, f"获取结果列表失败: {str(e)}")

@app.get("/download/{filename}")
async def download_result(filename: str):
    """下载处理结果文件"""
    try:
        file_path = RESULTS_DIR / filename

        if not file_path.exists():
            raise HTTPException(404, "文件不存在")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"下载失败: {str(e)}")

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务处理状态"""
    try:
        status_file = RESULTS_DIR / f"status_{task_id}.json"

        if not status_file.exists():
            raise HTTPException(404, "任务不存在")

        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        return JSONResponse(status_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"获取状态失败: {str(e)}")

@app.get("/results/{task_id}")
async def get_task_results(task_id: str):
    """获取任务的OCR结果（JSON格式）"""
    try:
        # 从status文件中获取结果
        status_file = RESULTS_DIR / f"status_{task_id}.json"

        if not status_file.exists():
            raise HTTPException(404, "任务结果不存在")

        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        # 检查任务是否完成
        if status_data.get('status') != 'completed':
            raise HTTPException(400, "任务尚未完成")

        # 返回OCR结果
        result = status_data.get('result', {})

        return JSONResponse({
            "status": "success",
            "task_id": task_id,
            "page_count": result.get("page_count", 0),
            "markdown": result.get("markdown", ""),
            "file_info": result.get("file_info", {}),
            "processing_time": result.get("file_info", {}).get("processing_time", ""),
            "full_result": result
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"获取结果失败: {str(e)}")

@app.get("/report/{task_id}")
async def get_task_report(task_id: str):
    """获取任务的Markdown报告（用于浏览器预览）"""
    try:
        # 从status文件中获取结果
        status_file = RESULTS_DIR / f"status_{task_id}.json"

        if not status_file.exists():
            raise HTTPException(404, "任务报告不存在")

        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        # 检查任务是否完成
        if status_data.get('status') != 'completed':
            raise HTTPException(400, "任务尚未完成，无法查看报告")

        # 获取Markdown内容
        result = status_data.get('result', {})
        markdown_content = result.get("markdown", "")

        if not markdown_content:
            raise HTTPException(404, "未找到报告内容")

        # 生成HTML页面展示Markdown
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR识别报告 - {task_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4f46e5;
            padding-bottom: 10px;
        }}
        .meta {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 14px;
            color: #666;
        }}
        .content {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            background: #fafafa;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 OCR识别报告</h1>
        <div class="meta">
            <p><strong>任务ID:</strong> {task_id}</p>
            <p><strong>文件名:</strong> {result.get("file_info", {}).get("original_name", "未知")}</p>
            <p><strong>页数:</strong> {result.get("page_count", 0)}</p>
            <p><strong>处理时间:</strong> {result.get("file_info", {}).get("processing_time", "未知")}</p>
        </div>
        <div class="content">{markdown_content}</div>
        <div class="footer">
            <p>由 DeepSeek-OCR 提供技术支持</p>
        </div>
    </div>
</body>
</html>
"""

        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ 获取报告失败: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"获取报告失败: {str(e)}")

# ==================== 用户问题分析接口 ====================

class AnalyzeRequest(BaseModel):
    """分析请求"""
    task_id: str
    user_query: str

@app.post("/analyze")
async def analyze_question(request: AnalyzeRequest):
    """
    根据用户问题生成可视化报告

    参数:
        task_id: 任务ID（已完成OCR和结构化的任务）
        user_query: 用户问题（如"分析该基金2024年的整体业绩表现"）

    返回:
        {
            "status": "success",
            "html": "HTML报告内容",
            "title": "报告标题",
            "summary": "分析摘要",
            "answer_id": "answer_xxx"
        }
    """
    try:
        task_id = request.task_id
        user_query = request.user_query

        print(f"收到分析请求: task_id={task_id}, query={user_query}")

        # 1. 检查任务是否存在并已完成
        status_file = RESULTS_DIR / f"status_{task_id}.json"
        if not status_file.exists():
            raise HTTPException(404, "任务不存在")

        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)

        if status_data.get('status') != 'completed':
            raise HTTPException(400, "任务尚未完成，无法进行分析")

        # 2. 加载结构化分析结果
        analyzed_file = RESULTS_DIR / f"{task_id}_analyzed.json"
        if not analyzed_file.exists():
            raise HTTPException(404, "未找到结构化分析结果，请确保文档已完成处理")

        with open(analyzed_file, 'r', encoding='utf-8') as f:
            analyzed_data = json.load(f)

        print(f"加载结构化数据成功，包含 {analyzed_data.get('total_chunks', 0)} 个块")

        # 3. 生成可视化报告
        if ReportGenerator is None:
            raise HTTPException(500, "可视化生成器未加载")

        print(f"开始生成可视化报告...")
        generator = ReportGenerator()
        report = generator.generate_report(analyzed_data, user_query)

        # 4. 保存报告
        answer_id = f"answer_{int(time.time())}_{task_id}"
        report_file = RESULTS_DIR / f"{answer_id}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report.html)

        # 保存元数据
        metadata_file = RESULTS_DIR / f"{answer_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                "task_id": task_id,
                "user_query": user_query,
                "title": report.title,
                "summary": report.summary,
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, ensure_ascii=False, indent=2)

        print(f"可视化报告生成成功: {answer_id}")

        return JSONResponse({
            "status": "success",
            "html": report.html,
            "title": report.title,
            "summary": report.summary,
            "answer_id": answer_id,
            "report_url": f"/view_report/{answer_id}"
        })

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"分析失败: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"分析失败: {str(e)}")

@app.get("/view_report/{answer_id}")
async def view_report(answer_id: str):
    """查看生成的可视化报告"""
    try:
        report_file = RESULTS_DIR / f"{answer_id}.html"
        if not report_file.exists():
            raise HTTPException(404, "报告不存在")

        with open(report_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"加载报告失败: {str(e)}")


@app.post("/export_pdf")
async def export_pdf(request: dict):
    """
    导出 PDF 报告

    请求体:
    {
        "task_id": "任务ID",
        "answer_id": "回答ID",
        "title": "报告标题（可选）",
        "regenerate": false  # 是否重新生成更精美的报告
    }

    返回:
    {
        "pdf_url": "PDF下载链接",
        "pdf_path": "PDF文件路径",
        "filename": "文件名"
    }
    """
    if PDFExporter is None:
        raise HTTPException(500, "PDF导出模块未加载")

    try:
        task_id = request.get("task_id")
        answer_id = request.get("answer_id")
        title = request.get("title", "数据分析报告")
        regenerate = request.get("regenerate", False)

        if not task_id or not answer_id:
            raise HTTPException(400, "缺少必需参数: task_id 和 answer_id")

        # 1. 加载原始分析数据
        analyzed_file = RESULTS_DIR / f"{task_id}_analyzed.json"
        if not analyzed_file.exists():
            raise HTTPException(404, "分析数据不存在")

        with open(analyzed_file, 'r', encoding='utf-8') as f:
            analyzed_data = json.load(f)

        # 2. 加载可视化报告
        report_file = RESULTS_DIR / f"{answer_id}.html"
        if not report_file.exists():
            raise HTTPException(404, "可视化报告不存在")

        with open(report_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 3. 加载元数据
        metadata_file = RESULTS_DIR / f"{answer_id}_metadata.json"
        user_query = "数据分析"
        summary = ""

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                user_query = metadata.get("user_query", user_query)
                summary = metadata.get("summary", summary)
                if not title or title == "数据分析报告":
                    title = metadata.get("title", title)

        # 4. 初始化 PDF 导出器
        pdf_dir = RESULTS_DIR / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        exporter = PDFExporter(output_dir=str(pdf_dir))

        # 5. 生成 PDF
        output_filename = f"{answer_id}.pdf"

        # 注意：由于 HTML 报告包含 JavaScript (ECharts)，WeasyPrint 无法渲染
        # 因此我们总是生成包含静态数据表格的精美 PDF 报告
        print(f"🎨 生成包含数据表格的精美 PDF 报告...")
        pdf_path = exporter.generate_summary_pdf(
            analyzed_data=analyzed_data,
            visualization_html=html_content,
            user_query=user_query,
            summary=summary,
            title=title,
            output_filename=output_filename
        )

        # 6. 返回下载链接
        pdf_filename = os.path.basename(pdf_path)
        pdf_url = f"/download_pdf/{pdf_filename}"

        return JSONResponse({
            "status": "success",
            "pdf_url": pdf_url,
            "pdf_path": pdf_path,
            "filename": pdf_filename,
            "message": "PDF报告生成成功"
        })

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ PDF导出失败: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"PDF导出失败: {str(e)}")


@app.get("/download_pdf/{filename}")
async def download_pdf(filename: str):
    """下载 PDF 文件"""
    try:
        pdf_dir = RESULTS_DIR / "pdfs"
        pdf_file = pdf_dir / filename

        if not pdf_file.exists():
            raise HTTPException(404, "PDF文件不存在")

        return FileResponse(
            path=str(pdf_file),
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"下载PDF失败: {str(e)}")


# -----------------------
# 启动服务
# -----------------------
if __name__ == "__main__":
    print("启动智能数据分析API服务...")
    print("=" * 70)
    print(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"根路径: http://{settings.HOST}:{settings.PORT}/")
    print()
    print("OCR处理流程:")
    print(f"  1️.上传文档: POST /ocr")
    print(f"  2️.查询状态: GET /status/{{task_id}}")
    print(f"  3️.获取结果: GET /results/{{task_id}}")
    print(f"  4️.查看报告: GET /report/{{task_id}}")
    print()
    print("智能问答分析:")
    print(f"  分析问题: POST /analyze")
    print(f"     请求: {{\"task_id\": \"xxx\", \"user_query\": \"分析该基金2024年业绩\"}}")
    print(f"  查看报告: GET /view_report/{{answer_id}}")
    print()
    print(f"其他接口:")
    print(f"  健康检查: GET /health")
    print(f"  结果列表: GET /results")
    print()
    print(f"结果目录: {RESULTS_DIR}")
    print(f"OCR服务: {OCR_SERVICE_URL}")
    print(f"AI模块: {'✅ 已加载' if DataAnalyzer and ReportGenerator else '未加载'}")
    print("=" * 70)
    print("服务已启动，完整流程：上传文档 → OCR识别 → 信息结构化 → 智能问答 → 可视化报告")

    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")