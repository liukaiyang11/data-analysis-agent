import { Card } from './ui/card';
import { Button } from './ui/button';
import { FileText, Download, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';

interface DataVisualizationProps {
  theme: 'light' | 'dark';
  onPreviewReport: () => void;
  processedResults?: any;
  taskId?: string;
}

// API配置 - 动态获取主机地址
const getAPIBaseURL = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8708`;
  }
  return 'http://localhost:8708';
};
const API_BASE_URL = getAPIBaseURL();

export function DataVisualization({ theme, onPreviewReport, processedResults, taskId }: DataVisualizationProps) {
  const cardClass = theme === 'light'
    ? 'bg-white/60 border-white/40 shadow-xl shadow-indigo-500/10 hover:shadow-2xl hover:shadow-indigo-500/20 backdrop-blur-xl'
    : 'bg-slate-800/80 border-slate-700/50 shadow-xl shadow-blue-500/10 hover:shadow-2xl hover:shadow-blue-500/20 backdrop-blur-xl';

  // 如果有处理结果，显示可视化报告
  if (processedResults && processedResults.visualization_result) {
    const { html, title, summary, report_url, answer_id } = processedResults.visualization_result;

    const handleExportPDF = async () => {
      if (!taskId || !answer_id) {
        alert('无法导出 PDF：缺少必要的参数');
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/export_pdf`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            task_id: taskId,
            answer_id: answer_id,
            title: title || '数据分析报告',
            regenerate: false  // 可以改为 true 以生成更精美的报告
          })
        });

        if (!response.ok) {
          throw new Error(`导出失败: ${response.statusText}`);
        }

        const result = await response.json();

        // 触发下载
        const downloadUrl = `${API_BASE_URL}${result.pdf_url}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        alert('PDF 报告已开始下载！');
      } catch (error) {
        console.error('导出 PDF 失败:', error);
        alert(`导出 PDF 失败: ${error instanceof Error ? error.message : '未知错误'}`);
      }
    };

    const handleViewFullReport = () => {
      if (report_url) {
        window.open(`${API_BASE_URL}${report_url}`, '_blank');
      }
    };

    return (
      <div className="w-[70%] flex flex-col">
        {/* 顶部操作栏 */}
        <div className={`p-4 border-b backdrop-blur-xl ${
          theme === 'light'
            ? 'bg-white/60 border-white/40'
            : 'bg-slate-800/80 border-slate-700/50'
        }`}>
          <div className="flex items-center justify-between">
            <h2 className={`text-lg font-semibold bg-gradient-to-r bg-clip-text text-transparent ${
              theme === 'light'
                ? 'from-indigo-600 to-purple-600'
                : 'from-blue-400 to-cyan-400'
            }`}>
              {title || '数据分析可视化报告'}
            </h2>
            <div className="flex gap-2">
              <Button
                onClick={handleViewFullReport}
                size="sm"
                variant="outline"
                className={`gap-2 ${
                  theme === 'light'
                    ? 'border-indigo-200 hover:bg-indigo-50'
                    : 'border-slate-600 hover:bg-slate-700 text-gray-300'
                }`}
              >
                <FileText className="w-4 h-4" />
                全屏查看
              </Button>
              <Button
                onClick={handleExportPDF}
                size="sm"
                variant="outline"
                className={`gap-2 ${
                  theme === 'light'
                    ? 'border-indigo-200 hover:bg-indigo-50'
                    : 'border-slate-600 hover:bg-slate-700 text-gray-300'
                }`}
              >
                <Download className="w-4 h-4" />
                导出PDF
              </Button>
            </div>
          </div>
        </div>

        {/* HTML报告渲染区域 */}
        <div className="flex-1 overflow-hidden">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full h-full"
          >
            <iframe
              srcDoc={html}
              className="w-full h-full border-0"
              title="可视化报告"
              sandbox="allow-scripts allow-same-origin"
              style={{
                backgroundColor: 'white'
              }}
            />
          </motion.div>
        </div>
      </div>
    );
  }

  // 空状态显示 - 等待用户上传文档
  return (
    <div className="w-[70%] p-6 overflow-y-auto flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent ${
          theme === 'light'
            ? 'from-indigo-600 to-purple-600'
            : 'from-blue-400 to-cyan-400'
        }`}>
          数据分析可视化结果
        </h2>
      </div>

      {/* 空状态提示 - 优化版 */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-2xl"
        >
          <Card className={`p-10 transition-all relative overflow-hidden border-2 ${
            theme === 'light'
              ? 'bg-white/70 border-indigo-200/50 shadow-2xl shadow-indigo-500/10'
              : 'bg-slate-800/60 border-slate-600/50 shadow-2xl shadow-blue-500/20'
          }`}>
            {/* 动态背景光晕 */}
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                opacity: [0.3, 0.5, 0.3]
              }}
              transition={{ repeat: Infinity, duration: 4 }}
              className={`absolute inset-0 ${
                theme === 'light'
                  ? 'bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-pink-500/10'
                  : 'bg-gradient-to-br from-blue-500/10 via-cyan-500/10 to-teal-500/10'
              }`}
            />

            <div className="relative z-10 space-y-8">
              {/* 图标区域 */}
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                className="flex justify-center"
              >
                <div className={`w-32 h-32 rounded-2xl flex items-center justify-center backdrop-blur-sm ${
                  theme === 'light'
                    ? 'bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-300/30'
                    : 'bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-400/30'
                }`}>
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    <BarChart3 className={`w-16 h-16 ${
                      theme === 'light' ? 'text-indigo-600' : 'text-blue-400'
                    }`} />
                  </motion.div>
                </div>
              </motion.div>

              {/* 文字区域 */}
              <div className="text-center space-y-3">
                <motion.h3
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className={`text-2xl font-bold bg-gradient-to-r bg-clip-text text-transparent ${
                    theme === 'light'
                      ? 'from-indigo-600 via-purple-600 to-pink-600'
                      : 'from-blue-400 via-cyan-400 to-teal-400'
                  }`}>
                  等待文档上传
                </motion.h3>
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className={`text-base ${
                    theme === 'light' ? 'text-gray-600' : 'text-gray-300'
                  }`}>
                  请在右侧上传 PDF、图片或文本文件
                </motion.p>
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className={`text-sm ${
                    theme === 'light' ? 'text-gray-500' : 'text-gray-400'
                  }`}>
                  系统将自动进行OCR识别、数据分析和可视化报告生成
                </motion.p>
              </div>

              {/* 流程步骤 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className={`pt-8 border-t ${
                  theme === 'light' ? 'border-gray-200' : 'border-slate-600/50'
                }`}>
                <div className="grid grid-cols-3 gap-6">
                  {[
                    { num: 1, label: 'OCR识别', color: 'blue', delay: 0.6 },
                    { num: 2, label: '数据分析', color: 'cyan', delay: 0.7 },
                    { num: 3, label: '生成报告', color: 'teal', delay: 0.8 }
                  ].map((step) => (
                    <motion.div
                      key={step.num}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: step.delay }}
                      className="text-center"
                    >
                      <motion.div
                        whileHover={{ scale: 1.1 }}
                        className={`w-16 h-16 mx-auto rounded-xl flex items-center justify-center mb-3 backdrop-blur-sm ${
                          theme === 'light'
                            ? step.color === 'blue' ? 'bg-blue-100 border border-blue-200' :
                              step.color === 'cyan' ? 'bg-cyan-100 border border-cyan-200' :
                              'bg-teal-100 border border-teal-200'
                            : step.color === 'blue' ? 'bg-blue-500/20 border border-blue-400/30' :
                              step.color === 'cyan' ? 'bg-cyan-500/20 border border-cyan-400/30' :
                              'bg-teal-500/20 border border-teal-400/30'
                        }`}>
                        <span className={`text-3xl font-bold ${
                          theme === 'light' ?
                            (step.color === 'blue' ? 'text-blue-600' :
                             step.color === 'cyan' ? 'text-cyan-600' : 'text-teal-600') :
                            (step.color === 'blue' ? 'text-blue-400' :
                             step.color === 'cyan' ? 'text-cyan-400' : 'text-teal-400')
                        }`}>
                          {step.num}
                        </span>
                      </motion.div>
                      <div className={`text-sm font-medium ${
                        theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                      }`}>
                        {step.label}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* 装饰性元素 */}
              <div className="flex justify-center items-center space-x-2 pt-4">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    animate={{
                      scale: [1, 1.2, 1],
                      opacity: [0.3, 1, 0.3]
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 2,
                      delay: i * 0.3
                    }}
                    className={`w-2 h-2 rounded-full ${
                      theme === 'light' ? 'bg-indigo-400' : 'bg-blue-400'
                    }`}
                  />
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
