import React from 'react';
import { CircleDollarSign, Scale, ShieldOff, Undo2, Users } from 'lucide-react';
import { TipoBadge, StatusBadge } from './widgets';
import { formatDate, formatEscudo, secondaryBtn } from './tokens';

// Helpers de elegibilidade de ações por estado (espelho dos guards do backend).
const canComissao = (s) => ['proposta', 'inquerito'].includes(s.status);
const canDecidir = (s) => ['proposta', 'inquerito', 'recurso'].includes(s.status);
const canRecurso = (s) => s.status === 'decidida' && ['multa', 'perda_direitos'].includes(s.tipo);
const canAplicar = (s) => s.status === 'decidida';

export const SancaoCard = ({
  sancao: s, onComissao, onDecidir, onRecurso, onAplicar,
}) => (
  <div
    className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6"
    data-testid={`sancao-row-${s.id}`}
  >
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <TipoBadge tipo={s.tipo} />
          <StatusBadge status={s.status} />
          <span className="text-xs text-[#6B7280]">{formatDate(s.created_at)}</span>
        </div>
        <p className="mt-2 text-sm text-grafite">
          <span className="text-[#6B7280]">Membro:</span> <span className="font-mono">{s.user_id}</span>
        </p>
        <p className="mt-1 text-sm text-grafite line-clamp-2" title={s.motivo}>
          {s.motivo}
        </p>
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#6B7280]">
          {s.artigo_violado && <span>Artigo: {s.artigo_violado}</span>}
          {s.tipo === 'multa' && <span>Multa: {formatEscudo(s.multa_valor)}</span>}
          {s.tipo === 'perda_direitos' && <span>Direitos suspensos até: {formatDate(s.perda_direitos_ate)}</span>}
          {Array.isArray(s.comissao_inquerito) && s.comissao_inquerito.length > 0 && (
            <span>Comissão: {s.comissao_inquerito.length} membro(s)</span>
          )}
          {s.inquerito_prazo && <span>Prazo inquérito: {formatDate(s.inquerito_prazo)}</span>}
        </div>
        {/* T027: multa aplicada → receita lançada no caixa (garantida exactly-once pelo backend). */}
        {s.tipo === 'multa' && s.status === 'aplicada' && Number(s.multa_valor) > 0 && (
          <div
            className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-[#F0FDF4] border border-[#BBF7D0] px-2.5 py-1 text-xs"
            data-testid={`multa-receita-${s.id}`}
          >
            <CircleDollarSign className="w-3.5 h-3.5 text-[#166534]" aria-hidden="true" />
            <span className="font-medium text-[#166534]">
              Receita lançada no caixa: {formatEscudo(s.multa_valor)}
            </span>
            {s.aplicada_em && <span className="text-[#6B7280]">· {formatDate(s.aplicada_em)}</span>}
          </div>
        )}
      </div>
      <div className="flex flex-wrap items-center justify-end gap-2">
        {canComissao(s) && (
          <button onClick={() => onComissao(s)} className={secondaryBtn} data-testid={`comissao-${s.id}`}>
            <Users className="w-3.5 h-3.5" aria-hidden="true" />Comissão de inquérito
          </button>
        )}
        {canDecidir(s) && (
          <button onClick={() => onDecidir(s)} className={secondaryBtn} data-testid={`decidir-${s.id}`}>
            <Scale className="w-3.5 h-3.5" aria-hidden="true" />Decidir
          </button>
        )}
        {canRecurso(s) && (
          <button onClick={() => onRecurso(s)} className={secondaryBtn} data-testid={`recurso-${s.id}`}>
            <Undo2 className="w-3.5 h-3.5" aria-hidden="true" />Recurso
          </button>
        )}
        {canAplicar(s) && (
          <button
            onClick={() => onAplicar(s)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white border border-[#FECACA] text-[#B91C1C] text-xs font-medium hover:bg-[#FEF2F2] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
            data-testid={`aplicar-${s.id}`}
          >
            <ShieldOff className="w-3.5 h-3.5" aria-hidden="true" />Aplicar
          </button>
        )}
      </div>
    </div>
  </div>
);
