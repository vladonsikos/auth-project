import axiosInstance from '../../../shared/api/axios';
import type { Role, PaginatedResponse } from '../../../shared/types';

const API_BASE = '/access';

export const getRoles = async (page = 1, pageSize = 10) => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  const response = await axiosInstance.get<PaginatedResponse<Role>>(`${API_BASE}/roles/?${params}`);
  return response.data;
};

export const createRole = async (data: { name: string; description?: string }) => {
  const response = await axiosInstance.post<Role>(`${API_BASE}/roles/`, data);
  return response.data;
};

export const updateRole = async (id: number, data: { name?: string; description?: string }) => {
  const response = await axiosInstance.patch<Role>(`${API_BASE}/roles/${id}/`, data);
  return response.data;
};

export const deleteRole = async (id: number) => {
  await axiosInstance.delete(`${API_BASE}/roles/${id}/`);
};
