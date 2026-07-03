import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, BadgeCheck, Briefcase, Save, Trash2, History, Wand2 } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { UserAvatar } from '../../../components/UserAvatar';
import { cargosAPI, governanceAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { ROLE_LABELS, privilegeLabel } from '../../../lib/cargoLabels';
import { ROLES, STATUSES, DEPARTAMENTOS, DEPARTAMENTO_OUTRO, formatHistoryDate } from './tokens';

export const EditUserModal = ({
  editingUser,
  setEditingUser,
  privileges,
  customRoles = [],
  onSave,
  onAskDelete,
  onRemovePhoto,
  removingPhoto,
}) => {
  // Histórico de mandatos do utilizador em edição (timeline só-leitura).
  const { data: cargoHistory = [] } = useQuery({
    queryKey: queryKeys.cargos.history(editingUser?.id),
    queryFn: async () => (await cargosAPI.history(editingUser.id)).data.cargo_history,
    enabled: !!editingUser?.id,
  });

  // Estrutura de governança — defaults de cargo (role + privilégios) já existentes.
  const { data: structure } = useQuery({
    queryKey: queryKeys.governance.structure(),
    queryFn: async () => (await governanceAPI.structure()).data,
  });
  const cargoEntry = (structure?.cargos || []).find((c) => c.key === editingUser?.cargo);
  // Contas técnicas não têm cargo estatutário → sem predefinições.
  const canApplyCargoDefaults = editingUser?.account_type !== 'technical' && Boolean(cargoEntry);

  const applyCargoDefaults = () => {
    if (!cargoEntry) return;
    // FR-010 (spec 017): aplicar predefinições substitui a função personalizada.
    if (editingUser.custom_role_id
      && !window.confirm('Este sócio tem uma função personalizada. Aplicar as predefinições do cargo substitui-a. Continuar?')) {
      return;
    }
    setEditingUser({
      ...editingUser,
      custom_role_id: null,
      role: cargoEntry.role_default,
      privileges: [...(cargoEntry.privileges_default || [])],
    });
  };

  // Função personalizada selecionada (spec 017): o valor do seletor usa a
  // sentinela `custom:<id>`; ao selecionar, materializa socio + privilégios
  // da função (read-only); ao voltar a uma fixa, destaca (custom_role_id=null).
  const selectedCustomRole = customRoles.find((r) => r.id === editingUser.custom_role_id);
  const roleValue = selectedCustomRole ? `custom:${selectedCustomRole.id}` : editingUser.role;
  const onRoleChange = (v) => {
    if (v.startsWith('custom:')) {
      const cr = customRoles.find((r) => r.id === v.slice(7));
      if (!cr) return;
      setEditingUser({ ...editingUser, custom_role_id: cr.id, role: 'socio', privileges: [...(cr.privileges || [])] });
    } else {
      setEditingUser({ ...editingUser, custom_role_id: null, role: v });
    }
  };

  // Departamento: «Outro» ativo quando o valor atual não pertence à lista canónica
  // (preserva registos legados / texto livre — FR-013).
  const [deptOutro, setDeptOutro] = useState(
    Boolean(editingUser?.department) && !DEPARTAMENTOS.includes(editingUser.department),
  );
  const onDeptSelect = (v) => {
    if (v === DEPARTAMENTO_OUTRO) {
      setDeptOutro(true);
      setEditingUser({ ...editingUser, department: '' });
    } else {
      setDeptOutro(false);
      setEditingUser({ ...editingUser, department: v });
    }
  };

  const togglePrivilege = (priv) => {
    if (selectedCustomRole) return; // privilégios geridos pela função (ligação viva)
    const current = editingUser.privileges || [];
    const updated = current.includes(priv)
      ? current.filter((p) => p !== priv)
      : [...current, priv];
    setEditingUser({ ...editingUser, privileges: updated });
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) setEditingUser(null); }}>
      <DialogContent className="max-w-lg rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="edit-user-modal">
        {/* Modal Header */}
        <DialogHeader className="px-5 py-4 border-b border-gray-100 text-left space-y-0">
          <div className="flex items-center gap-3">
            <UserAvatar
              className="rounded-lg"
              name={editingUser.name}
              photoUrl={editingUser.photo_url}
              fallbackClassName="rounded-lg bg-[#F5F5F5] text-grafite"
            />
            <div className="min-w-0">
              <DialogTitle className="font-bold text-grafite text-sm truncate">{editingUser.name}</DialogTitle>
              <DialogDescription className="text-xs text-[#6B7280] truncate">{editingUser.email}</DialogDescription>
            </div>
            {editingUser.photo_url && (
              <button
                type="button"
                onClick={onRemovePhoto}
                disabled={removingPhoto}
                className="ml-auto inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-carmesim transition-colors disabled:opacity-50 shrink-0"
                data-testid="admin-remove-photo-btn"
              >
                <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                Remover foto
              </button>
            )}
          </div>
        </DialogHeader>

        {/* Modal Body */}
        <div className="p-5 space-y-5">
          {/* Basic Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">Nome</label>
              <Input
                value={editingUser.name || ''}
                onChange={(e) => setEditingUser({ ...editingUser, name: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
                data-testid="modal-edit-name"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">N.º Sócio <span className="normal-case tracking-normal text-[#9CA3AF]">(imutável)</span></label>
              <div
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-[#F5F5F5] text-[#6B7280] font-mono"
                data-testid="modal-member-id-readonly"
              >
                {editingUser.member_id || '—'}
              </div>
            </div>
          </div>

          {/* Role + Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">
                <Shield className="w-3 h-3 inline mr-1" />
                Função no Sistema
              </label>
              <select
                value={roleValue}
                onChange={(e) => onRoleChange(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
                data-testid="modal-edit-role"
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
                {customRoles.length > 0 && (
                  <optgroup label="Funções personalizadas">
                    {customRoles.map((r) => (
                      <option key={r.id} value={`custom:${r.id}`}>{r.name}</option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">
                <BadgeCheck className="w-3 h-3 inline mr-1" />
                Estado
              </label>
              <select
                value={editingUser.status}
                onChange={(e) => setEditingUser({ ...editingUser, status: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
                data-testid="modal-edit-status"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Cargo — só-leitura: atribuído via Cargos & Mandatos (regista histórico) */}
          <div>
            <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">
              <Briefcase className="w-3 h-3 inline mr-1" />
              Cargo na Associação
            </label>
            <div
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-[#F5F5F5] text-grafite"
              data-testid="modal-edit-cargo"
            >
              {editingUser.cargo || 'Sócio'}
            </div>
            <p className="text-[11px] text-[#9CA3AF] mt-1">
              O cargo é gerido em <span className="text-grafite font-medium">Cargos &amp; Mandatos</span> (atribui mandato e valida vagas).
            </p>
          </div>

          {/* Privileges */}
          <div>
            <div className="flex items-center justify-between mb-2 gap-2">
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold">
                <Shield className="w-3 h-3 inline mr-1" />
                Privilégios
              </label>
              {canApplyCargoDefaults && (
                <button
                  type="button"
                  onClick={applyCargoDefaults}
                  className="inline-flex items-center gap-1.5 text-xs font-medium text-grafite border border-[#D1D5DB] px-2.5 py-1.5 rounded-md hover:bg-gray-50 transition-colors shrink-0"
                  data-testid="apply-cargo-defaults-btn"
                >
                  <Wand2 className="w-3.5 h-3.5" aria-hidden="true" />
                  Aplicar predefinições do cargo
                </button>
              )}
            </div>
            {selectedCustomRole && (
              <p className="text-[11px] text-[#9CA3AF] mb-2" data-testid="custom-role-privileges-note">
                Privilégios definidos pela função «{selectedCustomRole.name}» — editam-se na função e propagam a todos os sócios que a têm.
              </p>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {privileges.map((priv) => {
                const checked = (editingUser.privileges || []).includes(priv);
                return (
                  <label
                    key={priv}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border transition-all ${
                      selectedCustomRole ? 'cursor-not-allowed opacity-70' : 'cursor-pointer'
                    } ${
                      checked ? 'border-carmesim bg-carmesim/5 text-carmesim' : 'border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                    data-testid={`privilege-${priv}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={!!selectedCustomRole}
                      onChange={() => togglePrivilege(priv)}
                      className="sr-only"
                    />
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                      checked ? 'border-carmesim bg-carmesim' : 'border-gray-300'
                    }`}>
                      {checked && (
                        <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span className="text-xs font-medium">{privilegeLabel(priv)}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Histórico de Cargos (timeline só-leitura) */}
          {cargoHistory.length > 0 && (
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-2">
                <History className="w-3 h-3 inline mr-1" aria-hidden="true" />
                Histórico de Cargos
              </label>
              <ul className="space-y-1.5" data-testid="cargo-history-timeline">
                {cargoHistory.map((m) => (
                  <li key={m.id || `${m.cargo}-${m.inicio}`} className="flex items-center justify-between text-xs">
                    <span className="text-grafite font-medium">{m.cargo}</span>
                    <span className="font-mono text-[#6B7280]">
                      {formatHistoryDate(m.inicio) || '—'} → {m.fim ? formatHistoryDate(m.fim) : 'presente'}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Phone + Department */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">Telefone</label>
              <Input
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                value={editingUser.phone_number || ''}
                onChange={(e) => setEditingUser({ ...editingUser, phone_number: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">Departamento</label>
              <select
                value={deptOutro ? DEPARTAMENTO_OUTRO : (editingUser.department || '')}
                onChange={(e) => onDeptSelect(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
                data-testid="modal-edit-department"
              >
                <option value="">Selecionar…</option>
                {DEPARTAMENTOS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
                <option value={DEPARTAMENTO_OUTRO}>Outro</option>
              </select>
              {deptOutro && (
                <Input
                  value={editingUser.department || ''}
                  onChange={(e) => setEditingUser({ ...editingUser, department: e.target.value })}
                  placeholder="Especifique o departamento"
                  className="mt-2 w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
                  data-testid="modal-edit-department-outro"
                />
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-gray-100 bg-gray-50/50">
          <button
            onClick={onAskDelete}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-[#C7202F] border border-[#C7202F] px-3 py-2 rounded-md hover:bg-[#FBEAEC] transition-colors cursor-pointer"
            data-testid="delete-user-btn"
          >
            <Trash2 className="w-4 h-4" />
            Remover
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => setEditingUser(null)}
              className="px-4 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={onSave}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-floresta text-white rounded-lg text-sm font-semibold hover:bg-floresta-dark transition-colors"
              data-testid="modal-save-btn"
            >
              <Save className="w-4 h-4" />
              Guardar
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
