import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { Input } from '../../../components/ui/input';
import { Checkbox } from '../../../components/ui/checkbox';
import { Skeleton } from '../../../components/ui/skeleton';
import { usersAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { useDebounced } from './hooks';

export function MemberSelector({ selectedIds, onToggle }) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounced(search, 300);

  const { data: members = [], isLoading } = useQuery({
    queryKey: queryKeys.users.list({ search: debouncedSearch, scope: 'comunicados' }),
    queryFn: async () => {
      const params = { status: 'ativo', limit: 50 };
      if (debouncedSearch) params.search = debouncedSearch;
      return (await usersAPI.getAll(params)).data;
    },
  });

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" aria-hidden="true" />
        <Input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Procurar sócio por nome ou e-mail…"
          className="pl-9"
          aria-label="Procurar sócio"
          data-testid="comunicado-member-search"
        />
      </div>

      <div className="border border-[#E5E7EB] rounded-md max-h-60 overflow-y-auto divide-y divide-[#E5E7EB]">
        {isLoading ? (
          <div className="p-3 space-y-2">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-9 w-full rounded-md" />)}
          </div>
        ) : members.length === 0 ? (
          <p className="p-4 text-sm text-[#6B7280] text-center">Nenhum sócio encontrado.</p>
        ) : (
          members.map((m) => {
            const checked = selectedIds.includes(m.id);
            return (
              <label
                key={m.id}
                className="flex items-center gap-3 px-3 py-2 hover:bg-[#F5F5F5] cursor-pointer transition-colors"
                data-testid={`comunicado-member-${m.id}`}
              >
                <Checkbox checked={checked} onCheckedChange={() => onToggle(m.id)} />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm text-grafite truncate">{m.name || 'Sem nome'}</span>
                  <span className="block text-xs text-[#6B7280] truncate">{m.email}</span>
                </span>
              </label>
            );
          })
        )}
      </div>

      <p className="text-xs text-[#6B7280]">
        {selectedIds.length} sócio(s) selecionado(s).
      </p>
    </div>
  );
}
