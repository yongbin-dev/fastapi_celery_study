import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { api } from '@/shared/utils/api';
import type { ApiResponse } from '@/shared/types';

export const useGet = <T>(
  key: string,
  url: string,
  options?: Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: [key],
    queryFn: async (): Promise<T> => {
      const response = await api.get<ApiResponse<T>>(url);
      return response.data.data;
    },
    ...options,
  });
};

export const usePost = <T, P = unknown>(
  url: string,
  options?: Omit<UseMutationOptions<T, Error, P>, 'mutationFn'>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: P): Promise<T> => {
      const response = await api.post<ApiResponse<T>>(url, data);
      return response.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
    ...options,
  });
};

export const usePut = <T, P = unknown>(
  url: string,
  options?: Omit<UseMutationOptions<T, Error, P>, 'mutationFn'>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: P): Promise<T> => {
      const response = await api.put<ApiResponse<T>>(url, data);
      return response.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
    ...options,
  });
};

export const useDelete = <T = unknown>(
  url: string,
  options?: Omit<UseMutationOptions<T, Error, void>, 'mutationFn'>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<T> => {
      const response = await api.delete<ApiResponse<T>>(url);
      return response.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
    ...options,
  });
};
