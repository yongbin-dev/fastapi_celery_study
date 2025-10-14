export interface User {
  id: string;
  email: string;
  name: string;
}

export interface ApiResponse<T> {
  success: boolean;
  status: string;
  message: string;
  timestamp: string;
  data: T | null;
  error_code?: string;
  details?: any;
  meta?: any;
}

export interface PaginatedResponse<T> {
  data: T[];
  page: number;
  limit: number;
  total: number;
}
