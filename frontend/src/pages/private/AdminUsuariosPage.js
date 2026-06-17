import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersAPI, adminAPI, cargosAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { PRIVILEGE_LABELS } from '../../lib/cargoLabels';
import { toast } from 'sonner';
import { Users, UserPlus } from 'lucide-react';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../components/ui/alert-dialog';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

import { EMPTY_INVITE } from './usuarios/tokens';
import { FiltersBar } from './usuarios/FiltersBar';
import { UsersTable } from './usuarios/UsersTable';
import { UsersCards } from './usuarios/UsersCards';
import { EditUserModal } from './usuarios/EditUserModal';
import { InviteModal } from './usuarios/InviteModal';

export const AdminUsuariosPage = () => {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteData, setInviteData] = useState(EMPTY_INVITE);
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
    setInviteData(EMPTY_INVITE);
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

      <FiltersBar
        search={search} setSearch={setSearch}
        filterRole={filterRole} setFilterRole={setFilterRole}
        filterStatus={filterStatus} setFilterStatus={setFilterStatus}
      />

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
          <UsersTable users={users} onEdit={setEditingUser} />
          <UsersCards users={users} onEdit={setEditingUser} />
        </>
      )}

      {editingUser && (
        <EditUserModal
          editingUser={editingUser}
          setEditingUser={setEditingUser}
          privileges={PRIVILEGES}
          onSave={handleSaveUser}
          onAskDelete={() => setDeleteConfirm(editingUser.id)}
          onRemovePhoto={() => removePhotoMutation.mutate(editingUser.id)}
          removingPhoto={removePhotoMutation.isPending}
        />
      )}

      <AlertDialog open={!!deleteConfirm} onOpenChange={(o) => { if (!o) setDeleteConfirm(null); }}>
        <AlertDialogContent className="max-w-sm" data-testid="delete-confirm-modal">
          <AlertDialogHeader>
            <AlertDialogTitle>Remover utilizador?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação é irreversível. O utilizador perderá acesso ao portal.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDeleteConfirm(null)}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteMutation.mutate(deleteConfirm)}
              className="bg-[#C7202F] text-white hover:bg-[#A51B27]"
              data-testid="confirm-delete-btn"
            >
              Sim, remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {showInviteModal && (
        <InviteModal
          inviteData={inviteData}
          setInviteData={setInviteData}
          inviteResult={inviteResult}
          inviting={inviteMutation.isPending}
          onSend={handleInvite}
          onClose={resetInviteModal}
        />
      )}
    </div>
  );
};

export default AdminUsuariosPage;
