import re
import json
import os
from typing import List, Dict, Any
from transformers import Qwen2TokenizerFast
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# ✅ LangChain 1.0 新的导入路径
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI  # 在线 LLM
from pydantic import BaseModel, Field

# ==================== 加载环境变量 ====================
load_dotenv()

# ==================== 配置 ====================
TOKENIZER_PATH = os.getenv("QWEN_TOKENIZER_PATH", "./data/Data_analysis/Qwen-tokenizer")
tokenizer = Qwen2TokenizerFast.from_pretrained(TOKENIZER_PATH)
CHUNK_SIZE = int(os.getenv("ANALYSIS_CHUNK_SIZE", "1500"))  # token数
MAX_WORKERS = int(os.getenv("ANALYSIS_MAX_WORKERS", "10"))  # ✅ 并发数

# API 配置（从 .env 文件读取）
API_KEY = os.getenv("ANALYSIS_API_KEY", "sk-e3ffbd4faceb4d498415e53e6e45ef5b")
API_BASE = os.getenv("ANALYSIS_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL_NAME = os.getenv("ANALYSIS_MODEL_NAME", "qwen3-max")

# ==================== 数据模型 ====================
class ExtractedTable(BaseModel):
    """提取的表格"""
    title: str = Field(description="表格标题")
    headers: List[str] = Field(description="表头列表")
    rows: List[List[str]] = Field(description="数据行列表")
    note: str = Field(default="", description="备注说明")

class ChunkAnalysis(BaseModel):
    """单个chunk的分析结果"""
    summary: str = Field(description="内容摘要")
    tables: List[ExtractedTable] = Field(description="提取的表格列表")
    key_points: List[str] = Field(description="关键要点列表")

# ==================== Markdown切分器 ====================
class TitleBasedMarkdownSplitter:
    """基于标题的Markdown切分器"""
    
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size
        self.head_pattern = re.compile(r"^#+\s")
    
    def split_text(self, markdown: str) -> List[Document]:
        """切分markdown文本"""
        lines = markdown.splitlines(keepends=True)
        split_points = self._find_title_split_points(lines)
        initial_chunks = self._create_chunks_by_title(lines, split_points)
        return self._merge_small_chunks(initial_chunks)
    
    def _find_title_split_points(self, lines: List[str]) -> List[Dict]:
        """找到所有标题切分点（改进版：保留完整标题路径）"""
        points = [{"line": 0, "level": 0, "metadata": {}}]
        
        # ✅ 改用栈结构保存标题路径
        title_stack = []  # [(level, title), ...]
        
        for i, line in enumerate(lines):
            level = self._get_header_level(line)
            if level > 0:
                title = line.strip("#").strip()
                
                # 弹出所有更高或同级的标题
                while title_stack and title_stack[-1][0] >= level:
                    title_stack.pop()
                
                # 加入当前标题
                title_stack.append((level, title))
                
                # 构建完整路径的 metadata
                metadata = {}
                for lvl, tit in title_stack:
                    # ✅ 改为 "Header_1", "Header_2" 等，避免覆盖
                    metadata[f"Header_{lvl}"] = tit
                
                # ✅ 额外保存完整路径
                metadata["header_path"] = " > ".join([t for _, t in title_stack])
                
                points.append({
                    "line": i, 
                    "level": level, 
                    "metadata": metadata.copy()
                })
        
        points.append({"line": len(lines), "level": 0, "metadata": {}})
        return points
    
    def _create_chunks_by_title(self, lines: List[str], points: List[Dict]) -> List[Document]:
        """按标题创建初始chunks"""
        chunks = []
        for i in range(len(points) - 1):
            start = points[i]["line"]
            end = points[i + 1]["line"]
            content = "".join(lines[start:end])
            metadata = points[i]["metadata"]
            chunks.append(Document(page_content=content, metadata=metadata))
        return chunks
    
    def _merge_small_chunks(self, chunks: List[Document]) -> List[Document]:
        """合并小块"""
        result = []
        chunk_tmp = []
        head_chunk_tmp = []
        current_length = 0
        
        for chunk in chunks:
            chunk_tokens = len(tokenizer(chunk.page_content)["input_ids"])
            current_length += chunk_tokens
            
            if current_length <= self.chunk_size:
                chunk_tmp.append(chunk)
                if self.head_pattern.match(chunk.page_content):
                    head_chunk_tmp.append(chunk)
                else:
                    head_chunk_tmp = []
            else:
                if head_chunk_tmp:
                    chunk_tmp = chunk_tmp[:-len(head_chunk_tmp)]
                
                if chunk_tmp:
                    result.append(self._combine_chunks(chunk_tmp))
                
                chunk_tmp = head_chunk_tmp + [chunk]
                head_chunk_tmp = [chunk] if self.head_pattern.match(chunk.page_content) else []
                current_length = len(tokenizer("\n".join([c.page_content for c in chunk_tmp]))["input_ids"])
        
        if chunk_tmp:
            result.append(self._combine_chunks(chunk_tmp))
        
        return result
    
    def _combine_chunks(self, chunks: List[Document]) -> Document:
        """合并多个chunk"""
        content = "\n".join([c.page_content for c in chunks])
        metadata = {}
        for c in chunks:
            metadata.update(c.metadata)
        return Document(page_content=content, metadata=metadata)
    
    def _get_header_level(self, line: str) -> int:
        """获取标题级别"""
        match = re.match(r"^(#+)\s+", line)
        return len(match.group(1)) if match else 0

# ==================== 数据分析器 ====================
class DataAnalyzer:
    """数据分析器 (调用在线 LLM + 并发)"""
    
    def __init__(self, api_key: str = API_KEY, base_url: str = API_BASE, model: str = MODEL_NAME, max_workers: int = MAX_WORKERS):
        # 初始化在线 LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.1,
            max_tokens=2048,
            http_client=None,  # 明确设置 http_client 为 None，避免 proxies 冲突
        )
        
        self.splitter = TitleBasedMarkdownSplitter(chunk_size=CHUNK_SIZE)
        self.output_parser = PydanticOutputParser(pydantic_object=ChunkAnalysis)
        self.max_workers = max_workers
        # Prompt
        self.prompt = PromptTemplate(
            template="""你是一个专业的金融文档分析师，擅长从年度报告、财务报表等文档中提取结构化数据。

## 分析任务
对以下文档片段进行深度分析，输出结构化数据（JSON格式）。

## 输出要求

### 1. 内容摘要 (summary)
- 用 1-2 句话概括该片段的核心内容
- 突出数字、时间、变化趋势等关键信息
- 如果包含多个主题，简要列举

### 2. 表格提取 (tables)
**转换原则**：
- **原文已有表格**：直接提取并保留原始结构
- **可结构化数据**：将列表、对比、统计等信息转为表格
  - 示例：多个并列数据（如"收入100万、支出80万、净利润20万"）
  - 示例：时间序列对比（如"2023年X，2024年Y"）
  - 示例：多维度描述（如"产品A特性1、特性2；产品B特性1、特性2"）
- **纯叙述性文字**：如政策说明、风险提示、流程描述等，不强制转表格

**表格要求**：
- `title`: 简洁明确的表格标题（如"2024年收支对比"）
- `headers`: 列名清晰（如["项目", "金额", "占比"]）
- `rows`: 每行数据对齐
- `note`: 补充说明（如单位、数据来源、计算方法）

**表格数量**：
- 根据内容自然划分，不强制数量
- 优先合并相关数据到同一表格
- 避免过度拆分（如将5个数字拆成5个表格）

### 3. 关键要点 (key_points)
- 提取 3-10 个核心要点（视内容而定）
- 每个要点独立成句，包含完整信息
- 重点标注：
  - 数字变化（如"营收同比增长25%"）
  - 时间节点（如"2024年7月实施新政策"）
  - 关键结论（如"主要风险为市场波动"）
- 要点之间避免重复信息

---

## 输入数据

**文档片段**：
```
{markdown_chunk}
```

**文档层级元数据**：
```json
{metadata}
```
- `header_path`: 完整标题路径（如"§3 财务指标 > 3.1 主要数据"）
- `Header_1`, `Header_2`等：各级标题内容

---

## 输出格式

{format_instructions}

---

## 注意事项
1. **保持客观**：不添加原文没有的解读或推测
2. **数据准确**：确保数字、百分比、单位正确
3. **信息完整**：关键上下文（如时间范围、对比基准）不能丢失
4. **格式统一**：
   - 金额加千分位（如"1,234,567.89"）
   - 百分比保留小数（如"12.34%"）
   - 日期统一格式（如"2024-12-31"）

请严格按照JSON格式输出分析结果：""",
            input_variables=["markdown_chunk", "metadata"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        self.chain = self.prompt | self.llm
    
    def _process_single_chunk(self, chunk: Document, chunk_id: int) -> Dict[str, Any]:
        """处理单个chunk (用于并发)"""
        try:
            print(f"处理块 {chunk_id + 1}...")
            
            # 传入优化后的 metadata（JSON格式更易LLM理解）
            result = self.chain.invoke({
                "markdown_chunk": chunk.page_content,
                "metadata": json.dumps(chunk.metadata, ensure_ascii=False, indent=2)
            })
            
            analysis = self.output_parser.parse(result.content)
            
            print(f"块 {chunk_id + 1} 分析完成")
            
            return {
                "chunk_id": chunk_id,
                "original_content": chunk.page_content,
                "metadata": chunk.metadata,  # ✅ 保留完整 metadata
                "analysis": analysis.model_dump()
            }
        
        except Exception as e:
            print(f"⚠️ 块 {chunk_id + 1} 解析失败: {e}")
            return {
                "chunk_id": chunk_id,
                "error": str(e),
                "raw_output": result.content if 'result' in locals() else None
            }
    
    def analyze_ocr_json(self, ocr_json: Dict[str, Any], use_concurrent: bool = True) -> Dict[str, Any]:
        """分析OCR返回的JSON
        
        Args:
            ocr_json: OCR结果
            use_concurrent: 是否使用并发 (默认True)
        """
        markdown = ocr_json.get("markdown", "")
        
        # 1. 切分markdown
        chunks = self.splitter.split_text(markdown)
        print(f"文档已切分为 {len(chunks)} 个块")
        
        # 2. 分析每个chunk
        if use_concurrent:
            print(f"使用并发模式 (max_workers={self.max_workers})")
            analyzed_chunks = self._analyze_concurrent(chunks)
        else:
            print(f"使用串行模式")
            analyzed_chunks = self._analyze_sequential(chunks)
        
        # 3. 构建最终结果
        return {
            "source": ocr_json,
            "total_chunks": len(chunks),
            "analyzed_chunks": analyzed_chunks,
            "metadata": {
                "chunk_size": CHUNK_SIZE,
                "tokenizer": "Qwen2",
                "model": MODEL_NAME,
                "concurrent": use_concurrent,
                "max_workers": self.max_workers if use_concurrent else 1
            }
        }
    
    def _analyze_sequential(self, chunks: List[Document]) -> List[Dict[str, Any]]:
        """串行处理"""
        results = []
        for i, chunk in enumerate(chunks):
            result = self._process_single_chunk(chunk, i)
            results.append(result)
        return results
    
    def _analyze_concurrent(self, chunks: List[Document]) -> List[Dict[str, Any]]:
        """并发处理 (使用线程池)"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = [
                executor.submit(self._process_single_chunk, chunk, i)
                for i, chunk in enumerate(chunks)
            ]
            
            # 按顺序收集结果
            results = []
            for future in futures:
                result = future.result()
                results.append(result)
            
            # 按 chunk_id 排序
            results.sort(key=lambda x: x["chunk_id"])
            
        return results

# ==================== 使用示例 ====================
if __name__ == "__main__":
    import time
    
    # 初始化分析器
    analyzer = DataAnalyzer(
        api_key=API_KEY,
        base_url=API_BASE,
        model=MODEL_NAME,
        max_workers=5  # ✅ 并发数
    )
    
    # 读取OCR结果
    with open("./data/data/10华夏收入混合型证券投资基金2024年年度报告.json", encoding="utf-8") as f:
        ocr_data = json.load(f)
    
    # 执行分析 (并发模式)
    print("🚀 开始分析 (并发模式)...")
    start_time = time.time()
    
    result = analyzer.analyze_ocr_json(ocr_data, use_concurrent=True)
    
    elapsed = time.time() - start_time
    
    # 保存结果
    import os
    with open(os.path.join(os.path.dirname(__file__),"analyzed_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分析完成! 结果已保存到 analyzed_result.json")
    print(f"📊 总块数: {result['total_chunks']}")
    print(f"✅ 成功: {sum(1 for c in result['analyzed_chunks'] if 'analysis' in c)}")
    print(f"⚠️ 失败: {sum(1 for c in result['analyzed_chunks'] if 'error' in c)}")
    print(f"⏱️  耗时: {elapsed:.2f}秒")
    print(f"⚡ 平均每块: {elapsed/result['total_chunks']:.2f}秒")