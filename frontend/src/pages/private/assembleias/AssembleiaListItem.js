import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, ChevronRight, MapPin } from 'lucide-react';
import { StatusBadge, TipoBadge } from './widgets';
import { formatDateTime } from './tokens';

export const AssembleiaListItem = ({ assembleia: a, active, onSelect }) => (
  <div className="relative">
    <button
      onClick={() => onSelect(a.id)}
      className={`w-full text-left bg-white rounded-lg border shadow-sm p-4 transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 ${active ? 'border-carmesim ring-1 ring-carmesim/30' : 'border-[#E5E7EB] hover:bg-[#F5F5F5]'}`}
      data-testid={`assembleia-row-${a.id}`}
      aria-current={active ? 'true' : undefined}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <TipoBadge tipo={a.tipo} />
        <StatusBadge status={a.status} />
      </div>
      <p className="font-semibold text-grafite leading-snug">{a.titulo}</p>
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#6B7280]">
        <span className="inline-flex items-center gap-1"><Calendar className="w-3.5 h-3.5" aria-hidden="true" />{formatDateTime(a.data)}</span>
        {a.local && <span className="inline-flex items-center gap-1"><MapPin className="w-3.5 h-3.5" aria-hidden="true" />{a.local}</span>}
      </div>
    </button>
    {/* Entrada para a sala "ao vivo" (camada participativa) — sai do
        botão pai p/ permitir click próprio sem `button-in-button`. */}
    {(a.status === 'convocada' || a.status === 'em_curso') && (
      <Link
        to={`/assembleias/${a.id}`}
        className="absolute right-3 bottom-3 text-xs text-carmesim hover:underline inline-flex items-center gap-1"
        data-testid={`assembleia-sala-${a.id}`}
      >
        Sala ao vivo
        <ChevronRight className="w-3 h-3" aria-hidden="true" />
      </Link>
    )}
  </div>
);
