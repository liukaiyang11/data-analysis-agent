import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Download, X } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ReportPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  theme: 'light' | 'dark';
}

const previewData = [
  { month: '1月', value: 4200 },
  { month: '2月', value: 5800 },
  { month: '3月', value: 7200 },
  { month: '4月', value: 6800 },
  { month: '5月', value: 8900 },
  { month: '6月', value: 9500 },
];

export function ReportPreviewModal({ isOpen, onClose, theme }: ReportPreviewModalProps) {
  const cardClass = theme === 'light' 
    ? 'bg-white/60 border-white/40 backdrop-blur-xl shadow-lg shadow-indigo-500/10' 
    : 'bg-slate-800/80 border-slate-700/50 backdrop-blur-xl shadow-lg shadow-blue-500/10';

  const textColor = theme === 'light' ? '#1f2937' : '#f1f5f9';
  const gridColor = theme === 'light' ? '#e5e7eb' : '#475569';

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className={`max-w-4xl backdrop-blur-2xl border ${
          theme === 'light' 
            ? 'bg-white/90 border-white/60 shadow-2xl shadow-indigo-500/20' 
            : 'bg-slate-900/95 border-slate-700/60 shadow-2xl shadow-blue-500/30'
        }`}
      >
        <DialogHeader>
          <DialogTitle>数据分析报告预览</DialogTitle>
          <DialogDescription>
            2024年上半年销售数据综合分析报告
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <Card className={`p-6 ${cardClass}`}>
            <h3 className="mb-4">核心发现</h3>
            <ul className="space-y-2 text-sm opacity-80">
              <li>• 销售额同比增长 <span className={theme === 'light' ? 'text-indigo-600' : 'text-blue-400'}>126.8%</span>，整体趋势向好</li>
              <li>• 用户增长率持续上升，6月达到 <span className={theme === 'light' ? 'text-purple-600' : 'text-cyan-400'}>35%</span> 的峰值</li>
              <li>• 产品A占据最大市场份额（35%），建议继续加大投入</li>
              <li>• 5-6月是销售旺季，建议提前备货和营销准备</li>
            </ul>
          </Card>

          <Card className={`p-6 ${cardClass}`}>
            <h3 className="mb-4">销售额趋势图</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={previewData}>
                <defs>
                  <linearGradient id="modalBarGradient" x1="0" y1="0" x2="0" y2="1">
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
                <Bar dataKey="value" fill="url(#modalBarGradient)" name="销售额（万元）" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className={`p-6 ${cardClass}`}>
            <h3 className="mb-4">建议与展望</h3>
            <p className="text-sm opacity-80 leading-relaxed">
              基于当前数据分析，建议在第三季度继续保持产品A的市场推广力度，
              同时关注产品D的增长潜力。预计下半年销售额将继续保持稳定增长态势，
              全年有望突破10亿元大关。建议加强数据驱动决策，定期review关键指标。
            </p>
          </Card>

          <div className="flex gap-3 pt-2">
            <Button
              onClick={onClose}
              variant="outline"
              className={`flex-1 backdrop-blur-sm transition-all ${
                theme === 'light'
                  ? 'border-indigo-200 bg-white/50 hover:bg-indigo-50 hover:border-indigo-300'
                  : 'border-slate-600 bg-slate-800/50 hover:bg-slate-700/70 hover:border-blue-400/50 text-gray-100'
              }`}
            >
              <X className="w-4 h-4 mr-2" />
              关闭
            </Button>
            <Button
              className={`flex-1 gap-2 text-white border-0 shadow-lg transition-all hover:scale-[1.02] ${
                theme === 'light'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60'
                  : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/60'
              }`}
            >
              <Download className="w-4 h-4" />
              导出完整报告
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
