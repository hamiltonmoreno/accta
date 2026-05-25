import React, { useState, useEffect, useCallback } from 'react';
import QRCode from 'react-qr-code';
import {
  Loader2, Copy, Check, Download, ShieldCheck, AlertTriangle,
  ArrowRight, ArrowLeft, KeyRound,
} from 'lucide-react';
import { toast } from 'sonner';
import { mfaAPI } from '../utils/api';
import { InputOTP, InputOTPGroup, InputOTPSlot } from './ui/input-otp';
import { Checkbox } from './ui/checkbox';
import { Alert, AlertDescription } from './ui/alert';

// Wizard de ativação de MFA (spec-mfa-frontend-pr2 §4). Agnóstico do contentor
// (Dialog no Perfil, página cheia no enrolment obrigatório). Dá UI ao que o
// backend já impõe — não decide políticas. `onComplete` é chamado depois de o
// utilizador confirmar que guardou os códigos de recuperação.
//
// Neutral-led + Carmesim como acento único: ≤1 botão primário (o de avanço) por
// passo; restantes neutros.
const btnPrimary =
  'inline-flex items-center justify-center gap-2 h-11 px-5 rounded-lg bg-carmesim text-white ' +
  'hover:bg-carmesim-dark font-semibold text-sm transition-colors disabled:opacity-50 ' +
  'disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 ' +
  'focus-visible:ring-offset-2 outline-none';
const btnSecondary =
  'inline-flex items-center justify-center gap-2 h-11 px-5 rounded-lg border border-[#D1D5DB] ' +
  'text-grafite hover:bg-gray-50 font-semibold text-sm transition-colors disabled:opacity-50 ' +
  'focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none';

// Cópia para clipboard com feedback efémero (ícone muda para Check ~1.5s).
const useCopy = () => {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(async (text, msg = 'Copiado') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success(msg);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error('Não foi possível copiar');
    }
  }, []);
  return { copied, copy };
};

