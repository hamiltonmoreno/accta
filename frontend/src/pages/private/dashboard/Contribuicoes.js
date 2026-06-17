import React from 'react';
import { CheckCircle } from 'lucide-react';

// Cartão estático "Tudo em dia" — quotas são descontadas em folha; não há cobrança ativa.
export const Contribuicoes = () => (
  <div className="bg-white border border-gray-200/80 rounded-2xl p-5 sm:p-6 animate-fade-up">
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-lg font-semibold text-grafite" data-testid="contributions-title">Contribuicoes</h2>
      <span className="text-xs text-[#6B7280] uppercase tracking-wider hidden sm:block">Desconto em Folha</span>
    </div>
    <div className="text-center py-8">
      <div className="w-14 h-14 bg-[#F0FDF4] rounded-2xl flex items-center justify-center mx-auto mb-3">
        <CheckCircle className="w-7 h-7 text-[#15803D]" />
      </div>
      <p className="text-sm text-grafite font-semibold" data-testid="contributions-status">Tudo em dia!</p>
      <p className="text-xs text-[#6B7280] mt-1">Quotas descontadas automaticamente na folha salarial</p>
    </div>
  </div>
);
