import React, { useState } from 'react';
import { UserPlus, Link2 } from 'lucide-react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { ROLES, DEPARTAMENTOS, DEPARTAMENTO_OUTRO } from './tokens';
import { ROLE_LABELS } from '../../../lib/cargoLabels';

const SELECT_CLASS =
  'w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white';

export const InviteModal = ({
  inviteData, setInviteData, inviteResult, inviting, onSend, onClose, customRoles = [],
}) => {
  // Função personalizada (spec 017): sentinela `custom:<id>` no seletor; o
  // convidado nasce socio + privilégios da função (o backend materializa).
  const roleValue = inviteData.custom_role_id ? `custom:${inviteData.custom_role_id}` : inviteData.role;
  const onRoleChange = (v) => {
    if (v.startsWith('custom:')) {
      setInviteData({ ...inviteData, custom_role_id: v.slice(7), role: 'socio' });
    } else {
      setInviteData({ ...inviteData, custom_role_id: '', role: v });
    }
  };
  // «Outro» ativo quando o departamento atual não pertence à lista canónica.
  const [deptOutro, setDeptOutro] = useState(
    Boolean(inviteData.department) && !DEPARTAMENTOS.includes(inviteData.department),
  );

  const onDeptSelect = (v) => {
    if (v === DEPARTAMENTO_OUTRO) {
      setDeptOutro(true);
      setInviteData({ ...inviteData, department: '' });
    } else {
      setDeptOutro(false);
      setInviteData({ ...inviteData, department: v });
    }
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg rounded-2xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="invite-modal">
        <DialogHeader className="px-6 py-4 border-b border-gray-100 text-left space-y-0">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-carmesim" />
            <DialogTitle className="font-bold text-lg text-grafite">
              {inviteResult ? 'Convite Criado' : 'Convidar Sócio'}
            </DialogTitle>
          </div>
        </DialogHeader>

        {inviteResult ? (
          <div className="p-6 space-y-4">
            <div className="text-center">
              <div className="w-12 h-12 bg-[#F0FDF4] rounded-2xl flex items-center justify-center mx-auto mb-3">
                <Link2 className="w-6 h-6 text-[#15803D]" />
              </div>
              <p className="text-sm text-gray-600 mb-1">Convite criado para <strong>{inviteResult.email}</strong></p>
              {inviteResult.email_sent ? (
                <p className="text-xs text-[#15803D] font-medium">Email de convite enviado com sucesso!</p>
              ) : (
                <p className="text-xs text-[#B45309] font-medium">Convite criado, mas o email não foi enviado. Reenvie o convite quando o serviço de email estiver disponível.</p>
              )}
            </div>

            <button
              onClick={onClose}
              className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 text-grafite rounded-lg text-sm font-medium transition-colors"
            >
              Fechar
            </button>
          </div>
        ) : (
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Nome Completo *</label>
                <Input
                  value={inviteData.name}
                  onChange={(e) => setInviteData({ ...inviteData, name: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                  placeholder="Nome do novo sócio"
                  data-testid="invite-name"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Email *</label>
                <Input
                  type="email"
                  inputMode="email"
                  autoComplete="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                  placeholder="email@controlador.cv"
                  data-testid="invite-email"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Nível de acesso</label>
                <select
                  value={roleValue}
                  onChange={(e) => onRoleChange(e.target.value)}
                  className={SELECT_CLASS}
                  data-testid="invite-role"
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
                <label className="block text-xs font-medium text-gray-600 mb-1">N.º de Membro</label>
                <Input
                  value={inviteData.member_id}
                  onChange={(e) => setInviteData({ ...inviteData, member_id: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                  placeholder="ACCTA-XXX"
                  data-testid="invite-member-id"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Licença ATC</label>
                <Input
                  value={inviteData.license_number}
                  onChange={(e) => setInviteData({ ...inviteData, license_number: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                  placeholder="ATC-CV-XXXX-XXX"
                  data-testid="invite-license"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Departamento</label>
                <select
                  value={deptOutro ? DEPARTAMENTO_OUTRO : (inviteData.department || '')}
                  onChange={(e) => onDeptSelect(e.target.value)}
                  className={SELECT_CLASS}
                  data-testid="invite-department"
                >
                  <option value="">Selecionar…</option>
                  {DEPARTAMENTOS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                  <option value={DEPARTAMENTO_OUTRO}>Outro</option>
                </select>
                <p className="text-[11px] text-[#9CA3AF] mt-1">Etiqueta organizacional — não altera acessos.</p>
                {deptOutro && (
                  <Input
                    value={inviteData.department}
                    onChange={(e) => setInviteData({ ...inviteData, department: e.target.value })}
                    className="mt-2 w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                    placeholder="Especifique o departamento"
                    data-testid="invite-department-outro"
                  />
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Telefone</label>
                <Input
                  type="tel"
                  inputMode="tel"
                  autoComplete="tel"
                  value={inviteData.phone_number}
                  onChange={(e) => setInviteData({ ...inviteData, phone_number: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                  placeholder="+238 xxxxxxx"
                  data-testid="invite-phone"
                />
              </div>
            </div>

            <button
              onClick={onSend}
              disabled={inviting || !inviteData.name || !inviteData.email}
              className="w-full py-2.5 bg-floresta hover:bg-floresta-dark text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="send-invite-btn"
            >
              {inviting ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Criar Convite
                </>
              )}
            </button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
