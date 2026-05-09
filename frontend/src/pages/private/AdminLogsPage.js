import React, { useEffect, useState } from 'react';
import { auditAPI } from '../../utils/api';
import { ClipboardList, Activity } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const AdminLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      const response = await auditAPI.getLogs();
      setLogs(response.data);
    } catch (error) {
      console.error('Erro ao carregar logs:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-sans font-bold text-4xl text-grafite mb-2" data-testid="admin-logs-title">
          Audit Logs
        </h1>
        <p className="text-gray-600">Registro de todas as ações administrativas no sistema</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-technical rounded-xl p-6 animate-fade-up">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center">
              <ClipboardList className="w-6 h-6 text-carmesim" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-grafite mb-1">{logs.length}</div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Total de Registros</div>
        </div>

        <div className="card-technical rounded-xl p-6 animate-fade-up">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-grafite" />
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-carmesim mb-1">
            {logs.filter((log) => {
              const logDate = new Date(log.created_at);
              const today = new Date();
              return logDate.toDateString() === today.toDateString();
            }).length}
          </div>
          <div className="text-sm text-gray-500 uppercase tracking-wider">Hoje</div>
        </div>
      </div>

      {/* Logs Timeline */}
      <div className="card-technical rounded-xl p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12" data-testid="no-logs">
            <p className="text-gray-500">Nenhum registro de auditoria</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg animate-fade-in"
                data-testid={`log-${log.id}`}
              >
                <div className="w-2 h-2 bg-carmesim rounded-full mt-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-sans text-grafite mb-1">{log.action}</p>
                  <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
                    <span>User ID: {log.user_id}</span>
                    {log.target_id && <span>Target: {log.target_id}</span>}
                    <span>
                      {format(new Date(log.created_at), "dd/MM/yyyy 'às' HH:mm:ss", { locale: ptBR })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
