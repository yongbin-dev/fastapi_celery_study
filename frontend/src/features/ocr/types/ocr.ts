export interface TextBox {
  text: string;
  confidence: number;
  bbox: [
    [number, number],
    [number, number],
    [number, number],
    [number, number],
  ];
}

export interface OcrResponse {
  id: number;
  text_boxes: TextBox[];
  full_text: string;
  status: string;
  public_path: string;
  average_confidence: number;
  error: string | null;
}
