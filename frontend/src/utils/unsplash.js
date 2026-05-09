/**
 * Devolve atributos srcSet+sizes para um asset Unsplash, evitando carregar
 * imagens de 2074px em telemóveis (~700KB vs ~150KB no w=640).
 *
 * Uso:
 *   <img src={unsplash(BASE).src} {...unsplashSrcSet(BASE)} alt="" />
 * ou:
 *   <img src={URL_BASE.replace('w=2074','w=1280')} srcSet={unsplashSrcSet(URL_BASE)} sizes="100vw" />
 *
 * BASE deve ser uma URL Unsplash com `?q=80&w=NNNN&auto=format&fit=crop`.
 * Ignora o `w=` que vier no input — substitui pelos da escala.
 */
const SCALE_WIDTHS = [640, 1024, 1600];

const stripWidth = (url) => url.replace(/([?&])w=\d+&?/, (m, sep) => sep);

export const unsplashSrcSet = (url) => {
  const clean = stripWidth(url);
  return SCALE_WIDTHS
    .map((w) => `${clean}${clean.includes('?') ? '&' : '?'}w=${w} ${w}w`)
    .join(', ');
};

export const unsplashFallbackSrc = (url, width = 1280) => {
  const clean = stripWidth(url);
  return `${clean}${clean.includes('?') ? '&' : '?'}w=${width}`;
};
