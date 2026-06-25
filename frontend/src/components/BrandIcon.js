import { useQuery } from '@tanstack/react-query';
import { brandAPI, mediaUrl } from '../utils/api';
import { queryKeys } from '../lib/queryClient';
import { ACCTALogo } from './ACCTALogo';

/**
 * Mark quadrado da marca para contextos compactos (sidebar recolhida, ecrãs estreitos).
 * Lê o ícone configurado na Aparência (spec 005 — icone-marca-pwa) via a mesma query
 * pública da restante marca. Sem ícone próprio (None / erro / query falhada) → cai para
 * o ícone vetorial por defeito (`ACCTALogo variant="icon"`), pelo que nunca fica vazio.
 *
 * Partilha a query/cache do BrandLogo/FaviconManager. Não trata do favicon nem do ícone
 * PWA — esses vivem, respetivamente, no FaviconManager e no endpoint /api/brand/icon.
 */
export const BrandIcon = ({ className = 'h-8 w-8' }) => {
  const { data } = useQuery({
    queryKey: queryKeys.brand.public(),
    queryFn: async () => (await brandAPI.getPublic()).data,
    staleTime: 30 * 60 * 1000, // marca é quase-estática
  });

  const icon = data?.icon_url;
  if (icon) {
    return (
      <img
        src={mediaUrl(icon)}
        alt={data?.alt || 'ACCTA'}
        className={`${className} object-contain rounded`}
      />
    );
  }
  return <ACCTALogo variant="icon" className={className} />;
};

export default BrandIcon;