export const SetupMFA = ({ onComplete }) => {
  const [step, setStep] = useState('qr'); // 'qr' | 'confirm' | 'backup'

  // Passo qr
  const [setupData, setSetupData] = useState(null); // { secret, otpauth_uri }
  const [setupLoading, setSetupLoading] = useState(true);
  const [setupError, setSetupError] = useState(false);
  const secretCopy = useCopy();

  // Passo confirm
  const [otp, setOtp] = useState('');
  const [verifying, setVerifying] = useState(false);

  // Passo backup
  const [backupCodes, setBackupCodes] = useState([]);
  const [acknowledged, setAcknowledged] = useState(false);
  const backupCopy = useCopy();

  const initSetup = useCallback(async () => {
    setSetupLoading(true);
    setSetupError(false);
    try {
      const res = await mfaAPI.setup();
      setSetupData(res.data);
    } catch {
      setSetupError(true);
      toast.error('Não foi possível iniciar a configuração. Tente novamente.');
    } finally {
      setSetupLoading(false);
    }
  }, []);

  useEffect(() => {
    initSetup();
  }, [initSetup]);

  const handleVerify = async () => {
    if (otp.length !== 6) return;
    setVerifying(true);
    try {
      const res = await mfaAPI.verify(otp);
      setBackupCodes(res.data.backup_codes || []);
      setStep('backup');
    } catch {
      toast.error('Código inválido');
      setOtp('');
    } finally {
      setVerifying(false);
    }
  };

  const downloadCodes = () => {
    const content =
      'ACCTA — Códigos de recuperação MFA\n' +
      'Guarde estes códigos num local seguro. Cada um só pode ser usado uma vez.\n\n' +
      backupCodes.join('\n') + '\n';
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'accta-mfa-backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  // ---- Passo: QR ----------------------------------------------------------
  if (step === 'qr') {
    return (
      <div className="space-y-5" data-testid="mfa-step-qr">
        <p className="text-sm text-[#6B7280]">
          Use uma app de autenticação (Google Authenticator, Authy, Microsoft
          Authenticator…) para ler o código QR. Depois introduza o código de 6 dígitos
          gerado.
        </p>

        {setupLoading ? (
          <div className="flex items-center justify-center py-10 text-[#6B7280]" role="status" aria-live="polite">
            <Loader2 className="w-6 h-6 animate-spin" aria-hidden="true" />
            <span className="sr-only">A gerar o código…</span>
          </div>
        ) : setupError ? (
          <div className="text-center py-6">
            <button type="button" onClick={initSetup} className={btnSecondary}>
              Tentar novamente
            </button>
          </div>
        ) : (
          <>
            <div className="flex justify-center">
              <div className="p-4 bg-white border border-gray-200 rounded-xl">
                <QRCode value={setupData.otpauth_uri} size={176} />
              </div>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-widest text-[#6B7280] mb-2 font-semibold">
                Ou introduza esta chave manualmente
              </label>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-[#F5F5F5] border border-gray-200 rounded-lg text-sm font-mono text-grafite break-all">
                  {setupData.secret}
                </code>
                <button
                  type="button"
                  onClick={() => secretCopy.copy(setupData.secret, 'Chave copiada')}
                  className={btnSecondary + ' h-10 px-3'}
                  aria-label="Copiar chave"
                >
                  {secretCopy.copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button type="button" onClick={() => setStep('confirm')} className={btnPrimary}>
                Continuar
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  // ---- Passo: confirmar OTP ----------------------------------------------
  if (step === 'confirm') {
    return (
      <div className="space-y-5" data-testid="mfa-step-confirm">
        <p className="text-sm text-[#6B7280]">
          Introduza o código de 6 dígitos apresentado na sua app de autenticação.
        </p>

        <div className="flex justify-center">
          <InputOTP
            maxLength={6}
            value={otp}
            onChange={setOtp}
            inputMode="numeric"
            autoFocus
            data-testid="mfa-otp-input"
          >
            <InputOTPGroup>
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <InputOTPSlot key={i} index={i} className="h-11 w-11 text-base" />
              ))}
            </InputOTPGroup>
          </InputOTP>
        </div>

        <div className="flex items-center justify-between pt-1">
          <button
            type="button"
            onClick={() => { setStep('qr'); setOtp(''); }}
            className={btnSecondary}
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </button>
          <button
            type="button"
            onClick={handleVerify}
            disabled={otp.length !== 6 || verifying}
            className={btnPrimary}
            data-testid="mfa-verify-btn"
          >
            {verifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
            Ativar
          </button>
        </div>
      </div>
    );
  }

  // ---- Passo: códigos de recuperação -------------------------------------
  return (
    <div className="space-y-5" data-testid="mfa-step-backup">
      <Alert className="border-[#D97706]/40 bg-[#FFFBEB]">
        <AlertTriangle className="h-4 w-4 text-[#B45309]" />
        <AlertDescription className="text-[#B45309]">
          Guarde estes códigos num local seguro. <strong>Não voltarão a ser mostrados.</strong>{' '}
          Cada código permite entrar uma vez caso perca o acesso à app de autenticação.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-2 gap-2" data-testid="mfa-backup-codes">
        {backupCodes.map((code) => (
          <code
            key={code}
            className="px-3 py-2 bg-[#F5F5F5] border border-gray-200 rounded-lg text-sm font-mono text-grafite text-center tracking-wider"
          >
            {code}
          </code>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => backupCopy.copy(backupCodes.join('\n'), 'Códigos copiados')}
          className={btnSecondary}
        >
          {backupCopy.copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          Copiar todos
        </button>
        <button type="button" onClick={downloadCodes} className={btnSecondary}>
          <Download className="w-4 h-4" />
          Descarregar (.txt)
        </button>
      </div>

      <label className="flex items-start gap-3 cursor-pointer select-none">
        <Checkbox
          checked={acknowledged}
          onCheckedChange={(v) => setAcknowledged(v === true)}
          className="mt-0.5"
          data-testid="mfa-ack-checkbox"
        />
        <span className="text-sm text-grafite">Guardei os meus códigos de recuperação</span>
      </label>

      <div className="flex justify-end pt-1">
        <button
          type="button"
          onClick={onComplete}
          disabled={!acknowledged}
          className={btnPrimary}
          data-testid="mfa-finish-btn"
        >
          <KeyRound className="w-4 h-4" />
          Concluir
        </button>
      </div>
    </div>
  );
};

export default SetupMFA;
