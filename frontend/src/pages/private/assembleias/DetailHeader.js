import React from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar, FileText, Gavel, Lock, MapPin, UserPlus,
} from 'lucide-react';
import { StatusBadge, TipoBadge } from './widgets';
import { formatDateTime, secondaryBtn } from './tokens';

export const DetailHeader = ({
  detail, canManage, isEncerrada, onPresenca, onDeliberacao, onEncerrar,
}) => (
  <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
    <div className="flex flex-wrap items-center gap-2 mb-2">
      <TipoBadge tipo={detail.tipo} />
      <StatusBadge status={detail.status} />
    </div>
    <h2 className="text-lg font-bold text-grafite">{detail.titulo}</h2>
    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-[#6B7280]">
      <span className="inline-flex items-center gap-1.5"><Calendar className="w-4 h-4" aria-hidden="true" />{formatDateTime(detail.data)}</span>
      {detail.local && <span className="inline-flex items-center gap-1.5"><MapPin className="w-4 h-4" aria-hidden="true" />{detail.local}</span>}
    </div>

    {Array.isArray(detail.ordem_trabalhos) && detail.ordem_trabalhos.length > 0 && (
      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] mb-1.5">Ordem de trabalhos</p>
        <ol className="list-decimal list-inside space-y-0.5 text-sm text-grafite">
          {detail.ordem_trabalhos.map((p, i) => (
            <li key={i}>{typeof p === 'string' ? p : (p?.titulo || p?.ponto || '—')}</li>
          ))}
        </ol>
      </div>
    )}

    {detail.acta_document_id && (
      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] mb-1.5">Acta</p>
        <Link
          to="/documentos"
          className="inline-flex items-center gap-1.5 text-sm text-carmesim font-medium hover:underline focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded"
          data-testid="acta-link"
        >
          <FileText className="w-4 h-4" aria-hidden="true" /> Acta registada — ver na biblioteca de documentos
        </Link>
      </div>
    )}

    {/* Ações de gestão */}
    {canManage && (
      <div className="mt-5 flex flex-wrap gap-2">
        <button onClick={onPresenca} disabled={isEncerrada} className={secondaryBtn} data-testid="presenca-btn">
          <UserPlus className="w-4 h-4" aria-hidden="true" />Registar presença
        </button>
        <button onClick={onDeliberacao} disabled={isEncerrada} className={secondaryBtn} data-testid="deliberacao-btn">
          <Gavel className="w-4 h-4" aria-hidden="true" />Registar deliberação
        </button>
        <button onClick={onEncerrar} disabled={isEncerrada} className={secondaryBtn} data-testid="encerrar-btn">
          <Lock className="w-4 h-4" aria-hidden="true" />Encerrar
        </button>
      </div>
    )}
  </div>
);
