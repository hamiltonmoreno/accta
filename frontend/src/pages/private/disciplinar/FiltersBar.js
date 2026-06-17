import React from 'react';
import { SANCAO_TIPO_LABELS, SANCAO_STATUS_LABELS } from '../../../lib/governanceLabels';
import {
  TIPO_OPTIONS, STATUS_OPTIONS, secondaryBtn, selectCls,
} from './tokens';

export const FiltersBar = ({ statusFilter, setStatusFilter, tipoFilter, setTipoFilter }) => (
  <div className="flex flex-wrap items-end gap-3 bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4">
    <div className="min-w-[180px]">
      <label className="block text-xs font-medium text-gray-600 mb-1.5">Estado</label>
      <select
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        className={selectCls}
        data-testid="filter-status"
      >
        <option value="">Todos os estados</option>
        {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{SANCAO_STATUS_LABELS[s]}</option>)}
      </select>
    </div>
    <div className="min-w-[180px]">
      <label className="block text-xs font-medium text-gray-600 mb-1.5">Tipo</label>
      <select
        value={tipoFilter}
        onChange={(e) => setTipoFilter(e.target.value)}
        className={selectCls}
        data-testid="filter-tipo"
      >
        <option value="">Todos os tipos</option>
        {TIPO_OPTIONS.map((t) => <option key={t} value={t}>{SANCAO_TIPO_LABELS[t]}</option>)}
      </select>
    </div>
    {(statusFilter || tipoFilter) && (
      <button
        onClick={() => { setStatusFilter(''); setTipoFilter(''); }}
        className={secondaryBtn}
        data-testid="filter-clear"
      >
        Limpar filtros
      </button>
    )}
  </div>
);
