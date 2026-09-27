import { motion } from 'framer-motion';

interface HeaderProps {
  theme: 'light' | 'dark';
}

export function Header({ theme }: HeaderProps) {
  return (
    <header className={`py-4 px-6 border-b backdrop-blur-xl transition-all ${
      theme === 'light'
        ? 'bg-white/40 border-white/20 shadow-lg shadow-purple-500/5'
        : 'bg-slate-900/60 border-slate-700/50 shadow-lg shadow-blue-500/10'
    }`}>
      <div className="flex items-center justify-between">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className={`tracking-tight bg-gradient-to-r bg-clip-text text-transparent text-3xl font-bold ${
              theme === 'light'
                ? 'from-slate-700 via-blue-600 to-indigo-700'
                : 'from-blue-300 via-cyan-300 to-teal-300'
            }`}
          >
            AI全自动数据分析系统
          </motion.h1>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="flex space-x-4 mt-2"
          >
            <span className={`text-sm ${
              theme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`}>
              智能文档识别
            </span>
            <motion.span
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="text-blue-400"
            >
              •
            </motion.span>
            <span className={`text-sm ${
              theme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`}>
              深度数据分析
            </span>
            <motion.span
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ repeat: Infinity, duration: 2, delay: 0.7 }}
              className="text-cyan-400"
            >
              •
            </motion.span>
            <span className={`text-sm ${
              theme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`}>
              可视化报告生成
            </span>
          </motion.div>
        </div>

        <div className="flex items-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
            className="w-2 h-2 bg-blue-400 rounded-full"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="ml-2 w-2 h-2 bg-cyan-400 rounded-full"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1, duration: 0.5 }}
            className="ml-2 w-2 h-2 bg-indigo-400 rounded-full"
          />
        </div>
      </div>
    </header>
  );
}
