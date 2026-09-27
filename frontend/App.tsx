import { useState } from 'react';
import { motion } from 'framer-motion';
import { Header } from './components/Header';
import { DataVisualization } from './components/DataVisualization';
import { ChatAssistant } from './components/ChatAssistant';
import { ReportPreviewModal } from './components/ReportPreviewModal';

export default function App() {
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [processedResults, setProcessedResults] = useState<any>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // 使用高端深色主题
  const theme = 'dark';

  return (
    <div
      className="min-h-screen flex flex-col transition-all duration-500 relative overflow-hidden text-gray-100"
      style={{ fontFamily: "'Inter', 'HarmonyOS Sans', 'Noto Sans SC', sans-serif" }}
    >
      {/* 高端深色背景渐变 */}
      <div className="fixed inset-0 -z-10">
        {/* 主背景 */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" />

        {/* 次要渐变层 */}
        <div className="absolute inset-0 bg-gradient-to-tr from-blue-950/20 via-transparent to-indigo-950/20" />
        <div className="absolute inset-0 bg-gradient-to-bl from-cyan-950/10 via-transparent to-teal-950/10" />

        {/* 网格背景 */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgb(59, 130, 246) 1px, transparent 0)',
            backgroundSize: '50px 50px'
          }}
        />

        {/* 动态光晕 */}
        <div className="fixed top-0 left-1/4 w-[600px] h-[600px] rounded-full blur-3xl -z-10 bg-blue-600/5 animate-pulse" />
        <div className="fixed bottom-0 right-1/4 w-[500px] h-[500px] rounded-full blur-3xl -z-10 bg-cyan-600/5 animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full blur-3xl -z-10 bg-indigo-600/3 animate-pulse" style={{ animationDelay: '4s' }} />
      </div>

      <Header theme={theme} />

      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="flex-1 flex overflow-hidden"
      >
        <DataVisualization
          theme={theme}
          processedResults={processedResults}
          taskId={currentTaskId || undefined}
          onPreviewReport={() => {
            if (currentTaskId) {
              const apiUrl = `http://${window.location.hostname}:8708/report/${currentTaskId}`;
              window.open(apiUrl, '_blank');
            } else {
              setIsReportModalOpen(true);
            }
          }}
        />
        {/* 左右栏分隔线 */}
        <motion.div
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.8, delay: 0.8, ease: "easeOut" }}
          className={`w-px transition-colors origin-top ${
            theme === 'light'
              ? 'bg-gradient-to-b from-indigo-200 via-purple-200 to-pink-200'
              : 'bg-gradient-to-b from-slate-700 via-slate-600 to-slate-700'
          }`}
        />
        <ChatAssistant
          theme={theme}
          onProcessingComplete={(results: any, taskId: string) => {
            setProcessedResults(results);
            setCurrentTaskId(taskId);
          }}
        />
      </motion.main>

      <motion.footer
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 1 }}
        className="py-4 text-center border-t backdrop-blur-xl border-slate-700/30 bg-slate-900/40"
      >
        <div className="flex flex-col items-center space-y-1">
          <motion.p
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ repeat: Infinity, duration: 3 }}
            className="text-sm text-slate-400"
          >
            AI全自动数据分析系统
          </motion.p>
          <div className="flex items-center justify-center space-x-2">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="w-1 h-1 bg-blue-400 rounded-full"
            />
            <p className="text-xs text-slate-500 opacity-70">
              智能分析，洞察未来
            </p>
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ repeat: Infinity, duration: 2, delay: 1 }}
              className="w-1 h-1 bg-cyan-400 rounded-full"
            />
          </div>
        </div>
      </motion.footer>

      <ReportPreviewModal 
        isOpen={isReportModalOpen} 
        onClose={() => setIsReportModalOpen(false)}
        theme={theme}
      />
    </div>
  );
}
