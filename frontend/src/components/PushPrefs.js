import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { BellRing, Share } from 'lucide-react';
import { Switch } from './ui/switch';
import {
  isPushSupported,
  getIosNeedsInstall,
  getExistingSubscription,
  subscribeToPush,
  unsubscribeFromPush,
} from '../utils/push';

// Toggle de notificações push no celular (Web Push / PWA). Vive no Perfil, ao
// lado das preferências de email. A ativação exige um clique do utilizador
// (o browser não permite pedir permissão sem gesto).
export const PushPrefs = () => {
  const supported = isPushSupported();
  const iosNeedsInstall = supported && getIosNeedsInstall();

  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    if (!supported) {
      setReady(true);
      return undefined;
    }
    getExistingSubscription()
      .then((sub) => {
        if (active) setEnabled(Boolean(sub) && Notification.permission === 'granted');
      })
      .finally(() => active && setReady(true));
    return () => {
      active = false;
    };
  }, [supported]);

  // Dispositivo sem suporte (ex.: browser antigo): não mostra o card.
  if (!supported) return null;

  const handleToggle = async (checked) => {
    setBusy(true);
    try {
      if (checked) {
        await subscribeToPush();
        setEnabled(true);
        toast.success('Notificações no celular ativadas.');
      } else {
        await unsubscribeFromPush();
        setEnabled(false);
        toast.success('Notificações no celular desativadas.');
      }
    } catch (err) {
      setEnabled(false);
      toast.error(err?.message || 'Não foi possível alterar as notificações.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card-technical p-5 animate-fade-up" data-testid="push-prefs-section">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">
        <BellRing className="w-3 h-3 inline mr-1" aria-hidden="true" /> Notificações no Celular
      </h3>

      {iosNeedsInstall ? (
        <div className="flex items-start gap-3 text-sm text-grafite" data-testid="push-ios-hint">
          <Share className="w-4 h-4 mt-0.5 flex-shrink-0 text-[#6B7280]" aria-hidden="true" />
          <p>
            No iPhone, para receber notificações: toque em <strong>Partilhar</strong> e escolha{' '}
            <strong>Adicionar à Tela de Início</strong>. Depois abra a app por esse ícone e ative aqui.
          </p>
        </div>
      ) : (
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <label htmlFor="push-opt" className="text-sm font-medium text-grafite block">
              Receber notificações neste dispositivo
            </label>
            <p className="text-xs text-[#6B7280] mt-1">
              Avisos (comunicados, finanças, eventos, votações) chegam à tela mesmo com a app fechada.
            </p>
          </div>
          <Switch
            id="push-opt"
            checked={enabled}
            disabled={busy || !ready}
            onCheckedChange={handleToggle}
            data-testid="push-opt-switch"
          />
        </div>
      )}
    </div>
  );
};
