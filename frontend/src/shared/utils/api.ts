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
    if (
      response.data &&
      response.data.status == 'success' &&
      response.data.data !== undefined
    ) {
      return { ...response, data: response.data.data };
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
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
