import React from 'react';
import { Label } from '../../../components/ui/label';
import { Input } from '../../../components/ui/input';
import { Textarea } from '../../../components/ui/textarea';
import { Checkbox } from '../../../components/ui/checkbox';
import { ORGAO_SEGMENT_LABELS } from './tokens';

// Keys de órgão aceites pelo backend (helpers.members_of_orgao). A Assembleia
// Geral é `mesa_ag`; `assembleia_geral` NÃO é válido (ver data-model §1).
const ORGAO_KEYS = ['direcao', 'mesa_ag', 'conselho_fiscal'];

// Estados de sócio (espelha USER_STATUSES). `pendente_aprovacao` alcança contas
// ainda não aprovadas — avisado no preview (US3).
const STATUS_OPTIONS = [
  ['ativo', 'Ativo'],
  ['inativo', 'Inativo'],
  ['pendente_convite', 'Pendente de convite'],
  ['pendente_aprovacao', 'Pendente de aprovação'],
  ['rejeitado', 'Rejeitado'],
];

function CheckGroup({ label, options, selected, onToggle, hint }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {options.map(([value, text]) => (
          <label key={value} className="flex items-center gap-2 cursor-pointer">
            <Checkbox checked={selected.includes(value)} onCheckedChange={() => onToggle(value)} />
            <span className="text-sm text-grafite">{text}</span>
          </label>
        ))}
      </div>
      {hint && <p className="text-xs text-[#6B7280]">{hint}</p>}
    </div>
  );
}

/**
 * Compositor da audiência segmentada (FR-001/FR-014). Constrói o objeto plano
 * `af` (orgaos, cargos, categorias, statuses, joined_after/before, nominal).
 * A composição é OR dentro do tipo e AND entre tipos — resolvida server-side.
 */
export function AudienceBuilder({ af, setAf, cargoOptions, categoriaOptions, restricted = false }) {
  const toggle = (key, value) =>
    setAf((prev) => {
      const arr = prev[key];
      return { ...prev, [key]: arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value] };
    });
  const setField = (key, value) => setAf((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="space-y-5 rounded-lg border border-[#E5E7EB] p-4">
      <p className="text-xs text-[#6B7280]">
        {restricted
          ? 'Selecione o(s) órgão(s) social(is) destinatário(s).'
          : (<>Critérios do mesmo tipo somam-se (OU); tipos diferentes cruzam-se (E). Só
            os sócios que cumprem <strong>todos</strong> os tipos preenchidos são incluídos.</>)}
      </p>

      <CheckGroup
        label="Órgão social"
        options={ORGAO_KEYS.map((k) => [k, ORGAO_SEGMENT_LABELS[k] || k])}
        selected={af.orgaos}
        onToggle={(v) => toggle('orgaos', v)}
      />

      {!restricted && cargoOptions.length > 0 && (
        <CheckGroup
          label="Cargo"
          options={cargoOptions}
          selected={af.cargos}
          onToggle={(v) => toggle('cargos', v)}
        />
      )}

      {!restricted && (
        <>
          <CheckGroup
            label="Categoria de membro"
            options={categoriaOptions}
            selected={af.categorias}
            onToggle={(v) => toggle('categorias', v)}
          />

          <CheckGroup
            label="Estado"
            options={STATUS_OPTIONS}
            selected={af.statuses}
            onToggle={(v) => toggle('statuses', v)}
            hint="Sem critério de estado, o envio vai apenas para sócios ativos."
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="af-joined-after">Admitidos a partir de</Label>
              <Input
                id="af-joined-after" type="date" value={af.joined_after}
                onChange={(e) => setField('joined_after', e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="af-joined-before">Admitidos até</Label>
              <Input
                id="af-joined-before" type="date" value={af.joined_before}
                onChange={(e) => setField('joined_before', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="af-nominal">Lista nominal — opcional</Label>
            <Textarea
              id="af-nominal" rows={2} value={af.nominal}
              onChange={(e) => setField('nominal', e.target.value)}
              placeholder="ACCTA-0042, sócio@exemplo.cv — separados por vírgula ou linha"
            />
            <p className="text-xs text-[#6B7280]">
              member_id ou e-mail. Combina por E com os outros critérios (não adiciona pessoas fora deles).
            </p>
          </div>
        </>
      )}
    </div>
  );
}

export default AudienceBuilder;
