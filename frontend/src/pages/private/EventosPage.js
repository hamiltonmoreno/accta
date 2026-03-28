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
    outro: { color: 'bg-gray-100 text-gray-700', border: 'border-gray-500' },
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
    <div className="space-y-5 sm:space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <h1 className="page-title" data-testid="events-title">
            Eventos & Agenda
          </h1>
          <p className="page-subtitle">Assembleias, formacoes e encontros da associacao</p>
        </div>
        
        {isAdmin && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center justify-center gap-2 bg-grafite text-white px-4 py-2.5 rounded-lg hover:bg-grafite/90 transition-all font-mono text-xs uppercase tracking-wider touch-target"
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
            className={`px-3 sm:px-4 py-2 rounded-lg font-mono text-xs uppercase tracking-wider transition-all whitespace-nowrap touch-target ${
              filter === f ? 'bg-grafite text-white' : 'bg-white text-gray-500 hover:bg-gray-50 border border-gray-100'
            }`}
          >
            {f === 'upcoming' ? 'Próximos' : f === 'past' ? 'Realizados' : 'Todos'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-grafite" />
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="card-technical rounded-xl p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-medium mb-1">Nenhum evento encontrado</p>
          <p className="text-sm text-gray-400">
            {isAdmin ? 'Clique em "Novo Evento" para criar' : 'Os eventos serão exibidos aqui quando disponíveis'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
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
                className={`card-technical card-hover overflow-hidden border-l-4 ${style.border} ${isPastEvent ? 'opacity-70' : ''}`}
                data-testid={`event-${event.id}`}
              >
                <div className="p-4 sm:p-6">
                  <div className="flex items-start justify-between mb-3 sm:mb-4">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <div className="w-10 h-10 sm:w-12 sm:h-12 bg-grafite rounded-lg flex items-center justify-center flex-shrink-0">
                        <Calendar className="w-5 h-5 sm:w-6 sm:h-6 text-carmesim" />
                      </div>
                      <div>
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] sm:text-xs font-mono uppercase ${style.color}`}>
                          {getEventLabel(event.type)}
                        </span>
                        <div className="text-[10px] sm:text-xs text-gray-400 mt-0.5">
                          {event.visibility === 'socios' ? 'Sócios' : event.visibility === 'direcao' ? 'Direção' : 'Público'}
                        </div>
                      </div>
                    </div>

                    {isAdmin && (
                      <button
                        onClick={() => handleDelete(event.id)}
                        className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
                      <span className="truncate max-w-[200px]">{event.location}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 sm:pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-1.5 text-xs sm:text-sm text-gray-400">
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
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors font-medium text-xs sm:text-sm"
                          >
                            <UserCheck className="w-3.5 h-3.5" />
                            Inscrito
                          </button>
                        ) : isFull ? (
                          <span className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-500 rounded-lg text-xs sm:text-sm">
                            Lotado
                          </span>
                        ) : (
                          <button
                            onClick={() => handleRegister(event.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-grafite text-white rounded-lg hover:bg-grafite/90 transition-colors font-medium text-xs sm:text-sm"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            Inscrever-me
                          </button>
                        )}
                      </>
                    )}

                    {isPastEvent && (
                      <span className="text-xs text-gray-400">Realizado</span>
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
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200">
            <h2 className="font-bold text-xl sm:text-2xl text-grafite">Novo Evento</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4 sm:space-y-5">
            <div>
              <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Titulo *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                placeholder="Ex: Assembleia Geral Ordinaria"
                required
              />
            </div>

            <div>
              <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Descricao</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40 resize-none"
                rows={3}
                placeholder="Detalhes do evento..."
              />
            </div>

            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Tipo *</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                >
                  <option value="assembleia">Assembleia</option>
                  <option value="formacao">Formacao</option>
                  <option value="social">Social</option>
                  <option value="reuniao">Reuniao</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div>
                <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Visibilidade</label>
                <select
                  value={formData.visibility}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                >
                  <option value="publico">Público</option>
                  <option value="socios">Sócios</option>
                  <option value="direcao">Direção</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Data *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                  required
                />
              </div>
              <div>
                <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Hora *</label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Local *</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                placeholder="Ex: Sede da ACCTA, Praia"
                required
              />
            </div>

            <div>
              <label className="block font-mono text-[10px] sm:text-xs uppercase tracking-wider text-gray-400 mb-1.5">Limite de Participantes</label>
              <input
                type="number"
                value={formData.max_attendees}
                onChange={(e) => setFormData({ ...formData, max_attendees: e.target.value })}
                className="w-full px-3 sm:px-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim/40"
                placeholder="Deixe vazio para ilimitado"
                min="1"
              />
            </div>

            <div className="flex gap-3 sm:gap-4 pt-3 sm:pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors font-mono text-xs uppercase tracking-wider"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 bg-grafite text-white px-4 py-2.5 rounded-lg hover:bg-grafite/90 transition-colors font-mono text-xs uppercase tracking-wider disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Criar
              </button>
            </div>
          </form>
        </div>
      </motion.div>
    </>
  );
};
