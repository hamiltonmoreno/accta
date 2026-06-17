import React from 'react';
import {
  BarChart3, Calendar, FolderKanban, Heart, Image, FileText, Medal,
  MessageSquare, ThumbsUp, Vote,
} from 'lucide-react';

export const PersonalReport = ({ personalReport, myRanking, rankingOn, rankBreakdown }) => {
  const tiles = [
    { icon: Calendar, label: 'Eventos', value: personalReport.events_attended, total: personalReport.total_events, color: 'bg-carmesim/10 text-carmesim', signalKey: 'evento_presenca' },
    { icon: Vote, label: 'Votacoes', value: personalReport.polls_voted, total: personalReport.total_polls, color: 'bg-[#EFF6FF] text-[#1D4ED8]', signalKey: 'votacao_voto' },
    { icon: MessageSquare, label: 'Publicacoes', value: personalReport.wall_posts, total: null, color: 'bg-[#F0FDF4] text-[#15803D]', signalKey: 'mural_post' },
    { icon: ThumbsUp, label: 'Likes Recebidos', value: personalReport.likes_received, total: null, color: 'bg-[#F5F5F5] text-[#3A3A3A]', signalKey: 'mural_like_recebido' },
    { icon: FolderKanban, label: 'Projetos', value: personalReport.projects_member, total: null, color: 'bg-[#F5F5F5] text-[#3A3A3A]', signalKey: 'projeto_participacao' },
    { icon: Image, label: 'Fotos', value: personalReport.photos_approved, total: personalReport.photos_submitted, color: 'bg-[#FFFBEB] text-[#B45309]', signalKey: 'galeria_foto' },
    { icon: Heart, label: 'Beneficios', value: personalReport.benefits_used, total: null, color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
    { icon: FileText, label: 'Documentos', value: personalReport.documents_available, total: null, color: 'bg-[#F5F5F5] text-[#3A3A3A]' },
  ];

  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl overflow-hidden animate-fade-up" data-testid="personal-report">
      <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-carmesim" />
          <h2 className="text-lg font-semibold text-grafite">A Minha Participacao</h2>
        </div>
        {rankingOn ? (
          <div className="flex items-center gap-2.5" data-testid="ranking-score-header">
            {myRanking.rank && myRanking.rank <= 3 && (
              <Medal
                className={`w-5 h-5 ${myRanking.rank === 1 ? 'text-carmesim' : 'text-[#6B7280]'}`}
                aria-hidden="true"
              />
            )}
            <div className="text-right">
              <div className="font-bold text-lg text-grafite leading-none">
                {myRanking.score}
                <span className="text-xs font-normal text-[#6B7280] ml-1">pts</span>
              </div>
              <div className="text-xs text-[#6B7280] mt-0.5">
                {myRanking.rank ? `#${myRanking.rank} de ${myRanking.total_members}` : 'Atuacao'}
              </div>
            </div>
          </div>
        ) : (
          <span className="text-xs text-[#6B7280] uppercase tracking-wider hidden sm:block">Relatorio pessoal</span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-px bg-gray-100">
        {tiles.map((item, idx) => (
          <div key={item.label} className="bg-white p-4 sm:p-5 flex flex-col items-center text-center" data-testid={`report-stat-${idx}`}>
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center mb-2.5 ${item.color}`}>
              <item.icon className="w-4 h-4" />
            </div>
            <div className="font-bold text-xl text-grafite">{item.value}</div>
            {item.total !== null && item.total > 0 && (
              <div className="text-xs text-[#6B7280] font-mono mt-0.5">de {item.total}</div>
            )}
            <div className="text-xs text-gray-500 mt-1">{item.label}</div>
            {rankingOn && item.signalKey && rankBreakdown[item.signalKey]?.points > 0 && (
              <div className="text-[11px] font-semibold text-[#6B7280] mt-1">
                +{rankBreakdown[item.signalKey].points} pts
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
