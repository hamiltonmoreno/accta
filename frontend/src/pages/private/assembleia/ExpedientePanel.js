import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { EXPEDIENTE_TIPO_LABELS } from '../../../lib/governanceLabels';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Input } from '../../../components/ui/input';
import { fieldCls, labelCls } from './tokens';

export const ExpedientePanel = ({ assembleia, snapshot, isMesa }) => {
  const qc = useQueryClient();
  const [tipo, setTipo] = useState('correspondencia');
  const [texto, setTexto] = useState('');
  const [aclamacao, setAclamacao] = useState(true);

  const { data: entries = [], refetch } = useQuery({
    queryKey: ['assembleia', assembleia.id, 'expediente'],
    queryFn: async () => (await assembleiasAPI.expediente(assembleia.id)).data.expediente || [],
    staleTime: 10000,
  });
  const ver = snapshot?.version;
  useEffect(() => { if (ver != null) refetch(); }, [ver, refetch]);

  const addMut = useMutation({
    mutationFn: (data) => assembleiasAPI.addExpediente(assembleia.id, data),
    onSuccess: () => {
      toast.success('Expediente registado');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id, 'expediente'] });
      setTexto('');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro'),
  });

  return (
    <div className="space-y-4">
      {entries.length === 0 ? (
        <p className="text-sm text-[#6B7280] italic">Sem expediente registado.</p>
      ) : (
        <ul className="divide-y divide-[#E5E7EB] border border-[#E5E7EB] rounded-md">
          {entries.map((e) => (
            <li key={e.id} className="px-3 py-2 text-sm">
              <span className="inline-block text-xs px-1.5 py-0.5 rounded bg-[#F5F5F5] text-[#6B7280] border border-[#E5E7EB] mr-2">
                {EXPEDIENTE_TIPO_LABELS[e.tipo] || e.tipo}
              </span>
              {e.aprovado_por_aclamacao && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F0FDF4] text-[#15803D] border border-[#BBF7D0] mr-2">
                  por aclamação
                </span>
              )}
              <span className="text-[#3A3A3A]">{e.texto}</span>
            </li>
          ))}
        </ul>
      )}

      {isMesa && (
        <form
          className="space-y-2 pt-3 border-t border-[#E5E7EB]"
          onSubmit={(ev) => {
            ev.preventDefault();
            const payload = { tipo, texto };
            if (tipo !== 'correspondencia') payload.aprovado_por_aclamacao = aclamacao;
            addMut.mutate(payload);
          }}
        >
          <p className="text-xs font-medium text-[#6B7280]">Registar (Mesa)</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="sm:col-span-1">
              <label className={labelCls} htmlFor="exp-tipo">Tipo</label>
              <select id="exp-tipo" className={fieldCls} value={tipo} onChange={(ev) => setTipo(ev.target.value)}>
                {Object.entries(EXPEDIENTE_TIPO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className={labelCls} htmlFor="exp-texto">Texto</label>
              <Input id="exp-texto" className={fieldCls} required minLength={1} value={texto} onChange={(ev) => setTexto(ev.target.value)} />
            </div>
          </div>
          {tipo !== 'correspondencia' && (
            <label className="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={aclamacao} onChange={(ev) => setAclamacao(ev.target.checked)} />
              Aprovado por aclamação
            </label>
          )}
          <button type="submit" className={primaryBtn} disabled={addMut.isPending}>
            Registar
          </button>
        </form>
      )}
    </div>
  );
};
