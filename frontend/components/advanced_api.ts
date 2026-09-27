/**
 * 高级API服务模块 - 对接完整流程
 * OCR → 结构化分析 → 可视化报告
 */

const API_BASE_URL = 'http://localhost:8708';

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'ocr_processing' | 'analyzing' | 'visualizing' | 'completed' | 'error';
  current_step: string;
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
  has_results: boolean;
}

export interface UploadResponse {
  task_id: string;
  status: string;
  message: string;
  file_info: {
    filename: string;
    size_bytes: number;
    size_mb: number;
  };
}

export interface ProcessingResults {
  ocr_result: {
    markdown: string;
    page_count: number;
    file_name: string;
    file_info: any;
    processing_time: number;
    status: string;
  };
  analysis_result: {
    source: any;
    total_chunks: number;
    analyzed_chunks: any[];
    metadata: any;
  };
  visualization_result: {
    html: string;
    title: string;
    summary: string;
  };
  files: {
    json_file: string;
    html_file: string;
  };
}

/**
 * 上传文档开始完整处理流程
 */
export async function uploadDocument(
  file: File,
  options: {
    enableDescription?: boolean;
    userQuery?: string;
  } = {}
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('enable_description', options.enableDescription?.toString() || 'false');
  formData.append('user_query', options.userQuery || '分析此文档并生成可视化报告');

  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`上传失败: ${response.status} ${errorData.detail || response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('文档上传失败:', error);
    throw error;
  }
}

/**
 * 查询任务处理状态
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/status/${taskId}`);

    if (!response.ok) {
      throw new Error(`状态查询失败: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('状态查询失败:', error);
    throw error;
  }
}

/**
 * 获取处理结果
 */
export async function getProcessingResults(taskId: string): Promise<ProcessingResults> {
  try {
    const response = await fetch(`${API_BASE_URL}/results/${taskId}`);

    if (!response.ok) {
      throw new Error(`获取结果失败: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('获取处理结果失败:', error);
    throw error;
  }
}

/**
 * 获取HTML报告
 */
export async function getHtmlReport(taskId: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/report/${taskId}`);

    if (!response.ok) {
      throw new Error(`获取报告失败: ${response.status}`);
    }

    return await response.text();
  } catch (error) {
    console.error('获取HTML报告失败:', error);
    throw error;
  }
}

/**
 * 下载处理文件
 */
export async function downloadFile(taskId: string, fileType: 'json' | 'html'): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/download/${taskId}/${fileType}`);

    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileType}_${taskId}.${fileType}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('文件下载失败:', error);
    throw error;
  }
}

/**
 * 轮询任务状态直到完成
 */
export async function pollTaskUntilComplete(
  taskId: string,
  onProgress?: (status: TaskStatus) => void,
  pollInterval: number = 2000,
  maxAttempts: number = 150
): Promise<ProcessingResults> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getTaskStatus(taskId);

    // 调用进度回调
    if (onProgress) {
      onProgress(status);
    }

    // 检查是否完成或出错
    if (status.status === 'completed') {
      return await getProcessingResults(taskId);
    } else if (status.status === 'error') {
      throw new Error(status.message);
    }

    // 等待下次轮询
    await new Promise(resolve => setTimeout(resolve, pollInterval));
    attempts++;
  }

  throw new Error('处理超时');
}

/**
 * 完整的文档处理函数
 */
export async function processDocument(
  file: File,
  options: {
    enableDescription?: boolean;
    userQuery?: string;
    onProgress?: (status: TaskStatus) => void;
  } = {}
): Promise<{
  taskId: string;
  results: ProcessingResults;
  htmlReport: string;
}> {
  // 1. 上传文档
  const uploadResponse = await uploadDocument(file, options);

  // 2. 轮询处理状态
  const results = await pollTaskUntilComplete(
    uploadResponse.task_id,
    options.onProgress
  );

  // 3. 获取HTML报告
  const htmlReport = await getHtmlReport(uploadResponse.task_id);

  return {
    taskId: uploadResponse.task_id,
    results,
    htmlReport
  };
}

/**
 * 验证文件类型
 */
export function validateFileType(file: File): boolean {
  const allowedTypes = [
    'image/jpeg', 'image/jpg', 'image/png',
    'application/pdf', 'text/plain', 'text/markdown'
  ];

  return allowedTypes.includes(file.type) ||
         file.name.match(/\.(jpg|jpeg|png|pdf|txt|md)$/i) !== null;
}

/**
 * 验证文件大小
 */
export function validateFileSize(file: File, maxSizeMB: number = 100): boolean {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 获取任务状态描述
 */
export function getTaskStatusDescription(status: string): string {
  const statusMap: Record<string, string> = {
    'pending': '准备开始',
    'ocr_processing': 'OCR识别中',
    'analyzing': '信息分析中',
    'visualizing': '生成可视化报告',
    'completed': '处理完成',
    'error': '处理失败'
  };

  return statusMap[status] || status;
}

/**
 * 检查服务健康状态
 */
export async function checkHealth(): Promise<{
  status: string;
  timestamp: string;
  active_tasks: number;
  directories: any;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error('健康检查失败:', error);
    throw error;
  }
}