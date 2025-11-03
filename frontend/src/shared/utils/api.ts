import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiResponse } from '@/shared/types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

const ML_API_BASE_URL =
  import.meta.env.VITE_ML_API_BASE_URL || 'http://localhost:3000/api';

export const api = axios.create({
  baseURL: API_BASE_URL + '/api/v1/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ml_api = axios.create({
  baseURL: ML_API_BASE_URL + '/api/model',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor
const requestInterceptor = (config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

// Response Interceptor
const responseInterceptor = (response: any) => {
  if (
    response.data &&
    response.data.status === 'success' &&
    response.data.data !== undefined
  ) {
    return { ...response, data: response.data.data };
  }
  return response;
};

// Error Interceptor
const errorInterceptor = (error: AxiosError) => {
  console.log(error);
  if (error.response?.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }

  if (error.response?.data) {
    const errorData: any = error.response.data;
    const apiError = {
      message: errorData.message || '알 수 없는 오류가 발생했습니다',
      error_code: errorData.error_code,
      details: errorData.details,
      status: error.response.status,
      originalError: error,
    };
    return Promise.reject(apiError);
  }

  return Promise.reject({
    message: error.message || '서버와 통신할 수 없습니다',
    status: 0,
    originalError: error,
  });
};

// Apply interceptors
api.interceptors.request.use(requestInterceptor);
api.interceptors.response.use(responseInterceptor, errorInterceptor);

ml_api.interceptors.request.use(requestInterceptor);
ml_api.interceptors.response.use(responseInterceptor, errorInterceptor);

export const createApiCall = <T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
) => {
  return async (data?: any): Promise<ApiResponse<T>> => {
    const response = await api[method](url, data);
    return response.data;
  };
};