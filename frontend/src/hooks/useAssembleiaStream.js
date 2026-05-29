import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { assembleiasAPI } from '../utils/api';

// Backoff exponencial p/ reabrir a SSE após `onerror` — 2s, 8s, depois 30s
// permanente. Sem isto o `es.close()` defeats o reconnect nativo do EventSource
// e a sala fica em polling 30s para o resto da sessão mesmo após o servidor
// recuperar.
const RECONNECT_BACKOFF_MS = [2000, 8000, 30000];
const FALLBACK_POLL_MS = 30000;

export function useAssembleiaStream(assembleiaId) {
  const qc = useQueryClient();
  const [snapshot, setSnapshot] = useState(null);
  const [connected, setConnected] = useState(false);
  const [lastEventAt, setLastEventAt] = useState(null);
  const esRef = useRef(null);
  const fallbackRef = useRef(null);
  const retryTimerRef = useRef(null);
  const retryAttemptRef = useRef(0);

  useEffect(() => {
    if (!assembleiaId) return undefined;

    const url = assembleiasAPI.streamUrl(assembleiaId);

    const handleSnapshot = (data) => {
      setSnapshot(data);
      setLastEventAt(Date.now());
      qc.setQueryData(['assembleia', assembleiaId, 'snapshot'], data);
    };

    const clearTimers = () => {
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      if (fallbackRef.current) {
        clearInterval(fallbackRef.current);
        fallbackRef.current = null;
      }
    };

    const startFallback = () => {
      if (fallbackRef.current) return;
      fallbackRef.current = setInterval(() => {
        qc.invalidateQueries({ queryKey: ['assembleia', assembleiaId] });
      }, FALLBACK_POLL_MS);
    };

    const scheduleReconnect = () => {
      const attempt = retryAttemptRef.current;
      const delay = RECONNECT_BACKOFF_MS[Math.min(attempt, RECONNECT_BACKOFF_MS.length - 1)];
      retryAttemptRef.current = attempt + 1;
      retryTimerRef.current = setTimeout(() => {
        retryTimerRef.current = null;
        start();
      }, delay);
    };

    const start = () => {
      if (esRef.current) return;
      try {
        const es = new EventSource(url, { withCredentials: true });
        esRef.current = es;
        es.onopen = () => {
          setConnected(true);
          retryAttemptRef.current = 0;
          // Recuperou: parar o fallback de 30s, o SSE volta a ser fonte primária.
          if (fallbackRef.current) {
            clearInterval(fallbackRef.current);
            fallbackRef.current = null;
          }
        };
        es.onmessage = (evt) => {
          try {
            const data = JSON.parse(evt.data);
            handleSnapshot(data);
          } catch (err) {
            // Snapshot malformado → invalida queries para forçar refetch e segue.
            console.warn('useAssembleiaStream: snapshot inválido', err);
            qc.invalidateQueries({ queryKey: ['assembleia', assembleiaId] });
          }
        };
        es.addEventListener('error', (evt) => {
          if (evt?.data) {
            // Evento de erro estruturado emitido pelo servidor (cf. SSE generator).
            try {
              const payload = JSON.parse(evt.data);
              console.warn('useAssembleiaStream: erro servidor', payload);
            } catch {
              /* opaque */
            }
          }
        });
        es.onerror = () => {
          setConnected(false);
          es.close();
          esRef.current = null;
          // Polling como rede-de-segurança enquanto tenta reconectar.
          startFallback();
          scheduleReconnect();
        };
      } catch {
        setConnected(false);
        startFallback();
        scheduleReconnect();
      }
    };

    const stop = () => {
      setConnected(false);
      clearTimers();
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    };

    const onVisibility = () => {
      if (document.hidden) {
        stop();
      } else {
        retryAttemptRef.current = 0;
        qc.invalidateQueries({ queryKey: ['assembleia', assembleiaId] });
        start();
      }
    };

    if (!document.hidden) start();
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      stop();
    };
  }, [assembleiaId, qc]);

  return { snapshot, connected, lastEventAt };
}
