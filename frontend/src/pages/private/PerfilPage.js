import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { usersAPI, cargosAPI, governanceAPI, comunicadosAPI, mfaAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { Switch } from '../../components/ui/switch';
import { SetupMFA } from '../../components/SetupMFA';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '../../components/ui/dialog';
import { PRIVILEGE_LABELS, cargoLabelFrom, memberCategoryLabel } from '../../lib/governanceLabels';
import { toast } from 'sonner';
import {
  Mail, Phone, Shield, Award, FileText, Calendar, Save, Briefcase, Hash,
  Pencil, X, History, AlertTriangle, Users as UsersIcon, Cake, Droplet,
  MapPin, Home, Globe, HeartPulse, Building2, BadgeCheck, Clock,
  CheckCircle2, Fingerprint, User as UserIcon, ShieldCheck, Lock, Loader2,
} from 'lucide-react';
import {
  USER_STATUS_CONFIG, USER_STATUS_FALLBACK, getStatusConfig,
} from '../../lib/statusConfig';

// Datas só-com-dia ("AAAA-MM-DD") têm de ser interpretadas no fuso LOCAL:
// `new Date("2027-01-31")` é meia-noite UTC e, num fuso a oeste (Cabo Verde =
// UTC-1), recua para o dia anterior. Construímos a partir dos componentes para
// evitar o desvio de um dia em datas/contagens. Datas-hora completas (ISO com
// 'T') também passam pela porção de data, o que é o pretendido para exibição.
const toLocalDate = (value) => {
  if (!value) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
  const d = m
    ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
    : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
};

const formatDate = (iso) => {
  const d = toLocalDate(iso);
  return d ? d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' }) : null;
};

// Idade a partir da data de nascimento (AAAA-MM-DD). Devolve null se inválida.
const calcAge = (dob) => {
  const d = toLocalDate(dob);
  if (!d) return null;
  const now = new Date();
  let age = now.getFullYear() - d.getFullYear();
  const m = now.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age -= 1;
  return age >= 0 && age < 130 ? age : null;
};

const BLOOD_TYPE_OPTIONS = [
  { value: '', label: '—' },
  ...['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((t) => ({ value: t, label: t })),
];

const GENDER_OPTIONS = [
  { value: '', label: '—' },
  { value: 'Feminino', label: 'Feminino' },
  { value: 'Masculino', label: 'Masculino' },
  { value: 'Outro', label: 'Outro' },
  { value: 'Prefiro não indicar', label: 'Prefiro não indicar' },
];

const labelCls = 'block text-xs uppercase tracking-widest text-gray-500 font-semibold mb-1';
const inputCls =
  'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none';
// Botões: Carmesim como acento único (1 primário por contexto); restantes neutros.
const btnPrimaryCls =
  'inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-carmesim text-white ' +
  'hover:bg-carmesim-dark font-semibold text-sm transition-colors disabled:opacity-50 ' +
  'disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none';
const btnSecondaryCls =
  'inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg border border-[#D1D5DB] ' +
  'text-grafite hover:bg-gray-50 font-semibold text-sm transition-colors disabled:opacity-50 ' +
  'focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 outline-none';

const FormInput = ({ id, testId, label, value, onChange, type = 'text', placeholder, max }) => (
  <div>
    <label htmlFor={id} className={labelCls}>{label}</label>
    <input
      id={id}
      type={type}
      value={value}
      maxLength={max}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={inputCls}
      data-testid={testId || id}
    />
  </div>
);

const FormSelect = ({ id, label, value, onChange, options }) => (
  <div>
    <label htmlFor={id} className={labelCls}>{label}</label>
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={inputCls} data-testid={id}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  </div>
);

// Timeline só-leitura do percurso do próprio sócio na associação. Mostra o
// label do cargo (a key canónica é interna), com marcação de suplente.
const MeusCargosSection = ({ userId, structure }) => {
  const { data: history = [] } = useQuery({
    queryKey: queryKeys.cargos.history(userId),
    queryFn: async () => (await cargosAPI.history(userId)).data.cargo_history,
    enabled: !!userId,
  });
  if (history.length === 0) return null;
  return (
    <div className="card-technical p-5 animate-fade-up">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">
        <History className="w-3 h-3 inline mr-1" aria-hidden="true" /> Os Meus Cargos e Mandatos
      </h3>
      <ul className="space-y-2" data-testid="meus-cargos-timeline">
        {history.map((m) => (
          <li key={m.id || `${m.cargo}-${m.inicio}`} className="flex items-center justify-between text-sm">
            <span className="text-grafite font-medium">
              {m.label || cargoLabelFrom(structure, m.cargo)}
              {m.suplente && <span className="ml-1.5 text-xs text-[#6B7280]">(suplente)</span>}
            </span>
            <span className="font-mono text-xs text-[#6B7280]">
              {formatDate(m.inicio) || '—'} → {m.fim ? formatDate(m.fim) : 'presente'}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

const PrivilegesSection = ({ privileges }) => {
  if (!privileges || privileges.length === 0) return null;

  return (
    <div className="card-technical p-5 animate-fade-up">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Privilégios Atribuídos</h3>
      <div className="flex flex-wrap gap-2">
        {privileges.map((p) => (
          <span key={p} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-carmesim/10 text-carmesim text-xs font-semibold rounded-lg">
            <Shield className="w-3 h-3" />
            {PRIVILEGE_LABELS[p] || p}
          </span>
        ))}
      </div>
    </div>
  );
};

const InfoRow = ({ icon: Icon, label, value }) => (
  <div className="flex items-start gap-3 py-3 border-b border-gray-50 last:border-0">
    <Icon className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
    <div className="min-w-0">
      <span className="text-xs uppercase tracking-widest text-gray-500 font-semibold block">{label}</span>
      <span className="text-sm text-grafite font-medium break-words" data-testid={`profile-${label.toLowerCase().replace(/\s/g, '-')}`}>{value || '—'}</span>
    </div>
  </div>
);

// Aviso de validade da licença — ajuda o sócio a renovar a tempo (sem multa).
// Verde (>60 dias) → âmbar (≤60) → carmesim (expirada/urgente).
const LicenseExpiryNotice = ({ expiry }) => {
  const exp = toLocalDate(expiry);
  if (!exp) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((exp - today) / 86400000);

  let cfg;
  if (days < 0) {
    cfg = {
      cls: 'border-carmesim/30 bg-carmesim/5 text-carmesim',
      Icon: AlertTriangle,
      msg: `Licença expirada há ${Math.abs(days)} dia(s). Renove com urgência para evitar multa.`,
    };
  } else if (days === 0) {
    cfg = {
      cls: 'border-carmesim/30 bg-carmesim/5 text-carmesim',
      Icon: AlertTriangle,
      msg: 'A sua licença expira hoje. Renove para evitar multa.',
    };
  } else if (days <= 60) {
    cfg = {
      cls: 'border-[#FDE68A] bg-[#FFFBEB] text-[#B45309]',
      Icon: Clock,
      msg: `A sua licença expira em ${days} dia(s) (${formatDate(expiry)}). Renove a tempo para evitar multa.`,
    };
  } else {
    cfg = {
      cls: 'border-[#BBF7D0] bg-[#F0FDF4] text-[#15803D]',
      Icon: CheckCircle2,
      msg: `Licença válida até ${formatDate(expiry)}.`,
    };
  }
  const { Icon } = cfg;
  return (
    <div className={`flex items-start gap-2 rounded-lg border p-3 mt-3 ${cfg.cls}`} role="status" data-testid="license-expiry-notice">
      <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <p className="text-xs font-medium">{cfg.msg}</p>
    </div>
  );
};

const EMPTY_FORM = {
  name: '', phone_number: '', bio: '',
  date_of_birth: '', blood_type: '', gender: '', nationality: '', nif: '',
  address: '', postal_code: '', city: '', residence_island: '',
  emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relationship: '',
  profession: '', employer: '', license_number: '', license_category: '', license_expiry_date: '',
};

// Segurança / Autenticação de dois fatores (spec-mfa-frontend-pr2 §5). O backend
// é a fonte da verdade (status/mandatory); aqui só damos UI para ativar/desativar.
const SecuritySection = () => {
  const { refreshUser } = useAuth();
  const qc = useQueryClient();
  const [activateOpen, setActivateOpen] = useState(false);
  const [disableOpen, setDisableOpen] = useState(false);
  const [password, setPassword] = useState('');

  const { data: status, isLoading } = useQuery({
    queryKey: queryKeys.mfa.status(),
    queryFn: async () => (await mfaAPI.status()).data,
  });

  const refreshAll = async () => {
    if (refreshUser) await refreshUser();
    qc.invalidateQueries({ queryKey: queryKeys.mfa.status() });
  };

  const disableMutation = useMutation({
    mutationFn: (pw) => mfaAPI.disable(pw),
    onSuccess: async () => {
      await refreshAll();
      setDisableOpen(false);
      setPassword('');
      toast.success('Autenticação de dois fatores desativada.');
    },
    onError: (error) => {
      if (error.response?.status === 403) toast.error('Password incorreta');
      else toast.error(error.response?.data?.detail || 'Erro ao desativar o MFA.');
    },
  });

  const enabled = !!status?.enabled;
  const mandatory = !!status?.mandatory;
  const remaining = status?.backup_codes_remaining ?? 0;

  return (
    <div className="card-technical p-5 animate-fade-up" data-testid="mfa-section">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">
        <ShieldCheck className="w-3 h-3 inline mr-1" aria-hidden="true" /> Autenticação de Dois Fatores
      </h3>

      {isLoading ? (
        <div className="flex items-center gap-2 text-sm text-[#6B7280]" role="status" aria-live="polite">
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> A carregar…
        </div>
      ) : (
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${
                enabled ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#F5F5F5] text-[#3A3A3A]'
              }`}
              data-testid="mfa-status-badge"
            >
              {enabled ? <CheckCircle2 className="w-3 h-3" aria-hidden="true" /> : <Lock className="w-3 h-3" aria-hidden="true" />}
              {enabled ? 'Ativo' : 'Inativo'}
            </span>
            <p className="text-xs text-[#6B7280] mt-2">
              Protege o acesso à sua conta com um código gerado por uma app de autenticação.
            </p>
            {mandatory && (
              <p className="text-xs text-[#B45309] mt-1">Obrigatório para o seu cargo.</p>
            )}
            {enabled && (
              <p className="text-xs text-[#6B7280] mt-1">
                Códigos de recuperação restantes: <strong className="text-grafite">{remaining}</strong>
              </p>
            )}
          </div>

          <div className="shrink-0">
            {!enabled && (
              <button type="button" onClick={() => setActivateOpen(true)} className={btnPrimaryCls} data-testid="mfa-activate-btn">
                <ShieldCheck className="w-4 h-4" /> Ativar 2FA
              </button>
            )}
            {enabled && !mandatory && (
              <button type="button" onClick={() => setDisableOpen(true)} className={btnSecondaryCls} data-testid="mfa-disable-btn">
                <Lock className="w-4 h-4" /> Desativar
              </button>
            )}
          </div>
        </div>
      )}

      {/* Dialog: ativar (renderiza o wizard partilhado) */}
      <Dialog open={activateOpen} onOpenChange={setActivateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Ativar autenticação de dois fatores</DialogTitle>
            <DialogDescription>Siga os passos para proteger a sua conta.</DialogDescription>
          </DialogHeader>
          <SetupMFA
            onComplete={async () => {
              await refreshAll();
              setActivateOpen(false);
              toast.success('Autenticação de dois fatores ativada.');
            }}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog: desativar (confirma com password) */}
      <Dialog open={disableOpen} onOpenChange={(o) => { setDisableOpen(o); if (!o) setPassword(''); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Desativar 2FA</DialogTitle>
            <DialogDescription>
              Confirme a sua password para desativar a autenticação de dois fatores.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => { e.preventDefault(); if (password) disableMutation.mutate(password); }}
            className="space-y-4"
          >
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="A sua password"
              className={inputCls}
              data-testid="mfa-disable-password"
              autoFocus
            />
            <DialogFooter>
              <button type="button" onClick={() => setDisableOpen(false)} className={btnSecondaryCls}>
                Cancelar
              </button>
              <button type="submit" disabled={!password || disableMutation.isPending} className={btnPrimaryCls}>
                {disableMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                Desativar
              </button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export const PerfilPage = () => {
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

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

  // Preferência de comunicados informativos por email. O switch reflecte se o
  // sócio RECEBE (ON) — o campo persistido é o opt-OUT, logo invertemos.
  const emailPrefsMutation = useMutation({
    mutationFn: (data) => comunicadosAPI.updateEmailPreferences(data),
    onSuccess: async () => {
      if (refreshUser) await refreshUser();
      toast.success('Preferência de email atualizada.');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar a preferência de email.');
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

  const roleLabel = { admin: 'Administrador', socio: 'Sócio', financeiro: 'Gestor Financeiro', moderador: 'Moderador' };
  const statusCfg = getStatusConfig(USER_STATUS_CONFIG, user.status, USER_STATUS_FALLBACK);
  const cargoNome = cargoLabelFrom(structure, user.cargo);
  const isSocioBase = !user.cargo || user.cargo === 'socio';
  // Suspensão de direitos disciplinar ainda vigente?
  const suspendedUntil = user.rights_suspended_until;
  const rightsSuspended = !!suspendedUntil && new Date(suspendedUntil) > new Date();
  const StatusIcon = statusCfg.icon;
  const age = calcAge(user.date_of_birth);
  const dobLabel = user.date_of_birth
    ? `${formatDate(user.date_of_birth)}${age != null ? ` (${age} anos)` : ''}`
    : null;

  return (
    <div className="max-w-3xl mx-auto space-y-6" data-testid="profile-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="page-title" data-testid="profile-title">Meu Perfil</h1>
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

      {/* Profile Card */}
      <div className="card-technical overflow-hidden animate-fade-up">
        {/* Banner */}
        <div className="h-20 bg-gradient-to-r from-grafite to-grafite/80 relative">
          <div className="absolute -bottom-8 left-6">
            <div className="w-16 h-16 bg-carmesim rounded-xl flex items-center justify-center text-white text-2xl font-bold shadow-lg border-4 border-white">
              {user.name?.charAt(0).toUpperCase()}
            </div>
          </div>
        </div>

        <div className="pt-12 px-6 pb-6">
          {/* Name + badges */}
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-grafite" data-testid="profile-name">{user.name}</h2>
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider ${statusCfg.className}`}>
              <StatusIcon className="w-3 h-3" aria-hidden="true" />
              {user.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-1">{roleLabel[user.role] || user.role}</p>
          {!isSocioBase && (
            <p className="text-xs text-carmesim font-semibold">{cargoNome}</p>
          )}
        </div>
      </div>

      {/* Banner de suspensão de direitos (perda de direitos disciplinar) */}
      {rightsSuspended && (
        <div
          className="flex items-start gap-3 rounded-lg border border-[#FDE68A] bg-[#FFFBEB] p-4"
          role="alert"
          data-testid="rights-suspended-banner"
        >
          <AlertTriangle className="w-5 h-5 text-[#B45309] flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-sm">
            <p className="font-semibold text-[#B45309]">Direitos suspensos</p>
            <p className="text-[#6B7280]">
              Os seus direitos de voto e elegibilidade estão suspensos até{' '}
              {formatDate(suspendedUntil) || suspendedUntil}.
              {user.rights_suspension_reason ? ` Motivo: ${user.rights_suspension_reason}.` : ''}
            </p>
          </div>
        </div>
      )}

      {/* Edit Form */}
      {editing && (
        <div className="card-technical p-6 space-y-6 animate-fade-up" data-testid="profile-edit-form">
          {/* Dados pessoais */}
          <div className="space-y-4">
            <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Dados Pessoais</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormInput id="profile-name" testId="profile-edit-name" label="Nome" value={form.name} onChange={set('name')} max={120} />
              <FormInput id="profile-phone" testId="profile-edit-phone" label="Telefone" value={form.phone_number} onChange={set('phone_number')} type="tel" placeholder="+238 9XX XXXX" max={30} />
              <FormInput id="profile-dob" label="Data de Nascimento" value={form.date_of_birth} onChange={set('date_of_birth')} type="date" />
              <FormSelect id="profile-blood" label="Tipo Sanguíneo" value={form.blood_type} onChange={set('blood_type')} options={BLOOD_TYPE_OPTIONS} />
              <FormSelect id="profile-gender" label="Género" value={form.gender} onChange={set('gender')} options={GENDER_OPTIONS} />
              <FormInput id="profile-nationality" label="Nacionalidade" value={form.nationality} onChange={set('nationality')} placeholder="Cabo-verdiana" max={60} />
              <FormInput id="profile-nif" label="NIF" value={form.nif} onChange={set('nif')} max={40} />
            </div>
            <div>
              <label htmlFor="profile-bio" className={labelCls}>Biografia</label>
              <textarea
                id="profile-bio"
                value={form.bio}
                onChange={(e) => set('bio')(e.target.value)}
                rows={3}
                maxLength={1000}
                placeholder="Fale um pouco sobre si..."
                className={`${inputCls} resize-none`}
                data-testid="profile-edit-bio"
              />
            </div>
          </div>

          {/* Morada */}
          <div className="space-y-4 pt-2 border-t border-gray-100">
            <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Morada</h3>
            <FormInput id="profile-address" label="Endereço" value={form.address} onChange={set('address')} placeholder="Rua, n.º, andar" max={200} />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FormInput id="profile-postal" label="Código Postal" value={form.postal_code} onChange={set('postal_code')} max={20} />
              <FormInput id="profile-city" label="Cidade / Concelho" value={form.city} onChange={set('city')} max={80} />
              <FormInput id="profile-island" label="Ilha de Residência" value={form.residence_island} onChange={set('residence_island')} placeholder="Santiago" max={60} />
            </div>
          </div>

          {/* Contacto de emergência */}
          <div className="space-y-4 pt-2 border-t border-gray-100">
            <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Contacto de Emergência</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FormInput id="profile-ec-name" label="Nome" value={form.emergency_contact_name} onChange={set('emergency_contact_name')} max={120} />
              <FormInput id="profile-ec-phone" label="Telefone" value={form.emergency_contact_phone} onChange={set('emergency_contact_phone')} type="tel" placeholder="+238 9XX XXXX" max={30} />
              <FormInput id="profile-ec-rel" label="Parentesco" value={form.emergency_contact_relationship} onChange={set('emergency_contact_relationship')} placeholder="Cônjuge, filho/a..." max={60} />
            </div>
          </div>

          {/* Profissional e licença */}
          <div className="space-y-4 pt-2 border-t border-gray-100">
            <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Dados Profissionais e Licença</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormInput id="profile-profession" label="Profissão" value={form.profession} onChange={set('profession')} max={120} />
              <FormInput id="profile-employer" label="Entidade Empregadora" value={form.employer} onChange={set('employer')} max={120} />
              <FormInput id="profile-license-number" label="N.º de Licença" value={form.license_number} onChange={set('license_number')} max={60} />
              <FormInput id="profile-license-category" label="Categoria / Título" value={form.license_category} onChange={set('license_category')} max={80} />
              <FormInput id="profile-license-expiry" label="Validade da Licença" value={form.license_expiry_date} onChange={set('license_expiry_date')} type="date" />
            </div>
            <LicenseExpiryNotice expiry={form.license_expiry_date} />
          </div>

          <button
            onClick={handleSave}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-carmesim text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-carmesim-dark transition-colors disabled:opacity-50"
            data-testid="profile-save-btn"
          >
            <Save className="w-4 h-4" />
            {loading ? 'A guardar...' : 'Guardar alterações'}
          </button>
        </div>
      )}

      {/* Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="card-technical p-5 animate-fade-up">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Dados Pessoais</h3>
          <InfoRow icon={Mail} label="Email" value={user.email} />
          <InfoRow icon={Phone} label="Telefone" value={user.phone_number} />
          <InfoRow icon={Cake} label="Nascimento" value={dobLabel} />
          <InfoRow icon={Droplet} label="Tipo Sanguíneo" value={user.blood_type} />
          <InfoRow icon={UserIcon} label="Género" value={user.gender} />
          <InfoRow icon={Globe} label="Nacionalidade" value={user.nationality} />
          <InfoRow icon={Fingerprint} label="NIF" value={user.nif} />
          <InfoRow icon={FileText} label="Biografia" value={user.bio} />
          <InfoRow icon={Hash} label="N.º Sócio" value={user.member_id} />
        </div>

        <div className="card-technical p-5 animate-fade-up">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Morada</h3>
          <InfoRow icon={MapPin} label="Endereço" value={user.address} />
          <InfoRow icon={Home} label="Código Postal" value={user.postal_code} />
          <InfoRow icon={Building2} label="Cidade" value={user.city} />
          <InfoRow icon={MapPin} label="Ilha" value={user.residence_island} />
        </div>

        <div className="card-technical p-5 animate-fade-up">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Contacto de Emergência</h3>
          <InfoRow icon={HeartPulse} label="Nome" value={user.emergency_contact_name} />
          <InfoRow icon={Phone} label="Telefone" value={user.emergency_contact_phone} />
          <InfoRow icon={UsersIcon} label="Parentesco" value={user.emergency_contact_relationship} />
        </div>

        <div className="card-technical p-5 animate-fade-up">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Profissional e Licença</h3>
          <InfoRow icon={Briefcase} label="Profissão" value={user.profession} />
          <InfoRow icon={Building2} label="Entidade" value={user.employer} />
          <InfoRow icon={Award} label="N.º Licença" value={user.license_number} />
          <InfoRow icon={BadgeCheck} label="Categoria" value={user.license_category} />
          <InfoRow icon={Clock} label="Validade" value={formatDate(user.license_expiry_date)} />
          <LicenseExpiryNotice expiry={user.license_expiry_date} />
        </div>

        <div className="card-technical p-5 animate-fade-up md:col-span-2">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Associação</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 sm:gap-x-8">
            <InfoRow icon={Shield} label="Função" value={roleLabel[user.role]} />
            <InfoRow icon={Briefcase} label="Cargo" value={cargoNome} />
            <InfoRow icon={UsersIcon} label="Categoria" value={memberCategoryLabel(user.member_category)} />
            <InfoRow icon={Calendar} label="Admissão" value={formatDate(user.admission_date) || '—'} />
          </div>
        </div>
      </div>

      {/* Privileges */}
      <PrivilegesSection privileges={user.privileges} />

      {/* Preferências de email */}
      <div className="card-technical p-5 animate-fade-up" data-testid="email-prefs-section">
        <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">
          <Mail className="w-3 h-3 inline mr-1" aria-hidden="true" /> Preferências de Email
        </h3>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <label htmlFor="email-opt-informativos" className="text-sm font-medium text-grafite block">
              Receber comunicados informativos por email
            </label>
            <p className="text-xs text-[#6B7280] mt-1">
              Os comunicados oficiais (convocatórias, deliberações) chegam sempre.
            </p>
          </div>
          <Switch
            id="email-opt-informativos"
            checked={!user.email_opt_out_informativos}
            disabled={emailPrefsMutation.isPending}
            onCheckedChange={(checked) =>
              emailPrefsMutation.mutate({ email_opt_out_informativos: !checked })
            }
            data-testid="email-opt-informativos-switch"
          />
        </div>
      </div>

      {/* Segurança / Autenticação de dois fatores */}
      <SecuritySection />

      {/* Histórico de cargos do próprio sócio */}
      <MeusCargosSection userId={user.id} structure={structure} />
    </div>
  );
};
