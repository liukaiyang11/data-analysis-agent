import { useState, useRef } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Upload, Send, ChevronDown, ChevronUp, FileText, Download, Loader2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  uploadFileForOCR,
  callRealOCR,
  validateFileType,
  validateFileSize,
  formatFileSize,
  type OCRResponse,
  type OCRResult
} from './api';

interface ChatAssistantProps {
  theme: 'light' | 'dark';
  onOCRResult?: (result: OCRResult) => void;
}

interface ChatMessage {
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: Date;
  ocrResult?: OCRResult;
}

export function ChatAssistantUpdated({ theme, onOCRResult }: ChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      type: 'system',
      content: '👋 欢迎使用AI数据分析系统！您可以上传文档进行OCR分析，或直接向我提问。',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isParseOpen, setIsParseOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>('');
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [useRealService, setUseRealService] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const cardClass = theme === 'light'
    ? 'bg-white/60 border-white/40 backdrop-blur-xl shadow-xl shadow-indigo-500/10'
    : 'bg-slate-800/80 border-slate-700/50 backdrop-blur-xl shadow-xl shadow-blue-500/10';

  const addMessage = (message: Omit<ChatMessage, 'timestamp'>) => {
    setMessages(prev => [...prev, { ...message, timestamp: new Date() }]);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = inputValue.trim();
    addMessage({ type: 'user', content: userMessage });
    setInputValue('');

    // 显示处理中消息
    const processingId = Date.now();
    addMessage({
      type: 'assistant',
      content: '正在分析您的问题...'
    });

    // 模拟AI回复
    setTimeout(() => {
      setMessages(prev => prev.slice(0, -1)); // 移除处理中消息

      let response = '';
      if (userMessage.includes('分析') || userMessage.includes('趋势')) {
        response = '我已为您生成数据分析图表，请查看左侧可视化面板。如需更详细的分析，请上传相关文档。';
      } else if (userMessage.includes('报告') || userMessage.includes('生成')) {
        response = '报告功能已准备就绪。您可以上传文档自动生成分析报告，或点击"预览报告"查看示例报告。';
      } else if (userMessage.includes('帮助') || userMessage.includes('怎么用')) {
        response = '我可以帮您：\n1. 📄 上传PDF/图片文档进行OCR分析\n2. 📊 生成数据可视化图表\n3. 📝 创建分析报告\n4. 💬 回答数据分析相关问题\n\n请上传文档或告诉我您的需求！';
      } else {
        response = '收到您的问题。如果您有具体的文档需要分析，请上传文件，我可以为您提供更精准的分析结果。';
      }

      addMessage({ type: 'assistant', content: response });
    }, 1500);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    if (!validateFileType(file)) {
      addMessage({
        type: 'system',
        content: '❌ 文件格式不支持。请上传 JPG、PNG、PDF、TXT 或 MD 格式的文件。'
      });
      return;
    }

    // 验证文件大小
    if (!validateFileSize(file)) {
      addMessage({
        type: 'system',
        content: '❌ 文件大小超过限制。请上传小于 100MB 的文件。'
      });
      return;
    }

    setUploadedFile(file);
    setIsProcessing(true);
    setProcessingStatus('正在上传文件...');

    // 添加用户上传消息
    addMessage({
      type: 'user',
      content: `📄 上传文件: ${file.name} (${formatFileSize(file.size)})`
    });

    // 添加处理中消息
    addMessage({
      type: 'assistant',
      content: `🔄 正在使用${useRealService ? '真实OCR' : '模拟OCR'}处理文档，请稍候...`
    });

    try {
      setProcessingStatus('正在进行OCR处理...');

      // 调用OCR API
      const result: OCRResponse = await uploadFileForOCR(file, {
        enableDescription: true,
        useRealService: useRealService
      });

      // 移除处理中消息
      setMessages(prev => prev.slice(0, -1));

      if (result.status === 'success') {
        setProcessingStatus('处理完成！');
        setOcrResult(result as OCRResult);
        setIsParseOpen(true);

        // 添加成功消息
        let successMessage = `✅ 文档处理完成！\n\n📊 处理结果：\n`;
        successMessage += `• 文件名：${result.file_name || file.name}\n`;
        successMessage += `• 页数：${result.page_count} 页\n`;
        successMessage += `• 处理时间：${result.processing_time || 0} 秒\n`;
        successMessage += `• 处理模式：${result.mock_mode ? '模拟' : '真实'}OCR\n\n`;
        successMessage += `📝 已提取文档内容，您可以：\n`;
        successMessage += `• 查看左侧数据可视化结果\n`;
        successMessage += `• 点击"预览报告"查看详细内容\n`;
        successMessage += `• 继续提问获取更多分析`;

        addMessage({
          type: 'assistant',
          content: successMessage,
          ocrResult: result as OCRResult
        });

        // 通知父组件
        if (onOCRResult && result as OCRResult) {
          onOCRResult(result as OCRResult);
        }
      } else if (result.status === 'processing') {
        setProcessingStatus('文件已提交，正在后台处理...');
        addMessage({
          type: 'assistant',
          content: `⏳ 文件已提交到后台处理。${result.message || '请稍候...'}`
        });
      } else {
        throw new Error(result.message || '处理失败');
      }

    } catch (error) {
      console.error('OCR处理失败:', error);
      setProcessingStatus('');

      // 移除处理中消息
      setMessages(prev => prev.slice(0, -1));

      addMessage({
        type: 'system',
        content: `❌ 文档处理失败：${error instanceof Error ? error.message : '未知错误'}\n\n💡 建议：\n• 检查文件是否损坏\n• 尝试使用模拟模式\n• 联系技术支持`
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRetryOCR = async () => {
    if (!uploadedFile) return;

    setIsProcessing(true);
    setProcessingStatus('正在重新处理...');

    try {
      const result: OCRResponse = useRealService
        ? await callRealOCR(uploadedFile, true)
        : await uploadFileForOCR(uploadedFile, { enableDescription: true, useRealService: false });

      if (result.status === 'success') {
        setOcrResult(result as OCRResult);
        addMessage({
          type: 'assistant',
          content: `✅ 重新处理成功！${result.mock_mode ? '(模拟模式)' : '(真实OCR)'}`,
          ocrResult: result as OCRResult
        });
      }
    } catch (error) {
      addMessage({
        type: 'system',
        content: `❌ 重新处理失败：${error instanceof Error ? error.message : '未知错误'}`
      });
    } finally {
      setIsProcessing(false);
      setProcessingStatus('');
    }
  };

  const handleDownloadResult = async () => {
    if (!ocrResult?.saved_files) return;

    try {
      // 下载JSON结果
      const { downloadResult } = await import('./api');
      await downloadResult(ocrResult.saved_files.json_file.split('/').pop() || '');
      addMessage({
        type: 'system',
        content: '📥 结果文件已开始下载'
      });
    } catch (error) {
      addMessage({
        type: 'system',
        content: '❌ 下载失败，请稍后重试'
      });
    }
  };

  return (
    <div className="w-1/2 p-6">
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h2 className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent ${
            theme === 'light'
              ? 'from-indigo-600 to-purple-600'
              : 'from-blue-400 to-cyan-400'
          }`}>
            智能分析助理
          </h2>

          {/* OCR模式切换 */}
          <div className="flex items-center gap-2">
            <label className="text-xs opacity-70">OCR模式:</label>
            <button
              onClick={() => setUseRealService(!useRealService)}
              className={`px-2 py-1 text-xs rounded transition-all ${
                useRealService
                  ? theme === 'light'
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-green-900/30 text-green-400 border border-green-700/50'
                  : theme === 'light'
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-blue-900/30 text-blue-400 border border-blue-700/50'
              }`}
            >
              {useRealService ? '🔥 真实' : '⚡ 模拟'}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 mb-6">
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: message.type === 'user' ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-4 rounded-2xl backdrop-blur-xl shadow-lg ${
                  message.type === 'user'
                    ? theme === 'light'
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-indigo-500/30'
                      : 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-blue-500/40'
                    : message.type === 'system'
                      ? theme === 'light'
                        ? 'bg-yellow-50/90 border border-yellow-200 text-yellow-800'
                        : 'bg-yellow-900/30 border border-yellow-700/50 text-yellow-300'
                      : theme === 'light'
                        ? 'bg-white/80 text-gray-800 border border-white/40 shadow-gray-200/50'
                        : 'bg-slate-700/90 text-gray-100 border border-slate-600/50 shadow-slate-900/50'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>
                {message.timestamp && (
                  <p className="text-xs opacity-60 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* 文件上传区域 */}
        <Card className={`p-4 ${cardClass}`}>
          <Collapsible open={isParseOpen} onOpenChange={setIsParseOpen}>
            <CollapsibleTrigger asChild>
              <button className="w-full flex items-center justify-between hover:opacity-80 transition-opacity">
                <div className="flex items-center gap-2">
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : ocrResult ? (
                    <FileText className="w-4 h-4 text-green-500" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  <span className="text-sm">
                    {isProcessing
                      ? processingStatus
                      : ocrResult
                        ? `✅ 已处理: ${ocrResult.file_name || uploadedFile?.name}`
                        : `📂 上传文档 (${useRealService ? '真实OCR' : '模拟模式'})`
                    }
                  </span>
                </div>
                {(ocrResult || uploadedFile) ? (
                  isParseOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                ) : null}
              </button>
            </CollapsibleTrigger>

            {(ocrResult || uploadedFile) && (
              <CollapsibleContent className="mt-4">
                {ocrResult ? (
                  <div className={`p-4 rounded-lg text-sm backdrop-blur-sm ${
                    theme === 'light'
                      ? 'bg-green-50/50 border border-green-100'
                      : 'bg-green-900/20 border border-green-700/30'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-green-700 dark:text-green-300">
                        📊 处理结果：
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={handleRetryOCR}
                          disabled={isProcessing}
                          className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-50"
                        >
                          🔄 重试
                        </button>
                        <button
                          onClick={handleDownloadResult}
                          className="text-xs px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200"
                        >
                          📥 下载
                        </button>
                      </div>
                    </div>
                    <div className="space-y-1 text-green-600 dark:text-green-400">
                      <p>• 文件名：{ocrResult.file_name}</p>
                      <p>• 页数：{ocrResult.page_count} 页</p>
                      <p>• 处理时间：{ocrResult.processing_time} 秒</p>
                      <p>• 模式：{ocrResult.mock_mode ? '模拟OCR' : '真实OCR'}</p>
                    </div>

                    {/* 显示部分OCR内容 */}
                    {ocrResult.markdown && (
                      <div className="mt-3 p-2 bg-white/50 rounded border border-green-200">
                        <p className="text-xs text-gray-600 mb-1">文档内容预览：</p>
                        <p className="text-xs line-clamp-3">
                          {ocrResult.markdown.substring(0, 200)}...
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className={`p-4 rounded-lg text-sm backdrop-blur-sm ${
                    theme === 'light'
                      ? 'bg-indigo-50/50 border border-indigo-100'
                      : 'bg-slate-700/50 border border-slate-600/50 text-gray-100'
                  }`}>
                    <p className="opacity-80 mb-2">等待处理...</p>
                    <div className="space-y-1 opacity-70">
                      <p>• 文件名：{uploadedFile.name}</p>
                      <p>• 大小：{formatFileSize(uploadedFile.size)}</p>
                      <p>• 类型：{uploadedFile.type || '未知'}</p>
                    </div>
                  </div>
                )}
              </CollapsibleContent>
            )}
          </Collapsible>

          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.pdf,.txt,.md"
            onChange={handleFileUpload}
            disabled={isProcessing}
            className="hidden"
            id="file-upload"
          />

          {!uploadedFile && !isProcessing && (
            <label
              htmlFor="file-upload"
              className={`mt-3 block text-center py-3 px-4 rounded-lg cursor-pointer transition-all text-sm backdrop-blur-sm ${
                theme === 'light'
                  ? 'bg-indigo-50/50 hover:bg-indigo-100/80 border border-indigo-100 hover:border-indigo-200'
                  : 'bg-slate-700/50 hover:bg-slate-600/70 border border-slate-600/50 text-gray-200'
              }`}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              选择文件上传
            </label>
          )}
        </Card>

        {/* 聊天输入 */}
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="请输入你的问题..."
            disabled={isProcessing}
            className={`flex-1 backdrop-blur-xl ${
              theme === 'light'
                ? 'bg-white/80 border-indigo-200 focus:border-indigo-400 focus:ring-indigo-400'
                : 'bg-slate-800/70 border-slate-600 focus:border-blue-400 focus:ring-blue-400 text-gray-100 placeholder:text-gray-400'
            }`}
          />
          <Button
            onClick={handleSend}
            disabled={isProcessing || !inputValue.trim()}
            className={`gap-2 text-white border-0 shadow-lg transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
              theme === 'light'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60'
                : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/60'
            }`}
          >
            <Send className="w-4 h-4" />
            发送
          </Button>
        </div>
      </div>
    </div>
  );
}