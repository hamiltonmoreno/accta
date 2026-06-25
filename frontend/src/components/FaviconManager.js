import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { brandAPI, mediaUrl } from '../utils/api';
import { queryKeys } from '../lib/queryClient';

/**
 * Aplica o favicon configurado na Aparência (spec-gestao-logo-marca) em runtime.
 * Lê a marca pública e atualiza o href do `<link rel="icon" id="app-favicon">`
 * (e do apple-touch-icon) declarado em `public/index.html`. Sem favicon próprio
 * (None / erro / query falhada) → mantém o `/favicon.ico` estático por defeito,
 * pelo que o portal fica idêntico a hoje antes de qualquer upload.
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
    const apple = document.getElementById('app-apple-icon');
    if (link) link.setAttribute('href', favicon ? mediaUrl(favicon) : '/favicon.ico');
    // O apple-touch-icon ignora .ico: favicon próprio → essa imagem; sem favicon → default PNG.
    if (apple) apple.setAttribute('href', favicon ? mediaUrl(favicon) : '/logo192.png');
  }, [favicon]);

  return null;
};

export default FaviconManager;
