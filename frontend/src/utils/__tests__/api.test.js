/**
 * Unit tests for utils/api.js — axios client.
 *
 * Sprint 10 — JWT em httpOnly cookie. Sem request interceptor de token.
 * Cobertura:
 *  - withCredentials: true (cookie cross-origin)
 *  - 401 em rota privada -> dispatch event + redirect
 *  - 401 em rota publica -> sem redirect
 *  - API groups exportados
 */

process.env.REACT_APP_BACKEND_URL = 'https://test-backend.example.com';

// Mock axios — instancia chainable que regista interceptors.
jest.mock('axios', () => {
  const requestHandlers = [];
  const responseHandlers = [];
  const instance = {
    defaults: { baseURL: '', withCredentials: false },
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
        instance.defaults.withCredentials = config.withCredentials;
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

    test('axios instance has withCredentials=true (Sprint 10 cookie auth)', () => {
      expect(api.defaults.withCredentials).toBe(true);
    });

    test('no request interceptor (token injection removed in Sprint 10)', () => {
      // Cookie httpOnly e enviado automaticamente pelo browser via withCredentials.
      // Frontend nao precisa de injectar Authorization header.
      expect(api.interceptors.request.handlers).toHaveLength(0);
    });

    test('exports the major API groups', () => {
      expect(authAPI).toBeDefined();
      expect(authAPI.login).toBeInstanceOf(Function);
      expect(authAPI.forgotPassword).toBeInstanceOf(Function);
      expect(usersAPI).toBeDefined();
      expect(financesAPI).toBeDefined();
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
      const interceptor = api.interceptors.response.handlers[0].rejected;

      await expect(
        interceptor({ response: { status: 401 } }),
      ).rejects.toBeDefined();

      expect(dispatchedEvents).toContain('accta:force-logout');
      expect(window.location.replace).toHaveBeenCalledWith('/login');
    });

    test('does NOT force logout on 401 from a public route', async () => {
      window.location.pathname = '/login';
      const interceptor = api.interceptors.response.handlers[0].rejected;

      await expect(
        interceptor({ response: { status: 401 } }),
      ).rejects.toBeDefined();

      expect(window.location.replace).not.toHaveBeenCalled();
    });

    test('non-401 errors pass through untouched', async () => {
      const interceptor = api.interceptors.response.handlers[0].rejected;
      const error = { response: { status: 500, data: 'oops' } };

      await expect(interceptor(error)).rejects.toBe(error);
    });
  });
});
