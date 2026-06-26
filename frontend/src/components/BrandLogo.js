import React, { useState, useEffect } from 'react';
import { mediaUrl } from '../utils/api';
import { useBrand } from '../lib/useBrand';
import { ACCTALogoHorizontal } from './ACCTALogo';
import { cn } from '../lib/utils';

/**
 * Fonte única da marca (spec-gestao-logo-marca §4.1). Lê a config da marca e
 * decide entre IMAGEM carregada e o SVG fallback (ACCTALogo). Mantém o contrato
 * que os usos atuais esperam: `dark` (escolhe a versão p/ fundo escuro) e
 * `className`. Sem imagem (ou em erro/404/query falhada) → SVG atual → o portal
 * fica idêntico a hoje e a marca nunca fica vazia.
 */
export const BrandLogo = ({ dark = false, className = '' }) => {
  const [imageFailed, setImageFailed] = useState(false);

  const { data } = useBrand();

  const url = dark ? data?.logo_dark_url : data?.logo_light_url;
  const alt = data?.alt || 'ACCTA Cabo Verde';

  // Reset do estado de erro quando a URL muda (novo upload).
  useEffect(() => {
    setImageFailed(false);
  }, [url]);

  if (url && !imageFailed) {
    return (
      <img
        src={mediaUrl(url)}
        alt={alt}
        onError={() => setImageFailed(true)}
        className={cn('h-9 w-auto max-h-9 max-w-[180px] object-contain', className)}
      />
    );
  }
  // Fallback: SVG vetorial atual, com a variante correta para o fundo.
  return <ACCTALogoHorizontal dark={dark} className={className} />;
};

export default BrandLogo;
