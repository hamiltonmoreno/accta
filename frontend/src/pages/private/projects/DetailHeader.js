import React, { useState } from 'react';
import { ArrowLeft, CheckCircle, EyeOff } from 'lucide-react';
import {
  PROJECT_STATUS_CONFIG, PROJECT_STATUS_FALLBACK, getStatusConfig,
} from '../../../lib/statusConfig';

export const DetailHeader = ({
  project, isAdmin, onBack, onStatusChange, onApprove,
}) => {
  const [editingStatus, setEditingStatus] = useState(false);
  const canEditProjectStatus = isAdmin;
  const st = getStatusConfig(PROJECT_STATUS_CONFIG, project.status, PROJECT_STATUS_FALLBACK);
  const StatusIcon = st.icon;

  return (
    <div>
      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-carmesim mb-3 transition-colors" data-testid="back-to-projects">
        <ArrowLeft className="w-4 h-4" /> Voltar aos projetos
      </button>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="project-title">{project.title}</h1>
          <div className="flex items-center gap-3 mt-1.5 flex-wrap">
            <div className="relative">
              <button onClick={() => canEditProjectStatus && setEditingStatus(!editingStatus)}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${st.className} ${canEditProjectStatus ? 'cursor-pointer hover:opacity-80' : ''}`}
                data-testid="project-status-badge">
                <StatusIcon className="w-3 h-3" aria-hidden="true" />
                {st.label}
              </button>
              {editingStatus && canEditProjectStatus && (
                <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1 min-w-[140px]">
                  {Object.entries(PROJECT_STATUS_CONFIG).map(([key, val]) => {
                    const ValIcon = val.icon;
                    return (
                      <button key={key} onClick={() => { onStatusChange(key); setEditingStatus(false); }}
                        className="w-full px-3 py-1.5 text-left text-sm hover:bg-gray-50 flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${val.dotClassName}`} />
                        <ValIcon className="w-3.5 h-3.5 text-[#6B7280]" aria-hidden="true" />
                        {val.label}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            {project.visibility === 'privado' && (
              <span className="flex items-center gap-1 text-xs text-carmesim font-semibold"><EyeOff className="w-3.5 h-3.5" /> Privado</span>
            )}
            {project.category && <span className="text-xs text-[#6B7280] bg-gray-100 px-2 py-0.5 rounded-full">{project.category}</span>}
          </div>
        </div>

        {/* Admin approve button */}
        {isAdmin && project.status === 'proposta' && (
          <button onClick={onApprove} className="btn-primary flex items-center gap-2 text-sm" data-testid="approve-project-btn">
            <CheckCircle className="w-4 h-4" /> Aprovar Projeto
          </button>
        )}
      </div>
    </div>
  );
};
