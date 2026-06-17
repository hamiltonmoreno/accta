import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { UserPlus, CheckCircle, Loader2, Mail, User, Phone, Building2 } from 'lucide-react';
import { toast } from 'sonner';
import { registrationAPI } from '../../utils/api';
import { registrationSchema } from '../../utils/authSchemas';
import { Input } from '../../components/ui/input';

// Fallback caso o endpoint público de opções falhe — mantém o form utilizável.
const CARGOS_FALLBACK = [
  'Sócio', 'Vogal', 'Tesoureiro', 'Secretário',
  'Vice-Presidente', 'Presidente', 'Direcção', 'Conselho Fiscal',
];

export const CriarContaPage = () => {
  const [cargos, setCargos] = useState(CARGOS_FALLBACK);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registrationSchema),
    mode: 'onBlur',
    defaultValues: { cargo_declarado: 'Sócio', consent_data: false },
  });

  useEffect(() => {
    registrationAPI.options()
      .then((res) => {
        if (Array.isArray(res.data?.cargos) && res.data.cargos.length) {
          setCargos(res.data.cargos);
        }
      })
      .catch(() => {/* mantém fallback */});
  }, []);

  const onSubmit = async (values) => {
    try {
      await registrationAPI.submit(values);
      setSuccess(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao enviar o pedido. Tente novamente.');
    }
  };

  if (success) {
    return (
      <section className="min-h-screen flex items-center justify-center bg-gray-50 px-4 pt-28 pb-16">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full text-center animate-fade-up">
          <div className="w-14 h-14 bg-[#F0FDF4] rounded-2xl flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-7 h-7 text-[#16A34A]" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-2" data-testid="registo-success">Pedido enviado</h1>
          <p className="text-sm text-[#6B7280] mb-6">
            Recebemos o seu pedido de inscrição. Vamos enviar-lhe um email assim que for analisado pela direção da ACCTA.
          </p>
          <Link
            to="/"
            className="inline-block px-5 py-2.5 border border-[#D1D5DB] rounded-lg text-sm font-medium text-grafite hover:bg-gray-50 transition-colors"
            data-testid="voltar-inicio"
          >
            Voltar à página inicial
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="min-h-screen bg-gray-50 px-4 pt-28 pb-16">
      <div
        className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-lg w-full mx-auto animate-fade-up"
        data-testid="criar-conta-form"
      >
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-carmesim/10 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <UserPlus className="w-6 h-6 text-carmesim" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-1">Pedido de inscrição</h1>
          <p className="text-sm text-[#6B7280]">
            Preencha os seus dados. A direção da ACCTA irá analisar o pedido.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {/* Honeypot anti-bot — deve ficar vazio (escondido de utilizadores reais) */}
          <Input
            type="text"
            tabIndex={-1}
            autoComplete="off"
            aria-hidden="true"
            className="hidden"
            {...register('website')}
          />

          <div>
            <label htmlFor="reg-name" className="block text-xs font-medium text-gray-600 mb-1.5">Nome completo *</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
              <Input
                id="reg-name"
                type="text"
                aria-invalid={errors.name ? 'true' : 'false'}
                {...register('name')}
                placeholder="O seu nome"
                className="w-full pl-9 pr-3 py-3 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none aria-[invalid=true]:border-carmesim/60"
                data-testid="reg-name"
              />
            </div>
            {errors.name && <p className="text-xs text-[#B91C1C] mt-1" role="alert">{errors.name.message}</p>}
          </div>

          <div>
            <label htmlFor="reg-email" className="block text-xs font-medium text-gray-600 mb-1.5">Email *</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
              <Input
                id="reg-email"
                type="email"
                aria-invalid={errors.email ? 'true' : 'false'}
                {...register('email')}
                placeholder="email@exemplo.cv"
                className="w-full pl-9 pr-3 py-3 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none aria-[invalid=true]:border-carmesim/60"
                data-testid="reg-email"
              />
            </div>
            {errors.email && <p className="text-xs text-[#B91C1C] mt-1" role="alert">{errors.email.message}</p>}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="reg-phone" className="block text-xs font-medium text-gray-600 mb-1.5">Telefone</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
                <Input
                  id="reg-phone"
                  type="tel"
                  {...register('phone_number')}
                  placeholder="(opcional)"
                  className="w-full pl-9 pr-3 py-3 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
                  data-testid="reg-phone"
                />
              </div>
            </div>
            <div>
              <label htmlFor="reg-dept" className="block text-xs font-medium text-gray-600 mb-1.5">Departamento</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
                <Input
                  id="reg-dept"
                  type="text"
                  {...register('department')}
                  placeholder="(opcional)"
                  className="w-full pl-9 pr-3 py-3 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
                  data-testid="reg-dept"
                />
              </div>
            </div>
          </div>

          <div>
            <label htmlFor="reg-cargo" className="block text-xs font-medium text-gray-600 mb-1.5">Cargo na associação</label>
            <select
              id="reg-cargo"
              {...register('cargo_declarado')}
              className="w-full px-3 py-3 border border-gray-200 rounded-lg text-sm bg-white focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
              data-testid="reg-cargo"
            >
              {cargos.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <p className="text-xs text-[#6B7280] mt-1">
              Apenas declarativo — a direção confirma o cargo e o nível de acesso ao aprovar.
            </p>
          </div>

          <label htmlFor="reg-consent" className="flex items-start gap-2.5 cursor-pointer">
            <input
              id="reg-consent"
              type="checkbox"
              {...register('consent_data')}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-carmesim focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid="reg-consent"
            />
            <span className="text-xs text-[#6B7280] leading-relaxed">
              Concordo com o tratamento dos meus dados pessoais pela ACCTA para efeitos de gestão da inscrição (RGPD).
            </span>
          </label>
          {errors.consent_data && <p className="text-xs text-[#B91C1C]" role="alert">{errors.consent_data.message}</p>}

          <div className="rounded-lg bg-gray-50 border border-gray-200 px-3 py-2.5">
            <p className="text-xs text-[#6B7280]">
              O nº de associado será atribuído automaticamente após aprovação.
            </p>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-floresta text-white hover:bg-floresta-dark h-11 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            data-testid="reg-submit"
          >
            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
            {isSubmitting ? 'A enviar...' : 'Enviar pedido'}
          </button>

          <p className="text-center text-sm text-[#6B7280]">
            Já tem conta?{' '}
            <Link to="/login" className="text-carmesim hover:text-carmesim-dark font-medium transition-colors">
              Entrar
            </Link>
          </p>
        </form>
      </div>
    </section>
  );
};
