export interface TextBox {
  text: string;
  confidence: number;
  bbox: [[number, number], [number, number], [number, number], [number, number]];
}

export interface OcrResponse {
  text_boxes: TextBox[];
  full_text: string;
  status: string;
  total_boxes: number;
  average_confidence: number;
}
