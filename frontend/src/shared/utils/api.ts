import axios from 'axios';
import type { ApiResponse } from '@/shared/types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

export const api = axios.create({
  baseURL: API_BASE_URL + '/api/v1/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    // 성공 응답: data 필드만 추출
    if (
      response.data &&
      response.data.status === 'success' &&
      response.data.data !== undefined
    ) {
      return { ...response, data: response.data.data };
    }
    return response;
  },
  (error) => {
    // 401 에러 처리
    console.log(error);
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }

    // 백엔드 에러 응답 추출
    if (error.response?.data) {
      const errorData = error.response.data;

      // 사용자 친화적 에러 객체 생성
      const apiError = {
        message: errorData.message || '알 수 없는 오류가 발생했습니다',
        error_code: errorData.error_code,
        details: errorData.details,
        status: error.response.status,
        originalError: error,
      };

      return Promise.reject(apiError);
    }

    // 네트워크 에러 또는 응답 없음
    return Promise.reject({
      message: error.message || '서버와 통신할 수 없습니다',
      status: 0,
      originalError: error,
    });
  }
);

export const createApiCall = <T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string
) => {
  return async (data?: any): Promise<ApiResponse<T>> => {
    const response = await api[method](url, data);
    return response.data;
  };
};
