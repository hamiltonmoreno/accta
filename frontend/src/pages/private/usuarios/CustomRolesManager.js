import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Layers, Plus, Pencil, Trash2, Users, ArrowLeft, Save, AlertTriangle } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle,
} from '../../../components/ui/dialog';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../../components/ui/alert-dialog';
import { Input } from '../../../components/ui/input';
import { customRolesAPI } from '../../../utils/api';
import { queryKeys } from '../../../lib/queryClient';
import { privilegeLabel } from '../../../lib/cargoLabels';

const EMPTY_FORM = { name: '', description: '', privileges: [] };

// Gestor de funções personalizadas (spec 017): catálogo CRUD de pacotes
// nomeados de privilégios, admin-only. Um só Dialog que alterna entre a
// lista e o formulário criar/editar; eliminação com confirmação destrutiva.
export const CustomRolesManager = ({ open, onClose, privileges }) => {
  const qc = useQueryClient();
  const [form, setForm] = useState(null); // null = vista de lista; {id?} = formulário
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data: roles = [], isLoading } = useQuery({
    queryKey: queryKeys.customRoles.list(),
    queryFn: async () => (await customRolesAPI.list()).data.custom_roles,
    enabled: open,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: queryKeys.customRoles.list() });
    // Edição propaga privilégios aos sócios que têm a função (ligação viva).
    qc.invalidateQueries({ queryKey: ['users'] });
  };

  const onError = (err) => toast.error(err.response?.data?.detail || 'Erro ao guardar a função');

  const createMutation = useMutation({
    mutationFn: (data) => customRolesAPI.create(data),
    onSuccess: () => {
      toast.success('Função criada');
      setForm(null);
      invalidate();
    },
    onError,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => customRolesAPI.update(id, data),
    onSuccess: (res) => {
      const n = res.data?.propagated_to || 0;
      toast.success(n > 0 ? `Função atualizada — aplicada a ${n} sócio(s)` : 'Função atualizada');
      setForm(null);
      invalidate();
    },
    onError,
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => customRolesAPI.remove(id),
    onSuccess: () => {
      toast.success('Função eliminada');
      setDeleteTarget(null);
      invalidate();
    },
    onError: (err) => {
      // 409: função em uso — o detail do backend já inclui a contagem.
      setDeleteTarget(null);
      toast.error(err.response?.data?.detail || 'Erro ao eliminar a função');
    },
  });

  const togglePrivilege = (priv) => {
    const current = form.privileges || [];
    const updated = current.includes(priv)
      ? current.filter((p) => p !== priv)
      : [...current, priv];
    setForm({ ...form, privileges: updated });
  };

  const handleSave = () => {
    const data = {
      name: form.name.trim(),
      description: form.description?.trim() || null,
      privileges: form.privileges,
    };
    if (form.id) {
      updateMutation.mutate({ id: form.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const saving = createMutation.isPending || updateMutation.isPending;
  const canSave = Boolean(form?.name?.trim()) && (form?.privileges || []).length > 0;
  const editingInUse = form?.id ? (roles.find((r) => r.id === form.id)?.user_count || 0) : 0;

  return (
    <>
      <Dialog open={open} onOpenChange={(o) => { if (!o) { setForm(null); onClose(); } }}>
        <DialogContent className="max-w-lg rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="custom-roles-modal">
          <DialogHeader className="px-5 py-4 border-b border-gray-100 text-left space-y-0">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-carmesim" aria-hidden="true" />
              <DialogTitle className="font-bold text-lg text-grafite">
                {form ? (form.id ? 'Editar Função' : 'Nova Função') : 'Funções Personalizadas'}
              </DialogTitle>
            </div>
            <DialogDescription className="text-xs text-[#6B7280] pt-1">
              Pacotes de privilégios aplicáveis a sócios. Editar uma função atualiza todos os sócios que a têm.
            </DialogDescription>
          </DialogHeader>

          {form ? (
            /* ===== Formulário criar/editar ===== */
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">Nome *</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  maxLength={60}
                  placeholder="Ex.: Coordenador de Eventos"
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
                  data-testid="custom-role-name"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-1">Descrição</label>
                <Input
                  value={form.description || ''}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  maxLength={200}
                  placeholder="Opcional"
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
                  data-testid="custom-role-description"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-2">Privilégios *</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {privileges.map((priv) => {
                    const checked = (form.privileges || []).includes(priv);
                    return (
                      <label
                        key={priv}
                        className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-all ${
                          checked ? 'border-carmesim bg-carmesim/5 text-carmesim' : 'border-gray-200 text-gray-600 hover:border-gray-300'
                        }`}
                        data-testid={`custom-role-privilege-${priv}`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
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

              {/* Aviso de impacto (FR/US3): edição com sócios afetados */}
              {editingInUse > 0 && (
                <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg border border-[#F59E0B]/40 bg-[#FFFBEB]" data-testid="custom-role-impact-warning">
                  <AlertTriangle className="w-4 h-4 text-[#B45309] flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <p className="text-xs text-[#B45309]">
                    Esta alteração aplica-se a <strong>{editingInUse} sócio{editingInUse !== 1 ? 's' : ''}</strong> com esta função.
                  </p>
                </div>
              )}

              <div className="flex items-center justify-between pt-1">
                <button
                  type="button"
                  onClick={() => setForm(null)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" aria-hidden="true" />
                  Voltar
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={!canSave || saving}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-floresta hover:bg-floresta-dark text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="custom-role-save-btn"
                >
                  <Save className="w-4 h-4" aria-hidden="true" />
                  Guardar
                </button>
              </div>
            </div>
          ) : (
            /* ===== Lista ===== */
            <div className="p-5 space-y-3">
              {isLoading ? (
                <p className="text-sm text-[#6B7280]">A carregar…</p>
              ) : roles.length === 0 ? (
                <p className="text-sm text-[#6B7280]" data-testid="custom-roles-empty">
                  Ainda não existem funções personalizadas.
                </p>
              ) : (
                <ul className="space-y-2" data-testid="custom-roles-list">
                  {roles.map((r) => (
                    <li key={r.id} className="border border-gray-200 rounded-lg px-4 py-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-grafite truncate">{r.name}</p>
                          {r.description && <p className="text-xs text-[#6B7280] mt-0.5">{r.description}</p>}
                          <p className="text-xs text-[#6B7280] mt-1">
                            {(r.privileges || []).map(privilegeLabel).join(', ')}
                          </p>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => setForm({ id: r.id, name: r.name, description: r.description || '', privileges: [...(r.privileges || [])] })}
                            className="p-2 text-gray-500 hover:text-grafite hover:bg-gray-100 rounded-md transition-colors"
                            aria-label={`Editar ${r.name}`}
                            data-testid={`edit-custom-role-${r.id}`}
                          >
                            <Pencil className="w-4 h-4" aria-hidden="true" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleteTarget(r)}
                            className="p-2 text-gray-500 hover:text-carmesim hover:bg-[#FBEAEC] rounded-md transition-colors"
                            aria-label={`Eliminar ${r.name}`}
                            data-testid={`delete-custom-role-${r.id}`}
                          >
                            <Trash2 className="w-4 h-4" aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                      <p className="inline-flex items-center gap-1 text-xs text-[#6B7280] mt-2">
                        <Users className="w-3.5 h-3.5" aria-hidden="true" />
                        {r.user_count || 0} sócio{(r.user_count || 0) !== 1 ? 's' : ''}
                      </p>
                    </li>
                  ))}
                </ul>
              )}

              <button
                type="button"
                onClick={() => setForm({ ...EMPTY_FORM })}
                className="w-full inline-flex items-center justify-center gap-1.5 py-2.5 bg-floresta hover:bg-floresta-dark text-white rounded-lg text-sm font-semibold transition-colors"
                data-testid="new-custom-role-btn"
              >
                <Plus className="w-4 h-4" aria-hidden="true" />
                Nova Função
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Confirmação destrutiva de eliminação (409 em uso tratado no onError) */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => { if (!o) setDeleteTarget(null); }}>
        <AlertDialogContent className="max-w-sm" data-testid="delete-custom-role-modal">
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar «{deleteTarget?.name}»?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget?.user_count > 0
                ? `Esta função está atribuída a ${deleteTarget.user_count} sócio(s) — a eliminação será recusada até retirar a função a todos.`
                : 'Esta ação é irreversível.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteTarget(null)}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate(deleteTarget.id)}
              className="bg-[#C7202F] text-white hover:bg-[#A51B27]"
              data-testid="confirm-delete-custom-role-btn"
            >
              Sim, eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
