import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { assembleiasAPI } from '../../../utils/api';
import { primaryBtn } from '../../../lib/buttonStyles';
import { Input } from '../../../components/ui/input';
import { secondaryBtn, fieldCls, labelCls } from './tokens';

export const CheckinParticipantePanel = ({ assembleia, presente, refetchAssemb }) => {
  const qc = useQueryClient();
  const [code, setCode] = useState('');

  const checkinMut = useMutation({
    mutationFn: (data) => assembleiasAPI.checkin(assembleia.id, data),
    onSuccess: () => {
      toast.success('Presença registada');
      qc.invalidateQueries({ queryKey: ['assembleia', assembleia.id] });
      refetchAssemb?.();
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Não foi possível registar presença'),
  });

  if (presente) {
    return (
      <div className="rounded-md bg-[#F0FDF4] border border-[#BBF7D0] px-3 py-2 text-sm text-[#15803D] inline-flex items-center gap-2">
        <CheckCircle2 className="w-4 h-4" />
        Presente nesta sessão.
      </div>
    );
  }

  const meeting = assembleia.meeting_link;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {meeting ? (
          <button
            type="button"
            className={primaryBtn}
            disabled={checkinMut.isPending}
            onClick={async () => {
              await checkinMut.mutateAsync({ method: 'join_click' });
              window.open(meeting, '_blank', 'noopener');
            }}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Entrar na reunião
          </button>
        ) : (
          <button
            type="button"
            className={primaryBtn}
            disabled={checkinMut.isPending}
            onClick={() => checkinMut.mutate({ method: 'join_click' })}
          >
            Registar presença
          </button>
        )}
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex-1 min-w-[160px]">
          <label className={labelCls} htmlFor="checkin-code">Código de sessão (opcional)</label>
          <Input
            id="checkin-code"
            className={fieldCls}
            placeholder="ABC123"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            maxLength={8}
          />
        </div>
        <button
          type="button"
          className={secondaryBtn}
          disabled={!code || checkinMut.isPending}
          onClick={() => checkinMut.mutate({ method: 'self_code', code: code.trim() })}
        >
          Confirmar com código
        </button>
      </div>
    </div>
  );
};
