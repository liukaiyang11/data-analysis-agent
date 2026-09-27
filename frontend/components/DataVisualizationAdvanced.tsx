import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { FileText, Download, Maximize2, RefreshCw, BarChart3, Eye } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  processDocument,
  getTaskStatus,
  downloadFile,
  validateFileType,
  validateFileSize,
  formatFileSize,
  getTaskStatusDescription,
  type TaskStatus,
  type ProcessingResults,
  type TaskStatus as TaskStatusType
} from './advanced_api';

interface DataVisualizationAdvancedProps {
  theme: 'light' | 'dark';
  onPreviewReport?: (htmlReport: string, results: ProcessingResults) => void;
  onOCRResult?: (results: ProcessingResults) => void;
}

export function DataVisualizationAdvanced({
  theme,
  onPreviewReport,
  onOCRResult
}: DataVisualizationAdvancedProps) {
  const [processingResults, setProcessingResults] = useState<ProcessingResults | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [htmlReport, setHtmlReport] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileInputRef, setFileInputRef] = useState<HTMLInputElement | null>(null);
  const [userQuery, setUserQuery] = useState('分析此文档并生成可视化报告');

  const cardClass = theme === 'light'
    ? 'bg-white/60 border-white/40 shadow-xl shadow-indigo-500/10 hover:shadow-2xl hover:shadow-indigo-500/20 backdrop-blur-xl'
    : 'bg-slate-800/80 border-slate-700/50 shadow-xl shadow-blue-500/10 hover:shadow-2xl hover:shadow-blue-500/20 backdrop-blur-xl';

  const textColor = theme === 'light' ? '#1f2937' : '#f1f5f9';

  // 处理文件上传
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    if (!validateFileType(file)) {
      alert('文件格式不支持。请上传 JPG、PNG、PDF、TXT 或 MD 格式的文件。');
      return;
    }

    // 验证文件大小
    if (!validateFileSize(file)) {
      alert(`文件大小超过限制。请上传小于 100MB 的文件。`);
      return;
    }

    try {
      setIsProcessing(true);
      setCurrentTaskId(null);
      setTaskStatus(null);

      // 开始处理文档
      const response = await processDocument(file, {
        enableDescription: true,
        userQuery: userQuery,
        onProgress: (status) => {
          setTaskStatus(status);
        }
      });

      // 设置结果
      setProcessingResults(response.results);
      setHtmlReport(response.htmlReport);
      setCurrentTaskId(response.taskId);

      // 通知父组件
      if (onOCRResult) {
        onOCRResult(response.results);
      }

    } catch (error) {
      console.error('文档处理失败:', error);
      alert(`文档处理失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsProcessing(false);
    }

    // 清空文件输入
    if (fileInputRef) {
      fileInputRef.value = '';
    }
  };

  // 下载文件
  const handleDownload = async (fileType: 'json' | 'html') => {
    if (!currentTaskId) return;

    try {
      await downloadFile(currentTaskId, fileType);
    } catch (error) {
      console.error('下载失败:', error);
      alert('下载失败，请稍后重试');
    }
  };

  // 预览报告
  const handlePreviewReport = () => {
    if (htmlReport && processingResults) {
      onPreviewReport?.(htmlReport, processingResults);
    }
  };

  // 重新处理
  const handleReprocess = () => {
    if (fileInputRef) {
      fileInputRef.click();
    }
  };

  // 渲染任务状态
  const renderTaskStatus = () => {
    if (!taskStatus) return null;

    return (
      <Card className={`p-4 ${cardClass}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {taskStatus.status === 'processing' && (
              <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            )}
            <span className="text-sm font-medium">
              {getTaskStatusDescription(taskStatus.status)}
            </span>
          </div>
          <span className="text-xs opacity-60">
            {taskStatus.progress}%
          </span>
        </div>

        {/* 进度条 */}
        <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${taskStatus.progress}%` }}
          />
        </div>

        {/* 当前步骤 */}
        <p className="text-sm opacity-80">{taskStatus.message}</p>
      </Card>
    );
  };

  // 渲染处理结果
  const renderResults = () => {
    if (!processingResults) return null;

    return (
      <Card className={`p-6 ${cardClass}`}>
        <h3 className={`mb-4 ${theme === 'light' ? 'text-gray-700' : 'text-gray-100'}`}>
          <Eye className="w-4 h-4 inline mr-2" />
          处理结果
        </h3>

        <div className="space-y-4">
          {/* OCR结果 */}
          <div>
            <h4 className={`text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-600' : 'text-gray-300'}`}>
              OCR识别结果
            </h4>
            <div className={`p-3 rounded-lg text-xs ${theme === 'light' ? 'bg-blue-50 border border-blue-200' : 'bg-blue-900/20 border border-blue-700/30'}`}>
              <div className="grid grid-cols-2 gap-2">
                <div>文件名: {processingResults.ocr_result.file_name}</div>
                <div>页数: {processingResults.ocr_result.page_count}</div>
                <div>处理时间: {processingResults.ocr_result.processing_time.toFixed(2)}s</div>
                <div>状态: {processingResults.ocr_result.status}</div>
              </div>
            </div>
          </div>

          {/* 分析结果 */}
          <div>
            <h4 className={`text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-600' : 'text-gray-300'}`}>
              结构化分析
            </h4>
            <div className={`p-3 rounded-lg text-xs ${theme === 'light' ? 'bg-green-50 border border-green-200' : 'bg-green-900/20 border border-green-700/30'}`}>
              <div className="grid grid-cols-2 gap-2">
                <div>总块数: {processingResults.analysis_result.total_chunks}</div>
                <div>已分析: {processingResults.analysis_result.analyzed_chunks.length}</div>
              </div>
            </div>
          </div>

          {/* 可视化结果 */}
          <div>
            <h4 className={`text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-600' : 'text-gray-300'}`}>
              可视化报告
            </h4>
            <div className={`p-3 rounded-lg text-xs ${theme === 'light' ? 'bg-purple-50 border border-purple-200' : 'bg-purple-900/20 border border-purple-700/30'}`}>
              <div>
                <div>标题: {processingResults.visualization_result.title}</div>
                <div className="mt-2 text-xs opacity-70">
                  {processingResults.visualization_result.summary.substring(0, 200)}...
                </div>
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownload('json')}
              className={`text-xs ${
                theme === 'light'
                  ? 'border-green-200 text-green-700 hover:bg-green-50'
                  : 'border-green-700 text-green-400 hover:bg-green-900/20'
              }`}
            >
              <Download className="w-3 h-3 mr-1" />
              下载JSON
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownload('html')}
              className={`text-xs ${
                theme === 'light'
                  ? 'border-blue-200 text-blue-700 hover:bg-blue-50'
                  : 'border-blue-700 text-blue-400 hover:bg-blue-900/20'
              }`}
            >
              <Download className="w-3 h-3 mr-1" />
              下载HTML
            </Button>
          </div>
        </div>
      </Card>
    );
  };

  return (
    <div className="w-1/2 p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent ${
          theme === 'light'
            ? 'from-indigo-600 to-purple-600'
            : 'from-blue-400 to-cyan-400'
        }`}>
          智能数据分析
        </h2>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReprocess}
            className={`gap-2 transition-all ${
              theme === 'light'
                ? 'hover:bg-indigo-50 hover:text-indigo-600'
                : 'hover:bg-slate-700 hover:text-cyan-400 text-gray-300'
            }`}
          >
            <RefreshCw className="w-4 h-4" />
            重新处理
          </Button>
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

      <div className="space-y-6">
        {/* 文件上传区域 */}
        <Card className={`p-6 ${cardClass}`}>
          <h3 className={`mb-4 ${theme === 'light' ? 'text-gray-700' : 'text-gray-100'}`}>
            <FileText className="w-4 h-4 inline mr-2" />
            上传文档进行智能分析
          </h3>

          {/* 用户查询输入 */}
          <div className="mb-4">
            <label className={`block text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'}`}>
              分析要求
            </label>
            <textarea
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
              placeholder="例如：分析此文档并生成可视化报告、重点提取财务数据、生成趋势分析图表..."
              className={`w-full p-3 text-sm rounded-lg border backdrop-blur-xl resize-none h-20 ${
                theme === 'light'
                  ? 'bg-white/80 border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 text-gray-800 placeholder-gray-500'
                  : 'bg-slate-800/70 border-slate-600 focus:border-blue-400 focus:ring-blue-400 text-gray-100 placeholder-gray-400'
              }`}
            />
          </div>

          {/* 文件上传 */}
          <input
            ref={setFileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.pdf,.txt,.md"
            onChange={handleFileUpload}
            disabled={isProcessing}
            className="hidden"
            id="document-upload"
          />

          <label
            htmlFor="document-upload"
            className={`block w-full text-center py-8 px-4 rounded-lg cursor-pointer transition-all border-2 border-dashed ${
              isProcessing
                ? 'opacity-50 cursor-not-allowed'
                : theme === 'light'
                  ? 'hover:bg-indigo-50 hover:border-indigo-300 hover:shadow-lg'
                  : 'hover:bg-slate-700 hover:border-blue-400 hover:shadow-lg'
            } ${
              theme === 'light'
                ? 'bg-indigo-50/50 border-indigo-200'
                : 'bg-slate-700/50 border-slate-600 text-gray-200'
            }`}
          >
            {isProcessing ? (
              <div className="flex items-center justify-center gap-2">
                <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
                <span className="text-sm">处理中...</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <FileText className="w-12 h-12 text-gray-400" />
                <div className="text-center">
                  <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
                    点击或拖拽上传文档
                  </p>
                  <p className="text-sm text-gray-500">
                    支持 JPG、PNG、PDF、TXT、MD 格式
                  </p>
                  <p className="text-xs text-gray-400">
                    最大文件大小: 100MB
                  </p>
                </div>
              </div>
            )}
          </label>
        </Card>

        {/* 任务状态 */}
        {taskStatus && renderTaskStatus()}

        {/* 处理结果 */}
        {processingResults && renderResults()}

        {/* 默认提示 */}
        {!isProcessing && !processingResults && (
          <Card className={`p-8 ${cardClass}`}>
            <div className="text-center">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className={`text-lg font-medium mb-2 ${theme === 'light' ? 'text-gray-700' : 'text-gray-200'}`}>
                准备开始分析
              </h3>
              <p className={`text-sm ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
                上传文档以开始智能数据分析流程
              </p>
              <p className={`text-xs mt-2 ${theme === 'light' ? 'text-gray-400' : 'text-gray-500'}`}>
                完整流程: OCR识别 → 结构化分析 → 可视化报告
              </p>
            </div>
          </Card>
        )}

        {/* 预览和导出按钮 */}
        {htmlReport && (
          <div className="flex gap-4">
            <Button
              onClick={handlePreviewReport}
              className={`flex-1 gap-2 text-white border-0 shadow-lg transition-all hover:scale-[1.02] ${
                theme === 'light'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60'
                  : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/60'
              }`}
            >
              <Eye className="w-4 h-4" />
              预览报告
            </Button>
            <Button
              variant="outline"
              className={`flex-1 gap-2 backdrop-blur-sm transition-all hover:scale-[1.02] ${
                theme === 'light'
                  ? 'border-purple-200 bg-white/50 hover:bg-purple-50 hover:border-purple-300 hover:shadow-lg hover:shadow-purple-200/50'
                  : 'border-slate-600 bg-slate-800/50 hover:bg-slate-700/70 hover:border-blue-400/50 hover:shadow-lg hover:shadow-blue-500/30 text-gray-100'
              }`}
            >
              <Download className="w-4 h-4" />
              导出PDF
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}