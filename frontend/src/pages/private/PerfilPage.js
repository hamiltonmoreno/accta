import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { usersAPI } from '../../utils/api';
import { toast } from 'sonner';
import {
  User as UserIcon, Mail, Phone, Shield, Award, FileText,
  Calendar, Save, BadgeCheck, Briefcase, Hash, Pencil, X
} from 'lucide-react';

const PRIVILEGE_LABELS = {
  manage_users: 'Gerir Utilizadores',
  manage_finances: 'Gerir Finanças',
  manage_events: 'Gerir Eventos',
  manage_documents: 'Gerir Documentos',
  moderate_content: 'Moderar Conteúdo',
  manage_benefits: 'Gerir Benefícios',
  view_audit_logs: 'Ver Logs',
};

const PrivilegesSection = ({ privileges }) => {
  if (!privileges || privileges.length === 0) return null;
  
  return (
    <div className="card-technical p-5 animate-fade-up">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-gray-400 mb-3">Privilégios Atribuídos</h3>
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
      <span className="text-sm text-grafite font-medium" data-testid={`profile-${label.toLowerCase().replace(/\s/g, '-')}`}>{value || '—'}</span>
    </div>
  </div>
);

export const PerfilPage = () => {
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '',
    phone_number: '',
    bio: '',
  });

  useEffect(() => {
    if (user) {
      setForm({
        name: user.name || '',
        phone_number: user.phone_number || '',
        bio: user.bio || '',
      });
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await usersAPI.updateProfile(form);
      if (refreshUser) await refreshUser();
      toast.success('Perfil atualizado com sucesso!');
      setEditing(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar perfil');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  const roleLabel = { admin: 'Administrador', socio: 'Sócio', financeiro: 'Gestor Financeiro', moderador: 'Moderador' };
  const statusColors = { ativo: 'bg-green-100 text-green-700', inativo: 'bg-gray-100 text-gray-600' };

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
            onClick={() => setEditing(false)}
            className="inline-flex items-center gap-2 text-sm font-semibold text-gray-400 hover:text-grafite transition-colors"
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
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider ${statusColors[user.status] || 'bg-gray-100 text-gray-600'}`}>
              <BadgeCheck className="w-3 h-3" />
              {user.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-1">{roleLabel[user.role] || user.role}</p>
          {user.cargo && user.cargo !== 'Sócio' && (
            <p className="text-xs text-carmesim font-semibold">{user.cargo}</p>
          )}
        </div>
      </div>

      {/* Edit Form */}
      {editing && (
        <div className="card-technical p-6 space-y-4 animate-fade-up">
          <h3 className="font-semibold text-sm text-grafite">Editar Informações</h3>

          <div>
            <label htmlFor="profile-name" className="block text-xs uppercase tracking-widest text-gray-500 font-semibold mb-1">Nome</label>
            <input
              id="profile-name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 focus:border-carmesim/30 outline-none"
              data-testid="profile-edit-name"
            />
          </div>

          <div>
            <label htmlFor="profile-phone" className="block text-xs uppercase tracking-widest text-gray-500 font-semibold mb-1">Telefone</label>
            <input
              id="profile-phone"
              type="tel"
              inputMode="tel"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
              placeholder="+238 9XX XXXX"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 focus:border-carmesim/30 outline-none"
              data-testid="profile-edit-phone"
            />
          </div>

          <div>
            <label htmlFor="profile-bio" className="block text-xs uppercase tracking-widest text-gray-500 font-semibold mb-1">Biografia</label>
            <textarea
              id="profile-bio"
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              rows={3}
              placeholder="Fale um pouco sobre si..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 focus:border-carmesim/30 outline-none resize-none"
              data-testid="profile-edit-bio"
            />
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
          <h3 className="font-semibold text-xs uppercase tracking-widest text-gray-400 mb-3">Dados Pessoais</h3>
          <InfoRow icon={Mail} label="Email" value={user.email} />
          <InfoRow icon={Phone} label="Telefone" value={user.phone_number} />
          <InfoRow icon={FileText} label="Biografia" value={user.bio} />
          <InfoRow icon={Hash} label="N.º Sócio" value={user.member_id} />
        </div>

        <div className="card-technical p-5 animate-fade-up">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-gray-400 mb-3">Associação</h3>
          <InfoRow icon={Shield} label="Função" value={roleLabel[user.role]} />
          <InfoRow icon={Briefcase} label="Cargo" value={user.cargo || 'Sócio'} />
          <InfoRow icon={Award} label="Licença" value={user.license_number} />
          <InfoRow icon={Calendar} label="Admissão" value={user.admission_date ? new Date(user.admission_date).toLocaleDateString('pt-PT') : '—'} />
        </div>
      </div>

      {/* Privileges */}
      <PrivilegesSection privileges={user.privileges} />
    </div>
  );
};
