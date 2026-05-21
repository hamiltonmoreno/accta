import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { PageBanner } from '../../components/PageBanner';

const eventTypeConfig = {
  assembleia: { icon: CalendarDays, label: 'Assembleia', color: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  formacao: { icon: GraduationCap, label: 'Formação', color: 'bg-[#F0FDF4] text-[#15803D]' },
  social: { icon: PartyPopper, label: 'Evento Social', color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  reuniao: { icon: Handshake, label: 'Reunião', color: 'bg-[#FFFBEB] text-[#B45309]' },
  outro: { icon: Megaphone, label: 'Outro', color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
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
      <PageBanner
        pageKey="eventos"
        badge="Agenda"
        title="Eventos da ACCTA"
        subtitle="Assembleias, formações, encontros e mais. Fique por dentro da agenda da associação."
      />

      {/* Stats */}
      <section className="py-8 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-center gap-8">
            <div className="text-center">
              <div className="font-sans font-bold text-3xl text-grafite">{upcomingEvents.length}</div>
              <div className="text-sm text-gray-500">Próximos Eventos</div>
            </div>
            <div className="text-center">
              <div className="font-sans font-bold text-3xl text-[#6B7280]">{pastEvents.length}</div>
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
                className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all ${
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
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8" data-testid="events-loading">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-72 rounded-xl" />
              ))}
            </div>
          ) : filteredEvents.length === 0 ? (
            <EmptyState
              icon={Calendar}
              title={filter === 'upcoming' ? 'Nenhum evento programado' : 'Nenhum evento encontrado'}
              description="Os eventos públicos serão exibidos aqui quando disponíveis"
            />
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredEvents.map((event, index) => {
                const typeConfig = eventTypeConfig[event.type] || eventTypeConfig.outro;
                const IconComponent = typeConfig.icon;
                const eventDate = new Date(event.date);
                const isPastEvent = isPast(eventDate);

                return (
                  <div key={event.id}
                    className={`card-technical rounded-xl overflow-hidden ${isPastEvent ? 'opacity-70' : ''} animate-fade-up`}
                    data-testid={`event-${event.id}`}>
                    {/* Date Header */}
                    <div className="bg-grafite px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-sans font-bold text-3xl text-white">
                            {format(eventDate, 'dd')}
                          </div>
                          <div className="text-white uppercase text-sm">
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
                        <span className="inline-flex items-center gap-2 text-[#6B7280] font-medium text-sm">
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
                  </div>
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
            className="inline-flex items-center gap-2 bg-carmesim text-white px-8 py-4 rounded-lg font-bold hover:bg-carmesim/90 transition-all"
          >
            Entrar na Área do Associado
            <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
