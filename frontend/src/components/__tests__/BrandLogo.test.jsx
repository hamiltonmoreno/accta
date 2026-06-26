import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// brandAPI.getPublic nunca resolve → o que aparecer no 1.º render veio do
// localStorage (semente), não da rede. É isso que prova a ausência de flash.
jest.mock('../../utils/api', () => ({
  mediaUrl: (p) => `/media${p}`,
  brandAPI: { getPublic: jest.fn(() => new Promise(() => {})) },
}));

const { BrandLogo } = require('../BrandLogo');

const wrap = (ui) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
};

beforeEach(() => localStorage.clear());

test('semeado do localStorage: pinta a logo configurada já no 1.º render (sem flash do vetor por defeito)', () => {
  localStorage.setItem(
    'accta:brand',
    JSON.stringify({ logo_light_url: '/uploads/logos/atual.png', alt: 'ACCTA' })
  );
  wrap(<BrandLogo />);
  expect(screen.getByRole('img')).toHaveAttribute('src', '/media/uploads/logos/atual.png');
});

test('sem cache: cai no vetor por defeito, nunca uma logo errada', () => {
  wrap(<BrandLogo />);
  expect(screen.queryByRole('img')).toBeNull(); // ACCTALogoHorizontal é SVG inline, não <img>
});
