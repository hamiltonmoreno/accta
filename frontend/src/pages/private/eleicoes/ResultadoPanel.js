import React, { useMemo } from 'react';
import { AlertTriangle, Trophy } from 'lucide-react';
import { formatDate } from './tokens';

// Painel de resultado (AGREGADO apenas — spec §18).
export const ResultadoPanel = ({ resultado, listas }) => {
  const porLista = resultado.por_lista || {};
  const letraById = useMemo(() => {
    const m = {};
    listas.forEach((l) => { m[l.id] = l; });
    return m;
  }, [listas]);

  const rows = Object.entries(porLista)
    .map(([listaId, count]) => ({ listaId, count, lista: letraById[listaId] }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="space-y-4">
      {resultado.empate && (
        <div className="flex items-start gap-2 px-4 py-3 rounded-md bg-[#FFFBEB] ring-1 ring-[#FDE68A]" data-testid="empate-warning">
          <AlertTriangle className="w-4 h-4 text-[#B45309] mt-0.5 shrink-0" aria-hidden="true" />
          <div className="text-sm text-[#B45309]">
            <span className="font-semibold">Empate.</span> É necessária nova eleição.
            {resultado.nova_eleicao_ate && <> Prazo até {formatDate(resultado.nova_eleicao_ate)}.</>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Brancos</p>
          <p className="text-xl font-bold text-grafite">{resultado.brancos ?? 0}</p>
        </div>
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Nulos</p>
          <p className="text-xl font-bold text-grafite">{resultado.nulos ?? 0}</p>
        </div>
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Votos válidos</p>
          <p className="text-xl font-bold text-grafite">{resultado.total_validos ?? 0}</p>
        </div>
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Total boletins</p>
          <p className="text-xl font-bold text-grafite">{resultado.total_boletins ?? 0}</p>
        </div>
      </div>

      <div className="space-y-2">
        {rows.length === 0 ? (
          <p className="text-sm text-[#6B7280]">Sem votos por lista.</p>
        ) : rows.map(({ listaId, count, lista }) => {
          const winner = resultado.vencedora === listaId && !resultado.empate;
          return (
            <div
              key={listaId}
              className={`flex items-center justify-between px-4 py-3 rounded-md border ${winner ? 'border-[#BBF7D0] bg-[#F0FDF4]' : 'border-[#E5E7EB] bg-white'}`}
              data-testid={`resultado-lista-${listaId}`}
            >
              <span className="flex items-center gap-2 text-sm text-grafite">
                {winner && <Trophy className="w-4 h-4 text-[#15803D]" aria-hidden="true" />}
                <span className="font-semibold">Lista {lista?.letra || '?'}</span>
                {lista?.nome && <span className="text-[#6B7280]">{lista.nome}</span>}
                {winner && <span className="text-xs font-semibold text-[#15803D]">Vencedora</span>}
              </span>
              <span className={`text-lg font-bold ${winner ? 'text-[#15803D]' : 'text-grafite'}`}>{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
