import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Clock, MapPin } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const UpcomingEvents = ({ events }) => {
  const navigate = useNavigate();
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden animate-fade-up">
      <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-grafite">Proximos Eventos</h2>
        <button
          onClick={() => navigate('/eventos')}
          className="text-xs text-carmesim hover:text-carmesim-dark font-semibold flex items-center gap-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
        >
          Ver todos <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Desktop: Table style */}
      <div className="hidden md:block">
        <table className="w-full">
          <thead className="bg-gray-50/80">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Evento</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Data</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Local</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Hora</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr
                key={event.id}
                className="border-t border-gray-50 hover:bg-gray-50/50 cursor-pointer transition-colors outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#C7202F]/40"
                onClick={() => navigate('/eventos')}
                role="button"
                tabIndex={0}
                aria-label="Ver todos os eventos"
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate('/eventos'); } }}
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-grafite rounded-xl flex flex-col items-center justify-center flex-shrink-0">
                      <span className="font-bold text-xs text-white leading-none">
                        {format(new Date(event.date), 'dd')}
                      </span>
                      <span className="text-xs text-white uppercase font-bold leading-none mt-0.5">
                        {format(new Date(event.date), 'MMM', { locale: ptBR })}
                      </span>
                    </div>
                    <span className="font-medium text-sm text-grafite">{event.title}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {format(new Date(event.date), "dd 'de' MMMM", { locale: ptBR })}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1.5 text-sm text-gray-500">
                    <MapPin className="w-3.5 h-3.5 text-gray-400" />
                    {event.location}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 font-mono">
                  {format(new Date(event.date), 'HH:mm')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile: Card style */}
      <div className="md:hidden divide-y divide-gray-50">
        {events.map((event) => (
          <button
            key={event.id}
            className="flex items-start gap-3 p-4 hover:bg-gray-50 transition-colors text-left w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#C7202F]/40"
            onClick={() => navigate('/eventos')}
          >
            <div className="w-11 h-11 bg-grafite rounded-xl flex flex-col items-center justify-center flex-shrink-0">
              <span className="font-bold text-sm text-white leading-none">
                {format(new Date(event.date), 'dd')}
              </span>
              <span className="text-xs text-white uppercase font-bold leading-none mt-0.5">
                {format(new Date(event.date), 'MMM', { locale: ptBR })}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-sm text-grafite truncate">{event.title}</h3>
              <div className="flex items-center gap-1.5 text-xs text-[#6B7280] mt-1">
                <Clock className="w-3 h-3 flex-shrink-0" />
                <span>{format(new Date(event.date), 'HH:mm')}</span>
                <span className="text-gray-300 mx-0.5">|</span>
                <MapPin className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">{event.location}</span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
