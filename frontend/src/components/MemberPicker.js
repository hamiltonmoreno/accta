import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { cargosAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { Skeleton } from './ui/skeleton';

/**
 * Procura de sócios (debounced) — componente partilhado pelos módulos de
 * governança (assembleias, disciplina, cargos, eleições). Extraído de 4 cópias
 * praticamente idênticas.
 *
 * Props:
 *  - value:        sócio seleccionado (ou null). Quando definido mostra a pílula
 *                  "seleccionado + Alterar".
 *  - onSelect:     (candidate | null) => void
 *  - testId:       data-testid do input de procura
 *  - placeholder:  texto do input (default genérico)
 *  - excludeCargo: cargo a excluir da lista de candidatos (enviado como
 *                  exclude_cargo à API; usado em /admin/cargos).
 *  - showCargo:    incluir " · cargo" no subtítulo de cada candidato (default true).
 *  - gateOnQuery:  só mostrar a lista depois de o utilizador escrever algo
 *                  (default false → mostra sempre).
 *  - emptyLabel:   texto quando não há resultados.
 */
export const MemberPicker = ({
  value,
  onSelect,
  testId,
  placeholder = 'Procurar por nome, email ou nº associado...',
  excludeCargo,
  showCargo = true,
  gateOnQuery = false,
  emptyLabel = 'Nenhum sócio encontrado.',
}) => {
  const [search, setSearch] = useState('');
  const [debounced, setDebounced] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const { data: candidates = [], isFetching, isError } = useQuery({
    queryKey: queryKeys.cargos.candidates({ q: debounced, excludeCargo }),
    queryFn: async () =>
      (await cargosAPI.candidates({
        q: debounced || undefined,
        exclude_cargo: excludeCargo || undefined,
      })).data.candidates,
    staleTime: 30 * 1000,
  });

  if (value) {
    return (
      <div className="flex items-center justify-between px-3 py-2.5 rounded-md border border-[#D1D5DB] bg-[#F5F5F5]">
        <span className="text-sm text-grafite truncate">
          {value.name} <span className="font-mono text-xs text-[#6B7280]">{value.member_id || ''}</span>
        </span>
        <button
          type="button"
          onClick={() => onSelect(null)}
          className="text-xs text-carmesim font-semibold hover:underline cursor-pointer ml-2 shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded px-1"
        >
          Alterar
        </button>
      </div>
    );
  }

  const showList = !gateOnQuery || !!debounced;

  return (
    <div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={placeholder}
          className="w-full pl-9 pr-3 py-2.5 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
          data-testid={testId}
        />
      </div>
      {showList && (
        <div className="mt-1.5 max-h-44 overflow-y-auto rounded-md border border-gray-100 divide-y divide-gray-50">
          {isFetching && candidates.length === 0 ? (
            <div className="px-3 py-3"><Skeleton className="h-4 w-40" /></div>
          ) : isError ? (
            <p className="px-3 py-3 text-xs text-carmesim font-medium">Não foi possível carregar os sócios. Tente novamente.</p>
          ) : candidates.length === 0 ? (
            <p className="px-3 py-3 text-xs text-[#6B7280]">{emptyLabel}</p>
          ) : (
            candidates.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => onSelect(c)}
                className="w-full text-left px-3 py-2 hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                data-testid={`candidate-${c.id}`}
              >
                <span className="text-sm text-grafite">{c.name}</span>
                <span className="ml-2 font-mono text-xs text-[#6B7280]">{c.member_id || ''}</span>
                <span className="block text-xs text-[#6B7280]">{c.email}{showCargo && c.cargo ? ` · ${c.cargo}` : ''}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default MemberPicker;
