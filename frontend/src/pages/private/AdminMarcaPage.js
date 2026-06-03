import React, { useRef, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { brandAPI, uploadAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { BrandLogo } from '../../components/BrandLogo';
import { toast } from 'sonner';
import { Palette, Upload, RotateCcw, Save } from 'lucide-react';
import { Skeleton } from '../../components/ui/skeleton';

const LogoSlot = ({ label, hint, field, url, dark, onUpload, onReset, busy }) => {
  const fileRef = useRef(null);
  return (
    <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 space-y-3" data-testid={`logo-slot-${field}`}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-grafite">{label}</h3>
        {!url && <span className="text-xs text-[#6B7280]">SVG por defeito</span>}
      </div>
      {/* Preview no fundo correspondente (claro / grafite) para validar legibilidade. */}
      <div className={`h-24 rounded-md flex items-center justify-center px-4 ${dark ? 'bg-grafite' : 'bg-white border border-[#E5E7EB]'}`}>
        {url ? (
          <img src={url} alt={`Logótipo (${label})`} className="max-h-16 max-w-[200px] object-contain" />
        ) : (
          <BrandLogo dark={dark} className="h-9" />
        )}
      </div>
      <p className="text-xs text-[#6B7280]">{hint}</p>
      <input
        ref={fileRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onUpload(field, f);
          e.target.value = '';
        }}
        data-testid={`logo-file-${field}`}
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          className="flex-1 inline-flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50"
          data-testid={`logo-replace-${field}`}
        >
          <Upload className="w-4 h-4" aria-hidden="true" />
          {busy ? 'A enviar...' : 'Substituir'}
        </button>
        {url && (
          <button
            type="button"
            onClick={() => onReset(field)}
            disabled={busy}
            className="inline-flex items-center gap-1 px-3 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50"
            data-testid={`logo-reset-${field}`}
            title="Repor o logótipo por defeito (SVG)"
          >
            <RotateCcw className="w-4 h-4" aria-hidden="true" /> Repor
          </button>
        )}
      </div>
    </div>
  );
};

export const AdminMarcaPage = ({ embedded = false }) => {
  const qc = useQueryClient();
  const [busyField, setBusyField] = useState(null);
  const [alt, setAlt] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.brand.all(),
    queryFn: async () => (await brandAPI.getAll()).data,
  });

  useEffect(() => {
    if (data?.alt) setAlt(data.alt);
  }, [data?.alt]);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: queryKeys.brand.all() });
    qc.invalidateQueries({ queryKey: queryKeys.brand.public() });
  };

  const updateMutation = useMutation({
    mutationFn: (payload) => brandAPI.update(payload),
    onSuccess: () => { toast.success('Marca atualizada.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao atualizar a marca'),
    onSettled: () => setBusyField(null),
  });

  const handleUpload = async (field, file) => {
    setBusyField(field);
    try {
      const res = await uploadAPI.uploadFile('brand', file);
      updateMutation.mutate({ [field]: res.data.file_url });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao enviar a imagem');
      setBusyField(null);
    }
  };

  const handleReset = (field) => {
    setBusyField(field);
    updateMutation.mutate({ [field]: '' }); // "" repõe o default (SVG)
  };

  return (
    <div className="space-y-6">
      {!embedded && (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
            <Palette className="w-5 h-5 text-carmesim" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-grafite">Marca / Logótipo</h1>
            <p className="text-sm text-[#6B7280]">
              Carregue o logótipo do portal. Recomendado PNG transparente ~360×72px. Sem upload, usa-se o logótipo vetorial por defeito.
            </p>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="grid sm:grid-cols-2 gap-4">
          {[...Array(2)].map((_, i) => <Skeleton key={i} className="h-56 w-full rounded-lg" />)}
        </div>
      ) : (
        <>
          <div className="grid sm:grid-cols-2 gap-4">
            <LogoSlot
              label="Fundo claro"
              hint="Usado no cabeçalho, ecrãs de autenticação e barra lateral."
              field="logo_light_url"
              url={data?.logo_light_url}
              dark={false}
              onUpload={handleUpload}
              onReset={handleReset}
              busy={busyField === 'logo_light_url' && updateMutation.isPending}
            />
            <LogoSlot
              label="Fundo escuro"
              hint="Usado no rodapé e no painel escuro do login."
              field="logo_dark_url"
              url={data?.logo_dark_url}
              dark
              onUpload={handleUpload}
              onReset={handleReset}
              busy={busyField === 'logo_dark_url' && updateMutation.isPending}
            />
          </div>

          {/* Texto alternativo */}
          <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4">
            <label className="block text-xs font-medium text-[#6B7280] mb-1">Texto alternativo do logótipo</label>
            <div className="flex gap-2 max-w-md">
              <input
                type="text"
                value={alt}
                maxLength={200}
                onChange={(e) => setAlt(e.target.value)}
                placeholder="ACCTA Cabo Verde"
                className="flex-1 border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                data-testid="brand-alt-input"
              />
              <button
                type="button"
                onClick={() => { setBusyField('alt'); updateMutation.mutate({ alt: alt || 'ACCTA Cabo Verde' }); }}
                disabled={updateMutation.isPending || alt === (data?.alt || '')}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50"
                data-testid="brand-alt-save"
              >
                <Save className="w-4 h-4" aria-hidden="true" /> Guardar
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminMarcaPage;
