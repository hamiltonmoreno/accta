import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersAPI, adminAPI, cargosAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { ROLE_LABELS, PRIVILEGE_LABELS } from '../../lib/cargoLabels';
import { toast } from 'sonner';
import {
  Users, Search, Shield, BadgeCheck, Briefcase, Save,
  Trash2, ChevronDown, Filter, UserCog, UserPlus, Clock, Link2, History
} from 'lucide-react';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../components/ui/alert-dialog';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle,
} from '../../components/ui/dialog';
import {
  ROLE_CONFIG, ROLE_FALLBACK,
  USER_STATUS_CONFIG, USER_STATUS_FALLBACK,
  getStatusConfig,
} from '../../lib/statusConfig';
import { EmptyState } from '../../components/EmptyState';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { UserAvatar } from '../../components/UserAvatar';

// CARGOS e PRIVILEGES vêm do backend (GET /users/meta/cargos). Aqui só os
// conjuntos pequenos e estáveis; rótulos PT em lib/cargoLabels.
const ROLES = ['admin', 'socio', 'financeiro', 'moderador'];
const STATUSES = ['ativo', 'inativo', 'pendente_convite'];

const formatHistoryDate = (iso) => {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return null;
  }
};

export const AdminUsuariosPage = () => {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteData, setInviteData] = useState({ name: '', email: '', role: 'socio', member_id: '', license_number: '', department: '', phone_number: '' });
  const [inviteResult, setInviteResult] = useState(null);

  // Debounce search 300ms — evita re-fetch a cada tecla.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const filters = { search: debouncedSearch, role: filterRole, status: filterStatus };

  const { data: users = [], isLoading: loading } = useQuery({
    queryKey: queryKeys.users.list(filters),
    queryFn: async () => {
      const params = {};
      if (filters.search) params.search = filters.search;
      if (filters.role) params.role = filters.role;
      if (filters.status) params.status = filters.status;
      return (await usersAPI.getAll(params)).data;
    },
  });

  // Metadata canónica do backend (cargos + privilégios). Estático -> staleTime alto.
  const { data: meta } = useQuery({
    queryKey: queryKeys.cargos.meta(),
    queryFn: async () => (await cargosAPI.getMeta()).data,
    staleTime: 60 * 60 * 1000,
  });
  const PRIVILEGES = meta?.privileges || Object.keys(PRIVILEGE_LABELS);

  // Histórico de mandatos do utilizador em edição (timeline só-leitura).
  const { data: cargoHistory = [] } = useQuery({
    queryKey: queryKeys.cargos.history(editingUser?.id),
    queryFn: async () => (await cargosAPI.history(editingUser.id)).data.cargo_history,
    enabled: !!editingUser?.id,
  });

  const invalidateUsers = () => qc.invalidateQueries({ queryKey: ['users'] });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => usersAPI.adminUpdate(id, data),
    onSuccess: () => {
      toast.success('Utilizador atualizado!');
      setEditingUser(null);
      invalidateUsers();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao atualizar'),
  });

  const deleteMutation = useMutation({
    mutationFn: (userId) => usersAPI.delete(userId),
    onSuccess: () => {
      toast.success('Utilizador removido');
      setDeleteConfirm(null);
      setEditingUser(null); // Fecha tambem o edit-modal que disparou o delete
      invalidateUsers();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao remover'),
  });

  // Moderação reativa da foto: admin/moderador removem (não definem) — o backend
  // notifica o utilizador. Atualiza o editingUser localmente para refletir já.
  const removePhotoMutation = useMutation({
    mutationFn: (userId) => usersAPI.removePhoto(userId),
    onSuccess: () => {
      toast.success('Foto removida');
      setEditingUser((u) => (u ? { ...u, photo_url: null } : u));
      invalidateUsers();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao remover a foto'),
  });

  const inviteMutation = useMutation({
    mutationFn: (data) => adminAPI.invite(data),
    onSuccess: (res) => {
      setInviteResult(res.data);
      toast.success(`Convite criado para ${inviteData.name}`);
      invalidateUsers();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar convite'),
  });

  const inviting = inviteMutation.isPending;

  const handleSaveUser = () => {
    if (!editingUser) return;
    updateMutation.mutate({
      id: editingUser.id,
      data: {
        // member_id (imutável) e cargo (gerido em /admin/cargos, com histórico
        // de mandatos) não são enviados — spec-identidade-cargos.
        name: editingUser.name,
        role: editingUser.role,
        status: editingUser.status,
        privileges: editingUser.privileges || [],
        department: editingUser.department,
        phone_number: editingUser.phone_number,
      },
    });
  };

  const handleDelete = (userId) => deleteMutation.mutate(userId);

  const togglePrivilege = (priv) => {
    if (!editingUser) return;
    const current = editingUser.privileges || [];
    const updated = current.includes(priv)
      ? current.filter((p) => p !== priv)
      : [...current, priv];
    setEditingUser({ ...editingUser, privileges: updated });
  };

  const handleInvite = () => {
    if (!inviteData.name || !inviteData.email) {
      toast.error('Nome e email sao obrigatorios');
      return;
    }
    inviteMutation.mutate(inviteData);
  };

  const resetInviteModal = () => {
    setShowInviteModal(false);
    setInviteResult(null);
    setInviteData({ name: '', email: '', role: 'socio', member_id: '', license_number: '', department: '', phone_number: '' });
  };

  return (
    <div className="space-y-6" data-testid="admin-users-page">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="admin-users-title">Gestão de Membros</h1>
          <p className="page-subtitle">{users.length} membro{users.length !== 1 ? 's' : ''} registado{users.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-floresta hover:bg-floresta-dark text-white rounded-lg text-sm font-semibold transition-colors"
          data-testid="invite-user-btn"
        >
          <UserPlus className="w-4 h-4" />
          Convidar Socio
        </button>
      </div>

      {/* Search + Filters */}
      <div className="card-technical p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar por nome, email ou n.º sócio..."
              className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
              data-testid="users-search-input"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
              data-testid="filter-role"
            >
              <option value="">Todas as funções</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
              data-testid="filter-status"
            >
              <option value="">Todos os estados</option>
              {STATUSES.map((s) => (
                <option key={s} value={s} className="capitalize">{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Users Table/Cards */}
      {loading ? (
        <div className="card-technical overflow-hidden" data-testid="users-loading">
          <div className="divide-y divide-gray-50">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3.5">
                <Skeleton className="w-9 h-9 rounded-lg flex-shrink-0" />
                <div className="flex-1 min-w-0 space-y-2">
                  <Skeleton className="h-3.5 w-40" />
                  <Skeleton className="h-3 w-56" />
                </div>
                <Skeleton className="h-5 w-20 rounded-full" />
                <Skeleton className="h-5 w-20 rounded-full" />
              </div>
            ))}
          </div>
        </div>
      ) : users.length === 0 ? (
        <EmptyState icon={Users} title="Nenhum utilizador encontrado" testId="no-users" />
      ) : (
        <>
          {/* Desktop Table */}
          <div className="hidden md:block card-technical overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/50">
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Membro</th>
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Cargo</th>
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Função</th>
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Estado</th>
                    <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Privilégios</th>
                    <th className="text-right px-4 py-3 text-xs uppercase tracking-widest text-[#6B7280] font-semibold">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => {
                    const roleCfg = getStatusConfig(ROLE_CONFIG, u.role, ROLE_FALLBACK);
                    const RoleIcon = roleCfg.icon;
                    const statusCfg = getStatusConfig(USER_STATUS_CONFIG, u.status, USER_STATUS_FALLBACK);
                    const StatusIcon = statusCfg.icon;
                    return (
                    <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <UserAvatar
                            size="sm"
                            className="rounded-lg"
                            name={u.name}
                            photoUrl={u.photo_url}
                            fallbackClassName="rounded-lg bg-[#F5F5F5] text-grafite"
                          />
                          <div className="min-w-0">
                            <div className="font-semibold text-grafite truncate">{u.name}</div>
                            <div className="text-xs text-[#6B7280] truncate">{u.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-medium text-grafite">{u.cargo || 'Sócio'}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${roleCfg.className}`}>
                          <RoleIcon className="w-3 h-3" aria-hidden="true" />
                          {ROLE_LABELS[u.role] || u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${statusCfg.className}`}>
                          <StatusIcon className="w-3 h-3" aria-hidden="true" />
                          {u.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {(u.privileges || []).slice(0, 2).map((p) => (
                            <span key={p} className="text-xs px-1.5 py-0.5 bg-carmesim/10 text-carmesim rounded font-medium">
                              {PRIVILEGE_LABELS[p]?.split(' ')[0] || p}
                            </span>
                          ))}
                          {(u.privileges || []).length > 2 && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">+{u.privileges.length - 2}</span>
                          )}
                          {(!u.privileges || u.privileges.length === 0) && <span className="text-xs text-[#6B7280]">—</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setEditingUser({ ...u, privileges: u.privileges || [] })}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-carmesim hover:text-carmesim-dark transition-colors"
                          data-testid={`edit-user-${u.id}`}
                        >
                          <UserCog className="w-3.5 h-3.5" />
                          Gerir
                        </button>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {users.map((u) => {
              const roleCfg = getStatusConfig(ROLE_CONFIG, u.role, ROLE_FALLBACK);
              const RoleIcon = roleCfg.icon;
              const statusCfg = getStatusConfig(USER_STATUS_CONFIG, u.status, USER_STATUS_FALLBACK);
              const StatusIcon = statusCfg.icon;
              return (
              <div key={u.id} className="card-technical p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <UserAvatar
                      className="rounded-lg"
                      name={u.name}
                      photoUrl={u.photo_url}
                      fallbackClassName="rounded-lg bg-[#F5F5F5] text-grafite"
                    />
                    <div className="min-w-0">
                      <div className="font-semibold text-grafite text-sm truncate">{u.name}</div>
                      <div className="text-xs text-[#6B7280]">{u.cargo || 'Sócio'}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setEditingUser({ ...u, privileges: u.privileges || [] })}
                    className="p-2 text-carmesim hover:bg-carmesim/10 rounded-lg transition-colors"
                    aria-label="Gerir utilizador"
                  >
                    <UserCog className="w-4 h-4" aria-hidden="true" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold ${roleCfg.className}`}>
                    <RoleIcon className="w-3 h-3" aria-hidden="true" />
                    {ROLE_LABELS[u.role]}
                  </span>
                  <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold ${statusCfg.className}`}>
                    <StatusIcon className="w-3 h-3" aria-hidden="true" />
                    {u.status}
                  </span>
                </div>
              </div>
              );
            })}
          </div>
        </>
      )}

      {/* ===== Edit Modal ===== */}
      {editingUser && (
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
                      onClick={() => removePhotoMutation.mutate(editingUser.id)}
                      disabled={removePhotoMutation.isPending}
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
                      value={editingUser.role}
                      onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none bg-white"
                      data-testid="modal-edit-role"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                      ))}
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
                  <label className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold mb-2">
                    <Shield className="w-3 h-3 inline mr-1" />
                    Privilégios
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {PRIVILEGES.map((priv) => {
                      const checked = (editingUser.privileges || []).includes(priv);
                      return (
                        <label
                          key={priv}
                          className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-all ${
                            checked ? 'border-carmesim bg-carmesim/5 text-carmesim' : 'border-gray-200 text-gray-600 hover:border-gray-300'
                          }`}
                          data-testid={`privilege-${priv}`}
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
                          <span className="text-xs font-medium">{PRIVILEGE_LABELS[priv]}</span>
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
                    <Input
                      value={editingUser.department || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, department: e.target.value })}
                      placeholder="Ex: Torre de Controlo Sal"
                      className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-between px-5 py-4 border-t border-gray-100 bg-gray-50/50">
                <button
                  onClick={() => setDeleteConfirm(editingUser.id)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#B91C1C] hover:text-[#991B1B] transition-colors"
                  data-testid="delete-user-btn"
                >
                  <Trash2 className="w-3.5 h-3.5" />
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
                    onClick={handleSaveUser}
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
      )}
      {/* Delete Confirm */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={(o) => { if (!o) setDeleteConfirm(null); }}>
        <AlertDialogContent className="max-w-sm" data-testid="delete-confirm-modal">
          <AlertDialogHeader>
            <AlertDialogTitle>Remover utilizador?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação é irreversível. O utilizador perderá acesso ao portal.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteConfirm(null)}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => handleDelete(deleteConfirm)}
              className="bg-[#C7202F] text-white hover:bg-[#A51B27]"
              data-testid="confirm-delete-btn"
            >
              Sim, remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ===== INVITE MODAL ===== */}
      {showInviteModal && (
        <Dialog open onOpenChange={(o) => { if (!o) resetInviteModal(); }}>
          <DialogContent className="max-w-lg rounded-2xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="invite-modal">
              <DialogHeader className="px-6 py-4 border-b border-gray-100 text-left space-y-0">
                <div className="flex items-center gap-2">
                  <UserPlus className="w-5 h-5 text-carmesim" />
                  <DialogTitle className="font-bold text-lg text-grafite">{inviteResult ? 'Convite Criado' : 'Convidar Socio'}</DialogTitle>
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
                      <p className="text-xs text-[#B45309] font-medium">Convite criado, mas o email nao foi enviado. Reenvie o convite quando o servico de email estiver disponivel.</p>
                    )}
                  </div>

                  <button
                    onClick={resetInviteModal}
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
                        placeholder="Nome do novo socio"
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
                      <label className="block text-xs font-medium text-gray-600 mb-1">Funcao</label>
                      <select
                        value={inviteData.role}
                        onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                        className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none"
                        data-testid="invite-role"
                      >
                        <option value="socio">Socio</option>
                        <option value="financeiro">Financeiro</option>
                        <option value="moderador">Moderador</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">N. Membro</label>
                      <Input
                        value={inviteData.member_id}
                        onChange={(e) => setInviteData({ ...inviteData, member_id: e.target.value })}
                        className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                        placeholder="ACCTA-XXX"
                        data-testid="invite-member-id"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Licenca ATC</label>
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
                      <Input
                        value={inviteData.department}
                        onChange={(e) => setInviteData({ ...inviteData, department: e.target.value })}
                        className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none"
                        placeholder="Ex: Torre, Aproximacao"
                        data-testid="invite-department"
                      />
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
                    onClick={handleInvite}
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
      )}
      </div>
  );
};
