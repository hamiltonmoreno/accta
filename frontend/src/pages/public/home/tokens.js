import {
  Building2, Landmark, Navigation, PlaneLanding, Radio, Search, TowerControl,
} from 'lucide-react';

export const NEWS_IMAGES = [
  'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1474302770737-173ee21bab63?q=80&w=800&auto=format&fit=crop',
];

// Mapas visuais para as secções educativas (conteúdo em content/cta/).
export const CONTROL_ICONS = { TWR: TowerControl, APP: PlaneLanding, ACC: Navigation };

export const ATS_ICONS = {
  AAC: Landmark,
  ASA: Radio,
  'Cabo Verde Airports': Building2,
  IPIAAM: Search,
};

// Resumo de uma linha por etapa — o detalhe completo vive em /profissao.
export const CAMINHO_RESUMO = {
  'Pré-requisitos': '21 anos, certificado médico Classe 3 e inglês ICAO nível 4.',
  'Formação inicial': 'Curso teórico numa ATO aprovada pela AAC, com exame.',
  'Formação operacional': 'Qualificação (ADI/APP/ACC) com tráfego real sob OJTI.',
  'Ingresso numa unidade': 'Averbamento de órgão e autorização para a posição.',
  'Manutenção': 'Revalidação periódica e recência operacional contínua.',
};
