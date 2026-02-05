import React from 'react';
import { Vote } from 'lucide-react';

export const VotacoesPage = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-outfit font-bold text-4xl text-primary mb-2" data-testid="polls-title">
          Votações
        </h1>
        <p className="text-slate-600">Participe das decisões da associação</p>
      </div>

      <div className="card-technical rounded-xl p-12 text-center">
        <Vote className="w-16 h-16 text-accent mx-auto mb-4" />
        <h3 className="font-outfit font-semibold text-xl text-primary mb-2">
          Sistema de Votações
        </h3>
        <p className="text-slate-600">
          O sistema de votações está em desenvolvimento e estará disponível em breve.
        </p>
      </div>
    </div>
  );
};
