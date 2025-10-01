import type { TextBox } from './ocr';

/**
 * OCR 실행 상태
 */
export type OcrExecutionStatus = 'success' | 'failed';

/**
 * OCR 텍스트 박스 (백엔드 모델 매핑)
 */
export interface OcrTextBox {
  id: number;
  ocr_execution_id: number;
  text: string;
  confidence: number;
  bbox: [
    [number, number],
    [number, number],
    [number, number],
    [number, number],
  ];
}

/**
 * OCR 실행 정보 (백엔드 모델 매핑)
 */
export interface OcrExecution {
  id: number;
  chain_id: string | null;
  image_path: string;
  status: OcrExecutionStatus;
  error: string | null;
  created_at?: string;
  updated_at?: string;
  text_boxes?: OcrTextBox[];
}

/**
 * 히스토리 카드 표시용 확장 정보
 */
export interface OcrHistoryItem extends OcrExecution {
  thumbnail?: string;
  fileName?: string;
  fileSize?: number;
  displayTime?: string;
  totalBoxes?: number;
  averageConfidence?: number;
}

/**
 * 히스토리 리스트 필터 옵션
 */
export type HistoryFilterOption = 'all' | 'success' | 'failed';

/**
 * 히스토리 리스트 정렬 옵션
 */
export type HistorySortOption = 'newest' | 'oldest' | 'name-asc' | 'name-desc';
