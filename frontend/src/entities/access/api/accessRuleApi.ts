import axiosInstance from '../../../shared/api/axios';
import type { AccessRule, AccessRuleInput } from '../types';

const API_BASE = '/access';

export const getAccessRules = async (roleId?: number) => {
  const params = roleId ? `?role=${roleId}` : '';
  const response = await axiosInstance.get<AccessRule[]>(`${API_BASE}/rules/${params}`);
  return response.data;
};

export const getBusinessElements = async () => {
  const response = await axiosInstance.get(`${API_BASE}/elements/`);
  return response.data;
};

export const createAccessRule = async (data: AccessRuleInput) => {
  const response = await axiosInstance.post<AccessRule>(`${API_BASE}/rules/`, data);
  return response.data;
};

export const updateAccessRule = async (id: number, data: Partial<AccessRuleInput>) => {
  const response = await axiosInstance.patch<AccessRule>(`${API_BASE}/rules/${id}/`, data);
  return response.data;
};
