import React, { useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Camera, Trash2 } from 'lucide-react';
import { UserAvatar } from '../../../components/UserAvatar';
import { AvatarCropDialog } from '../../../components/AvatarCropDialog';
import { usersAPI, uploadAPI } from '../../../utils/api';
import {
  USER_STATUS_CONFIG, USER_STATUS_FALLBACK, getStatusConfig,
} from '../../../lib/statusConfig';
import { cargoLabelFrom } from '../../../lib/governanceLabels';
import { ROLE_LABEL } from './tokens';

export const ProfileCard = ({ user, structure, refreshUser, cropSrc, setCropSrc }) => {
  const fileInputRef = useRef(null);

  const photoMutation = useMutation({
    mutationFn: async (file) => {
      const up = await uploadAPI.uploadFile('avatars', file);
      await usersAPI.updateProfile({ photo_url: up.data.file_url });
    },
    onSuccess: async () => {
      if (refreshUser) await refreshUser();
      setCropSrc(null);
      toast.success('Foto de perfil atualizada!');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar a foto.');
    },
  });

  const removePhotoMutation = useMutation({
    mutationFn: () => usersAPI.updateProfile({ photo_url: '' }),
    onSuccess: async () => {
      if (refreshUser) await refreshUser();
      toast.success('Foto removida.');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Erro ao remover a foto.');
    },
  });

  const onFilePicked = (e) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // permite re-selecionar o mesmo ficheiro
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      toast.error('Formato inválido. Use JPG ou PNG.');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      toast.error('A imagem excede o limite de 2 MB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setCropSrc(reader.result);
    reader.readAsDataURL(file);
  };

  const onCropConfirmed = (blob) => {
    photoMutation.mutate(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }));
  };

  const statusCfg = getStatusConfig(USER_STATUS_CONFIG, user.status, USER_STATUS_FALLBACK);
  const StatusIcon = statusCfg.icon;
  const cargoNome = cargoLabelFrom(structure, user.cargo);
  const isSocioBase = !user.cargo || user.cargo === 'socio';

  return (
    <>
      <AvatarCropDialog
        open={!!cropSrc}
        imageSrc={cropSrc}
        onCancel={() => setCropSrc(null)}
        onConfirm={onCropConfirmed}
        pending={photoMutation.isPending}
      />

      <div className="card-technical overflow-hidden animate-fade-up">
        {/* Banner */}
        <div className="h-20 bg-gradient-to-r from-grafite to-grafite/80 relative">
          <div className="absolute -bottom-8 left-6">
            <div className="relative">
              <UserAvatar
                size="lg"
                name={user.name}
                photoUrl={user.photo_url}
                className="rounded-xl border-4 border-white shadow-lg"
                fallbackClassName="rounded-xl"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={photoMutation.isPending || user.status !== 'ativo'}
                aria-label="Alterar foto de perfil"
                className="absolute -bottom-1 -right-1 p-1.5 rounded-full bg-floresta text-white shadow-md hover:bg-floresta-dark transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50"
                data-testid="change-photo-btn"
              >
                <Camera className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png"
                onChange={onFilePicked}
                className="hidden"
                data-testid="photo-file-input"
              />
            </div>
          </div>
        </div>

        <div className="pt-12 px-6 pb-6">
          {user.photo_url && (
            <div className="flex justify-end -mt-4 mb-2">
              <button
                type="button"
                onClick={() => removePhotoMutation.mutate()}
                disabled={removePhotoMutation.isPending}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#6B7280] hover:text-carmesim transition-colors disabled:opacity-50"
                data-testid="remove-photo-btn"
              >
                <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                Remover foto
              </button>
            </div>
          )}
          {/* Name + badges */}
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-grafite" data-testid="profile-name">{user.name}</h2>
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider ${statusCfg.className}`}>
              <StatusIcon className="w-3 h-3" aria-hidden="true" />
              {user.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-1">{ROLE_LABEL[user.role] || user.role}</p>
          {!isSocioBase && (
            <p className="text-xs text-carmesim font-semibold">{cargoNome}</p>
          )}
        </div>
      </div>
    </>
  );
};
