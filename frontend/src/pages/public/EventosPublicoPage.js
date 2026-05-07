import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { eventsAPI } from '../../utils/api';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  Users,
  ChevronRight,
  CalendarDays,
  GraduationCap,
  PartyPopper,
  Handshake,
  Megaphone
} from 'lucide-react';
import { format, isFuture, isPast } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const eventTypeConfig = {
  assembleia: { icon: CalendarDays, label: 'Assembleia', color: 'bg-blue-100 text-blue-700' },
  formacao: { icon: GraduationCap, label: 'Formação', color: 'bg-green-100 text-green-700' },
  social: { icon: PartyPopper, label: 'Evento Social', color: 'bg-pink-100 text-pink-700' },
  reuniao: { icon: Handshake, label: 'Reunião', color: 'bg-amber-100 text-amber-700' },
  outro: { icon: Megaphone, label: 'Outro', color: 'bg-gray-100 text-gray-700' },
};

export const EventosPublicoPage = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('upcoming'); // upcoming, past, all

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const response = await eventsAPI.getPublic();
      setEvents(response.data);
    } catch (error) {
      console.error('Erro ao carregar eventos:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = events.filter(event => {
    const eventDate = new Date(event.date);
    if (filter === 'upcoming') return isFuture(eventDate);
    if (filter === 'past') return isPast(eventDate);
    return true;
  });

  const upcomingEvents = events.filter(e => isFuture(new Date(e.date)));
  const pastEvents = events.filter(e => isPast(new Date(e.date)));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-24 bg-grafite overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'linear-gradient(rgba(0,255,156,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,156,0.3) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <span className="inline-block px-4 py-2 bg-carmesim/10 border border-carmesim/30 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Agenda
            </span>
            <h1 className="font-sans font-bold text-5xl lg:text-6xl text-white mb-6" data-testid="events-title">
              Eventos da{' '}
              <span className="text-carmesim">ACCTA</span>
            </h1>
            <p className="text-xl text-white/80 max-w-3xl mx-auto leading-relaxed">
              Assembleias, formações, encontros e mais. Fique por dentro da agenda da associação.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-8 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-center gap-8">
            <div className="text-center">
              <div className="font-sans font-bold text-3xl text-grafite">{upcomingEvents.length}</div>
              <div className="text-sm text-gray-500">Próximos Eventos</div>
            </div>
            <div className="text-center">
              <div className="font-sans font-bold text-3xl text-gray-400">{pastEvents.length}</div>
              <div className="text-sm text-gray-500">Eventos Realizados</div>
            </div>
          </div>
        </div>
      </section>

      {/* Events List */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          {/* Filters */}
          <div className="flex justify-center gap-4 mb-12">
            {[
              { value: 'upcoming', label: 'Próximos' },
              { value: 'past', label: 'Realizados' },
              { value: 'all', label: 'Todos' },
            ].map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`px-6 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
                  filter === f.value
                    ? 'bg-grafite text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
                data-testid={`filter-${f.value}`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="text-center py-16">
              <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 font-medium mb-2">
                {filter === 'upcoming' ? 'Nenhum evento programado' : 'Nenhum evento encontrado'}
              </p>
              <p className="text-sm text-gray-400">
                Os eventos públicos serão exibidos aqui quando disponíveis
              </p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredEvents.map((event, index) => {
                const typeConfig = eventTypeConfig[event.type] || eventTypeConfig.outro;
                const IconComponent = typeConfig.icon;
                const eventDate = new Date(event.date);
                const isPastEvent = isPast(eventDate);

                return (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`card-technical rounded-xl overflow-hidden ${isPastEvent ? 'opacity-70' : ''}`}
                    data-testid={`event-${event.id}`}
                  >
                    {/* Date Header */}
                    <div className="bg-grafite px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-sans font-bold text-3xl text-white">
                            {format(eventDate, 'dd')}
                          </div>
                          <div className="text-carmesim uppercase text-sm">
                            {format(eventDate, 'MMM yyyy', { locale: ptBR })}
                          </div>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-xs uppercase ${typeConfig.color}`}>
                          {typeConfig.label}
                        </div>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                      <h3 className="font-sans font-semibold text-xl text-grafite mb-3 line-clamp-2">
                        {event.title}
                      </h3>
                      <p className="text-gray-600 text-sm line-clamp-2 mb-4">
                        {event.description}
                      </p>

                      <div className="space-y-2 mb-4">
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Clock className="w-4 h-4" />
                          <span>{format(eventDate, 'HH:mm', { locale: ptBR })}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <MapPin className="w-4 h-4" />
                          <span className="line-clamp-1">{event.location}</span>
                        </div>
                      </div>

                      {isPastEvent ? (
                        <span className="inline-flex items-center gap-2 text-gray-400 font-medium text-sm">
                          Evento realizado
                        </span>
                      ) : (
                        <Link
                          to="/login"
                          className="inline-flex items-center gap-2 text-grafite font-semibold text-sm hover:text-carmesim transition-colors"
                        >
                          Fazer login para inscrever-se
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-grafite">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-3xl text-white mb-6">
            É associado? Aceda a todos os eventos
          </h2>
          <p className="text-lg text-white/80 mb-8">
            Os sócios têm acesso a eventos exclusivos e podem inscrever-se diretamente pela plataforma
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 bg-carmesim text-grafite px-8 py-4 rounded-lg font-bold hover:bg-carmesim/90 transition-all"
          >
            Entrar na Área do Associado
            <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
