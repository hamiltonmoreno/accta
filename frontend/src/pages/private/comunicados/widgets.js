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

/**
 * Rótulo PT legível de um `audience_filter` v2 (espelha describe_audience no
 * backend) — descreve os critérios, não as pessoas. Usado no histórico (FR-013).
 */
export function audienceDescription(af) {
  if (!af) return '—';
  const parts = [];
  if (af.orgaos?.length) parts.push(af.orgaos.map((o) => ORGAO_SEGMENT_LABELS[o] || o).join(', '));
  if (af.cargos?.length) parts.push(`cargos (${af.cargos.length})`);
  if (af.categorias?.length) {
    parts.push(`categoria ${af.categorias.map((c) => MEMBER_CATEGORY_LABELS[c] || c).join(', ')}`);
  }
  if (af.statuses?.length) parts.push(`estado ${af.statuses.join(', ')}`);
  const a = af.joined_after;
  const b = af.joined_before;
  if (a && b) parts.push(`admitidos ${a}–${b}`);
  else if (a) parts.push(`admitidos após ${a}`);
  else if (b) parts.push(`admitidos até ${b}`);
  if (af.nominal_member_ids?.length || af.nominal_emails?.length) parts.push('lista nominal');
  return parts.length ? parts.join(' · ') : 'audiência personalizada';
}
