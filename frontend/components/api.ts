/**
 * API 服务模块
 * 处理与后端的通信
 */

const API_BASE_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8708'
  : `http://${window.location.hostname}:8708`;

export interface OCRResult {
  markdown: string;
  page_count: number;
  file_name?: string;
  file_info?: {
    original_name: string;
    size_bytes: number;
    size_mb: number;
    temp_path?: string;
  };
  processing_time?: number;
  status: string;
  mock_mode?: boolean;
  saved_files?: {
    json_file: string;
    md_file: string;
  };
}

export interface OCRResponse {
  status: 'success' | 'processing' | 'error';
  markdown?: string;
  page_count?: number;
  file_name?: string;
  processing_time?: number;
  message?: string;
  temp_file?: string;
  file_info?: any;
  saved_files?: any;
}

export interface ResultsListResponse {
  total: number;
  results: Array<{
    filename: string;
    original_name: string;
    page_count: number;
    status: string;
    mock_mode: boolean;
    size: number;
    created_time: string;
  }>;
  results_dir: string;
}

/**
 * 上传文件进行OCR处理
 */
export async function uploadFileForOCR(
  file: File,
  options: {
    enableDescription?: boolean;
    useRealService?: boolean;
  } = {}
): Promise<OCRResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('enable_description', options.enableDescription?.toString() || 'false');
  formData.append('use_real_service', options.useRealService?.toString() || 'false');

  try {
    const response = await fetch(`${API_BASE_URL}/ocr`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('OCR上传失败:', error);
    throw error;
  }
}

/**
 * 直接调用真实OCR服务
 */
export async function callRealOCR(file: File, enableDescription: boolean = false): Promise<OCRResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('enable_description', enableDescription.toString());

  try {
    const response = await fetch(`${API_BASE_URL}/ocr/real`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('真实OCR调用失败:', error);
    throw error;
  }
}

/**
 * 获取处理结果列表
 */
export async function getResultsList(): Promise<ResultsListResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/results`);

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('获取结果列表失败:', error);
    throw error;
  }
}

/**
 * 下载处理结果文件
 */
export async function downloadResult(filename: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/download/${filename}`);

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('下载失败:', error);
    throw error;
  }
}

/**
 * 检查服务健康状态
 */
export async function checkHealth(): Promise<{
  status: string;
  ocr_service: string;
  results_dir: string;
  timestamp: string;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('健康检查失败:', error);
    throw error;
  }
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