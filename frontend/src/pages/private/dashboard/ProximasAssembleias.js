import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CalendarClock, ArrowRight } from 'lucide-react';

// Lista compacta das próximas AGAs / assembleias marcadas (spec 020 — A.3).
// Universal: qualquer autenticado pode navegar para /assembleias/{id}
// (já é rota autenticada sem gate adicional).
export const ProximasAssembleias = ({ proximas }) => {
  const navigate = useNavigate();
  if (!proximas || proximas.length === 0) return null;
  const fmt = (iso) => {
    if (!iso) return '';
    // ISO date/dtm — mostrar só a data (yyyy-mm-dd → pt)
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', year: 'numeric' });
  };
  return (
    <div className="bg-white border border-gray-200/80 rounded-2xl p-4 sm:p-5 animate-fade-up">
      <h3 className="text-lg font-semibold text-grafite mb-3 flex items-center gap-2">
        <CalendarClock className="w-5 h-5 text-grafite" /> Próximas Assembleias
      </h3>
      <ul className="divide-y divide-gray-100">
        {proximas.map((a) => (
          <li key={a.id}>
            <button
              type="button"
              onClick={() => navigate(`/assembleias/${a.id}`)}
              className="w-full flex items-center justify-between py-3 text-left hover:bg-gray-50/60 rounded-lg px-2 -mx-2 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
            >
              <div>
                <div className="text-sm font-semibold text-grafite">{a.titulo}</div>
                <div className="text-xs text-[#6B7280] mt-0.5">
                  {fmt(a.data)}{a.tipo ? ` · ${a.tipo}` : ''}
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-gray-400" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ProximasAssembleias;
