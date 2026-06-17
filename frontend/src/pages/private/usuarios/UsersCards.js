import React from 'react';
import { UserCog } from 'lucide-react';
import { UserAvatar } from '../../../components/UserAvatar';
import { ROLE_LABELS } from '../../../lib/cargoLabels';
import {
  ROLE_CONFIG, ROLE_FALLBACK,
  USER_STATUS_CONFIG, USER_STATUS_FALLBACK,
  getStatusConfig,
} from '../../../lib/statusConfig';

export const UsersCards = ({ users, onEdit }) => (
  <div className="md:hidden space-y-3">
    {users.map((u) => {
      const roleCfg = getStatusConfig(ROLE_CONFIG, u.role, ROLE_FALLBACK);
      const RoleIcon = roleCfg.icon;
      const statusCfg = getStatusConfig(USER_STATUS_CONFIG, u.status, USER_STATUS_FALLBACK);
      const StatusIcon = statusCfg.icon;
      return (
        <div key={u.id} className="card-technical p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <UserAvatar
                className="rounded-lg"
                name={u.name}
                photoUrl={u.photo_url}
                fallbackClassName="rounded-lg bg-[#F5F5F5] text-grafite"
              />
              <div className="min-w-0">
                <div className="font-semibold text-grafite text-sm truncate">{u.name}</div>
                <div className="text-xs text-[#6B7280]">{u.cargo || 'Sócio'}</div>
              </div>
            </div>
            <button
              onClick={() => onEdit({ ...u, privileges: u.privileges || [] })}
              className="p-2 text-carmesim hover:bg-carmesim/10 rounded-lg transition-colors"
              aria-label="Gerir utilizador"
            >
              <UserCog className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold ${roleCfg.className}`}>
              <RoleIcon className="w-3 h-3" aria-hidden="true" />
              {ROLE_LABELS[u.role]}
            </span>
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold ${statusCfg.className}`}>
              <StatusIcon className="w-3 h-3" aria-hidden="true" />
              {u.status}
            </span>
          </div>
        </div>
      );
    })}
  </div>
);
