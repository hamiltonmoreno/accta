process.env.REACT_APP_BACKEND_URL = 'https://test-backend.example.com';
jest.mock('axios', () => {
  const instance = {
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  };
  return { __esModule: true, default: { create: () => instance } };
});

jest.mock('../../../components/ui/alert-dialog', () => ({
  AlertDialog: ({ children }) => children,
  AlertDialogAction: ({ children }) => <button>{children}</button>,
  AlertDialogCancel: ({ children }) => <button>{children}</button>,
  AlertDialogContent: ({ children }) => <div>{children}</div>,
  AlertDialogDescription: ({ children }) => <p>{children}</p>,
  AlertDialogFooter: ({ children }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }) => <h2>{children}</h2>,
}));

jest.mock('../../../components/ui/skeleton', () => ({
  Skeleton: () => null,
}));

const { buildSettingsUpdate } = require('../financeiro/SettingsTab');

describe('buildSettingsUpdate', () => {
  it('keeps description-only saves outside quota governance', () => {
    expect(buildSettingsUpdate({
      settings: { quota_amount: 2000 },
      quotaAmount: '2000',
      quotaDesc: 'Quota Anual',
      assembleiaId: '',
      deliberacaoId: '',
    })).toEqual({ quota_description: 'Quota Anual' });
  });

  it('includes the assembly decision when quota amount changes', () => {
    expect(buildSettingsUpdate({
      settings: { quota_amount: 2000 },
      quotaAmount: '2500',
      quotaDesc: 'Quota Mensal',
      assembleiaId: ' ag-1 ',
      deliberacaoId: ' delib-1 ',
    })).toEqual({
      quota_description: 'Quota Mensal',
      quota_amount: 2500,
      assembleia_id: 'ag-1',
      deliberacao_id: 'delib-1',
    });
  });
});
