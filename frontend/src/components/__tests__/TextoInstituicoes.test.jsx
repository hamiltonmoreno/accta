import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { TextoInstituicoes } from '../TextoInstituicoes';

const links = (container) => Array.from(container.querySelectorAll('a'));

test('linka uma instituição conhecida com o URL oficial e abre noutro separador', () => {
  const { container } = render(<TextoInstituicoes texto="É regulado pela AAC no país." />);
  const a = container.querySelector('a');
  expect(a).toHaveTextContent('AAC');
  expect(a).toHaveAttribute('href', 'https://www.aac.cv/');
  expect(a).toHaveAttribute('target', '_blank');
  expect(a).toHaveAttribute('rel', 'noopener noreferrer');
});

test('linka apenas a 1ª ocorrência de cada instituição', () => {
  const { container } = render(<TextoInstituicoes texto="A AAC emite regras. A AAC licencia. AAC outra vez." />);
  expect(links(container)).toHaveLength(1);
});

test('linka instituições distintas no mesmo texto (ICAO e AAC)', () => {
  const { container } = render(
    <TextoInstituicoes texto="Segue normas ICAO e é regulado pela AAC." />
  );
  const hrefs = links(container).map((a) => a.getAttribute('href'));
  expect(hrefs).toContain('https://www.icao.int/');
  expect(hrefs).toContain('https://www.aac.cv/');
});

test('não linka palavras desconhecidas nem apanha siglas dentro de palavras (case-sensitive)', () => {
  // "casa" não deve virar link de ASA; "texto" simples sem instituições → 0 links.
  const { container } = render(<TextoInstituicoes texto="A casa fica perto do aeroporto." />);
  expect(links(container)).toHaveLength(0);
  expect(container).toHaveTextContent('A casa fica perto do aeroporto.');
});

test('preserva o texto em redor do link', () => {
  render(<TextoInstituicoes texto="prestado pela ASA no Sal" />);
  // o texto completo continua presente (antes e depois do link)
  const span = screen.getByText(/prestado pela/);
  expect(within(span).getByText('ASA')).toHaveAttribute('href', 'https://www.asa.cv/');
  expect(span).toHaveTextContent('prestado pela ASA no Sal');
});
