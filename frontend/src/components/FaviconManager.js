import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { brandAPI, mediaUrl } from '../utils/api';
import { queryKeys } from '../lib/queryClient';

/**
 * Aplica o favicon configurado na Aparência (spec-gestao-logo-marca) em runtime.
 * Lê a marca pública e atualiza o href do `<link rel="icon" id="app-favicon">`
 * declarado em `public/index.html`. Sem favicon próprio (None / erro / query
 * falhada) → mantém o `/favicon.ico` estático por defeito, pelo que o portal fica
 * idêntico a hoje antes de qualquer upload.
 *
 * Trata APENAS do favicon do separador. O ícone de app/homescreen
 * (`apple-touch-icon`) é o ícone quadrado da marca (spec 005), servido pelo
 * endpoint estável `/api/brand/icon` directamente no HTML — não é gerido aqui.
 *
 * Não renderiza nada. Montado uma vez no topo da app (dentro do
 * QueryClientProvider). Partilha a mesma query/cache do BrandLogo.
 */
export const FaviconManager = () => {
  const { data } = useQuery({
    queryKey: queryKeys.brand.public(),
    queryFn: async () => (await brandAPI.getPublic()).data,
    staleTime: 30 * 60 * 1000, // marca é quase-estática
  });

  const favicon = data?.favicon_url;

  useEffect(() => {
    const link = document.getElementById('app-favicon');
    if (link) link.setAttribute('href', favicon ? mediaUrl(favicon) : '/favicon.ico');
  }, [favicon]);

  return null;
};

export default FaviconManager;
