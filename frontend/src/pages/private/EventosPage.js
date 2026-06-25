import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eventsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { queryKeys } from '../../lib/queryClient';
import { Skeleton } from '../../components/ui/skeleton';
import { toast } from 'sonner';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../components/ui/alert-dialog';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  Users,
  Plus,
  Check,
  Loader2,
  UserCheck,
  Trash2,
  Wallet,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { format, isFuture, isPast } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  EVENT_TYPE_CONFIG, EVENT_TYPE_FALLBACK, getStatusConfig,
} from '../../lib/statusConfig';
import { EmptyState } from '../../components/EmptyState';

export const EventosPage = () => {
  const { user, isAdmin } = useAuth();
  const qc = useQueryClient();
  const [filter, setFilter] = useState('upcoming');
  const [showModal, setShowModal] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [financeEvent, setFinanceEvent] = useState(null);

  const { data: events = [], isLoading: loading } = useQuery({
    queryKey: queryKeys.events.list(),
    queryFn: async () => (await eventsAPI.getAll()).data,
  });

  const invalidateEvents = () => qc.invalidateQueries({ queryKey: queryKeys.events.list() });

  const registerMutation = useMutation({
    mutationFn: (eventId) => eventsAPI.register(eventId),
    onSuccess: () => {
      toast.success('Inscrição realizada com sucesso!');
      invalidateEvents();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao inscrever-se'),
  });

  const unregisterMutation = useMutation({
    mutationFn: (eventId) => eventsAPI.unregister(eventId),
    onSuccess: () => {
      toast.success('Inscrição cancelada');
      invalidateEvents();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao cancelar inscrição'),
  });

  const deleteMutation = useMutation({
    mutationFn: (eventId) => eventsAPI.delete(eventId),
    onSuccess: () => {
      toast.success('Evento eliminado');
      invalidateEvents();
    },
    onError: () => toast.error('Erro ao eliminar evento'),
  });

  const handleRegister = (eventId) => registerMutation.mutate(eventId);
  const handleUnregister = (eventId) => unregisterMutation.mutate(eventId);
  const handleDelete = (eventId) => deleteMutation.mutate(eventId);

  const filteredEvents = events.filter(event => {
    const eventDate = new Date(event.date);
    if (filter === 'upcoming') return isFuture(eventDate);
    if (filter === 'past') return isPast(eventDate);
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="events-title">
            Eventos & Agenda
          </h1>
          <p className="page-subtitle">Assembleias, formações e encontros da associação</p>
        </div>
        
        {isAdmin && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center justify-center gap-2 bg-floresta text-white px-4 py-2.5 rounded-lg hover:bg-floresta-dark transition-all text-sm font-semibold touch-target"
            data-testid="create-event-btn"
          >
            <Plus className="w-4 h-4" />
            Novo Evento
          </button>
        )}
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {['upcoming', 'past', 'all'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap touch-target ${
              filter === f ? 'bg-grafite text-white' : 'bg-white text-gray-500 hover:bg-gray-50 border border-gray-100'
            }`}
          >
            {f === 'upcoming' ? 'Próximos' : f === 'past' ? 'Realizados' : 'Todos'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-56 rounded-xl" />)}
        </div>
      ) : filteredEvents.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="Nenhum evento encontrado"
          description={isAdmin ? 'Clique em "Novo Evento" para criar' : 'Os eventos serão exibidos aqui quando disponíveis'}
          testId="no-events"
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {filteredEvents.map((event, index) => {
            const style = getStatusConfig(EVENT_TYPE_CONFIG, event.type, EVENT_TYPE_FALLBACK);
            const EventIcon = style.icon;
            const eventDate = new Date(event.date);
            const isPastEvent = isPast(eventDate);
            const isRegistered = event.attendees?.includes(user?.id);
            const isFull = event.max_attendees && event.attendees?.length >= event.max_attendees;

            return (
              <div key={event.id}
                className={`card-technical card-hover overflow-hidden border-l-4 ${style.border} ${isPastEvent ? 'opacity-70' : ''} animate-fade-up`}
                data-testid={`event-${event.id}`}>
                <div className="p-4 sm:p-6">
                  <div className="flex items-start justify-between mb-3 sm:mb-4">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <div className="w-10 h-10 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center flex-shrink-0">
                        <Calendar className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                      </div>
                      <div>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono uppercase ${style.className}`}>
                          <EventIcon className="w-3 h-3" aria-hidden="true" />
                          {style.label}
                        </span>
                        <div className="text-xs text-[#6B7280] mt-0.5">
                          {event.visibility === 'socios' ? 'Sócios' : event.visibility === 'direcao' ? 'Direção' : 'Público'}
                        </div>
                      </div>
                    </div>

                    {isAdmin && (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setFinanceEvent(event)}
                          className="p-1.5 text-grafite hover:bg-[#F5F5F5] rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                          aria-label="Finanças do evento"
                        >
                          <Wallet className="w-4 h-4" aria-hidden="true" />
                        </button>
                        <button
                          onClick={() => setConfirmDelete(event.id)}
                          className="p-1.5 text-[#C7202F] hover:bg-[#FBEAEC] rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                          aria-label="Eliminar evento"
                        >
                          <Trash2 className="w-4 h-4" aria-hidden="true" />
                        </button>
                      </div>
                    )}
                  </div>

                  <h3 className="font-semibold text-base sm:text-xl text-grafite mb-1 sm:mb-2 line-clamp-2">
                    {event.title}
                  </h3>
                  <p className="text-gray-500 text-xs sm:text-sm line-clamp-2 mb-3 sm:mb-4">
                    {event.description}
                  </p>

                  <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3 sm:mb-4 text-xs sm:text-sm text-gray-500">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-carmesim" />
                      <span>{format(eventDate, "dd MMM yyyy", { locale: ptBR })}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-carmesim" />
                      <span>{format(eventDate, 'HH:mm')}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-carmesim" />
                      <span className="truncate max-w-[200px]" title={event.location}>{event.location}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 sm:pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-1.5 text-xs sm:text-sm text-[#6B7280]">
                      <Users className="w-3.5 h-3.5" />
                      <span>
                        {event.attendees?.length || 0}
                        {event.max_attendees ? ` / ${event.max_attendees}` : ''} inscritos
                      </span>
                    </div>

                    {!isPastEvent && (
                      <>
                        {isRegistered ? (
                          <button
                            onClick={() => handleUnregister(event.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F0FDF4] text-[#15803D] rounded-lg hover:bg-[#DCFCE7] transition-colors font-medium text-xs sm:text-sm"
                          >
                            <UserCheck className="w-3.5 h-3.5" />
                            Inscrito
                          </button>
                        ) : isFull ? (
                          <span className="flex items-center gap-1.5 px-3 py-1.5 bg-[#FEF2F2] text-[#B91C1C] rounded-lg text-xs sm:text-sm">
                            Lotado
                          </span>
                        ) : (
                          <button
                            onClick={() => handleRegister(event.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#D1D5DB] text-[#3A3A3A] rounded-lg hover:bg-[#F5F5F5] transition-colors font-semibold text-xs sm:text-sm"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            Inscrever-me
                          </button>
                        )}
                      </>
                    )}

                    {isPastEvent && (
                      <span className="text-xs text-[#6B7280]">Realizado</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {financeEvent && (
          <EventFinanceDialog event={financeEvent} onClose={() => setFinanceEvent(null)} />
      )}

      {showModal && (
          <CreateEventModal
            onClose={() => setShowModal(false)}
          />
        )}
      <AlertDialog open={!!confirmDelete} onOpenChange={(open) => !open && setConfirmDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar evento</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja eliminar este evento? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-[#C7202F] hover:bg-[#A51B27]"
              onClick={() => { handleDelete(confirmDelete); setConfirmDelete(null); }}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

// Categorias de despesa (espelham backend EXPENSE_CATEGORIES). A despesa de
// evento é uma transação no caixa e exige categoria (spec-eventos-multas-caixa).
const EXPENSE_CATS = [
  ['operacional', 'Operacional'],
  ['eventos', 'Eventos'],
  ['juridico', 'Jurídico'],
  ['comunicacao', 'Comunicação'],
  ['viagens', 'Viagens'],
  ['outros_despesa', 'Outras Despesas'],
];
const fmtCve = (v) => `${Number(v || 0).toLocaleString('pt-PT')} CVE`;

// Finanças de evento: despesas + receitas + resultado, tudo ligado ao caixa central.
const EventFinanceDialog = ({ event, onClose }) => {
  const qc = useQueryClient();
  const eid = event.id;
  const [tab, setTab] = useState('despesa');
  const [form, setForm] = useState({ description: '', amount: '', category: 'eventos' });

  const detail = useQuery({
    queryKey: queryKeys.events.byId(eid),
    queryFn: async () => (await eventsAPI.getById(eid)).data,
  });
  const expenses = useQuery({
    queryKey: queryKeys.events.expenses(eid),
    queryFn: async () => (await eventsAPI.getExpenses(eid)).data.items,
  });
  const receitas = useQuery({
    queryKey: queryKeys.events.receitas(eid),
    queryFn: async () => (await eventsAPI.getReceitas(eid)).data.items,
  });
  const r = detail.data?.resultado_financeiro || { receitas: 0, despesas: 0, resultado: 0 };

  // byId(eid) = ['events', eid] é prefixo de detail/expenses/receitas → invalida as três.
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: queryKeys.events.byId(eid) });
  };

  const addMut = useMutation({
    mutationFn: () => {
      const payload = { description: form.description.trim(), amount: parseFloat(form.amount) };
      return tab === 'despesa'
        ? eventsAPI.addExpense(eid, { ...payload, category: form.category })
        : eventsAPI.addReceita(eid, payload);
    },
    onSuccess: () => {
      setForm({ description: '', amount: '', category: 'eventos' });
      invalidate();
      toast.success(tab === 'despesa' ? 'Despesa registada' : 'Receita registada');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao registar'),
  });

  const delMut = useMutation({
    mutationFn: ({ kind, txId }) =>
      kind === 'despesa' ? eventsAPI.deleteExpense(eid, txId) : eventsAPI.deleteReceita(eid, txId),
    onSuccess: () => { invalidate(); toast.success('Movimento removido'); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao remover'),
  });

  const canSubmit = form.description.trim() && parseFloat(form.amount) > 0 && !addMut.isPending;
  const rows = tab === 'despesa' ? (expenses.data || []) : (receitas.data || []);

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-2xl rounded-xl max-h-[90vh] overflow-y-auto" data-testid="event-finance-dialog">
        <DialogHeader>
          <DialogTitle>Finanças — {event.title}</DialogTitle>
        </DialogHeader>

        {/* Resultado do evento */}
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-lg border border-[#E5E7EB] p-3">
            <div className="text-xs text-[#6B7280] uppercase">Receitas</div>
            <div className="font-mono font-bold text-grafite">{fmtCve(r.receitas)}</div>
          </div>
          <div className="rounded-lg border border-[#E5E7EB] p-3">
            <div className="text-xs text-[#6B7280] uppercase">Despesas</div>
            <div className="font-mono font-bold text-grafite">{fmtCve(r.despesas)}</div>
          </div>
          <div className="rounded-lg border border-[#E5E7EB] p-3">
            <div className="text-xs text-[#6B7280] uppercase">Resultado</div>
            <div className={`font-mono font-bold flex items-center gap-1 ${r.resultado >= 0 ? 'text-[#15803D]' : 'text-[#C7202F]'}`}>
              {r.resultado >= 0
                ? <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" />
                : <TrendingDown className="w-3.5 h-3.5" aria-hidden="true" />}
              <span>{fmtCve(r.resultado)}</span>
              <span className="sr-only">{r.resultado >= 0 ? 'positivo' : 'défice'}</span>
            </div>
          </div>
        </div>

        {/* Tabs despesa/receita */}
        <div className="flex gap-2 mt-2">
          {['despesa', 'receita'].map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 ${tab === t ? 'bg-[#F5F5F5] text-grafite' : 'text-[#6B7280] hover:bg-[#F5F5F5]'}`}>
              {t === 'despesa' ? 'Despesas' : 'Receitas'}
            </button>
          ))}
        </div>

        {/* Formulário */}
        <div className="flex flex-wrap items-end gap-2 border border-[#E5E7EB] rounded-lg p-3">
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs text-[#6B7280] mb-1">Descrição</label>
            <input type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 outline-none" data-testid="event-fin-desc" />
          </div>
          <div className="w-28">
            <label className="block text-xs text-[#6B7280] mb-1">Valor (CVE)</label>
            <input type="number" min="0" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })}
              className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 outline-none" data-testid="event-fin-amount" />
          </div>
          {tab === 'despesa' && (
            <div className="w-40">
              <label className="block text-xs text-[#6B7280] mb-1">Categoria</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 outline-none" data-testid="event-fin-cat">
                {EXPENSE_CATS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
          )}
          <button onClick={() => addMut.mutate()} disabled={!canSubmit}
            className="inline-flex items-center gap-1.5 bg-floresta text-white px-4 py-2 rounded-md text-sm font-semibold hover:bg-floresta-dark disabled:opacity-60 cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
            data-testid="event-fin-submit">
            {addMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Registar
          </button>
        </div>

        {/* Lista */}
        <div className="border border-[#E5E7EB] rounded-lg overflow-hidden">
          {rows.length === 0 ? (
            <p className="text-sm text-[#6B7280] p-4 text-center">Sem {tab === 'despesa' ? 'despesas' : 'receitas'} registadas.</p>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-sm">
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id} className="border-b border-[#F5F5F5]" data-testid={`event-fin-row-${t.id}`}>
                    <td className="px-3 py-2 text-grafite">{t.description}{t.ato_id && <span className="ml-1.5 text-[10px] text-[#6B7280] uppercase">(co-aprovado)</span>}</td>
                    <td className="px-3 py-2 text-right font-mono">{fmtCve(t.amount)}</td>
                    <td className="px-3 py-2 text-xs text-[#6B7280]">{(t.date || '').slice(0, 10)}</td>
                    <td className="px-3 py-2 w-8">
                      <button onClick={() => delMut.mutate({ kind: tab, txId: t.id })} className="text-[#6B7280] hover:text-[#C7202F] cursor-pointer" aria-label="Remover movimento">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

const CreateEventModal = ({ onClose }) => {
  const qc = useQueryClient();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'assembleia',
    date: '',
    time: '',
    location: '',
    visibility: 'socios',
    max_attendees: '',
  });

  const createMutation = useMutation({
    mutationFn: (payload) => eventsAPI.create(payload),
    onSuccess: () => {
      toast.success('Evento criado com sucesso!');
      qc.invalidateQueries({ queryKey: queryKeys.events.list() });
      onClose();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar evento'),
  });

  const submitting = createMutation.isPending;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title || !formData.date || !formData.time || !formData.location) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }
    const dateTime = new Date(`${formData.date}T${formData.time}`);
    createMutation.mutate({
      title: formData.title,
      description: formData.description,
      type: formData.type,
      date: dateTime.toISOString(),
      location: formData.location,
      visibility: formData.visibility,
      max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : null,
    });
  };

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg rounded-xl p-0 gap-0 max-h-[90vh] overflow-y-auto" data-testid="create-event-modal">
        <DialogHeader className="p-4 sm:p-6 border-b border-gray-200 text-left space-y-0">
          <DialogTitle className="font-bold text-xl sm:text-2xl text-grafite">Novo Evento</DialogTitle>
        </DialogHeader>

          <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4 sm:space-y-5">
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Titulo *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                placeholder="Ex: Assembleia Geral Ordinaria"
                required
              />
            </div>

            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Descricao</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 resize-none"
                rows={3}
                placeholder="Detalhes do evento..."
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Tipo *</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                >
                  <option value="assembleia">Assembleia</option>
                  <option value="formacao">Formacao</option>
                  <option value="social">Social</option>
                  <option value="reuniao">Reuniao</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Visibilidade</label>
                <select
                  value={formData.visibility}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                >
                  <option value="publico">Público</option>
                  <option value="socios">Sócios</option>
                  <option value="direcao">Direção</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Data *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  required
                />
              </div>
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Hora *</label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Local *</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                placeholder="Ex: Sede da ACCTA, Praia"
                required
              />
            </div>

            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-[#6B7280] mb-1.5">Limite de Participantes</label>
              <input
                type="number"
                inputMode="numeric"
                value={formData.max_attendees}
                onChange={(e) => setFormData({ ...formData, max_attendees: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                placeholder="Deixe vazio para ilimitado"
                min="1"
              />
            </div>

            <div className="flex gap-3 sm:gap-4 pt-3 sm:pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2.5 bg-white border border-[#D1D5DB] text-[#3A3A3A] rounded-lg hover:bg-[#F5F5F5] transition-colors text-sm font-semibold"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 bg-floresta text-white px-4 py-2.5 rounded-lg hover:bg-floresta-dark transition-colors text-sm font-semibold disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Criar
              </button>
            </div>
          </form>
      </DialogContent>
    </Dialog>
  );
};
