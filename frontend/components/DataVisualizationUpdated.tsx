import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { FileText, Download, Maximize2, RefreshCw, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getResultsList, downloadResult, type OCRResult } from './api';

interface DataVisualizationProps {
  theme: 'light' | 'dark';
  onPreviewReport: () => void;
  ocrResult?: OCRResult | null;
}

// 模拟数据（作为后备）
const mockSalesData = [
  { month: '1月', value: 4200 },
  { month: '2月', value: 5800 },
  { month: '3月', value: 7200 },
  { month: '4月', value: 6800 },
  { month: '5月', value: 8900 },
  { month: '6月', value: 9500 },
];

const mockGrowthData = [
  { month: '1月', rate: 12 },
  { month: '2月', rate: 19 },
  { month: '3月', rate: 25 },
  { month: '4月', rate: 22 },
  { month: '5月', rate: 31 },
  { month: '6月', rate: 35 },
];

const mockCategoryData = [
  { name: '产品A', value: 35 },
  { name: '产品B', value: 28 },
  { name: '产品C', value: 22 },
  { name: '产品D', value: 15 },
];

const COLORS = ['#3B82F6', '#06B6D4', '#8B5CF6', '#F59E0B'];

export function DataVisualizationUpdated({ theme, onPreviewReport, ocrResult }: DataVisualizationProps) {
  const [salesData, setSalesData] = useState(mockSalesData);
  const [growthData, setGrowthData] = useState(mockGrowthData);
  const [categoryData, setCategoryData] = useState(mockCategoryData);
  const [resultsList, setResultsList] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useOCRData, setUseOCRData] = useState(false);

  const cardClass = theme === 'light'
    ? 'bg-white/60 border-white/40 shadow-xl shadow-indigo-500/10 hover:shadow-2xl hover:shadow-indigo-500/20 backdrop-blur-xl'
    : 'bg-slate-800/80 border-slate-700/50 shadow-xl shadow-blue-500/10 hover:shadow-2xl hover:shadow-blue-500/20 backdrop-blur-xl';

  const textColor = theme === 'light' ? '#1f2937' : '#f1f5f9';
  const gridColor = theme === 'light' ? '#e5e7eb' : '#475569';

  // 解析OCR结果中的数据
  const parseOCRData = (markdown: string) => {
    try {
      // 简单的数据解析逻辑（可以根据实际OCR结果格式调整）
      const lines = markdown.split('\n');
      const sales: any[] = [];
      const growth: any[] = [];
      const categories: any[] = [];

      let currentSection = '';
      lines.forEach((line, index) => {
        const trimmedLine = line.trim();

        // 检测数据部分
        if (trimmedLine.includes('销售额') || trimmedLine.includes('收入')) {
          currentSection = 'sales';
        } else if (trimmedLine.includes('增长率') || trimmedLine.includes('增长')) {
          currentSection = 'growth';
        } else if (trimmedLine.includes('产品') || trimmedLine.includes('分类')) {
          currentSection = 'categories';
        }

        // 解析表格数据
        if (trimmedLine.includes('|') && currentSection) {
          const parts = trimmedLine.split('|').map(p => p.trim()).filter(p => p);
          if (parts.length >= 3) {
            if (currentSection === 'sales' && parts[0].includes('月')) {
              // 解析销售数据
              for (let i = 1; i < parts.length; i++) {
                const month = parts[0];
                const value = parseFloat(parts[i].replace(/[^\d.]/g, ''));
                if (!isNaN(value)) {
                  sales.push({ month, value });
                }
              }
            } else if (currentSection === 'growth' && parts[0].includes('月')) {
              // 解析增长数据
              for (let i = 1; i < parts.length; i++) {
                const month = parts[0];
                const rate = parseFloat(parts[i].replace(/[^\d.]/g, ''));
                if (!isNaN(rate)) {
                  growth.push({ month, rate });
                }
              }
            } else if (currentSection === 'categories' && parts.length >= 2) {
              // 解析分类数据
              const name = parts[0];
              const value = parseFloat(parts[1].replace(/[^\d.]/g, ''));
              if (!isNaN(value)) {
                categories.push({ name, value });
              }
            }
          }
        }

        // 解析简单的数字格式（如：1月: 4200万元）
        const salesMatch = trimmedLine.match(/(\d+[月]?)[:：]\s*([\d,.]+)\s*(万元|元|万)/);
        if (salesMatch) {
          const month = salesMatch[1];
          const value = parseFloat(salesMatch[2].replace(/[,.]/g, ''));
          if (!isNaN(value)) {
            sales.push({ month, value });
          }
        }
      });

      return { sales, growth, categories };
    } catch (error) {
      console.error('解析OCR数据失败:', error);
      return { sales: [], growth: [], categories: [] };
    }
  };

  // 当有OCR结果时，解析数据
  useEffect(() => {
    if (ocrResult && ocrResult.markdown && useOCRData) {
      setIsLoading(true);
      const parsedData = parseOCRData(ocrResult.markdown);

      // 更新数据（如果解析成功则使用解析的数据，否则保持模拟数据）
      setSalesData(parsedData.sales.length > 0 ? parsedData.sales : mockSalesData);
      setGrowthData(parsedData.growth.length > 0 ? parsedData.growth : mockGrowthData);
      setCategoryData(parsedData.categories.length > 0 ? parsedData.categories : mockCategoryData);

      setTimeout(() => setIsLoading(false), 500);
    }
  }, [ocrResult, useOCRData]);

  // 获取处理结果列表
  const loadResultsList = async () => {
    try {
      const results = await getResultsList();
      setResultsList(results.results || []);
    } catch (error) {
      console.error('获取结果列表失败:', error);
    }
  };

  const handleRefreshData = () => {
    if (ocrResult && ocrResult.markdown) {
      setUseOCRData(!useOCRData);
    }
    loadResultsList();
  };

  const handleDownloadResults = async (filename: string) => {
    try {
      await downloadResult(filename);
    } catch (error) {
      console.error('下载失败:', error);
    }
  };

  useEffect(() => {
    loadResultsList();
  }, []);

  return (
    <div className="w-1/2 p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent ${
          theme === 'light'
            ? 'from-indigo-600 to-purple-600'
            : 'from-blue-400 to-cyan-400'
        }`}>
          数据分析可视化结果
        </h2>
        <div className="flex items-center gap-2">
          {/* 数据源切换 */}
          {ocrResult && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshData}
              className={`gap-2 transition-all ${
                theme === 'light'
                  ? 'hover:bg-indigo-50 hover:text-indigo-600'
                  : 'hover:bg-slate-700 hover:text-cyan-400 text-gray-300'
              }`}
            >
              <RefreshCw className="w-4 h-4" />
              {useOCRData ? 'OCR数据' : '模拟数据'}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className={`gap-2 transition-all ${
              theme === 'light'
                ? 'hover:bg-indigo-50 hover:text-indigo-600'
                : 'hover:bg-slate-700 hover:text-cyan-400 text-gray-300'
            }`}
          >
            <Maximize2 className="w-4 h-4" />
            全屏展示
          </Button>
        </div>
      </div>

      {/* 数据来源提示 */}
      {ocrResult && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-4 p-3 rounded-lg text-sm ${
            theme === 'light'
              ? 'bg-blue-50 border border-blue-200 text-blue-700'
              : 'bg-blue-900/20 border border-blue-700/30 text-blue-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span>
              📊 数据来源: {ocrResult.file_name} ({ocrResult.page_count}页)
            </span>
            <span className="text-xs opacity-70">
              {useOCRData ? '✅ 使用OCR解析数据' : '📈 显示模拟示例数据'}
            </span>
          </div>
        </motion.div>
      )}

      <div className="space-y-6">
        {/* 销售额趋势 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className={`p-6 transition-all relative overflow-hidden group ${cardClass}`}>
            {/* 卡片光晕效果 */}
            <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
              theme === 'light'
                ? 'bg-gradient-to-br from-indigo-500/5 to-purple-500/5'
                : 'bg-gradient-to-br from-blue-500/5 to-cyan-500/5'
            }`} />
            <h3 className={`mb-4 relative z-10 ${
              theme === 'light' ? 'text-gray-700' : 'text-gray-100'
            }`}>
              销售额趋势
              {isLoading && <RefreshCw className="w-4 h-4 inline ml-2 animate-spin" />}
            </h3>
            <ResponsiveContainer width="100%" height={250} className="relative z-10">
              <BarChart data={salesData}>
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={theme === 'light' ? '#6366f1' : '#3b82f6'} stopOpacity={0.9}/>
                    <stop offset="100%" stopColor={theme === 'light' ? '#8b5cf6' : '#06b6d4'} stopOpacity={0.6}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} opacity={0.3} />
                <XAxis dataKey="month" stroke={textColor} />
                <YAxis stroke={textColor} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: theme === 'light' ? 'rgba(255,255,255,0.95)' : 'rgba(0,0,0,0.8)',
                    border: `1px solid ${theme === 'light' ? '#e5e7eb' : '#374151'}`,
                    borderRadius: '12px',
                    backdropFilter: 'blur(10px)'
                  }}
                />
                <Legend />
                <Bar dataKey="value" fill="url(#barGradient)" name="销售额（万元）" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </motion.div>

        <div className="grid grid-cols-2 gap-6">
          {/* 用户增长率 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className={`p-6 transition-all relative overflow-hidden group ${cardClass}`}>
              <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
                theme === 'light'
                  ? 'bg-gradient-to-br from-cyan-500/5 to-blue-500/5'
                  : 'bg-gradient-to-br from-cyan-500/8 to-blue-500/8'
              }`} />
              <h3 className={`mb-4 relative z-10 ${
                theme === 'light' ? 'text-gray-700' : 'text-gray-100'
              }`}>
                增长率趋势
                {isLoading && <RefreshCw className="w-4 h-4 inline ml-2 animate-spin" />}
              </h3>
              <ResponsiveContainer width="100%" height={220} className="relative z-10">
                <LineChart data={growthData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} opacity={0.3} />
                  <XAxis dataKey="month" stroke={textColor} />
                  <YAxis stroke={textColor} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme === 'light' ? 'rgba(255,255,255,0.95)' : 'rgba(0,0,0,0.8)',
                      border: `1px solid ${theme === 'light' ? '#e5e7eb' : '#374151'}`,
                      borderRadius: '12px',
                      backdropFilter: 'blur(10px)'
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="rate"
                    stroke={theme === 'light' ? '#06b6d4' : '#38bdf8'}
                    strokeWidth={3}
                    name="增长率（%）"
                    dot={{ fill: theme === 'light' ? '#06b6d4' : '#38bdf8', r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>

          {/* 产品分布 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className={`p-6 transition-all relative overflow-hidden group ${cardClass}`}>
              <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
                theme === 'light'
                  ? 'bg-gradient-to-br from-purple-500/5 to-pink-500/5'
                  : 'bg-gradient-to-br from-blue-500/8 to-teal-500/8'
              }`} />
              <h3 className={`mb-4 relative z-10 ${
                theme === 'light' ? 'text-gray-700' : 'text-gray-100'
              }`}>
                分类分布
                {isLoading && <RefreshCw className="w-4 h-4 inline ml-2 animate-spin" />}
              </h3>
              <ResponsiveContainer width="100%" height={220} className="relative z-10">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme === 'light' ? 'rgba(255,255,255,0.95)' : 'rgba(0,0,0,0.8)',
                      border: `1px solid ${theme === 'light' ? '#e5e7eb' : '#374151'}`,
                      borderRadius: '12px',
                      backdropFilter: 'blur(10px)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>
        </div>

        {/* 历史记录 */}
        {resultsList.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Card className={`p-6 ${cardClass}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className={`${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-100'
                }`}>
                  <BarChart3 className="w-4 h-4 inline mr-2" />
                  处理历史
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={loadResultsList}
                  className={`gap-2 transition-all ${
                    theme === 'light'
                      ? 'hover:bg-indigo-50 hover:text-indigo-600'
                      : 'hover:bg-slate-700 hover:text-cyan-400 text-gray-300'
                  }`}
                >
                  <RefreshCw className="w-4 h-4" />
                  刷新
                </Button>
              </div>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {resultsList.slice(0, 5).map((result, index) => (
                  <div
                    key={index}
                    className={`flex items-center justify-between p-2 rounded text-sm ${
                      theme === 'light'
                        ? 'bg-gray-50 hover:bg-gray-100'
                        : 'bg-slate-700/50 hover:bg-slate-700/70'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-3 h-3" />
                      <span className={theme === 'light' ? 'text-gray-700' : 'text-gray-300'}>
                        {result.original_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs opacity-60">
                        {result.page_count}页
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownloadResults(result.filename)}
                        className="p-1 h-6"
                      >
                        <Download className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-4 pt-4">
          <Button
            onClick={onPreviewReport}
            className={`flex-1 gap-2 text-white border-0 shadow-lg transition-all hover:scale-[1.02] ${
              theme === 'light'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60'
                : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/60'
            }`}
          >
            <FileText className="w-4 h-4" />
            预览报告
          </Button>
          <Button
            variant="outline"
            className={`flex-1 gap-2 backdrop-blur-sm transition-all hover:scale-[1.02] ${
              theme === 'light'
                ? 'border-indigo-200 bg-white/50 hover:bg-indigo-50 hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-200/50'
                : 'border-slate-600 bg-slate-800/50 hover:bg-slate-700/70 hover:border-blue-400/50 hover:shadow-lg hover:shadow-blue-500/30 text-gray-100'
            }`}
          >
            <Download className="w-4 h-4" />
            导出PDF
          </Button>
        </div>
      </div>
    </div>
  );
}