import React, { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bannersAPI, uploadAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { Image as ImageIcon, Upload, Star, Save } from 'lucide-react';
import { Skeleton } from '../../components/ui/skeleton';

// Rótulos legíveis por chave de banner (apresentação; a lista canónica vem do backend).
const PAGE_LABELS = {
  home: 'Início', sobre: 'Sobre', profissao: 'Profissão', contactos: 'Contactos',
  beneficios: 'Benefícios', transparencia: 'Transparência', galeria: 'Galeria',
  eventos: 'Eventos', noticias: 'Notícias', validador: 'Validador',
};

const BannerCard = ({ bkey, info, onUpload, onSaveAlt, uploading, savingAlt }) => {
  const fileRef = useRef(null);
  const [alt, setAlt] = useState(info.alt || '');

  return (
    <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm overflow-hidden" data-testid={`banner-card-${bkey}`}>
      <div className="relative h-36 bg-[#F5F5F5]">
        {info.image_url ? (
          <img src={info.image_url} alt={`Pré-visualização: ${PAGE_LABELS[bkey] || bkey}`} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-[#9CA3AF]">
            <ImageIcon className="w-8 h-8" aria-hidden="true" />
          </div>
        )}
        {info.is_home && (
          <span className="absolute top-2 left-2 inline-flex items-center gap-1 px-2 py-1 rounded-full bg-grafite/80 text-white text-[11px] font-semibold">
            <Star className="w-3 h-3" aria-hidden="true" /> Banner principal
          </span>
        )}
      </div>

      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-grafite">{PAGE_LABELS[bkey] || bkey}</h3>
          {info.is_default && <span className="text-xs text-[#6B7280]">imagem por defeito</span>}
        </div>

        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(bkey, f);
            e.target.value = '';
          }}
          data-testid={`banner-file-${bkey}`}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50"
          data-testid={`banner-replace-${bkey}`}
        >
          <Upload className="w-4 h-4" aria-hidden="true" />
          {uploading ? 'A enviar...' : 'Substituir imagem'}
        </button>

        <div>
          <label className="block text-xs font-medium text-[#6B7280] mb-1">Texto alternativo (acessibilidade)</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={alt}
              maxLength={300}
              onChange={(e) => setAlt(e.target.value)}
              placeholder="Descreva a imagem…"
              className="flex-1 border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
            />
            <button
              type="button"
              onClick={() => onSaveAlt(bkey, alt)}
              disabled={savingAlt || alt === (info.alt || '')}
              className="inline-flex items-center gap-1 px-3 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50"
              data-testid={`banner-alt-save-${bkey}`}
            >
              <Save className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const AdminBannersPage = () => {
  const qc = useQueryClient();
  const [busyKey, setBusyKey] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.banners.all(),
    queryFn: async () => (await bannersAPI.getAll()).data,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: queryKeys.banners.all() });
    qc.invalidateQueries({ queryKey: queryKeys.banners.public() });
  };

  const updateMutation = useMutation({
    mutationFn: ({ key, payload }) => bannersAPI.update(key, payload),
    onSuccess: () => { toast.success('Banner atualizado.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao atualizar o banner'),
    onSettled: () => setBusyKey(null),
  });

  const handleUpload = async (key, file) => {
    setBusyKey(key);
    try {
      const res = await uploadAPI.uploadFile('banners', file);
      updateMutation.mutate({ key, payload: { image_url: res.data.file_url } });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao enviar a imagem');
      setBusyKey(null);
    }
  };

  const handleSaveAlt = (key, alt) => {
    setBusyKey(key);
    updateMutation.mutate({ key, payload: { alt } });
  };

  const banners = data?.banners || {};
  const keys = data?.keys || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
          <ImageIcon className="w-5 h-5 text-carmesim" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-grafite">Banners das Páginas</h1>
          <p className="text-sm text-[#6B7280]">
            Substitua a imagem de cada banner público. Recomendado ~1600×500px (16:5).
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-64 w-full rounded-lg" />)}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {keys.map((k) => (
            <BannerCard
              key={k}
              bkey={k}
              info={banners[k] || {}}
              onUpload={handleUpload}
              onSaveAlt={handleSaveAlt}
              uploading={busyKey === k && updateMutation.isPending}
              savingAlt={busyKey === k && updateMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminBannersPage;
