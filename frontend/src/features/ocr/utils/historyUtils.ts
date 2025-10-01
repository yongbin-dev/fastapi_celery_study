import type { OcrExecution, OcrHistoryItem } from '../types/history';

/**
 * OcrExecution을 OcrHistoryItem으로 변환
 */
export function transformToHistoryItem(
  execution: OcrExecution,
  imageBaseUrl: string = ''
): OcrHistoryItem {
  const fileName = execution.image_path.split('/').pop() || 'unknown';

  return {
    ...execution,
    fileName,
    thumbnail: imageBaseUrl ? `${imageBaseUrl}/${execution.image_path}` : undefined,
    displayTime: formatRelativeTime(execution.created_at),
    totalBoxes: execution.text_boxes?.length || 0,
    averageConfidence: calculateAverageConfidence(execution.text_boxes),
  };
}

/**
 * 상대 시간 포맷 (예: "5분 전")
 */
export function formatRelativeTime(dateString?: string): string {
  if (!dateString) return '';

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}시간 전`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}일 전`;

  const diffWeeks = Math.floor(diffDays / 7);
  if (diffWeeks < 4) return `${diffWeeks}주 전`;

  const diffMonths = Math.floor(diffDays / 30);
  return `${diffMonths}개월 전`;
}

/**
 * 평균 신뢰도 계산
 */
export function calculateAverageConfidence(
  textBoxes?: Array<{ confidence: number }>
): number {
  if (!textBoxes || textBoxes.length === 0) return 0;

  const sum = textBoxes.reduce((acc, box) => acc + box.confidence, 0);
  return sum / textBoxes.length;
}

/**
 * 파일 크기 포맷 (예: "2.4 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

/**
 * 날짜를 로컬 포맷으로 변환 (예: "2024-10-01 10:30")
 */
export function formatLocalDateTime(dateString?: string): string {
  if (!dateString) return '';

  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}`;
}
