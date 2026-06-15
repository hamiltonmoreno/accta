// Fallback embebido dos banners (espelha BANNER_DEFAULTS de backend/routes/
// banners.py). Usado pelo <PageBanner> se a query pública falhar/ainda não
// carregou — o banner nunca fica vazio (spec-padronizacao-banners §9). NÃO é a
// fonte de verdade: a config vem de GET /api/banners/public.

const U = (id) => `https://images.unsplash.com/photo-${id}?q=80&w=1600&auto=format&fit=crop`;

export const BANNER_DEFAULTS = {
  home: U('1436491865332-7a61a109cc05'),
  sobre: U('1522071820081-009f0129c71c'),
  profissao: U('1540962351504-03099e0a754b'),
  contactos: U('1672856181212-b5b5a0065a08'),
  beneficios: U('1600880292203-757bb62b4baf'),
  galeria: U('1436491865332-7a61a109cc05'),
  eventos: U('1474302770737-173ee21bab63'),
  noticias: U('1618506060789-b63788b0cecd'),
  validador: U('1540962351504-03099e0a754b'),
};

export const bannerDefault = (key) => BANNER_DEFAULTS[key] || BANNER_DEFAULTS.sobre;
