import React from 'react';
import { ExternalLink } from 'lucide-react';
import { instituicoes } from '../content/cta/instituicoes';

// Bloco "Fontes oficiais" (sub-projeto C) — lista compacta das instituições
// referidas na base de conhecimento, com link para o site oficial. Reutiliza o
// registo único `instituicoes`. Fundo claro (links Carmesim — frontend-design).

export const FontesOficiais = () => (
  <section className="py-12 sm:py-16 bg-gray-50">
    <div className="max-w-5xl mx-auto px-6">
      <div className="text-center mb-8">
        <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-4">
          Fontes oficiais
        </span>
        <h2 className="font-sans font-bold text-2xl sm:text-3xl text-grafite mb-2">
          Instituições de referência
        </h2>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto">
          Esta secção remete para as fontes oficiais. Confirme sempre
          a informação vigente nas páginas das respetivas entidades.
        </p>
      </div>

      <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {instituicoes.map((inst) => (
          <li key={inst.url} className="card-technical rounded-xl p-5">
            <a
              href={inst.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-start justify-between gap-3"
            >
              <span className="min-w-0">
                <span className="block font-semibold text-grafite group-hover:text-carmesim transition-colors truncate">
                  {inst.nome}
                </span>
                <span className="block text-xs text-gray-500 mt-0.5">{inst.papel}</span>
              </span>
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-carmesim transition-colors flex-shrink-0 mt-1" />
            </a>
          </li>
        ))}
      </ul>
    </div>
  </section>
);

export default FontesOficiais;
