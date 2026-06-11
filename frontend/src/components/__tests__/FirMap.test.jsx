import React from 'react';
import { render, screen } from '@testing-library/react';
import { FirMap } from '../FirMap';

test('renderiza o mapa do FIR com nome acessível e rótulos-chave', () => {
  render(<FirMap />);
  // imagem acessível (role img + aria-labelledby -> <title>)
  expect(screen.getByRole('img', { name: /FIR Oceânica do Sal/i })).toBeInTheDocument();
  // rótulos esquemáticos presentes
  expect(screen.getByText('Cabo Verde')).toBeInTheDocument();
  expect(screen.getByText(/FIR OCEÂNICA DO SAL/)).toBeInTheDocument();
  // legenda honesta a remeter para o AIP
  expect(screen.getByText(/AIP de\s+Cabo Verde/i)).toBeInTheDocument();
});
