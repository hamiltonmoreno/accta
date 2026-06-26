import React from 'react';
import { Shield, Lock } from 'lucide-react';
import { Input } from '../../../components/ui/input';
import { PRIVILEGE_LABELS } from '../../../lib/governanceLabels';
import { inputCls, labelCls } from './tokens';

export const FormInput = ({ id, testId, label, value, onChange, type = 'text', placeholder, max }) => (
  <div>
    <label htmlFor={id} className={labelCls}>{label}</label>
    <Input
      id={id}
      type={type}
      value={value}
      maxLength={max}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testId || id}
    />
  </div>
);

export const FormSelect = ({ id, label, value, onChange, options }) => (
  <div>
    <label htmlFor={id} className={labelCls}>{label}</label>
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={inputCls} data-testid={id}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  </div>
);

// `managed` marca um campo de identidade/associação gerido pela administração
// (não editável em autosserviço) — ícone de cadeado + rótulo para leitores de
// ecrã (spec 006 US5, FR-012/FR-013).
export const InfoRow = ({ icon: Icon, label, value, managed = false }) => (
  <div className="flex items-start gap-3 py-3 border-b border-gray-50 last:border-0">
    <Icon className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
    <div className="min-w-0">
      <span className="text-xs uppercase tracking-widest text-gray-500 font-semibold flex items-center gap-1">
        {label}
        {managed && (
          <>
            <Lock className="w-3 h-3 text-gray-400 flex-shrink-0" aria-hidden="true" title="Gerido pela administração" />
            <span className="sr-only">(gerido pela administração)</span>
          </>
        )}
      </span>
      <span className="text-sm text-grafite font-medium break-words" data-testid={`profile-${label.toLowerCase().replace(/\s/g, '-')}`}>{value || '—'}</span>
    </div>
  </div>
);

export const PrivilegesSection = ({ privileges }) => {
  if (!privileges || privileges.length === 0) return null;
  return (
    <div className="card-technical p-5 animate-fade-up">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Privilégios Atribuídos</h3>
      <div className="flex flex-wrap gap-2">
        {privileges.map((p) => (
          <span key={p} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-carmesim/10 text-carmesim text-xs font-semibold rounded-lg">
            <Shield className="w-3 h-3" />
            {PRIVILEGE_LABELS[p] || p}
          </span>
        ))}
      </div>
    </div>
  );
};
