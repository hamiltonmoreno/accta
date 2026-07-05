// CARGOS e PRIVILEGES vêm do backend (GET /users/meta/cargos). Aqui só os
// conjuntos pequenos e estáveis; rótulos PT em lib/cargoLabels.
// spec 018 D1/D2: níveis de acesso = Admin/Sócio; o acesso granular vem de
// privilégios e funções personalizadas (as antigas «Financeiro»/«Moderador»
// existem como funções seed).
export const ROLES = ['admin', 'socio'];
export const STATUSES = ['ativo', 'inativo', 'pendente_convite'];

// Departamentos internos da associação (espelha models.DEPARTAMENTOS no backend).
// Etiqueta organizacional; a UI acrescenta «Outro» (texto livre).
export const DEPARTAMENTOS = [
  'Formação e Certificação',
  'Segurança Operacional (Safety)',
  'Assuntos Profissionais e Laborais',
  'Assuntos Técnicos e Operacionais',
  'Relações Institucionais e Internacionais',
  'Comunicação e Imagem',
  'Assuntos Jurídicos',
  'Tesouraria e Finanças',
  'Eventos, Cultura e Ação Social',
];

// Sentinela de UI para permitir um valor fora da lista (texto livre).
export const DEPARTAMENTO_OUTRO = 'Outro';

export const formatHistoryDate = (iso) => {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return null;
  }
};

export const EMPTY_INVITE = {
  name: '',
  email: '',
  role: 'socio',
  custom_role_id: '',
  member_id: '',
  license_number: '',
  department: '',
  phone_number: '',
};
