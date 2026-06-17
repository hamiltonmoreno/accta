import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { Input } from '../../../components/ui/input';
import { secondaryBtn, fieldCls, labelCls } from './tokens';

export const DocumentosPanel = ({ assembleia, isMesa }) => {
  const qc = useQueryClient();
  const [docId, setDocId] = useState('');

  const { data: docs = [] } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'documentos'],
    queryFn: async () => (await assembleiasAPI.documentos(assembleia.id)).data.documentos || [],
    staleTime: 30000,
  });

  const anexarMut = useMutation({
    mutationFn: (document_id) => assembleiasAPI.anexarDocumento(assembleia.id, { document_id }),
    onSuccess: (res) => {
      if (res.data.tardio) {
        toast.warning('Documento anexado (tardio — <3 dias antes da sessão)');
      } else {
        toast.success('Documento anexado');
      }
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'documentos'] });
      setDocId('');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  return (
    <div className="space-y-3">
      {docs.length === 0 ? (
        <p className="text-sm text-[#6B7280] italic">Sem documentos anexados.</p>
      ) : (
        <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
          {docs.map((d) => (
            <li key={d.id} className="px-3 py-2 text-sm flex items-center justify-between">
              <span className="inline-flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-[#6B7280]" />
                {d.title || d.id}
              </span>
              {d.file_url && (
                <a href={d.file_url} target="_blank" rel="noopener noreferrer" className="text-xs text-carmesim hover:underline inline-flex items-center gap-1">
                  Abrir <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </li>
          ))}
        </ul>
      )}

      {isMesa && (
        <div className="flex flex-wrap items-end gap-2 pt-2 border-t border-[#E5E7EB]">
          <div className="flex-1 min-w-[220px]">
            <label className={labelCls} htmlFor="doc-id">document_id existente</label>
            <Input
              id="doc-id"
              className={fieldCls}
              placeholder="UUID do documento já carregado"
              value={docId}
              onChange={(e) => setDocId(e.target.value)}
            />
          </div>
          <button
            type="button"
            className={secondaryBtn}
            disabled={!docId || anexarMut.isPending}
            onClick={() => anexarMut.mutate(docId.trim())}
          >
            Anexar
          </button>
          <p className="w-full text-xs text-[#6B7280]">
            Anexar com <strong>&lt;3 dias</strong> de antecedência fica marcado como tardio (Art. 20).
            Upload integrado de ficheiros — futuro.
          </p>
        </div>
      )}
    </div>
  );
};
