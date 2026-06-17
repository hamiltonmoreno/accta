// Datas só-com-dia ("AAAA-MM-DD") têm de ser interpretadas no fuso LOCAL:
// `new Date("2027-01-31")` é meia-noite UTC e, num fuso a oeste (Cabo Verde =
// UTC-1), recua para o dia anterior. Construímos a partir dos componentes para
// evitar o desvio de um dia em datas/contagens. Datas-hora completas (ISO com
// 'T') também passam pela porção de data, o que é o pretendido para exibição.
export const toLocalDate = (value) => {
  if (!value) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
  const d = m
    ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
    : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
};

export const formatDate = (iso) => {
  const d = toLocalDate(iso);
  return d ? d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' }) : null;
};

// Idade a partir da data de nascimento (AAAA-MM-DD). Devolve null se inválida.
export const calcAge = (dob) => {
  const d = toLocalDate(dob);
  if (!d) return null;
  const now = new Date();
  let age = now.getFullYear() - d.getFullYear();
  const m = now.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age -= 1;
  return age >= 0 && age < 130 ? age : null;
};

export const BLOOD_TYPE_OPTIONS = [
  { value: '', label: '—' },
  ...['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((t) => ({ value: t, label: t })),
];

export const GENDER_OPTIONS = [
  { value: '', label: '—' },
  { value: 'Feminino', label: 'Feminino' },
  { value: 'Masculino', label: 'Masculino' },
  { value: 'Outro', label: 'Outro' },
  { value: 'Prefiro não indicar', label: 'Prefiro não indicar' },
];

export const ROLE_LABEL = {
  admin: 'Administrador', socio: 'Sócio', financeiro: 'Gestor Financeiro', moderador: 'Moderador',
};

export const labelCls = 'block text-xs uppercase tracking-widest text-gray-500 font-semibold mb-1';
export const inputCls =
  'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/30 outline-none';

export const EMPTY_FORM = {
  name: '', phone_number: '', bio: '',
  date_of_birth: '', blood_type: '', gender: '', nationality: '', nif: '',
  address: '', postal_code: '', city: '', residence_island: '',
  emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relationship: '',
  profession: '', employer: '', license_number: '', license_category: '', license_expiry_date: '',
};
