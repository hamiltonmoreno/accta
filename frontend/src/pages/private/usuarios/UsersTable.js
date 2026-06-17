import React from 'react';
import { UserCog } from 'lucide-react';
import { UserAvatar } from '../../../components/UserAvatar';
import { ROLE_LABELS, PRIVILEGE_LABELS } from '../../../lib/cargoLabels';
import {
  ROLE_CONFIG, ROLE_FALLBACK,
  USER_STATUS_CONFIG, USER_STATUS_FALLBACK,
  getStatusConfig,
} from '../../../lib/statusConfig';

export const UsersTable = ({ users, onEdit }) => (
  <div className="hidden md:block card-technical overflow-hidden">
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50/50">
            <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Membro</th>
            <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Cargo</th>
            <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Função</th>
            <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Estado</th>
            <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Privilégios</th>
            <th className="text-right px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Ações</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => {
            const roleCfg = getStatusConfig(ROLE_CONFIG, u.role, ROLE_FALLBACK);
            const RoleIcon = roleCfg.icon;
            const statusCfg = getStatusConfig(USER_STATUS_CONFIG, u.status, USER_STATUS_FALLBACK);
            const StatusIcon = statusCfg.icon;
            return (
              <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <UserAvatar
                      size="sm"
                      className="rounded-lg"
                      name={u.name}
                      photoUrl={u.photo_url}
                      fallbackClassName="rounded-lg bg-[#F5F5F5] text-grafite"
                    />
                    <div className="min-w-0">
                      <div className="font-semibold text-grafite truncate">{u.name}</div>
                      <div className="text-xs text-[#6B7280] truncate">{u.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs font-medium text-grafite">{u.cargo || 'Sócio'}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${roleCfg.className}`}>
                    <RoleIcon className="w-3 h-3" aria-hidden="true" />
                    {ROLE_LABELS[u.role] || u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${statusCfg.className}`}>
                    <StatusIcon className="w-3 h-3" aria-hidden="true" />
                    {u.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(u.privileges || []).slice(0, 2).map((p) => (
                      <span key={p} className="text-xs px-1.5 py-0.5 bg-carmesim/10 text-carmesim rounded font-medium">
                        {PRIVILEGE_LABELS[p]?.split(' ')[0] || p}
                      </span>
                    ))}
                    {(u.privileges || []).length > 2 && (
                      <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">+{u.privileges.length - 2}</span>
                    )}
                    {(!u.privileges || u.privileges.length === 0) && <span className="text-xs text-[#6B7280]">—</span>}
                  </div>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onEdit({ ...u, privileges: u.privileges || [] })}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-carmesim hover:text-carmesim-dark transition-colors"
                    data-testid={`edit-user-${u.id}`}
                  >
                    <UserCog className="w-3.5 h-3.5" />
                    Gerir
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
);
