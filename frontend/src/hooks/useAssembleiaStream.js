import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { assembleiasAPI } from '../utils/api';

/**
 * SSE por-assembleia (spec-sessao-assembleia §2.2 / §10).
 *
 * Espelha o padrão usado pelo `NotificationContext`:
 *  - `EventSource(withCredentials: true)` para autenticar pelo cookie HttpOnly,
 *  - Fallback de 30s (invalidação de queries TanStack) se o SSE falhar,
 *  - Pausa o stream enquanto o separador está oculto e reabre ao voltar.
 *
 * Retorna o último snapshot recebido — `{ version, phase, status, chamada,
 * current_item_id, quorum, speaking, open_vote }` — ou `null` antes do
 * primeiro evento.
 */
export function useAssembleiaStream(assembleiaId) {
  const qc = useQueryClient();
  const [snapshot, setSnapshot] = useState(null);
  const esRef = useRef(null);
  const fallbackRef = useRef(null);

  useEffect(() => {
    if (!assembleiaId) return undefined;

    const url = assembleiasAPI.streamUrl(assembleiaId);

    const handleSnapshot = (data) => {
      setSnapshot(data);
      // Propaga para a cache TanStack — outros consumidores re-renderizam
      // sem refetch HTTP. Os widgets podem ler ou via prop ou via useQuery
      // com queryKey ['assembleia', id, 'snapshot'].
      qc.setQueryData(['assembleia', assembleiaId, 'snapshot'], data);
    };

    const start = () => {
      if (esRef.current || fallbackRef.current) return;
      try {
        const es = new EventSource(url, { withCredentials: true });
        esRef.current = es;
        es.onmessage = (evt) => {
          try {
            const data = JSON.parse(evt.data);
            handleSnapshot(data);
          } catch {
            /* ignore parse errors */
          }
        };
        es.onerror = () => {
          es.close();
          esRef.current = null;
          // Fallback: invalida tudo da assembleia → as queries refazem fetch.
          fallbackRef.current = setInterval(() => {
            qc.invalidateQueries({ queryKey: ['assembleia', assembleiaId] });
          }, 30000);
        };
      } catch {
        fallbackRef.current = setInterval(() => {
          qc.invalidateQueries({ queryKey: ['assembleia', assembleiaId] });
        }, 30000);
      }
    };

    const stop = () => {
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
      if (fallbackRef.current) {
        clearInterval(fallbackRef.current);
        fallbackRef.current = null;
      }
    };

    const onVisibility = () => {
      if (document.hidden) {
        stop();
      } else {
        // Ao voltar à aba, refresh imediato + reabre o stream.
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

  return snapshot;
}
