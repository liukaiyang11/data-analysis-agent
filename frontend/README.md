# 赋范空间 AI全自动数据分析系统 - 前端项目

这是一个基于 React + TypeScript + Vite 构建的现代化数据分析可视化 Web 应用。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **样式**: Tailwind CSS + CSS Variables
- **UI 组件**: shadcn/ui (基于 Radix UI)
- **图表**: Recharts
- **动画**: Framer Motion
- **图标**: Lucide React

## 项目特性

- ✅ 完整的亮色/暗色主题切换
- ✅ 响应式设计
- ✅ 玻璃态 UI 设计
- ✅ 数据可视化仪表板（柱状图、折线图、饼图）
- ✅ AI 智能对话助手
- ✅ 报告预览与导出功能
- ✅ 50+ 可复用 UI 组件

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式运行

```bash
npm run dev
```

项目将在 [http://localhost:3000](http://localhost:3000) 启动。

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

## 项目结构

```
frontend/
├── components/           # 组件目录
│   ├── ui/              # shadcn/ui 基础组件库（50+ 组件）
│   ├── figma/           # Figma 相关组件
│   ├── Header.tsx       # 头部导航组件
│   ├── DataVisualization.tsx  # 数据可视化组件
│   ├── ChatAssistant.tsx      # 智能对话助手
│   └── ReportPreviewModal.tsx # 报告预览弹窗
├── styles/
│   └── globals.css      # 全局样式和主题变量
├── App.tsx              # 主应用组件
├── main.tsx             # React 渲染入口
├── index.html           # HTML 入口
├── vite.config.ts       # Vite 配置
├── tsconfig.json        # TypeScript 配置
├── tailwind.config.js   # Tailwind CSS 配置
└── package.json         # 项目依赖配置
```

## 主题系统

项目支持完整的亮色/暗色主题切换，通过 CSS Variables 实现：

- 亮色主题：渐变色（indigo/purple/pink）
- 暗色主题：深色底（slate）
- 支持 OKLCH 色彩空间

## UI 组件库

项目集成了完整的 shadcn/ui 组件库，包括：

**表单组件**: Button, Input, Select, Checkbox, Radio, Switch, Slider, Textarea
**布局组件**: Card, Sidebar, Sheet, Drawer, Separator, ScrollArea
**反馈组件**: Alert, Dialog, Toast, Tooltip, Popover
**导航组件**: Tabs, Breadcrumb, Pagination, NavigationMenu
**数据展示**: Table, Chart, Badge, Avatar, Progress, Skeleton

## 后续对接 FastAPI

项目已预留 API 接口对接位置，后续可以通过以下方式集成后端：

1. 在 `vite.config.ts` 中配置代理：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

2. 创建 API 请求函数（例如在 `api/` 目录下）

3. 替换组件中的 mock 数据为真实 API 调用

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题，请联系开发团队。
