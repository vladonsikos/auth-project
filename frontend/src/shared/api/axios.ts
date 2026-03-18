import axios, { AxiosError } from 'axios';

import { API_URL } from '../config';
import type { ApiError } from '../types';

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const config = error.config as typeof error.config & { _retryCount?: number };
    // Only retry on network errors or 5xx, not on 4xx
    const isRetryable = !error.response || error.response.status >= 500;
    if (isRetryable && config) {
      config._retryCount = (config._retryCount ?? 0) + 1;
      if (config._retryCount <= 3) {
        const delay = Math.min(1000 * 2 ** (config._retryCount - 1), 8000);
        await new Promise((res) => setTimeout(res, delay));
        return axiosInstance(config);
      }
    }
    throw error;
  }
);

export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data;

    if (responseData && typeof responseData === 'object') {
      // Handle field-specific errors like {password: ["minPassword"]}
      const entries = Object.entries(responseData);
      for (const [field, value] of entries) {
        if (Array.isArray(value) && value.length > 0) {
          const errorMsg = String(value[0]);
          // Map common error codes to user-friendly messages
          if (errorMsg === 'minPassword') {
            return 'Пароль должен быть не менее 6 символов';
          }
          if (errorMsg === 'required') {
            return `Поле "${field}" обязательно для заполнения`;
          }
          if (errorMsg === 'invalidEmail') {
            return 'Некорректный email адрес';
          }
          return errorMsg;
        }
        if (value != null && typeof value === 'string') {
          return value;
        }
      }
    }

    const responseError = error.response?.data as { detail?: string; message?: string } | undefined;
    if (responseError?.detail) return responseError.detail;
    if (responseError?.message) return responseError.message;

    if (error.message) return error.message;

    return 'Произошла непредвиденная ошибка';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Произошла непредвиденная ошибка';
};

export default axiosInstance;
