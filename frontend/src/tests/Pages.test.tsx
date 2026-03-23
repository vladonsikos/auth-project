import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

import { AuthProvider } from '../features/auth';
import { UsersPage } from '../pages/UsersPage';
import { RolesPage } from '../pages/RolesPage';
import { ThemeProvider } from '../shared/lib/ThemeProvider';
import '../shared/config/i18n';

// Mock useAuth so pages don't redirect
vi.mock('../features/auth/model/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      first_name: 'Admin',
      last_name: 'User',
      email: 'admin@example.com',
      is_active: true,
      roles: [{ id: 1, name: 'admin' }],
    },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const createWrapper = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>{children}</BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

describe('UsersPage', () => {
  it('renders page title', async () => {
    render(<UsersPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/users|пользователи/i)).toBeInTheDocument();
    });
  });

  it('renders Add User button', async () => {
    render(<UsersPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /add user|добавить пользователя/i })
      ).toBeInTheDocument();
    });
  });

  it('renders search input', () => {
    render(<UsersPage />, { wrapper: createWrapper() });
    expect(screen.getByPlaceholderText(/search|поиск/i)).toBeInTheDocument();
  });

  it('renders data table', async () => {
    render(<UsersPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(document.querySelector('.MuiDataGrid-root')).toBeInTheDocument();
    });
  });
});

describe('RolesPage', () => {
  it('renders page title', async () => {
    render(<RolesPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/roles|роли/i)).toBeInTheDocument();
    });
  });

  it('renders Add Role button', async () => {
    render(<RolesPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add role|добавить роль/i })).toBeInTheDocument();
    });
  });

  it('renders data table', async () => {
    render(<RolesPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(document.querySelector('.MuiDataGrid-root')).toBeInTheDocument();
    });
  });
});
