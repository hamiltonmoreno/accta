import React, { useState, useEffect, useCallback } from 'react';
import { usersAPI } from '../../utils/api';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Search, Shield, BadgeCheck, Briefcase, X, Save,
  Trash2, ChevronDown, Filter, UserCog
} from 'lucide-react';

const ROLE_LABELS = { admin: 'Administrador', socio: 'Sócio', financeiro: 'Financeiro', moderador: 'Moderador' };
const ROLE_COLORS = { admin: 'bg-red-100 text-red-700', socio: 'bg-blue-100 text-blue-700', financeiro: 'bg-amber-100 text-amber-700', moderador: 'bg-purple-100 text-purple-700' };
const STATUS_COLORS = { ativo: 'bg-green-100 text-green-700', inativo: 'bg-gray-100 text-gray-500' };

const PRIVILEGE_LABELS = {
  manage_users: 'Gerir Utilizadores',
  manage_finances: 'Gerir Finanças',
  manage_events: 'Gerir Eventos',
  manage_documents: 'Gerir Documentos',
  moderate_content: 'Moderar Conteúdo',
  manage_benefits: 'Gerir Benefícios',
  view_audit_logs: 'Ver Audit Logs',
};

const CARGOS = [
  'Presidente', 'Vice-Presidente', 'Secretário-Geral',
  'Tesoureiro', 'Vogal', 'Membro da Direção', 'Sócio'
];
const ROLES = ['admin', 'socio', 'financeiro', 'moderador'];
const STATUSES = ['ativo', 'inativo'];
const PRIVILEGES = Object.keys(PRIVILEGE_LABELS);

