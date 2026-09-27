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

# ==================== 配置 ====================
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("VISUALIZER_API_KEY", "sk-e3ffbd4faceb4d498415e53e6e45ef5b")
API_BASE = os.getenv("VISUALIZER_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL_NAME = os.getenv("VISUALIZER_MODEL_NAME", "qwen3-max")


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
    def build_context(analyzed_data: Dict[str, Any], max_tokens: int = 8000) -> str:
        """
        构建紧凑的上下文
        
        策略:
        1. 提取所有 tables (最重要)
        2. 提取所有 key_points
        3. 按章节组织 summary
        """
        chunks = analyzed_data.get("analyzed_chunks", [])
        
        # 1. 收集所有表格
        all_tables = []
        for chunk in chunks:
            if "analysis" in chunk:
                analysis = chunk["analysis"]
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                
                for table in analysis.get("tables", []):
                    all_tables.append({
                        "section": header_path,
                        "table": table
                    })
        
        # 2. 收集所有关键点
        all_key_points = []
        for chunk in chunks:
            if "analysis" in chunk:
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                points = chunk["analysis"].get("key_points", [])
                for point in points:
                    all_key_points.append(f"[{header_path}] {point}")
        
        # 3. 收集章节摘要
        all_summaries = []
        for chunk in chunks:
            if "analysis" in chunk:
                header_path = chunk.get("metadata", {}).get("header_path", "未知章节")
                summary = chunk["analysis"].get("summary", "")
                if summary:
                    all_summaries.append(f"**{header_path}**: {summary}")
        
        # 4. 组装上下文
        context_parts = []
        
        # 表格部分 (最重要,放最前面)
        if all_tables:
            context_parts.append("# 📊 数据表格\n")
            for i, item in enumerate(all_tables, 1):  # 限制20个表格
                table = item["table"]
                context_parts.append(f"## 表格 {i}: {table['title']}")
                context_parts.append(f"**章节**: {item['section']}")
                
                # 表格内容
                headers = " | ".join(table["headers"])
                context_parts.append(f"| {headers} |")
                context_parts.append(f"| {' | '.join(['---'] * len(table['headers']))} |")
                
                for row in table["rows"]:  # 每个表格限制10行
                    context_parts.append(f"| {' | '.join(row)} |")
                
                if table.get("note"):
                    context_parts.append(f"*注: {table['note']}*")
                context_parts.append("")
        
        # 关键点部分
        if all_key_points:
            context_parts.append("\n# 🔑 关键要点\n")
            for point in all_key_points:  # 限制50个要点
                context_parts.append(f"- {point}")
        
        # 章节摘要部分
        if all_summaries:
            context_parts.append("\n# 📝 章节摘要\n")
            context_parts.append("\n".join(all_summaries))  # 限制30个摘要
        
        return "\n".join(context_parts)

# ==================== HTML报告生成器 ====================
class ReportGenerator:
    """生成HTML数据分析报告"""
    
    def __init__(self, api_key: str = API_KEY, base_url: str = API_BASE, model: str = MODEL_NAME):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.2,
            max_tokens=10240,
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=HTMLReport)
        
        self.prompt = PromptTemplate(
                    template=r"""你是可视化前端工程师，需把【用户要求 user_requirements】与【数据 data_json】渲染为 **三栏单屏 ECharts 看板**，并给出**针对用户问题的摘要结论**。

                # 一、硬约束（必须遵守）
                1) 仅使用 ECharts（CDN：<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>），不可引入其他库。
                2) 单屏：100vw × 100svh，overflow:hidden；禁止滚动。
                3) **严禁编造数据**：只能使用 data_json 中实际存在的数据；若某图缺数据就跳过该图，**绝不允许使用示例数据填充或虚构任何字段/类别/数值**。
                4) 输出必须匹配 Pydantic 模型 **HTMLReport**：返回三个字段——
                - html：完整可运行 HTML 字符串（含<html>/<head>/<body>，内联 CSS/JS）。
                - title：页面主标题（优先用 user_requirements.title；否则从数据主题提取）。
                - summary：**面向 user_requirements 的回答**（中文），用 3–7 条要点或 1–2 段话，总结关键结论（趋势、高/低点、同比环比、占比、异常等），不要描述"页面/HTML/图表怎么写"。

                # 二、视觉与布局（默认，可被用户覆盖）
                - 风格：深色霓虹（Neon Dark），背景为渐变+网格/星轨暗纹（纯 CSS）；玻璃拟物卡片（半透明、描边、圆角 16px、内外阴影、微光）。
                - 三列大面板：左(#colL)、中(#colC)、右(#colR)等宽；列内卡片紧凑排布。
                - 动效：进入动画 600–900ms，ECharts animation 'cubicOut'；emphasis 轻微发光。
                - 颜色：主色电光蓝/青，辅色紫/橙；柱/面积使用渐变；折线 smooth+圆点+标签。
                - 监听 window.resize，**防抖 ≥120ms** 且仅在尺寸真实变化时调用 chart.resize()。

                # 三、图表清单与最少数量
                **若用户未显式指定 charts/layout**，则按下列清单从 data_json 自动匹配字段并渲染：
                - KPI 顶栏（可选）：显示 3–5 个核心指标（value / unit / asPercent），带数值递增动画。
                - 中列顶部（宽）：时间趋势（折线/面积），如"年度净值增长率/营收/利润"等。
                - 左列：①分类占比（饼或环，如行业/资产配置）②子分类占比（饼或环）③月度/季度柱状汇总。
                - 中列底部：①多指标对比（多序列柱状）②双折线对比（如"基金 vs 基准"）。
                - 右列：①横向排行榜（条形，如重仓股/费用明细）②分类柱状 ③子类柱状 ④其他维度柱状。
                > 目标：**根据实际数据生成合适数量的图表**（优先质量，避免用示例数据凑数）；若数据更多，可继续在三列内追加卡片但仍保持单屏可见（必要时收紧内边距与字号）。

                # 四、数据协议（尽量按此键名解析；缺失就跳过对应图）
                **重要**：以下仅为数据结构示例，展示如何组织 data_json。实际渲染时必须使用真实数据，不得使用这些示例值。
                
                data_json 可能包含的数据结构（**仅供参考格式**，必须替换为实际数据）：
                {{
                "kpi": [ {{"label":"基金规模","value":1234567890,"unit":"元"}}, {{"label":"年化收益","value":0.0329,"asPercent":true}} ],
                "pies": {{
                    "asset_allocation": [{{"name":"股票","value":45.2}},{{"name":"债券","value":36.1}},{{"name":"现金","value":18.7}}],
                    "industry": [{{"name":"制造业","value":28.5}},{{"name":"金融业","value":22.3}},{{"name":"信息技术","value":19.8}},{{"name":"其他","value":29.4}}],
                    "custom": [{{"name":"实际类别A","value":...}},{{"name":"实际类别B","value":...}}]
                }},
                "series": {{
                    "annualGrowth": {{"categories":["2022","2023","2024"],"data":[-18.19,-13.35,3.29],"name":"净值增长率","unit":"%" }},
                    "profit": {{"categories":["2022","2023","2024"],"data":[-4.52e8,-2.81e8,3.12e7],"name":"本期利润","unit":"元" }},
                    "fundVsBenchmark": {{"categories":["过去三个月","过去六个月","过去一年","过去三年","过去五年","自成立以来"],
                                        "series":[ {{"name":"基金","unit":"%","data":[0.28,15.30,3.29,-26.78,17.74,1203.80]}},
                                                    {{"name":"业绩基准","unit":"%","data":[-1.57,5.72,13.10,8.60,19.59,463.31]}} ] }},
                    "monthlyData": {{"categories":["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"],
                                "series":[ {{"name":"实际指标名","unit":"实际单位","data":[...实际数据...] }} ] }},
                    "topHoldings": {{"categories":["股票A","股票B","股票C","股票D","股票E"],"data":[12.5,10.3,8.7,7.2,6.8],"name":"占净值比例","unit":"%" }},
                    "feeBreakdown": {{"categories":["管理费","托管费","销售服务费","其他"],"data":[1500000,250000,180000,50000],"name":"费用","unit":"元" }},
                    "anyCategory": {{"categories":["从实际数据提取的类别1","类别2","类别3"],"data":[实际值1,实际值2,实际值3],"name":"实际指标名","unit":"实际单位" }}
                }}
                }}

                - 百分比：当 asPercent=true 或 unit="%" 时，小数按百分比显示（0.25→25%）；"25%" 字符串按 25% 处理。
                - 所有轴/tooltip/标签必须带单位，与数据一致；金额支持千分位与"万元"换算（若 user_requirements 指定）。
                
                **再次强调**：上述 data_json 中的所有具体值（如"股票A"、"制造业"、数字等）仅为格式示例，实际使用时必须从 knowledge_base 提取真实数据，不得直接使用这些示例值渲染图表。

                # 五、用户可覆盖的声明（若提供则优先）
                - user_requirements.theme / title / subtitle / logo / brandColors。
                - user_requirements.charts：数组；每项可指定 {{id,type,title,dataset,xField,yField,series[],unit,asPercent,options}}。
                - user_requirements.layout：自定义三列/网格及卡片顺序与占位；如未提供，使用默认三列策略。

                # 六、输出规范
                1) **html**：
                - 顶部：左 LOGO（可空）+ 中间标题 + 右“导出 PNG”按钮（逐图 getDataURL 下载）。
                - 背景与卡片：暗纹+玻璃拟物；发光描边；圆角与阴影。
                - 三列容器：#colL / #colC / #colR，列内若干 .panel，每个包含 .panel-title 与 .chart。
                - 至少 7 张图（若数据可用），柱/折/饼/对比优先；横向条形用于排行。
                - resize 防抖（≥120ms）+ 尺寸变更判断再触发 chart.resize()。
                2) **title**：主标题（中文）。
                3) **summary**：
                - 只围绕用户提出的问题回答；例如“该基金 2022–2024 的净值增长趋势如何、与基准对比如何、利润变化点、哪类占比最高”等；
                - 给出 3–7 个要点或 1–2 段摘要，包含关键数字或百分比，避免介绍“页面/HTML/图表如何实现”。

                # 七、你可以使用的变量
                - user_requirements（原样文本）：{user_query}
                - data_json（原样文本）：{knowledge_base}

                {format_instructions}

                请把 user_requirements 与 data_json 结合，产出 **HTML / title / summary**。HTML 必须渲染酷炫三栏、≥7 张图（若数据允许），summary 直接回答用户问题的结论。""",
                    input_variables=["user_query", "knowledge_base"],
                    partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
                )



        
        self.chain = self.prompt | self.llm
    
    def generate_report(self, analyzed_data: Dict[str, Any], user_query: str) -> HTMLReport:
        """
        生成HTML报告
        
        Args:
            analyzed_data: analyzer.py 输出的结果
            user_query: 用户问题 (如"分析2024年收益情况")
        
        Returns:
            HTMLReport 对象
        """
        # 构建知识库
        kb_builder = KnowledgeBaseBuilder()
        knowledge_base = kb_builder.build_context(analyzed_data)
        
        print(f"知识库大小: {len(knowledge_base)} 字符")
        print(f"用户需求: {user_query}")
        
        # 调用LLM生成报告
        result = self.chain.invoke({
            "user_query": user_query,
            "knowledge_base": knowledge_base
        })
        
        report = self.output_parser.parse(result.content)
        
        print(f"报告生成完成: {report.title}")
        
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
        
        print(f"💾 报告已保存: {output_file}")
        print(f"📝 摘要: {report.summary}\n")