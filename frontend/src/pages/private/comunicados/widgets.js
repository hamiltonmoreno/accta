import React from 'react';
import { Clock } from 'lucide-react';
import { Badge } from '../../../components/ui/badge';
import { ROLE_LABELS } from '../../../lib/cargoLabels';
import { MEMBER_CATEGORY_LABELS } from '../../../lib/governanceLabels';
import {
  ORGAO_SEGMENT_LABELS, SEGMENT_KIND_LABELS, STATUS_CONFIG,
} from './tokens';

export function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || {
    label: status || '—', icon: Clock, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]',
  };
  const Icon = cfg.icon;
  return (
    <Badge variant="outline" className={`gap-1 font-medium ${cfg.className}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {cfg.label}
    </Badge>
  );
}

export function segmentDescription(seg) {
  if (!seg) return '—';
  const base = SEGMENT_KIND_LABELS[seg.kind] || seg.kind;
  if (seg.kind === 'role') return `${base}: ${ROLE_LABELS[seg.value] || seg.value}`;
  if (seg.kind === 'member_category') return `${base}: ${MEMBER_CATEGORY_LABELS[seg.value] || seg.value}`;
  if (seg.kind === 'orgao') return `${base}: ${ORGAO_SEGMENT_LABELS[seg.value] || seg.value}`;
  if (seg.kind === 'manual') return `${base} (${(seg.user_ids || []).length})`;
  return base;
}
