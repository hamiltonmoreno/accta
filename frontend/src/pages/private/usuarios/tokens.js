// CARGOS e PRIVILEGES vêm do backend (GET /users/meta/cargos). Aqui só os
// conjuntos pequenos e estáveis; rótulos PT em lib/cargoLabels.
export const ROLES = ['admin', 'socio', 'financeiro', 'moderador'];
export const STATUSES = ['ativo', 'inativo', 'pendente_convite'];

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
  member_id: '',
  license_number: '',
  department: '',
  phone_number: '',
};
