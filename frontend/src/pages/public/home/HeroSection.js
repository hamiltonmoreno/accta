import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { mediaUrl } from '../../../utils/api';
import { unsplashSrcSet } from '../../../utils/unsplash';

export const HeroSection = ({ heroImg, alt }) => {
  const heroIsUnsplash = heroImg.includes('images.unsplash.com');
  return (
    <section className="relative min-h-[600px] sm:min-h-[85vh] lg:min-h-[90vh] flex items-center overflow-hidden">
      <div className="absolute inset-0">
        <img
          src={mediaUrl(heroImg)}
          srcSet={heroIsUnsplash ? unsplashSrcSet(heroImg) : undefined}
          sizes="100vw"
          alt={alt || ''}
          aria-hidden={alt ? undefined : 'true'}
          className="absolute inset-0 w-full h-full object-cover"
          loading="eager"
          fetchPriority="high"
          decoding="async"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/90 to-grafite/50 sm:from-grafite sm:via-grafite/85 sm:to-grafite/50" />
      </div>

      <div className="relative z-10 w-full max-w-7xl mx-auto px-5 sm:px-6 py-16 sm:py-20">
        <div className="max-w-2xl text-left">
          <div className="animate-fade-up">
            <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-carmesim/20 backdrop-blur-sm border border-carmesim/40 rounded-full mb-6 sm:mb-8">
              <span className="w-2 h-2 rounded-full bg-carmesim shrink-0" aria-hidden="true" />
              <span className="text-white font-sans text-xs sm:text-sm uppercase tracking-wider font-semibold">ACCTA · Cabo Verde</span>
            </div>

            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-4 sm:mb-6" data-testid="hero-title">
              O controlo de tráfego aéreo em Cabo Verde.
            </h1>

            <p className="text-base sm:text-xl lg:text-2xl text-white leading-relaxed mb-8 sm:mb-10 max-w-xl [text-shadow:0_1px_3px_rgba(0,0,0,0.4)]">
              Somos os controladores de tráfego aéreo que organizam, comunicam e protegem cada voo na FIR Oceânica do Sal — uma das maiores regiões de informação de voo do Atlântico.
            </p>

            <div className="flex flex-col sm:flex-row sm:justify-start gap-3 sm:gap-4">
              <Link
                to="/profissao"
                className="group inline-flex items-center justify-center gap-2 bg-floresta text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-floresta-dark transition-all shadow-lg shadow-floresta/25"
                data-testid="hero-cta-primary"
              >
                Conhecer a profissão
                <ArrowRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/30 px-6 sm:px-8 py-3.5 sm:py-4 rounded-lg font-bold text-sm sm:text-base hover:bg-white/20 transition-all"
                data-testid="hero-cta-secondary"
              >
                Área do associado
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
