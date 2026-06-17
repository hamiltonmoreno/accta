import React from 'react';
import { Link } from 'react-router-dom';

export const CTASection = () => (
  <section className="py-16 sm:py-24 bg-grafite relative overflow-hidden">
    <div className="absolute inset-0 opacity-10">
      <div className="absolute inset-0" style={{
        backgroundImage: 'linear-gradient(rgba(199,32,47,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(199,32,47,0.3) 1px, transparent 1px)',
        backgroundSize: '30px 30px',
      }} />
    </div>
    <div className="relative z-10 max-w-4xl mx-auto px-5 sm:px-6 text-center">
      <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-white mb-4 sm:mb-6">
        A ACCTA representa os controladores de tráfego aéreo de Cabo Verde.
      </h2>
      <p className="text-base sm:text-xl text-white/80 mb-8 sm:mb-10">
        Conheça quem somos, o que defendemos e como participamos no setor da navegação aérea.
      </p>
      <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4">
        <Link
          to="/sobre"
          className="inline-flex items-center justify-center gap-2 bg-floresta text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-floresta-dark transition-all"
        >
          Conhecer a associação
        </Link>
        <Link
          to="/contactos"
          className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-sm sm:text-lg hover:bg-white/20 transition-all"
        >
          Entrar em contacto
        </Link>
      </div>
    </div>
  </section>
);