export const AdminUsuariosPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const fetchUsers = useCallback(async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (filterRole) params.role = filterRole;
      if (filterStatus) params.status = filterStatus;
      const res = await usersAPI.getAll(params);
      setUsers(res.data);
    } catch (err) {
      toast.error('Erro ao carregar utilizadores');
    } finally {
      setLoading(false);
    }
  }, [search, filterRole, filterStatus]);

  useEffect(() => {
    const timer = setTimeout(fetchUsers, 300);
    return () => clearTimeout(timer);
  }, [fetchUsers]);

  const handleSaveUser = async () => {
    if (!editingUser) return;
    try {
      await usersAPI.adminUpdate(editingUser.id, {
        name: editingUser.name,
        role: editingUser.role,
        status: editingUser.status,
        cargo: editingUser.cargo,
        privileges: editingUser.privileges || [],
        member_id: editingUser.member_id,
        department: editingUser.department,
        phone_number: editingUser.phone_number,
      });
      toast.success('Utilizador atualizado!');
      setEditingUser(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao atualizar');
    }
  };

  const handleDelete = async (userId) => {
    try {
      await usersAPI.delete(userId);
      toast.success('Utilizador removido');
      setDeleteConfirm(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao remover');
    }
  };

  const togglePrivilege = (priv) => {
    if (!editingUser) return;
    const current = editingUser.privileges || [];
    const updated = current.includes(priv)
      ? current.filter((p) => p !== priv)
      : [...current, priv];
    setEditingUser({ ...editingUser, privileges: updated });
  };

  return (
    <div className="space-y-5" data-testid="admin-users-page">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="admin-users-title">Gestão de Membros</h1>
          <p className="text-sm text-gray-500">{users.length} membro{users.length !== 1 ? 's' : ''} registado{users.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="card-technical p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar por nome, email ou n.º sócio..."
              className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 focus:border-carmesim/30 outline-none"
              data-testid="users-search-input"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none bg-white"
              data-testid="filter-role"
            >
              <option value="">Todas as funções</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none bg-white"
              data-testid="filter-status"
            >
              <option value="">Todos os estados</option>
              {STATUSES.map((s) => (
                <option key={s} value={s} className="capitalize">{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Users Table/Cards */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">A carregar...</div>
      ) : users.length === 0 ? (
        <div className="card-technical p-8 text-center text-gray-400">Nenhum utilizador encontrado</div>
      ) : (
        <>
          {/* Desktop Table */}
          <div className="hidden md:block card-technical overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/50">
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Membro</th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Cargo</th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Função</th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Estado</th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Privilégios</th>
                    <th className="text-right px-4 py-3 text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 bg-carmesim rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                            {u.name?.charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-grafite truncate">{u.name}</div>
                            <div className="text-xs text-gray-400 truncate">{u.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-medium text-grafite">{u.cargo || 'Sócio'}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${ROLE_COLORS[u.role] || 'bg-gray-100 text-gray-600'}`}>
                          {ROLE_LABELS[u.role] || u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${STATUS_COLORS[u.status] || 'bg-gray-100 text-gray-600'}`}>
                          <BadgeCheck className="w-3 h-3" />
                          {u.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {(u.privileges || []).slice(0, 2).map((p) => (
                            <span key={p} className="text-[9px] px-1.5 py-0.5 bg-carmesim/10 text-carmesim rounded font-medium">
                              {PRIVILEGE_LABELS[p]?.split(' ')[0] || p}
                            </span>
                          ))}
                          {(u.privileges || []).length > 2 && (
                            <span className="text-[9px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">+{u.privileges.length - 2}</span>
                          )}
                          {(!u.privileges || u.privileges.length === 0) && <span className="text-[9px] text-gray-300">—</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setEditingUser({ ...u, privileges: u.privileges || [] })}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-carmesim hover:text-carmesim-dark transition-colors"
                          data-testid={`edit-user-${u.id}`}
                        >
                          <UserCog className="w-3.5 h-3.5" />
                          Gerir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {users.map((u) => (
              <div key={u.id} className="card-technical p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-carmesim rounded-lg flex items-center justify-center text-white font-bold flex-shrink-0">
                      {u.name?.charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="font-semibold text-grafite text-sm truncate">{u.name}</div>
                      <div className="text-xs text-gray-400">{u.cargo || 'Sócio'}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setEditingUser({ ...u, privileges: u.privileges || [] })}
                    className="p-2 text-carmesim hover:bg-carmesim/10 rounded-lg transition-colors"
                  >
                    <UserCog className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${ROLE_COLORS[u.role]}`}>
                    {ROLE_LABELS[u.role]}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${STATUS_COLORS[u.status]}`}>
                    {u.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ===== Edit Modal ===== */}
      <AnimatePresence>
        {editingUser && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
              onClick={() => setEditingUser(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed inset-4 sm:inset-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-full sm:max-w-lg z-50 bg-white rounded-xl shadow-xl overflow-hidden flex flex-col max-h-[90vh]"
              data-testid="edit-user-modal"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-carmesim rounded-lg flex items-center justify-center text-white font-bold">
                    {editingUser.name?.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-bold text-grafite text-sm">{editingUser.name}</h3>
                    <p className="text-xs text-gray-400">{editingUser.email}</p>
                  </div>
                </div>
                <button onClick={() => setEditingUser(null)} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* Basic Info */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">Nome</label>
                    <input
                      value={editingUser.name || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none"
                      data-testid="modal-edit-name"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">N.º Sócio</label>
                    <input
                      value={editingUser.member_id || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, member_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none"
                      data-testid="modal-edit-member-id"
                    />
                  </div>
                </div>

                {/* Role + Status */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">
                      <Shield className="w-3 h-3 inline mr-1" />
                      Função no Sistema
                    </label>
                    <select
                      value={editingUser.role}
                      onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none bg-white"
                      data-testid="modal-edit-role"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">
                      <BadgeCheck className="w-3 h-3 inline mr-1" />
                      Estado
                    </label>
                    <select
                      value={editingUser.status}
                      onChange={(e) => setEditingUser({ ...editingUser, status: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none bg-white"
                      data-testid="modal-edit-status"
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Cargo */}
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">
                    <Briefcase className="w-3 h-3 inline mr-1" />
                    Cargo na Associação
                  </label>
                  <select
                    value={editingUser.cargo || 'Sócio'}
                    onChange={(e) => setEditingUser({ ...editingUser, cargo: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none bg-white"
                    data-testid="modal-edit-cargo"
                  >
                    {CARGOS.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                {/* Privileges */}
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-2">
                    <Shield className="w-3 h-3 inline mr-1" />
                    Privilégios
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {PRIVILEGES.map((priv) => {
                      const checked = (editingUser.privileges || []).includes(priv);
                      return (
                        <label
                          key={priv}
                          className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-all ${
                            checked ? 'border-carmesim bg-carmesim/5 text-carmesim' : 'border-gray-200 text-gray-600 hover:border-gray-300'
                          }`}
                          data-testid={`privilege-${priv}`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => togglePrivilege(priv)}
                            className="sr-only"
                          />
                          <div className={`w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                            checked ? 'border-carmesim bg-carmesim' : 'border-gray-300'
                          }`}>
                            {checked && (
                              <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </div>
                          <span className="text-xs font-medium">{PRIVILEGE_LABELS[priv]}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                {/* Phone + Department */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">Telefone</label>
                    <input
                      value={editingUser.phone_number || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, phone_number: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-gray-400 font-semibold mb-1">Departamento</label>
                    <input
                      value={editingUser.department || ''}
                      onChange={(e) => setEditingUser({ ...editingUser, department: e.target.value })}
                      placeholder="Ex: Torre de Controlo Sal"
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-between px-5 py-4 border-t border-gray-100 bg-gray-50/50">
                <button
                  onClick={() => setDeleteConfirm(editingUser.id)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-red-500 hover:text-red-700 transition-colors"
                  data-testid="delete-user-btn"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Remover
                </button>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingUser(null)}
                    className="px-4 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleSaveUser}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-carmesim text-white rounded-lg text-sm font-semibold hover:bg-carmesim-dark transition-colors"
                    data-testid="modal-save-btn"
                  >
                    <Save className="w-4 h-4" />
                    Guardar
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirm */}
      <AnimatePresence>
        {deleteConfirm && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-[60]"
              onClick={() => setDeleteConfirm(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-xl p-6 z-[60] w-[90vw] max-w-sm"
              data-testid="delete-confirm-modal"
            >
              <h3 className="font-bold text-grafite mb-2">Remover utilizador?</h3>
              <p className="text-sm text-gray-500 mb-5">Esta ação é irreversível. O utilizador perderá acesso ao portal.</p>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => handleDelete(deleteConfirm)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 transition-colors"
                  data-testid="confirm-delete-btn"
                >
                  Sim, remover
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};
