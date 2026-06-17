import React from 'react';
import { Save } from 'lucide-react';
import { Textarea } from '../../../components/ui/textarea';
import { FormInput, FormSelect } from './widgets';
import { LicenseExpiryNotice } from './LicenseExpiryNotice';
import { BLOOD_TYPE_OPTIONS, GENDER_OPTIONS, labelCls } from './tokens';

export const EditForm = ({ form, set, onSave, loading }) => (
  <div className="card-technical p-6 space-y-6 animate-fade-up" data-testid="profile-edit-form">
    {/* Dados pessoais */}
    <div className="space-y-4">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Dados Pessoais</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormInput id="profile-name" testId="profile-edit-name" label="Nome" value={form.name} onChange={set('name')} max={120} />
        <FormInput id="profile-phone" testId="profile-edit-phone" label="Telefone" value={form.phone_number} onChange={set('phone_number')} type="tel" placeholder="+238 9XX XXXX" max={30} />
        <FormInput id="profile-dob" label="Data de Nascimento" value={form.date_of_birth} onChange={set('date_of_birth')} type="date" />
        <FormSelect id="profile-blood" label="Tipo Sanguíneo" value={form.blood_type} onChange={set('blood_type')} options={BLOOD_TYPE_OPTIONS} />
        <FormSelect id="profile-gender" label="Género" value={form.gender} onChange={set('gender')} options={GENDER_OPTIONS} />
        <FormInput id="profile-nationality" label="Nacionalidade" value={form.nationality} onChange={set('nationality')} placeholder="Cabo-verdiana" max={60} />
        <FormInput id="profile-nif" label="NIF" value={form.nif} onChange={set('nif')} max={40} />
      </div>
      <div>
        <label htmlFor="profile-bio" className={labelCls}>Biografia</label>
        <Textarea
          id="profile-bio"
          value={form.bio}
          onChange={(e) => set('bio')(e.target.value)}
          rows={3}
          maxLength={1000}
          placeholder="Fale um pouco sobre si..."
          className="resize-none"
          data-testid="profile-edit-bio"
        />
      </div>
    </div>

    {/* Morada */}
    <div className="space-y-4 pt-2 border-t border-gray-100">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Morada</h3>
      <FormInput id="profile-address" label="Endereço" value={form.address} onChange={set('address')} placeholder="Rua, n.º, andar" max={200} />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <FormInput id="profile-postal" label="Código Postal" value={form.postal_code} onChange={set('postal_code')} max={20} />
        <FormInput id="profile-city" label="Cidade / Concelho" value={form.city} onChange={set('city')} max={80} />
        <FormInput id="profile-island" label="Ilha de Residência" value={form.residence_island} onChange={set('residence_island')} placeholder="Santiago" max={60} />
      </div>
    </div>

    {/* Contacto de emergência */}
    <div className="space-y-4 pt-2 border-t border-gray-100">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Contacto de Emergência</h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <FormInput id="profile-ec-name" label="Nome" value={form.emergency_contact_name} onChange={set('emergency_contact_name')} max={120} />
        <FormInput id="profile-ec-phone" label="Telefone" value={form.emergency_contact_phone} onChange={set('emergency_contact_phone')} type="tel" placeholder="+238 9XX XXXX" max={30} />
        <FormInput id="profile-ec-rel" label="Parentesco" value={form.emergency_contact_relationship} onChange={set('emergency_contact_relationship')} placeholder="Cônjuge, filho/a..." max={60} />
      </div>
    </div>

    {/* Profissional e licença */}
    <div className="space-y-4 pt-2 border-t border-gray-100">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280]">Dados Profissionais e Licença</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormInput id="profile-profession" label="Profissão" value={form.profession} onChange={set('profession')} max={120} />
        <FormInput id="profile-employer" label="Entidade Empregadora" value={form.employer} onChange={set('employer')} max={120} />
        <FormInput id="profile-license-number" label="N.º de Licença" value={form.license_number} onChange={set('license_number')} max={60} />
        <FormInput id="profile-license-category" label="Categoria / Título" value={form.license_category} onChange={set('license_category')} max={80} />
        <FormInput id="profile-license-expiry" label="Validade da Licença" value={form.license_expiry_date} onChange={set('license_expiry_date')} type="date" />
      </div>
      <LicenseExpiryNotice expiry={form.license_expiry_date} />
    </div>

    <button
      onClick={onSave}
      disabled={loading}
      className="inline-flex items-center gap-2 bg-floresta text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-floresta-dark transition-colors disabled:opacity-50"
      data-testid="profile-save-btn"
    >
      <Save className="w-4 h-4" />
      {loading ? 'A guardar...' : 'Guardar alterações'}
    </button>
  </div>
);
