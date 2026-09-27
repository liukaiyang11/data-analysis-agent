#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek OCR API Server (vLLM) - 极简版 + 优化版
"""
import os
import io
import re
import argparse
import asyncio
from io import BytesIO
from typing import List
from concurrent.futures import ThreadPoolExecutor

import torch
from PIL import Image

try:
    import fitz
except Exception:
    fitz = None

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from vllm import LLM, SamplingParams
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr import DeepseekOCRForCausalLM
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor


app = FastAPI(title="DeepSeek OCR API (vLLM) - Optimized", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = None

cpu_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="CPU-Worker")
gpu_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="GPU-Worker")

vllm_lock = asyncio.Lock()

PROMPT_OCR = "<image>\n<|grounding|>Convert the document to markdown."
PROMPT_DESC = "<image>\nDescribe this image in detail."

# -----------------------
# Monkey Patch
# -----------------------
_original_tokenize = DeepseekOCRProcessor.tokenize_with_images

def _patched_tokenize(self, images, bos=True, eos=True, cropping=True, prompt=None):
    if prompt is not None:
        import config
        old = config.PROMPT
        config.PROMPT = prompt
        try:
            return _original_tokenize(self, images, bos, eos, cropping)
        finally:
            config.PROMPT = old
    return _original_tokenize(self, images, bos, eos, cropping)

DeepseekOCRProcessor.tokenize_with_images = _patched_tokenize


def pdf_to_images_sync(pdf_bytes: bytes, dpi: int = 144) -> List[Image.Image]:
    """PDF 转图片 """
    if fitz is None:
        raise RuntimeError("Please install PyMuPDF")
    
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    
    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA"):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert("RGB")
        
        images.append(img)
    
    doc.close()
    return images


def image_open_sync(image_bytes: bytes) -> Image.Image:
    """打开图片 (同步版本)"""
    return Image.open(BytesIO(image_bytes)).convert("RGB")


def clear_vllm_cache_sync():
    """清理 vLLM 缓存 (同步版本)"""
    if llm is None:
        return
    try:
        if hasattr(llm.llm_engine, 'input_preprocessor'):
            prep = llm.llm_engine.input_preprocessor
            if hasattr(prep, '_mm_processor_cache'):
                prep._mm_processor_cache.clear()
    except:
        pass


def tokenize_image_sync(image: Image.Image, prompt: str):
    """
    图像 tokenize (同步版本, CPU 密集)
    WARNING: 这是最大的优化点!
    """
    processor = DeepseekOCRProcessor()
    return processor.tokenize_with_images(images=[image], prompt=prompt)


def vllm_generate_sync(tokenized, prompt: str) -> str:
    """
    vLLM 推理 (同步版本, GPU 密集)
    注意: tokenized 已经在 CPU 线程池完成
    """
    batch_inputs = [{
        "prompt": prompt,
        "multi_modal_data": {"image": tokenized}
    }]
    
    if prompt == PROMPT_OCR:
        logits_proc = [NoRepeatNGramLogitsProcessor(20, 50, {128821, 128822})]
        params = SamplingParams(
            temperature=0.0,
            max_tokens=2048,
            skip_special_tokens=False,
            logits_processors=logits_proc,
            repetition_penalty=1.05,
        )
    else:
        params = SamplingParams(
            temperature=0.0,
            max_tokens=512,
            skip_special_tokens=False,
        )
    
    outputs = llm.generate(batch_inputs, params)
    return outputs[0].outputs[0].text


def clean_markdown_sync(text: str) -> str:
    """清理 Markdown (同步版本)"""
    text = re.sub(r'<\|ref\|>.*?<\|/ref\|>', '', text)
    text = re.sub(r'<\|det\|>.*?<\|/det\|>', '', text)
    text = re.sub(r'<\|.*?\|>', '', text)
    text = re.sub(r'\[\[.*?\]\]', '', text)
    text = re.sub(r'={50,}.*?={50,}', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()



async def pdf_to_images_async(pdf_bytes: bytes, dpi: int = 144) -> List[Image.Image]:
    """PDF 转图片 (异步)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(cpu_executor, pdf_to_images_sync, pdf_bytes, dpi)


async def image_open_async(image_bytes: bytes) -> Image.Image:
    """打开图片 (异步)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(cpu_executor, image_open_sync, image_bytes)


async def tokenize_image_async(image: Image.Image, prompt: str):
    """
    图像 tokenize (异步)
    NOTE: 关键优化: 在 CPU 线程池执行
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(cpu_executor, tokenize_image_sync, image, prompt)


