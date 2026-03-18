import axiosInstance from '../../../shared/api/axios';
import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  PaginatedResponse,
} from '../../../shared/types';

const API_BASE = '/auth';

export const getUsers = async (
  page = 1,
  pageSize = 10,
  search = '',
  filters?: Record<string, string>
) => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (search) params.set('search', search);
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
  }
  const response = await axiosInstance.get<PaginatedResponse<User>>(`${API_BASE}/users/?${params}`);
  return response.data;
};

export const createUser = async (data: CreateUserRequest) => {
  const response = await axiosInstance.post<User>(`${API_BASE}/users/`, data);
  return response.data;
};

export const updateUser = async (id: number, data: UpdateUserRequest) => {
  const response = await axiosInstance.patch<User>(`${API_BASE}/users/${id}/`, data);
  return response.data;
};

export const deleteUser = async (id: number) => {
  const response = await axiosInstance.delete(`${API_BASE}/users/${id}/`);
  return response.data;
};

export const bulkDeleteUsers = async (ids: number[]) => {
  const response = await axiosInstance.post(`${API_BASE}/users/bulk_delete/`, { ids });
  return response.data;
};
