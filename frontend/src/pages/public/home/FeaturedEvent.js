import React, { useCallback, useEffect, useState } from 'react';
import { Calendar, Clock, MapPin, Users } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const calcCountdown = (dateStr) => {
  const target = new Date(dateStr).getTime();
  const now = Date.now();
  const diff = Math.max(0, target - now);
  return {
    days: Math.floor(diff / 86400000),
    hours: Math.floor((diff % 86400000) / 3600000),
    minutes: Math.floor((diff % 3600000) / 60000),
    seconds: Math.floor((diff % 60000) / 1000),
  };
};

// Placeholder reserva espaço enquanto carrega (evita CLS); colapsa para nada
// quando não há evento (renderiza null).
export const FeaturedEvent = ({ event, loading }) => {
  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const tick = useCallback(() => event && setCountdown(calcCountdown(event.date)), [event]);

  useEffect(() => {
    if (!event) return undefined;
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [event, tick]);

  if (loading) {
    return (
      <section className="py-8 sm:py-10 bg-white border-b border-gray-100" aria-hidden="true" data-testid="featured-event-skeleton">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="rounded-2xl bg-grafite/5 animate-pulse min-h-[260px] sm:min-h-[220px] lg:min-h-[200px]" />
        </div>
      </section>
    );
  }

  if (!event) return null;

  return (
    <section className="py-8 sm:py-10 bg-white border-b border-gray-100" data-testid="featured-event-section">
      <div className="max-w-7xl mx-auto px-5 sm:px-6">
        <div className="relative overflow-hidden rounded-2xl bg-grafite p-5 sm:p-7 lg:p-8">
          <div className="relative z-10 grid lg:grid-cols-2 gap-8 items-center">
            {/* Event Info */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-carmesim/20 border border-carmesim/30 rounded-full mb-4 sm:mb-5">
                <Calendar className="w-3.5 h-3.5 text-white" />
                <span className="text-xs text-white font-semibold uppercase tracking-wider">Próximo evento</span>
              </div>
              <h2 className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-3" data-testid="featured-event-title">
                {event.title}
              </h2>
              <p className="text-sm sm:text-base text-white/70 leading-relaxed mb-5 max-w-md">
                {event.description?.slice(0, 150)}{event.description?.length > 150 ? '...' : ''}
              </p>
              <div className="flex flex-wrap gap-4 text-sm text-white/80">
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-white/60" />
                  <span>{format(new Date(event.date), "dd 'de' MMMM yyyy", { locale: ptBR })}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-white/60" />
                  <span>{format(new Date(event.date), 'HH:mm')}</span>
                </div>
                {event.location && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-white/60" />
                    <span>{event.location}</span>
                  </div>
                )}
              </div>
              {event.attendee_count > 0 && (
                <div className="mt-4 flex items-center gap-2 text-xs text-white/50">
                  <Users className="w-3.5 h-3.5" />
                  <span>{event.attendee_count} inscrito{event.attendee_count !== 1 ? 's' : ''}</span>
                </div>
              )}
            </div>

            {/* Countdown */}
            <div className="flex justify-center lg:justify-end">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4" data-testid="countdown-timer">
                {[
                  { value: countdown.days, label: 'Dias' },
                  { value: countdown.hours, label: 'Horas' },
                  { value: countdown.minutes, label: 'Min' },
                  { value: countdown.seconds, label: 'Seg' },
                ].map((unit) => (
                  <div key={unit.label} className="flex flex-col items-center animate-fade-up">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex items-center justify-center mb-2">
                      <span className="font-bold text-xl sm:text-2xl text-white font-mono" data-testid={`countdown-${unit.label.toLowerCase()}`}>
                        {String(unit.value).padStart(2, '0')}
                      </span>
                    </div>
                    <span className="text-xs text-white/50 uppercase tracking-widest font-semibold">{unit.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
