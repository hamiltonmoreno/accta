import React from 'react';
import { Search } from 'lucide-react';
import { Input } from '../../../components/ui/input';
import { ROLE_LABELS } from '../../../lib/cargoLabels';
import { ROLES, STATUSES } from './tokens';

export const FiltersBar = ({ search, setSearch, filterRole, setFilterRole, filterStatus, setFilterStatus }) => (
  <div className="card-technical p-4">
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Pesquisar por nome, email ou n.º sócio..."
          className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
          data-testid="users-search-input"
        />
      </div>
      <div className="flex gap-2">
        <select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
          className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
          data-testid="filter-role"
        >
          <option value="">Todas as funções</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
          data-testid="filter-status"
        >
          <option value="">Todos os estados</option>
          {STATUSES.map((s) => (
            <option key={s} value={s} className="capitalize">{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
      </div>
    </div>
  </div>
);
