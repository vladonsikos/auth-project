import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { afterAll, afterEach, beforeAll } from 'vitest';

const handlers = [
  // Authentication
  http.post('/api/auth/login/', () => {
    return HttpResponse.json({
      token: 'test-token',
      expires_at: new Date().toISOString(),
      user: {
        id: 1,
        first_name: 'Test',
        last_name: 'User',
        email: 'test@example.com',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });
  }),

  http.get('/api/auth/profile/', () => {
    return HttpResponse.json({
      id: 1,
      first_name: 'Test',
      last_name: 'User',
      email: 'test@example.com',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }),

  http.post('/api/auth/logout/', () => {
    return HttpResponse.json({ detail: 'Logged out' });
  }),

  // Users
  http.get('/api/auth/users/', () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          first_name: 'Admin',
          last_name: 'User',
          email: 'admin@example.com',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 2,
          first_name: 'Regular',
          last_name: 'User',
          email: 'user@example.com',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    });
  }),

  // Roles
  http.get('/api/access/roles/', () => {
    return HttpResponse.json({
      count: 4,
      next: null,
      previous: null,
      results: [
        { id: 1, name: 'admin', description: 'Administrator' },
        { id: 2, name: 'manager', description: 'Manager' },
        { id: 3, name: 'user', description: 'Regular User' },
        { id: 4, name: 'guest', description: 'Guest User' },
      ],
    });
  }),

  // Business Elements
  http.get('/api/access/elements/', () => {
    return HttpResponse.json([
      { id: 1, name: 'products', description: 'Products' },
      { id: 2, name: 'orders', description: 'Orders' },
      { id: 3, name: 'shops', description: 'Shops' },
    ]);
  }),

  // Access Rules
  http.get('/api/access/rules/', () => {
    return HttpResponse.json([]);
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));
afterEach(() => {
  server.resetHandlers();
  cleanup();
});
afterAll(() => server.close());
