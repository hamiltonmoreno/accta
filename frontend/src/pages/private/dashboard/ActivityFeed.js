import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ArrowRight } from 'lucide-react';
import { ActivityIcon } from './widgets';
import { timeAgo } from './tokens';

export const ActivityFeed = ({ items }) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden animate-fade-up" data-testid="activity-feed">
      <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-carmesim" />
          <h2 className="text-lg font-semibold text-grafite">Atividade Recente</h2>
        </div>
        <span className="text-xs text-[#6B7280] uppercase tracking-wider hidden sm:block">Ultimas atualizacoes</span>
      </div>

      <div className="divide-y divide-gray-50 max-h-[420px] overflow-y-auto">
        {items.map((item, i) => (
          <button
            key={`${item.type}-${i}`}
            onClick={() => item.link && navigate(item.link)}
            className="w-full flex items-start gap-3 px-5 sm:px-6 py-3.5 hover:bg-gray-50/80 transition-colors text-left"
            data-testid={`activity-item-${i}`}
          >
            <ActivityIcon type={item.type} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-grafite truncate">{item.title}</span>
                <span className="text-xs text-[#6B7280] font-mono whitespace-nowrap">{timeAgo(item.created_at)}</span>
              </div>
              <p className="text-xs text-gray-500 truncate mt-0.5">{item.description}</p>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0 mt-1" />
          </button>
        ))}
      </div>
    </div>
  );
};
