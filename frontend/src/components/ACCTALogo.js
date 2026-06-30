import React from 'react';
import { cn } from '../lib/utils';
import logoColor from '../assets/accta-logo.png';
import logoWhite from '../assets/accta-logo-white.png';
import logoMark from '../assets/accta-logo-mark.png';

/**
 * Logótipo institucional da ACCTA (símbolo "A" + trajetória/avião) como imagem
 * da marca — substitui o antigo vetor desenhado à mão. `dark` escolhe a versão
 * branca para fundos escuros. Serve de fallback do BrandLogo/BrandIcon quando
 * não há logótipo carregado na Aparência, pelo que a marca nunca fica vazia.
 */

// Logótipo horizontal. `dark` → versão branca (fundo escuro).
export const ACCTALogoHorizontal = ({ className = '', dark = false }) => (
  <img
    src={dark ? logoWhite : logoColor}
    alt="ACCTA Cabo Verde"
    className={cn('h-9 w-auto object-contain', className)}
  />
);

// Compat com a API anterior. `variant='icon'` → marca quadrada (contextos
// compactos, ex.: sidebar recolhida); caso contrário → logótipo horizontal.
export const ACCTALogo = ({ variant = 'full', className = '', dark = false }) => {
  if (variant === 'icon') {
    // Decorativa (alt=""): o ícone é sempre usado dentro de um controlo já
    // rotulado (ex.: <Link aria-label="ACCTA">), evitando rótulo duplicado.
    // Marca quadrada só na versão colorida — basta hoje (sidebar é clara); para
    // fundo escuro seria preciso uma variante branca quadrada.
    return <img src={logoMark} alt="" className={cn('object-contain', className)} />;
  }
  return <ACCTALogoHorizontal className={className} dark={dark} />;
};
