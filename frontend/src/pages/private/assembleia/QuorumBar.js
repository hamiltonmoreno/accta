import React from 'react';

export const QuorumBar = ({ snapshot, fallback }) => {
  // Preferir snapshot SSE (live); cair para `fallback` (GET /quorum) enquanto não chega.
  const q = snapshot?.quorum || fallback;
  if (!q) return <div className="h-6 bg-[#F5F5F5] rounded animate-pulse" />;
  const required = q.required ?? q.quorum_required ?? 0;
  const present = q.present_power ?? q.present_voting_power ?? 0;
  const met = q.met ?? present >= required;
  const ratio = required > 0 ? Math.min(1, present / required) : 0;
  const pct = Math.round(ratio * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-semibold text-[#3A3A3A]">
          Quórum: <span className={met ? 'text-[#15803D]' : 'text-[#B45309]'}>{present} / {required}</span>
        </span>
        <span className="text-xs text-[#6B7280]">
          {snapshot ? `Chamada ${snapshot.chamada || 1}` : ''}{' '}
          {met ? '✓ atingido' : '· em curso'}
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-[#F5F5F5] overflow-hidden" aria-hidden="true">
        <div
          className={`h-full transition-all ${met ? 'bg-[#15803D]' : 'bg-[#B45309]'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};
