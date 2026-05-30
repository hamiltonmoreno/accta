import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { relacoesAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import {
  Network, Plus, Search, Globe, Lock, Pencil, Trash2, Link as LinkIcon,
  Calendar, Building2, Handshake,
} from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

// Cat 5 F3 — espelha RELACAO_TIPOS / ESTADOS_FILIACAO do backend.
const TIPO_LABELS = {
  federacao_internacional: 'Federação Internacional',
  associacao_congenere: 'Associação Congénere',
  parceiro: 'Parceiro',
};
const TIPO_ICONS = {
  federacao_internacional: Network,
  associacao_congenere: Building2,
  parceiro: Handshake,
};

const ESTADO_LABELS = {
  filiado: 'Filiado',
  em_negociacao: 'Em Negociação',
  nao_filiado: 'Não Filiado',
  suspenso: 'Suspenso',
};
const ESTADO_STYLES = {
  filiado: 'bg-gray-50 text-grafite border-gray-300 font-bold',
  em_negociacao: 'bg-gray-100 text-grafite border-gray-300',
  nao_filiado: 'bg-gray-50 text-gray-600 border-gray-200',
  suspenso: 'bg-gray-50 text-carmesim border-carmesim/30',
};

const RelacaoCard = ({ relacao, canManage, onEdit, onDelete }) => {
  const Icon = TIPO_ICONS[relacao.tipo] || Network;
  const VisIcon = relacao.visibility === 'publico' ? Globe : Lock;

  return (
    <div
      className="bg-white border border-gray-200/80 rounded-2xl p-5 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-200 animate-fade-up flex gap-4"
      data-testid={`relacao-card-${relacao.id}`}
    >
      {relacao.logo_url ? (
        <img
          src={relacao.logo_url}
          alt={`Logo de ${relacao.nome}`}
          className="w-16 h-16 object-contain rounded-lg border border-gray-200 bg-white flex-shrink-0"
        />
      ) : (
        <div className="w-16 h-16 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-center flex-shrink-0">
          <Icon className="w-8 h-8 text-gray-300" aria-hidden="true" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
            <Icon className="w-3 h-3" aria-hidden="true" />
            {TIPO_LABELS[relacao.tipo]}
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-gray-500">
            <VisIcon className="w-3 h-3" />
            {relacao.visibility === 'publico' ? 'Público' : 'Sócios'}
          </span>
        </div>
        <h3 className="font-semibold text-grafite text-base mb-1.5">{relacao.nome}</h3>
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 mb-2 rounded-full text-[10px] uppercase tracking-wider border ${ESTADO_STYLES[relacao.estado_filiacao]}`}>
          {ESTADO_LABELS[relacao.estado_filiacao]}
          {relacao.desde && <span className="opacity-70">desde {relacao.desde}</span>}
        </span>
        {relacao.descricao && (
          <p className="text-sm text-gray-600 mb-2 line-clamp-3">{relacao.descricao}</p>
        )}
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-2">
          {relacao.website && (
            <a
              href={relacao.website}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-grafite hover:text-carmesim transition-colors font-semibold"
            >
              <LinkIcon className="w-3 h-3" /> Website
            </a>
          )}
          {relacao.quota_anual != null && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Quota: {Number(relacao.quota_anual).toLocaleString('pt-PT')} CVE/ano
            </span>
          )}
        </div>
        {canManage && (
          <div className="flex gap-1.5 pt-1">
            <button
              onClick={() => onEdit(relacao)}
              className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
              data-testid={`relacao-editar-${relacao.id}`}
            >
              <Pencil className="w-3 h-3" /> Editar
            </button>
            <button
              onClick={() => onDelete(relacao)}
              className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-carmesim text-carmesim hover:bg-carmesim/5 transition-colors"
              data-testid={`relacao-eliminar-${relacao.id}`}
            >
              <Trash2 className="w-3 h-3" /> Eliminar
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const RelacaoModal = ({ relacao, onClose }) => {
  const qc = useQueryClient();
  const isEdit = !!relacao;
  const [form, setForm] = useState(
    relacao || {
      nome: '',
      tipo: 'parceiro',
      descricao: '',
      website: '',
      contacto: '',
      estado_filiacao: 'nao_filiado',
      desde: '',
      quota_anual: '',
      logo_url: '',
      visibility: 'socios',
    }
  );
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome.trim()) {
      toast.error('Nome obrigatório');
      return;
    }
    setSaving(true);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach((k) => {
        if (payload[k] === '' || payload[k] == null) delete payload[k];
      });
      if (payload.quota_anual !== undefined) {
        payload.quota_anual = Number(payload.quota_anual);
        if (Number.isNaN(payload.quota_anual)) delete payload.quota_anual;
      }
      if (isEdit) {
        delete payload.tipo; // tipo é imutável
        await relacoesAPI.update(relacao.id, payload);
        toast.success('Relação atualizada');
      } else {
        await relacoesAPI.create(payload);
        toast.success('Relação criada');
      }
      qc.invalidateQueries({ queryKey: ['relacoes-externas'] });
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Editar relação' : 'Nova relação externa'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Nome *</label>
            <input
              type="text"
              value={form.nome}
              onChange={(e) => setForm({ ...form, nome: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="relacao-nome-input"
            />
          </div>
          {!isEdit && (
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Tipo *</label>
              <select
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="relacao-tipo-select"
              >
                <option value="federacao_internacional">Federação Internacional</option>
                <option value="associacao_congenere">Associação Congénere</option>
                <option value="parceiro">Parceiro</option>
              </select>
            </div>
          )}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descrição</label>
            <textarea
              rows={3}
              value={form.descricao || ''}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Estado</label>
              <select
                value={form.estado_filiacao}
                onChange={(e) => setForm({ ...form, estado_filiacao: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                data-testid="relacao-estado-select"
              >
                <option value="nao_filiado">Não Filiado</option>
                <option value="em_negociacao">Em Negociação</option>
                <option value="filiado">Filiado</option>
                <option value="suspenso">Suspenso</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Desde</label>
              <input
                type="date"
                value={form.desde || ''}
                onChange={(e) => setForm({ ...form, desde: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Quota anual (CVE)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.quota_anual || ''}
                onChange={(e) => setForm({ ...form, quota_anual: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Visibilidade</label>
              <select
                value={form.visibility}
                onChange={(e) => setForm({ ...form, visibility: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              >
                <option value="socios">Sócios</option>
                <option value="publico">Público</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Website</label>
            <input
              type="url"
              value={form.website || ''}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
              placeholder="https://..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Logo URL</label>
            <input
              type="url"
              value={form.logo_url || ''}
              onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
              placeholder="https://..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            />
          </div>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold">
            {saving ? 'A guardar...' : isEdit ? 'Guardar Alterações' : 'Criar'}
          </button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const RelacoesPage = () => {
  const { isAdmin, isDirecao } = useAuth();
  const canManage = isAdmin || isDirecao;
  const [filterTipo, setFilterTipo] = useState('');
  const [searchText, setSearchText] = useState('');
  const [editing, setEditing] = useState(null);
  const qc = useQueryClient();

  const { data, isLoading: loading } = useQuery({
    queryKey: ['relacoes-externas', { tipo: filterTipo || undefined }],
    queryFn: async () => {
      const params = filterTipo ? { tipo: filterTipo } : {};
      const res = await relacoesAPI.getAll(params);
      return res.data;
    },
  });
  const items = data?.items || [];

  const deleteMutation = useMutation({
    mutationFn: (id) => relacoesAPI.delete(id),
    onSuccess: () => {
      toast.success('Relação removida');
      qc.invalidateQueries({ queryKey: ['relacoes-externas'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao remover'),
  });

  const filtered = searchText
    ? items.filter((r) => {
        const q = searchText.toLowerCase();
        return r.nome.toLowerCase().includes(q) || (r.descricao || '').toLowerCase().includes(q);
      })
    : items;

  const tabs = [
    { val: '', label: 'Todas' },
    { val: 'federacao_internacional', label: 'Federações' },
    { val: 'associacao_congenere', label: 'Congéneres' },
    { val: 'parceiro', label: 'Parceiros' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="relacoes-title">Relações Externas</h1>
          <p className="page-subtitle">
            Cooperação com a IFATCA e associações congéneres, estado de filiação
            e acordos (Art. 2.f, 31.g, 53).
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => setEditing('new')}
            className="btn-primary flex items-center gap-2 text-sm w-fit"
            data-testid="relacao-new-btn"
          >
            <Plus className="w-4 h-4" /> Nova Relação
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-1.5 border-b border-gray-200">
        {tabs.map((t) => {
          const active = filterTipo === t.val;
          return (
            <button
              key={t.val}
              onClick={() => setFilterTipo(t.val)}
              data-testid={`relacoes-tab-${t.val || 'all'}`}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold uppercase tracking-wider border-b-2 -mb-[1px] transition-colors ${
                active ? 'text-grafite border-grafite' : 'text-gray-500 border-transparent hover:text-grafite'
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="card-technical p-3 sm:p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Pesquisar..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
            data-testid="relacoes-search"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Network}
          title="Sem relações registadas"
          description={canManage ? 'Adicione a primeira relação para começar' : 'Ainda não há relações públicas'}
          testId="relacoes-empty"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((r) => (
            <RelacaoCard
              key={r.id}
              relacao={r}
              canManage={canManage}
              onEdit={(x) => setEditing(x)}
              onDelete={(x) => {
                if (window.confirm(`Remover '${x.nome}'?`)) deleteMutation.mutate(x.id);
              }}
            />
          ))}
        </div>
      )}

      {editing && (
        <RelacaoModal relacao={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
      )}
    </div>
  );
};

export default RelacoesPage;
