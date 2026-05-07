/**
 * Unit tests for utils/api.js — the axios client used across the frontend.
 *
 * Coverage focus:
 *  - Token injection from localStorage into Authorization header
 *  - 401 response triggers logout dispatch + storage clear (private routes only)
 *  - 401 on a public route does NOT trigger logout
 *  - All API groups are exported
 *
 * We mock axios so Jest doesn't have to transform its ESM build.
 */

process.env.REACT_APP_BACKEND_URL = 'https://test-backend.example.com';

// Mock axios with a chainable instance that records interceptors.
jest.mock('axios', () => {
  const requestHandlers = [];
  const responseHandlers = [];
  const instance = {
    defaults: { baseURL: '' },
    interceptors: {
      request: {
        handlers: requestHandlers,
        use: (fulfilled, rejected) => {
          requestHandlers.push({ fulfilled, rejected });
          return requestHandlers.length - 1;
        },
      },
      response: {
        handlers: responseHandlers,
        use: (fulfilled, rejected) => {
          responseHandlers.push({ fulfilled, rejected });
          return responseHandlers.length - 1;
        },
      },
    },
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  };
  return {
    __esModule: true,
    default: {
      create: (config) => {
        instance.defaults.baseURL = config.baseURL;
        return instance;
      },
    },
  };
});

describe('utils/api', () => {
  let api;
  let authAPI;
  let usersAPI;
  let financesAPI;

  beforeEach(() => {
    jest.resetModules();
    localStorage.clear();
    const mod = require('../api');
    api = mod.default;
    authAPI = mod.authAPI;
    usersAPI = mod.usersAPI;
    financesAPI = mod.financesAPI;
  });

  describe('configuration', () => {
    test('axios instance has correct baseURL', () => {
      expect(api.defaults.baseURL).toBe('https://test-backend.example.com/api');
    });

    test('exports the major API groups', () => {
      expect(authAPI).toBeDefined();
      expect(authAPI.login).toBeInstanceOf(Function);
      expect(authAPI.forgotPassword).toBeInstanceOf(Function);
      expect(usersAPI).toBeDefined();
      expect(financesAPI).toBeDefined();
    });
  });

  describe('request interceptor — token injection', () => {
    test('adds Bearer token from localStorage when present', () => {
      localStorage.setItem('accta_token', 'fake-jwt-123');
      const interceptor = api.interceptors.request.handlers[0].fulfilled;
      const config = { headers: {} };
      const result = interceptor(config);
      expect(result.headers.Authorization).toBe('Bearer fake-jwt-123');
    });

    test('omits Authorization header when no token stored', () => {
      const interceptor = api.interceptors.request.handlers[0].fulfilled;
      const config = { headers: {} };
      const result = interceptor(config);
      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('response interceptor — 401 handling', () => {
    let originalLocation;
    let dispatchedEvents;

    beforeEach(() => {
      dispatchedEvents = [];
      originalLocation = window.location;
      delete window.location;
      window.location = { pathname: '/dashboard', replace: jest.fn() };
      window.dispatchEvent = (e) => {
        dispatchedEvents.push(e.type);
        return true;
      };
    });

    afterEach(() => {
      window.location = originalLocation;
    });

    test('forces logout when 401 received on private route', async () => {
      localStorage.setItem('accta_token', 'expired-token');
      localStorage.setItem('accta_user', JSON.stringify({ id: 'u1' }));
      const interceptor = api.interceptors.response.handlers[0].rejected;

      await expect(
        interceptor({ response: { status: 401 } })
      ).rejects.toBeDefined();

      expect(localStorage.getItem('accta_token')).toBeNull();
      expect(localStorage.getItem('accta_user')).toBeNull();
      expect(dispatchedEvents).toContain('accta:force-logout');
      expect(window.location.replace).toHaveBeenCalledWith('/login');
    });

    test('does NOT force logout on 401 from a public route', async () => {
      window.location.pathname = '/login';
      localStorage.setItem('accta_token', 'tok');
      const interceptor = api.interceptors.response.handlers[0].rejected;

      await expect(
        interceptor({ response: { status: 401 } })
      ).rejects.toBeDefined();

      expect(localStorage.getItem('accta_token')).toBe('tok');
      expect(window.location.replace).not.toHaveBeenCalled();
    });

    test('non-401 errors pass through untouched', async () => {
      localStorage.setItem('accta_token', 'tok');
      const interceptor = api.interceptors.response.handlers[0].rejected;
      const error = { response: { status: 500, data: 'oops' } };

      await expect(interceptor(error)).rejects.toBe(error);
      expect(localStorage.getItem('accta_token')).toBe('tok');
    });
  });
});
