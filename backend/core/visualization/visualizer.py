"""
数据可视化生成器
根据结构化数据和用户问题生成 HTML 数据分析报告
"""
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

# 导入配置
import sys
from pathlib import Path
# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config.settings import settings

# ==================== 配置 ====================


# ==================== 数据模型 ====================
class HTMLReport(BaseModel):
    """HTML报告"""
    html: str = Field(description="完整的HTML代码(包含<html>标签)")
    title: str = Field(description="报告标题")
    summary: str = Field(description="分析摘要")

# ==================== 知识库构建器 ====================
class KnowledgeBaseBuilder:
    """从 analyzed_result.json 构建知识库"""
    
    @staticmethod
    def build_context(analyzed_data: Dict[str, Any]) -> str:
        """
        构建紧凑的上下文 - 适配 Information_structuring_v2.py
        
        数据结构变化:
        - v1: analysis.tables[].headers/rows
        - v2: analysis.tables[].headers/rows (相同)
        
        策略:
        1. 提取所有 tables (最重要)
        2. 提取所有 key_points
        3. 按章节组织 summary
        """
        chunks = analyzed_data.get("analyzed_chunks", [])
        
        # 1. 收集所有表格
        all_tables = []
        for chunk in chunks:
            if "analysis" in chunk and "error" not in chunk:
                analysis = chunk["analysis"]
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                
                for table in analysis.get("tables", []):
                    # 跳过无效表格
                    if not table.get("headers") or not table.get("rows"):
                        continue
                    
                    all_tables.append({
                        "section": header_path,
                        "table": table
                    })
        
        # 2. 收集所有关键点
        all_key_points = []
        for chunk in chunks:
            if "analysis" in chunk and "error" not in chunk:
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                points = chunk["analysis"].get("key_points", [])
                for point in points:
                    if point:  # 过滤空字符串
                        all_key_points.append(f"[{header_path}] {point}")
        
        # 3. 收集章节摘要
        all_summaries = []
        for chunk in chunks:
            if "analysis" in chunk and "error" not in chunk:
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                summary = chunk["analysis"].get("summary", "")
                if summary and len(summary) > 5:  # 过滤无效摘要
                    all_summaries.append(f"**{header_path}**: {summary}")
        
        # 4. 组装上下文
        context_parts = []
        
        # 表格部分 (最重要,放最前面)
        if all_tables:
            context_parts.append("# 数据表格\n")
            for i, item in enumerate(all_tables, 1):
                table = item["table"]
                context_parts.append(f"## 表格 {i}: {table.get('title', '未命名表格')}")
                context_parts.append(f"**章节**: {item['section']}")
                
                # 表格内容
                headers = table.get("headers", [])
                rows = table.get("rows", [])
                
                if headers:
                    headers_str = " | ".join(str(h) for h in headers)
                    context_parts.append(f"| {headers_str} |")
                    context_parts.append(f"| {' | '.join(['---'] * len(headers))} |")
                
                for row in rows:
                    # 确保行数据与表头长度一致
                    row_data = [str(cell) for cell in row]
                    if len(row_data) < len(headers):
                        row_data.extend([''] * (len(headers) - len(row_data)))
                    elif len(row_data) > len(headers):
                        row_data = row_data[:len(headers)]
                    
                    context_parts.append(f"| {' | '.join(row_data)} |")
                
                if table.get("note"):
                    context_parts.append(f"*注: {table['note']}*")
                context_parts.append("")
        
        # 关键点部分
        if all_key_points:
            context_parts.append("\n# 关键要点\n")
            for point in all_key_points:  # 限制最多50条,避免过长
                context_parts.append(f"- {point}")
        
        # 章节摘要部分
        if all_summaries:
            context_parts.append("\n# 章节摘要\n")
            context_parts.append("\n".join(all_summaries))  # ✅ 限制最多30条
        
        context = "\n".join(context_parts)
        
        # 统计信息
        print(f"\n上下文统计:")
        print(f"  - 表格数量: {len(all_tables)}")
        print(f"  - 关键要点: {len(all_key_points)}")
        print(f"  - 章节摘要: {len(all_summaries)}")
        print(f"  - 总字符数: {len(context):,}")
        print(f"  - 预估 Token: ~{len(context) // 4:,}")
        
        # 警告: 上下文过大
        if len(context) > 100000:
            print(f"  警告: 上下文过大 ({len(context)} 字符),可能超出 LLM 限制!")
            print(f"  建议: 调整 max_tables/max_points 参数或优化数据")
        
        return context

