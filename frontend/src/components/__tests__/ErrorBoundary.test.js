/**
 * Tests for the ErrorBoundary component.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';

const Bomb = ({ message = 'kaboom' }) => {
  throw new Error(message);
};

describe('ErrorBoundary', () => {
  let errorSpy;
  beforeEach(() => {
    // The boundary always logs to console.error — silence it for cleaner test output.
    errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    errorSpy.mockRestore();
  });

  test('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>safe content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('safe content')).toBeInTheDocument();
  });

  test('shows fallback UI in Portuguese when a child throws', () => {
    render(
      <ErrorBoundary>
        <Bomb message="boom" />
      </ErrorBoundary>
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Algo correu mal')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /voltar ao início/i })).toHaveAttribute('href', '/');
  });

  test('"Tentar novamente" clears error state so swapped children render', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>
    );
    expect(screen.getByText('Algo correu mal')).toBeInTheDocument();
    // Swap to non-throwing children FIRST. The boundary keeps the error state
    // until reset is called, so the fallback is still shown.
    rerender(
      <ErrorBoundary>
        <div>recovered</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Algo correu mal')).toBeInTheDocument();
    // Now click reset — error state clears and the swapped children render.
    fireEvent.click(screen.getByRole('button', { name: /tentar novamente/i }));
    expect(screen.getByText('recovered')).toBeInTheDocument();
  });

  test('logs error to console.error so monitoring tools pick it up', () => {
    render(
      <ErrorBoundary>
        <Bomb message="watch me crash" />
      </ErrorBoundary>
    );
    // The boundary calls console.error("Uncaught render error:", err, info).
    const logged = errorSpy.mock.calls.some((call) =>
      call.some((arg) => typeof arg === 'string' && arg.includes('Uncaught render error'))
    );
    expect(logged).toBe(true);
  });
});
