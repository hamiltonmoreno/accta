import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

// react-router-dom: Link como <a>, useLocation sem hash.
jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
  useLocation: () => ({ hash: '' }),
}), { virtual: true });

// Accordion (radix + alias @/lib/utils): passthrough — mostra sempre o conteúdo.
jest.mock('../../../components/ui/accordion', () => ({
  Accordion: ({ children }) => <div>{children}</div>,
  AccordionItem: ({ children, ...p }) => <div {...p}>{children}</div>,
  AccordionTrigger: ({ children }) => <button type="button">{children}</button>,
  AccordionContent: ({ children }) => <div>{children}</div>,
}));
jest.mock('../../../components/ui/input', () => ({
  Input: (props) => <input {...props} />,
}));

// useAuth controlável por teste.
let mockAuth;
jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => mockAuth,
}));

const { AjudaPage } = require('../AjudaPage');

const authBase = {
  isAdmin: false, isFinanceiro: false, isModerador: false, isDirecao: false, isMesaAG: false,
  user: { role: 'socio', privileges: [] },
};

afterEach(() => { mockAuth = undefined; });

test('mostra Primeiros passos e o índice', () => {
  mockAuth = { ...authBase };
  render(<AjudaPage />);
  expect(screen.getByText('Central de Ajuda')).toBeInTheDocument();
  expect(screen.getByTestId('ajuda-secao-primeiros-passos')).toBeInTheDocument();
  expect(screen.getByTestId('ajuda-toc-primeiros-passos')).toBeInTheDocument();
});

test('socio NÃO vê Finanças nem Administração', () => {
  mockAuth = { ...authBase };
  render(<AjudaPage />);
  expect(screen.queryByTestId('ajuda-secao-financas')).toBeNull();
  expect(screen.queryByTestId('ajuda-secao-administracao')).toBeNull();
});

test('admin vê Finanças e Administração', () => {
  mockAuth = { ...authBase, isAdmin: true, user: { role: 'admin', privileges: [] } };
  render(<AjudaPage />);
  expect(screen.getByTestId('ajuda-secao-financas')).toBeInTheDocument();
  expect(screen.getByTestId('ajuda-secao-administracao')).toBeInTheDocument();
});

test('Conselho Fiscal (privilégio de leitura) vê Finanças sem ser admin', () => {
  mockAuth = { ...authBase, user: { role: 'socio', privileges: ['view_finances_readonly'] } };
  render(<AjudaPage />);
  expect(screen.getByTestId('ajuda-secao-financas')).toBeInTheDocument();
  expect(screen.queryByTestId('ajuda-secao-administracao')).toBeNull();
});

test('a pesquisa filtra as secções', () => {
  mockAuth = { ...authBase };
  render(<AjudaPage />);
  fireEvent.change(screen.getByTestId('ajuda-search'), { target: { value: 'carteira' } });
  expect(screen.getByTestId('ajuda-secao-meu-portal')).toBeInTheDocument();
  expect(screen.queryByTestId('ajuda-secao-governanca')).toBeNull();
});

test('pesquisa sem resultados mostra estado vazio', () => {
  mockAuth = { ...authBase };
  render(<AjudaPage />);
  fireEvent.change(screen.getByTestId('ajuda-search'), { target: { value: 'zzz-nao-existe-xpto' } });
  expect(screen.getByTestId('ajuda-vazio')).toBeInTheDocument();
});