# ==================== HTML报告生成器 ====================
class ReportGenerator:
    """生成HTML数据分析报告"""
    
    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = None, 
        model: str = None
    ):
        """
        初始化报告生成器
        
        Args:
            api_key: API密钥（默认从配置读取）
            base_url: API基础URL（默认从配置读取）
            model: 模型名称（默认从配置读取）
        """
        self.llm = ChatOpenAI(
            api_key=api_key or settings.VISUALIZER_API_KEY,
            base_url=base_url or settings.VISUALIZER_API_BASE,
            model=model or settings.VISUALIZER_MODEL_NAME,
            temperature=0.2,
            max_tokens=10240,
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=HTMLReport)
        
        self.prompt = PromptTemplate(
            template=r"""你是资深可视化前端工程师。基于【user_requirements】与【data_json】生成单屏深色炫酷财务/运营分析 HTML 看板 (ECharts)。本次重点修复：顶部 KPI 区过小且单调、第三张图质量差/指标错配、整体色彩层次不足。

必须输出 JSON：title, summary, html 三字段（HTMLReport）。不要增加其它键。仅使用 data_json 真实字段。

问题与针对性改进：
1. KPI 区过小 → 调整为视窗高度的 22%–26%，占据明确视觉层。超过 5 个 KPI 时自动换行或滑动，不要压缩字体。
2. 单调 → 每个 KPI 使用不同霓虹渐变背景 + 细边描边或下方彩色进度条；颜色循环：蓝(#00d8ff/#18bfff)、青绿(#29f0b5)、紫(#c084fc)、橙(#ff9f40)、玫红(#ff5f6d)、青蓝(#147d8d)。禁止全部灰色或仅文字换色。
3. 第三张图错误 → 第三图优先固定为“Top10 重仓/排名”水平条形图：
   - 数据来源：若存在前十大持仓（名称 + 权重或市值），按权重/市值降序。
   - 轴：x 为数值；y 为名称。若数值是百分比权重请将轴名称写“占净值(%)”；若是万元市值写“市值(万元)”。
   - 百分比判定：若值均在 0~1 之间且最大值 < 1 → 视为比例 *100 后展示；若值普遍 >1 且 <20 并伴随占比语义 → 可直接当百分比（不再乘 100）根据实际数据决定；不得混用单位。
   - 标签：条末显示 “数值 + 单位” 或 “数值%”；可附加占比（如 同时有市值与占比时）。
   - 渐变配色与其它图区分（不要与主趋势同色）。
   - 若没有任何重仓/排名数据 → 第三图回退为 “阶段/区间收益” 折线/柱+折，对比 基金 vs 基准，不生成空白。
4. 避免空白 → 动态生成实际图数对应的 grid areas，不写不存在的区域。
5. 避免主图过大 → 主趋势图宽度系数约 1.4~1.7×单小图；仅占一行高度，不得纵向跨两行。
6. 标签策略优化 → 主趋势柱/折全部显示；环/饼显示 名称 + 数值或占比；排名条形显示条末数值；阶段对比线仅显示最新或关键点（≤6 个点可全部显示）；高密度图隐藏非关键标签但保留 tooltip。
7. 色彩层次 → 背景使用径向或线性渐变 (#081d33 → #041020)，KPI 卡片渐变或半透明玻璃 (rgba(255,255,255,0.06~0.12)) + 内阴影/外发光；各图系列颜色与 KPI 保持统一调色盘但不重复主图全部颜色。
8. 不得写死 height:300px 等固定高度；使用 grid + flex:1；图容器 height:100%。
9. summary 单字符串，3–6 条，用 \n 分隔，不得是数组；只写业务洞察（趋势、占比、集中度、变化、异常），禁止出现“代码/实现/HTML”。
10. 仅用 data_json 中真实字段；剔除全 0/空列；分类 >15 合并“其他”。
11. 单位换算：金额≥1e8→亿元（保留2位小数），≥1e4→万元，否则原单位；百分比 1–2 位小数+%。tooltip 与标签一致。
12. 禁止使用 HTML 注释 <!-- -->；禁止出现双花括号包裹的 JS 对象；若需要格式化标签使用 JS 函数返回字符串，不在 prompt 中写单花括号占位符示例。

推荐布局 (示例，可自适应)：
- 有 4 图（主趋势 + 构成 + 排名 + 补充）：
  KPI 行 (22%–26%)
  主体行：grid-template-columns: 1.6fr 1fr 1fr 1fr
  areas: "main pie rank extra"
- 有 3 图： "main pie rank"
- 有 5 图：两行主体
  "main pie rank extra"
  "main pie rank supplement"
中小屏 <1000px：repeat(auto-fit,minmax(320px,1fr)) 自动重排；KPI 卡改为两行或水平滚动（overflow-x:auto）。

主图类型：
- 柱+折双轴（利润/净值增长率 或 收益 vs 增长率）
构成图：
- 环/饼（行业/资产结构）不超过 10 类，其余合并
排名图（第三图重点）：
- 水平条形 Top10（权重或市值）+ 梯度条 + 条末标签
补充图：
- 阶段收益、资产结构对比、雷达（≥4 维）或散点关系。若数据贫乏可以省略。

summary 示例（格式示意，不要硬编码）：
年度柱折图显示净利润由亏转盈\n
环形图显示制造业权重约六成居首\n
Top10 重仓股集中度保持在26%左右\n
阶段收益对比近半年显著跑赢短期基准

输入：
- user_requirements：{user_query}
- data_json：{knowledge_base}

{format_instructions}

请严格返回 JSON：title, summary, html。""",
            input_variables=["user_query", "knowledge_base"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )

        self.chain = self.prompt | self.llm
    
    def generate_report(self, analyzed_data: Dict[str, Any], user_query: str) -> HTMLReport:
        """
        生成HTML报告
        
        Args:
            analyzed_data: 输出的结果
            user_query: 用户问题 (如"分析2024年收益情况")
        
        Returns:
            HTMLReport 对象
        """
        # 构建知识库
        kb_builder = KnowledgeBaseBuilder()
        knowledge_base = kb_builder.build_context(analyzed_data)
        
        # 若无分析数据，直接返回占位报告
        if not analyzed_data.get("analyzed_chunks") or len(knowledge_base) < 100:
            empty_html = """<html><head><meta charset='utf-8'><title>暂无数据</title></head>
<body style="font-family:Arial;background:#111;color:#ccc;display:flex;align-items:center;justify-content:center;height:100vh;">
<div>
<h1>暂无可视化数据</h1>
<p>当前 analyzed_result_v2.json 未包含分析结构。请先运行解析/分析流程。</p>
<p>用户请求：{}</p>
</div>
</body></html>""".format(user_query)
            return HTMLReport(
                html=empty_html,
                title="暂无数据",
                summary="源文件尚未解析出结构化内容，无法生成有效业绩可视化。请先运行数据抽取流程。"
            )
        
        print(f"\开始生成报告...")
        print(f"用户问题: {user_query}")
        
        result = self.chain.invoke({
            "user_query": user_query,
            "knowledge_base": knowledge_base
        })
        
        report = self.output_parser.parse(result.content)
        
        print(f"报告生成成功!")
        
        return report

# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 1. 加载分析结果
    with open("./data/Data_analysis/backwark/analyzed_result.json", encoding="utf-8") as f:
        analyzed_data = json.load(f)
    
    # 2. 初始化报告生成器
    generator = ReportGenerator()
    
    # 3. 用户提问
    user_queries = [
        "分析该基金2024年的整体业绩表现",
        "对比2023年和2024年的主要财务指标",
        "提取前十大重仓股信息并可视化",
    ]
    
    # 4. 生成报告
    for i, query in enumerate(user_queries, 1):
        print(f"\n{'='*60}")
        print(f"生成报告 {i}/{len(user_queries)}")
        print(f"{'='*60}\n")
        
        report = generator.generate_report(analyzed_data, query)
        
        # 保存HTML
        output_file = f"report_{i}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report.html)
        
        print(f"报告已保存: {output_file}")
        print(f"摘要: {report.summary}\n")