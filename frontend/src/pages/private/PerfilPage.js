import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Pencil, X } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { usersAPI, governanceAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';

import { EMPTY_FORM } from './perfil/tokens';
import { PrivilegesSection } from './perfil/widgets';
import { ProfileCard } from './perfil/ProfileCard';
import { RightsSuspendedBanner } from './perfil/RightsSuspendedBanner';
import { EditForm } from './perfil/EditForm';
import { DetailsGrid } from './perfil/DetailsGrid';
import { EmailPrefs } from './perfil/EmailPrefs';
import { PushPrefs } from '../../components/PushPrefs';
import { MeusCargosSection } from './perfil/MeusCargosSection';

export const PerfilPage = () => {
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [cropSrc, setCropSrc] = useState(null);

  // Sincroniza o form a partir do user — mas nunca enquanto o form está aberto
  // (editing), para um refetch/refreshUser não sobrescrever edições em curso.
  // Fora de edição (mount inicial, pós-save, pós-cancel) reflecte o user actual.
  useEffect(() => {
    if (user && !editing) {
      setForm({
        ...EMPTY_FORM,
        ...Object.fromEntries(Object.keys(EMPTY_FORM).map((k) => [k, user[k] || ''])),
      });
    }
  }, [user, editing]);

  const set = (key) => (val) => setForm((f) => ({ ...f, [key]: val }));

  const updateMutation = useMutation({
    mutationFn: (data) => usersAPI.updateProfile(data),
    onSuccess: async () => {
      if (refreshUser) await refreshUser();
      toast.success('Perfil atualizado com sucesso!');
      setEditing(false);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar perfil');
    },
  });

  // Estrutura canónica (labels de cargo). Estática — cache longo.
  const { data: structure } = useQuery({
    queryKey: queryKeys.governance.structure(),
    queryFn: async () => (await governanceAPI.structure()).data,
    staleTime: 60 * 60 * 1000,
  });

  const loading = updateMutation.isPending;
  const handleSave = () => {
    if (!form.name.trim()) {
      toast.error('O nome não pode ficar vazio.');
      return;
    }
    updateMutation.mutate(form);
  };
  const handleCancel = () => {
    if (user) {
      setForm({
        ...EMPTY_FORM,
        ...Object.fromEntries(Object.keys(EMPTY_FORM).map((k) => [k, user[k] || ''])),
      });
    }
    setEditing(false);
  };

  if (!user) return null;

  // Suspensão de direitos disciplinar ainda vigente?
  const suspendedUntil = user.rights_suspended_until;
  const rightsSuspended = !!suspendedUntil && new Date(suspendedUntil) > new Date();

  return (
    <div className="max-w-3xl mx-auto space-y-6" data-testid="profile-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="profile-title">Meu Perfil</h1>
          <p className="text-sm text-[#6B7280] mt-1">
            Podes editar os teus dados pessoais, de contacto e profissionais. O email e os
            dados da associação são geridos pela administração.
          </p>
        </div>
        {!editing ? (
          <button
            onClick={() => setEditing(true)}
            className="inline-flex items-center gap-2 text-sm font-semibold text-carmesim hover:text-carmesim-dark transition-colors"
            data-testid="edit-profile-btn"
          >
            <Pencil className="w-4 h-4" />
            Editar
          </button>
        ) : (
          <button
            onClick={handleCancel}
            className="inline-flex items-center gap-2 text-sm font-semibold text-[#6B7280] hover:text-grafite transition-colors"
            data-testid="cancel-edit-btn"
          >
            <X className="w-4 h-4" />
            Cancelar
          </button>
        )}
      </div>

      <ProfileCard
        user={user}
        structure={structure}
        refreshUser={refreshUser}
        cropSrc={cropSrc}
        setCropSrc={setCropSrc}
      />

      {rightsSuspended && (
        <RightsSuspendedBanner
          suspendedUntil={suspendedUntil}
          reason={user.rights_suspension_reason}
        />
      )}

      {editing && (
        <EditForm form={form} set={set} onSave={handleSave} loading={loading} />
      )}

      <DetailsGrid user={user} structure={structure} />

      <PrivilegesSection privileges={user.privileges} />

      <EmailPrefs user={user} refreshUser={refreshUser} />

      <PushPrefs />

      <MeusCargosSection userId={user.id} structure={structure} />
    </div>
  );
};