async def vllm_generate_async(image: Image.Image, prompt: str) -> str:
    """
    完整的 vLLM 推理流程 (异步)
    优化: 分离 tokenize (CPU) 和 generate (GPU)
    """
    # 步骤1: tokenize (CPU 密集, 在 CPU 线程池执行)
    tokenized = await tokenize_image_async(image, prompt)
    
    # 步骤2: GPU 推理 (GPU 密集, 在 GPU 线程池执行, 有锁保护)
    async with vllm_lock:
        # 清理缓存 (在 GPU 线程池执行)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(gpu_executor, clear_vllm_cache_sync)
        
        # GPU 推理
        result = await loop.run_in_executor(
            gpu_executor,
            vllm_generate_sync,
            tokenized,
            prompt
        )
        
        return result


async def clean_markdown_async(text: str) -> str:
    """清理 Markdown (异步)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(cpu_executor, clean_markdown_sync, text)


async def generate_image_description_async(image: Image.Image) -> str:
    """生成图片描述 (异步)"""
    try:
        # GPU 推理
        result = await vllm_generate_async(image, PROMPT_DESC)
        
        # CPU 后处理
        loop = asyncio.get_event_loop()
        
        def process_desc(text):
            desc = re.sub(r'<\|ref\|>.*?<\|/ref\|>', '', text)
            desc = re.sub(r'<\|det\|>.*?<\|/det\|>', '', desc)
            desc = re.sub(r'<\|.*?\|>', '', desc)
            desc = re.sub(r'\[\[.*?\]\]', '', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            
            if len(desc) > 200:
                cutoff = desc[:200].rfind('.')
                if cutoff > 100:
                    desc = desc[:cutoff + 1]
                else:
                    desc = desc[:200].rsplit(' ', 1)[0] + '...'
            
            return desc
        
        desc = await loop.run_in_executor(cpu_executor, process_desc, result)
        return desc
    
    except Exception as e:
        print(f"WARNING: 图片描述失败: {e}")
        return ""


# -----------------------
# 模型初始化
# -----------------------
def initialize_model(model_path: str, gpu_id: int = 0):
    global llm
    
    ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)
    
    if torch.cuda.is_available():
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    os.environ['VLLM_USE_V1'] = '0'
    
    print(f"[INFO] 加载模型: {model_path}")
    
    llm = LLM(
        model=model_path,
        hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
        block_size=256,
        enforce_eager=False,
        trust_remote_code=True,
        max_model_len=3281,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.5,
        max_num_seqs=20,
        disable_mm_preprocessor_cache=True,
    )
    
    print("[SUCCESS] 模型加载完成")
    print(f"[INFO] 线程池配置:")
    print(f"   - CPU 线程池: {cpu_executor._max_workers} 线程")
    print(f"   - GPU 线程池: {gpu_executor._max_workers} 线程")


# -----------------------
# API 路由
# -----------------------
@app.get("/")
async def root():
    return {
        "service": "DeepSeek OCR (vLLM) - Optimized",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_ready": llm is not None,
        "cpu_workers": cpu_executor._max_workers,
        "gpu_workers": gpu_executor._max_workers,
    }


async def vllm_generate_batch_async(
    images: List[Image.Image], 
    prompt: str,
    show_progress: bool = True
) -> List[str]:
    """
    批量 vLLM 推理 - 真正的批处理优化
    
    Args:
        images: 图片列表
        prompt: 提示词
        show_progress: 是否显示进度
    
    Returns:
        生成的文本列表
    """
    total = len(images)
    
    # 步骤1: 并发 tokenize
    # 标准化图片 -> Vision Encoder (ViT) -> 图像特征向量 (例如：[196, 1024] - 196个位置，每个1024维)
    if show_progress:
        print(f"   [1/3] Tokenize {total} 页...")
    
    tokenize_tasks = [tokenize_image_async(img, prompt) for img in images]
    all_tokenized = await asyncio.gather(*tokenize_tasks)
    
    if show_progress:
        print(f"   [1/3] Tokenize 完成")
    
    # 步骤2: 构造批量输入
    batch_inputs = [
        {
            "prompt": prompt,
            "multi_modal_data": {"image": tok}
        }
        for tok in all_tokenized
    ]
    
    # 步骤3: 批量 GPU 推理
    async with vllm_lock:
        if show_progress:
            print(f"   [2/3] GPU 批量推理 {total} 页...")
        
        loop = asyncio.get_event_loop()
        
        # 清理缓存
        await loop.run_in_executor(gpu_executor, clear_vllm_cache_sync)
        
        # 批量推理
        def batch_generate():
            # 根据 prompt 类型选择参数
            if prompt == PROMPT_OCR:
                logits_proc = [NoRepeatNGramLogitsProcessor(20, 50, {128821, 128822})]
                params = SamplingParams(
                    temperature=0.0,
                    max_tokens=2048,
                    skip_special_tokens=False,
                    logits_processors=logits_proc,
                    repetition_penalty=1.05,
                )
            else:
                params = SamplingParams(
                    temperature=0.0,
                    max_tokens=512,
                    skip_special_tokens=False,
                )
            
            # NOTE: 关键: 批量调用
            outputs = llm.generate(batch_inputs, params)
            return [out.outputs[0].text for out in outputs]
        
        results = await loop.run_in_executor(gpu_executor, batch_generate)
        
        if show_progress:
            print(f"   [2/3] GPU 推理完成")
        
        return results


@app.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    enable_description: bool = Form(False),
):
    """OCmR 接口 (批量处理)"""
    if llm is None:
        raise HTTPException(503, "模型未加载")
    
    import time
    start_time = time.time()
    
    try:
        # 1. 读取文件
        contents = await file.read()
        t1 = time.time()
        
        # 2. 解析文件
        if file.filename.lower().endswith('.pdf'):
            # 如果是PDF，则转换为图片列表
            images = await pdf_to_images_async(contents)
        else:
            # 如果是图片，则直接打开
            images = [await image_open_async(contents)]
        
        t2 = time.time()
  
        # 3. 批量 OCR
        raw_results = await vllm_generate_batch_async(images, PROMPT_OCR)
        t3 = time.time()
        print(f"   OCR 耗时: {t3 - t2:.2f}s")
        
        # 4. 后处理
        print(f"   [3/3] 后处理...")
        
        async def postprocess(idx: int, raw: str, img: Image.Image) -> str:
            # 图片描述
            if enable_description:
                img_pattern = r'<\|ref\|>image<\|/ref\|><\|det\|>\[\[.*?\]\]<\|/det\|>'
                matches = list(re.finditer(img_pattern, raw))
                
                for match in matches:
                    desc = await generate_image_description_async(img)
                    replacement = f"[图片: {desc}]" if desc else "[图片]"
                    raw = raw.replace(match.group(0), replacement)
            
            # 清理 Markdown
            cleaned = await clean_markdown_async(raw)
            return cleaned if cleaned else ""
        
        tasks = [postprocess(i, raw, img) for i, (raw, img) in enumerate(zip(raw_results, images))]
        md_parts = await asyncio.gather(*tasks)
        
        t4 = time.time()
        print(f"   [3/3] 后处理完成 ({t4 - t3:.2f}s)")
        
        # 5. 合并结果
        final_md = "\n\n".join([md for md in md_parts if md])
        
        total_time = time.time() - start_time
        print(f"{'='*60}")
        print(f"[SUCCESS] 全部完成")
        print(f"   总耗时: {total_time:.2f}s")
        print(f"   平均: {total_time / len(images):.2f}s/页")
        print(f"{'='*60}\n")
        
        return JSONResponse({
            "markdown": final_md,
            "page_count": len(images),
            "processing_time": round(total_time, 2),
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] 处理失败: {e}")
        print(traceback.format_exc())
        raise HTTPException(500, f"处理失败: {e}")


# -----------------------
# 优雅关闭
# -----------------------
@app.on_event("shutdown")
async def shutdown_event():
    print("[INFO] 关闭线程池...")
    cpu_executor.shutdown(wait=True)
    gpu_executor.shutdown(wait=True)
    print("[SUCCESS] 线程池已关闭")


# -----------------------
# 启动
# -----------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="模型路径")
    parser.add_argument("--gpu-id", type=int, default=0, help="GPU ID")
    parser.add_argument("--port", type=int, default=8708, help="端口")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--cpu-workers", type=int, default=2, help="CPU 线程池大小")
    
    args = parser.parse_args()
    
    # 更新线程池大小
    global cpu_executor
    cpu_executor = ThreadPoolExecutor(
        max_workers=args.cpu_workers,
        thread_name_prefix="CPU-Worker"
    )
    
    initialize_model(args.model_path, args.gpu_id)
    
    print(f"\n[INFO] 服务启动: http://{args.host}:{args.port}")
    print(f"[INFO] 接口文档: http://{args.host}:{args.port}/docs\n")
    
    uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()