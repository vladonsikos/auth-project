export interface User {
  id: number;
  first_name: string;
  last_name: string;
  patronymic?: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  roles?: Role[];
}

export interface Role {
  id: number;
  name: string;
  description: string;
}

export type UserRole = 'admin' | 'manager' | 'user' | 'guest';

export interface CreateUserRequest {
  first_name: string;
  last_name: string;
  patronymic?: string;
  email: string;
  password: string;
  password_confirm?: string;
}

export interface UpdateUserRequest {
  first_name?: string;
  last_name?: string;
  patronymic?: string;
  email?: string;
  is_active?: boolean;
  role?: number;
  password?: string;
  password_confirm?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

export interface LoginResponse {
  token: string;
  refresh_token?: string;
  expires_at: string;
  user: User;
}
