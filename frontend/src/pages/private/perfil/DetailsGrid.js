import React from 'react';
import {
  Award, BadgeCheck, Briefcase, Building2, Cake, Calendar, Clock, Droplet,
  Fingerprint, Globe, Hash, HeartPulse, Home, Lock, Mail, MapPin,
  Phone, Shield, FileText, User as UserIcon, Users as UsersIcon,
} from 'lucide-react';
import { InfoRow } from './widgets';
import { LicenseExpiryNotice } from './LicenseExpiryNotice';
import { cargoLabelFrom, memberCategoryLabel } from '../../../lib/governanceLabels';
import { calcAge, formatDate, ROLE_LABEL } from './tokens';

export const DetailsGrid = ({ user, structure }) => {
  const cargoNome = cargoLabelFrom(structure, user.cargo);
  const age = calcAge(user.date_of_birth);
  const dobLabel = user.date_of_birth
    ? `${formatDate(user.date_of_birth)}${age != null ? ` (${age} anos)` : ''}`
    : null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div className="card-technical p-5 animate-fade-up">
        <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Dados Pessoais</h3>
        <InfoRow icon={Mail} label="Email" value={user.email} managed />
        <InfoRow icon={Phone} label="Telefone" value={user.phone_number} />
        <InfoRow icon={Cake} label="Nascimento" value={dobLabel} />
        <InfoRow icon={Droplet} label="Tipo Sanguíneo" value={user.blood_type} />
        <InfoRow icon={UserIcon} label="Género" value={user.gender} />
        <InfoRow icon={Globe} label="Nacionalidade" value={user.nationality} />
        <InfoRow icon={Fingerprint} label="NIF" value={user.nif} />
        <InfoRow icon={FileText} label="Biografia" value={user.bio} />
        <InfoRow icon={Hash} label="N.º Sócio" value={user.member_id} managed />
      </div>

      <div className="card-technical p-5 animate-fade-up">
        <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Morada</h3>
        <InfoRow icon={MapPin} label="Endereço" value={user.address} />
        <InfoRow icon={Home} label="Código Postal" value={user.postal_code} />
        <InfoRow icon={Building2} label="Cidade" value={user.city} />
        <InfoRow icon={MapPin} label="Ilha" value={user.residence_island} />
      </div>

      <div className="card-technical p-5 animate-fade-up">
        <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Contacto de Emergência</h3>
        <InfoRow icon={HeartPulse} label="Nome" value={user.emergency_contact_name} />
        <InfoRow icon={Phone} label="Telefone" value={user.emergency_contact_phone} />
        <InfoRow icon={UsersIcon} label="Parentesco" value={user.emergency_contact_relationship} />
      </div>

      <div className="card-technical p-5 animate-fade-up">
        <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">Profissional e Licença</h3>
        <InfoRow icon={Briefcase} label="Profissão" value={user.profession} />
        <InfoRow icon={Building2} label="Entidade" value={user.employer} />
        <InfoRow icon={Award} label="N.º Licença" value={user.license_number} />
        <InfoRow icon={BadgeCheck} label="Categoria" value={user.license_category} />
        <InfoRow icon={Clock} label="Validade" value={formatDate(user.license_expiry_date)} />
        <LicenseExpiryNotice expiry={user.license_expiry_date} />
      </div>

      <div className="card-technical p-5 animate-fade-up md:col-span-2">
        <div className="flex items-center justify-between gap-2 mb-3">
          <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Associação</h3>
          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
            <Lock className="w-3 h-3 text-gray-400" aria-hidden="true" />
            Gerido pela administração
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 sm:gap-x-8">
          <InfoRow icon={Shield} label="Função" value={ROLE_LABEL[user.role]} managed />
          <InfoRow icon={Briefcase} label="Cargo" value={cargoNome} managed />
          <InfoRow icon={UsersIcon} label="Categoria" value={memberCategoryLabel(user.member_category)} managed />
          <InfoRow icon={Calendar} label="Admissão" value={formatDate(user.admission_date) || '—'} managed />
        </div>
      </div>
    </div>
  );
};
