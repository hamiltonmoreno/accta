import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { PageBanner } from '../../components/PageBanner';
import { PortugueseContentNotice } from '../../components/PortugueseContentNotice';
import { useI18n } from '../../i18n';
import { useFormatDate } from '../../i18n/dates';
import { usePageMeta } from '../../i18n/usePageMeta';

const eventTypeConfig = {
  assembleia: { icon: CalendarDays, color: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  formacao: { icon: GraduationCap, color: 'bg-[#F0FDF4] text-[#15803D]' },
  social: { icon: PartyPopper, color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  reuniao: { icon: Handshake, color: 'bg-[#FFFBEB] text-[#B45309]' },
  outro: { icon: Megaphone, color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
};

export const EventosPublicoPage = () => {
  const [filter, setFilter] = useState('upcoming'); // upcoming, past, all
  const { t, lp } = useI18n();
  const formatDate = useFormatDate();
  usePageMeta('eventos');

  const { data: events = [], isLoading: loading } = useQuery({
    queryKey: ['publicEvents'],
    queryFn: async () => (await eventsAPI.getPublic()).data,
  });

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
        badge={t('eventos.banner.badge')}
        title={t('eventos.banner.title')}
        subtitle={t('eventos.banner.subtitle')}
      />

      {/* Stats */}
      <section className="py-8 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-center gap-8">
            <div className="text-center">
              <div className="font-sans font-bold text-3xl text-grafite">{upcomingEvents.length}</div>
              <div className="text-sm text-gray-500">{t('eventos.stats.upcoming')}</div>
            </div>
            <div className="text-center">
              <div className="font-sans font-bold text-3xl text-[#6B7280]">{pastEvents.length}</div>
              <div className="text-sm text-gray-500">{t('eventos.stats.past')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Events List */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          {/* Filters */}
          <div className="flex flex-wrap justify-center gap-3 sm:gap-4 mb-12">
            {['upcoming', 'past', 'all'].map((value) => ({ value, label: t(`eventos.filters.${value}`) })).map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 ${
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
              title={filter === 'upcoming' ? t('eventos.empty.upcoming') : t('eventos.empty.other')}
              description={t('eventos.empty.description')}
            />
          ) : (
            <>
            <PortugueseContentNotice className="mb-6" />
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
                            {formatDate(eventDate, 'MMM yyyy')}
                          </div>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-xs uppercase ${typeConfig.color}`}>
                          {t(`eventos.types.${eventTypeConfig[event.type] ? event.type : 'outro'}`)}
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
                          <span>{formatDate(eventDate, 'HH:mm')}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <MapPin className="w-4 h-4" />
                          <span className="line-clamp-1">{event.location}</span>
                        </div>
                      </div>

                      {isPastEvent ? (
                        <span className="inline-flex items-center gap-2 text-[#6B7280] font-medium text-sm">
                          {t('eventos.card.past')}
                        </span>
                      ) : (
                        <Link
                          to={lp('/login')}
                          className="inline-flex items-center gap-2 text-grafite font-semibold text-sm hover:text-carmesim transition-colors"
                        >
                          {t('eventos.card.loginToRegister')}
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            </>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-grafite">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-3xl text-white mb-6">
            {t('eventos.cta.title')}
          </h2>
          <p className="text-lg text-white/80 mb-8">
            {t('eventos.cta.subtitle')}
          </p>
          <Link
            to={lp('/login')}
            className="inline-flex items-center gap-2 bg-floresta text-white px-8 py-4 rounded-lg font-bold hover:bg-floresta-dark transition-all"
          >
            {t('eventos.cta.button')}
            <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
};
