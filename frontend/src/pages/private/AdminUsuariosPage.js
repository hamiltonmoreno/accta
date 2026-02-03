import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { usersAPI, auditAPI } from '../../utils/api';
import { Users, ShieldCheck, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';

export const AdminUsuariosPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await usersAPI.getAll();
      setUsers(response.data);
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (userId, newStatus) => {
    try {
      await usersAPI.updateStatus(userId, newStatus);
      toast.success('Status atualizado com sucesso!');
      loadUsers();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ativo':
        return 'bg-accent/10 text-accent';
      case 'inadimplente':
        return 'bg-alert/10 text-alert';
      case 'suspenso':
        return 'bg-slate-100 text-slate-500';
      case 'pendente':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-slate-100 text-slate-500';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="admin-users-title">
          Gestão de Usuários
        </h1>
        <p className="text-slate-600">Gerencie os sócios e seus status</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
            <Users className="w-6 h-6 text-accent" />
          </div>
          <div className="font-mono text-3xl font-bold text-primary mb-1">{users.length}</div>
          <div className="text-sm text-slate-500 uppercase tracking-wider">Total</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center mb-4">
            <ShieldCheck className="w-6 h-6 text-primary" />
          </div>
          <div className="font-mono text-3xl font-bold text-accent mb-1">
            {users.filter((u) => u.status === 'ativo').length}
          </div>
          <div className="text-sm text-slate-500 uppercase tracking-wider">Ativos</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="w-12 h-12 bg-alert rounded-lg flex items-center justify-center mb-4">
            <AlertCircle className="w-6 h-6 text-white" />
          </div>
          <div className="font-mono text-3xl font-bold text-alert mb-1">
            {users.filter((u) => u.status === 'inadimplente').length}
          </div>
          <div className="text-sm text-slate-500 uppercase tracking-wider">Inadimplentes</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="w-12 h-12 bg-slate-200 rounded-lg flex items-center justify-center mb-4">
            <Users className="w-6 h-6 text-slate-600" />
          </div>
          <div className="font-mono text-3xl font-bold text-slate-600 mb-1">
            {users.filter((u) => u.status === 'suspenso').length}
          </div>
          <div className="text-sm text-slate-500 uppercase tracking-wider">Suspensos</div>
        </motion.div>
      </div>

      {/* Users Table */}
      <div className="card-technical rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase font-mono text-xs">
                <tr>
                  <th className="px-6 py-4">Nome</th>
                  <th className="px-6 py-4">Email</th>
                  <th className="px-6 py-4">Nº Sócio</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Ações</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-t border-slate-100 hover:bg-slate-50 transition-colors" data-testid={`user-row-${user.id}`}>
                    <td className="px-6 py-4 font-manrope font-semibold text-primary">{user.name}</td>
                    <td className="px-6 py-4 font-mono text-sm text-slate-600">{user.email}</td>
                    <td className="px-6 py-4 font-mono text-slate-600">{user.member_id || 'N/A'}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs font-mono uppercase">
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wide ${getStatusColor(user.status)}`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <select
                        value={user.status}
                        onChange={(e) => handleStatusChange(user.id, e.target.value)}
                        className="px-3 py-1 border border-slate-200 rounded text-xs font-mono uppercase focus:outline-none focus:ring-2 focus:ring-primary"
                        data-testid={`status-select-${user.id}`}
                      >
                        <option value="ativo">Ativo</option>
                        <option value="inadimplente">Inadimplente</option>
                        <option value="suspenso">Suspenso</option>
                        <option value="pendente">Pendente</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
