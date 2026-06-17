import React from 'react';

export const InfoCards = ({ project, canManage, onProgressChange }) => (
  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
    <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
      <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Progresso</div>
      <div className="flex items-center gap-2">
        {canManage ? (
          <input type="range" min="0" max="100" step="5" value={project.progress}
            onChange={(e) => onProgressChange(e.target.value)}
            className="flex-1 accent-carmesim" data-testid="progress-slider" />
        ) : (
          <div className="flex-1 bg-gray-100 rounded-full h-2">
            <div className="bg-carmesim h-2 rounded-full" style={{ width: `${project.progress}%` }} />
          </div>
        )}
        <span className="font-mono text-sm font-bold text-grafite">{project.progress}%</span>
      </div>
    </div>
    <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
      <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Responsavel</div>
      <div className="text-sm font-medium text-grafite truncate">{project.responsible_name || project.created_by_name || '-'}</div>
    </div>
    <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
      <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Periodo</div>
      <div className="text-xs text-gray-600">{project.start_date || '?'} - {project.end_date || '?'}</div>
    </div>
    <div className="bg-white border border-gray-200/80 rounded-xl p-3.5">
      <div className="text-xs text-[#6B7280] uppercase tracking-wider mb-0.5">Orcamento</div>
      <div className="font-mono text-sm font-bold text-grafite">{(project.budget || 0).toLocaleString('pt')} CVE</div>
    </div>
  </div>
);
