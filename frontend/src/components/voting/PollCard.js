import React from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Clock, Calendar, Users } from 'lucide-react';

export const PollCard = ({ poll, isActive = false, children }) => {
  const startDate = new Date(poll.start_date);
  const endDate = new Date(poll.end_date);
  const now = new Date();
  
  const daysRemaining = isActive ? Math.ceil((endDate - now) / (1000 * 60 * 60 * 24)) : 0;
  const isUrgent = daysRemaining <= 3 && daysRemaining > 0;

  return (
    <div className="card-technical rounded-xl p-6" data-testid={`poll-${poll.id}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="font-sans font-semibold text-2xl text-grafite mb-2">{poll.title}</h3>
          <p className="text-gray-600 leading-relaxed mb-4">{poll.description}</p>
          
          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span className="font-mono">
                Início: {format(startDate, 'dd/MM/yyyy', { locale: ptBR })}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span className="font-mono">
                Término: {format(endDate, 'dd/MM/yyyy', { locale: ptBR })}
              </span>
            </div>
            {isActive && (
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
                isUrgent ? 'bg-alert/10 text-alert' : 'bg-carmesim/10 text-carmesim'
              }`}>
                <Clock className="w-4 h-4" />
                <span className="font-mono text-xs font-semibold">
                  {daysRemaining} dia{daysRemaining !== 1 ? 's' : ''} restante{daysRemaining !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <span
          className={`px-4 py-2 rounded-full text-xs font-mono uppercase tracking-wider whitespace-nowrap ${
            isActive
              ? 'bg-carmesim/10 text-carmesim'
              : 'bg-gray-100 text-gray-500'
          }`}
        >
          {isActive ? 'Aberta' : 'Encerrada'}
        </span>
      </div>

      {/* Additional Info */}
      {poll.options && (
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-4">
          <Users className="w-4 h-4" />
          <span>{poll.options.length} opções disponíveis</span>
        </div>
      )}

      {/* Children (voting interface or results) */}
      {children}
    </div>
  );
};
