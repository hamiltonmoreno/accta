import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { eventsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  Users,
  Plus,
  X,
  Check,
  Loader2,
  UserCheck,
  Trash2
} from 'lucide-react';
import { format, isFuture, isPast } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const getEventStyle = (type) => {
  const styles = {
    assembleia: { color: 'bg-blue-100 text-blue-700', border: 'border-blue-500' },
    formacao: { color: 'bg-green-100 text-green-700', border: 'border-green-500' },
    social: { color: 'bg-pink-100 text-pink-700', border: 'border-pink-500' },
    reuniao: { color: 'bg-amber-100 text-amber-700', border: 'border-amber-500' },
    outro: { color: 'bg-slate-100 text-slate-700', border: 'border-slate-500' },
  };
  return styles[type] || styles.outro;
};

const getEventLabel = (type) => {
  const labels = {
    assembleia: 'Assembleia',
    formacao: 'Formação',
    social: 'Social',
    reuniao: 'Reunião',
    outro: 'Outro',
  };
  return labels[type] || 'Outro';
};

export const EventosPage = () => {
  const { user, isAdmin } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('upcoming');
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const response = await eventsAPI.getAll();
      setEvents(response.data);
    } catch (error) {
      console.error('Erro ao carregar eventos:', error);
      toast.error('Erro ao carregar eventos');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (eventId) => {
    try {
      await eventsAPI.register(eventId);
      toast.success('Inscrição realizada com sucesso!');
      loadEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao inscrever-se');
    }
  };

  const handleUnregister = async (eventId) => {
    try {
      await eventsAPI.unregister(eventId);
      toast.success('Inscrição cancelada');
      loadEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao cancelar inscrição');
    }
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm('Tem certeza que deseja eliminar este evento?')) return;
    try {
      await eventsAPI.delete(eventId);
      toast.success('Evento eliminado');
      loadEvents();
    } catch (error) {
      toast.error('Erro ao eliminar evento');
    }
  };

  const filteredEvents = events.filter(event => {
    const eventDate = new Date(event.date);
    if (filter === 'upcoming') return isFuture(eventDate);
    if (filter === 'past') return isPast(eventDate);
    return true;
  });

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="events-title">
            Eventos & Agenda
          </h1>
          <p className="text-slate-600">Assembleias, formações e encontros da associação</p>
        </div>
        
        {isAdmin && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-all font-mono text-sm uppercase tracking-wider"
            data-testid="create-event-btn"
          >
            <Plus className="w-4 h-4" />
            Novo Evento
          </button>
        )}
      </div>

      <div className="flex gap-3">
        {['upcoming', 'past', 'all'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
              filter === f ? 'bg-primary text-white' : 'bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            {f === 'upcoming' ? 'Próximos' : f === 'past' ? 'Realizados' : 'Todos'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="card-technical rounded-xl p-12 text-center">
          <Calendar className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 font-medium mb-1">Nenhum evento encontrado</p>
          <p className="text-sm text-slate-400">
            {isAdmin ? 'Clique em "Novo Evento" para criar' : 'Os eventos serão exibidos aqui quando disponíveis'}
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {filteredEvents.map((event, index) => {
            const style = getEventStyle(event.type);
            const eventDate = new Date(event.date);
            const isPastEvent = isPast(eventDate);
            const isRegistered = event.attendees?.includes(user?.id);
            const isFull = event.max_attendees && event.attendees?.length >= event.max_attendees;

            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`card-technical rounded-xl overflow-hidden border-l-4 ${style.border} ${isPastEvent ? 'opacity-70' : ''}`}
                data-testid={`event-${event.id}`}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
                        <Calendar className="w-6 h-6 text-accent" />
                      </div>
                      <div>
                        <span className={`inline-block px-2 py-1 rounded text-xs font-mono uppercase ${style.color}`}>
                          {getEventLabel(event.type)}
                        </span>
                        <div className="text-xs text-slate-500 mt-1">
                          {event.visibility === 'socios' ? 'Sócios' : event.visibility === 'direcao' ? 'Direção' : 'Público'}
                        </div>
                      </div>
                    </div>

                    {isAdmin && (
                      <button
                        onClick={() => handleDelete(event.id)}
                        className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <h3 className="font-outfit font-semibold text-xl text-primary mb-2">
                    {event.title}
                  </h3>
                  <p className="text-slate-600 text-sm line-clamp-2 mb-4">
                    {event.description}
                  </p>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Calendar className="w-4 h-4 text-accent" />
                      <span>{format(eventDate, "dd MMM yyyy", { locale: ptBR })}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Clock className="w-4 h-4 text-accent" />
                      <span>{format(eventDate, 'HH:mm')}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-600 col-span-2">
                      <MapPin className="w-4 h-4 text-accent" />
                      <span className="line-clamp-1">{event.location}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Users className="w-4 h-4" />
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
                            className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors font-medium text-sm"
                          >
                            <UserCheck className="w-4 h-4" />
                            Inscrito
                          </button>
                        ) : isFull ? (
                          <span className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-600 rounded-lg text-sm">
                            Lotado
                          </span>
                        ) : (
                          <button
                            onClick={() => handleRegister(event.id)}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm"
                          >
                            <Plus className="w-4 h-4" />
                            Inscrever-me
                          </button>
                        )}
                      </>
                    )}

                    {isPastEvent && (
                      <span className="text-sm text-slate-400">Evento realizado</span>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      <AnimatePresence>
        {showModal && (
          <CreateEventModal
            onClose={() => setShowModal(false)}
            onSuccess={() => {
              setShowModal(false);
              loadEvents();
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

const CreateEventModal = ({ onClose, onSuccess }) => {
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
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.date || !formData.time || !formData.location) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    setSubmitting(true);
    try {
      const dateTime = new Date(`${formData.date}T${formData.time}`);
      await eventsAPI.create({
        title: formData.title,
        description: formData.description,
        type: formData.type,
        date: dateTime.toISOString(),
        location: formData.location,
        visibility: formData.visibility,
        max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : null,
      });
      toast.success('Evento criado com sucesso!');
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar evento');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between p-6 border-b border-slate-200">
            <h2 className="font-outfit font-bold text-2xl text-primary">Novo Evento</h2>
            <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Título *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Ex: Assembleia Geral Ordinária"
                required
              />
            </div>

            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Descrição</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3}
                placeholder="Detalhes do evento..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Tipo *</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="assembleia">Assembleia</option>
                  <option value="formacao">Formação</option>
                  <option value="social">Evento Social</option>
                  <option value="reuniao">Reunião</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Visibilidade</label>
                <select
                  value={formData.visibility}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="publico">Público</option>
                  <option value="socios">Sócios</option>
                  <option value="direcao">Direção</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Data *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Hora *</label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Local *</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Ex: Sede da ACCTA, Praia"
                required
              />
            </div>

            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-slate-500 mb-2">Limite de Participantes</label>
              <input
                type="number"
                value={formData.max_attendees}
                onChange={(e) => setFormData({ ...formData, max_attendees: e.target.value })}
                className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Deixe vazio para ilimitado"
                min="1"
              />
            </div>

            <div className="flex gap-4 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-3 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 transition-colors font-mono uppercase tracking-wider"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 bg-primary text-white px-4 py-3 rounded-lg hover:bg-primary/90 transition-colors font-mono uppercase tracking-wider disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Criar Evento
              </button>
            </div>
          </form>
        </div>
      </motion.div>
    </>
  );
};
