import React, { useState } from 'react';
import { toast } from 'sonner';
import { contactAPI } from '../../utils/api';
import {
  Mail,
  MapPin,
  Send,
  MessageSquare,
  Newspaper,
  HandshakeIcon,
  HelpCircle,
  Loader2,
  CheckCircle,
  ExternalLink,
  ChevronDown,
} from 'lucide-react';
import { unsplashSrcSet } from '../../utils/unsplash';
import { faq, contactosUteis, notaContactos } from '../../content/cta';

export const ContactosPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: 'geral',
    message: ''
  });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.message) {
      toast.error('Por favor, preencha todos os campos obrigatórios');
      return;
    }

    setSending(true);
    try {
      await contactAPI.submit(formData);
      setSent(true);
      toast.success('Mensagem enviada com sucesso!');
      setTimeout(() => {
        setFormData({ name: '', email: '', subject: 'geral', message: '' });
        setSent(false);
      }, 3000);
    } catch {
      toast.error('Erro ao enviar mensagem. Tente novamente.');
    } finally {
      setSending(false);
    }
  };

  const subjects = [
    { value: 'geral', label: 'Geral', icon: MessageSquare },
    { value: 'imprensa', label: 'Imprensa', icon: Newspaper },
    { value: 'parcerias', label: 'Parcerias', icon: HandshakeIcon },
    { value: 'duvidas', label: 'Dúvidas', icon: HelpCircle },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="relative py-20 sm:py-28 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1672856181212-b5b5a0065a08?q=80&w=1280&auto=format&fit=crop"
          srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1672856181212-b5b5a0065a08?q=80&auto=format&fit=crop')}
          sizes="100vw"
          alt=""
          aria-hidden="true"
          loading="lazy"
          decoding="async"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/85 to-grafite/50" />
        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6">
          <div className="max-w-2xl animate-fade-up">
            <span className="inline-block px-3 py-1.5 bg-white/10 text-white rounded-full text-xs uppercase tracking-wider font-semibold mb-5">
              Contactos
            </span>
            <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl text-white mb-4" data-testid="contact-title">
              Fale{' '}
              <span className="text-white">Conosco</span>
            </h1>
            <p className="text-base sm:text-xl text-white/80 max-w-xl leading-relaxed">
              Tem dúvidas sobre a associação, a profissão ou deseja propor uma parceria? Utilize os canais oficiais.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Info & Form */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16">
            {/* Contact Information */}
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-3xl text-grafite mb-8">
                Informações de Contacto
              </h2>

              <div className="space-y-6 mb-12">
                {/* Email General */}
                <div className="flex gap-5">
                  <div className="w-14 h-14 bg-carmesim rounded-xl flex items-center justify-center flex-shrink-0">
                    <Mail className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-1">Email Geral</h3>
                    <a href="mailto:secretariado@controlador.cv" className="text-carmesim hover:underline">
                      secretariado@controlador.cv
                    </a>
                  </div>
                </div>

                {/* Email Press */}
                <div className="flex gap-5">
                  <div className="w-14 h-14 bg-grafite/10 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Newspaper className="w-7 h-7 text-grafite" />
                  </div>
                  <div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-1">Imprensa</h3>
                    <a href="mailto:comunicacao@controlador.cv" className="text-carmesim hover:underline">
                      comunicacao@controlador.cv
                    </a>
                  </div>
                </div>

              </div>

              {/* Contactos úteis — recurso educativo (entidades terceiras).
                  Sede/telefone institucionais da ACCTA omitidos enquanto não
                  forem confirmados — sem placeholders (spec §5). */}
              <div>
                <h3 className="font-sans font-bold text-2xl text-grafite mb-2">
                  Contactos Úteis
                </h3>
                <p className="text-sm text-gray-500 mb-6">{notaContactos}</p>
                <ul className="space-y-4">
                  {contactosUteis.map((c) => (
                    <li key={c.entidade} className="card-technical rounded-xl p-5">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-grafite rounded-lg flex items-center justify-center flex-shrink-0">
                          <MapPin className="w-5 h-5 text-white" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-semibold text-grafite">{c.entidade}</h4>
                          <p className="text-xs text-carmesim uppercase tracking-wider font-semibold mb-1">{c.papel}</p>
                          <p className="text-sm text-gray-600">{c.contacto}</p>
                          <a
                            href={c.site}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-sm text-grafite font-medium hover:text-carmesim transition-colors mt-1"
                          >
                            Site oficial
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Contact Form */}
            <div className="animate-fade-up">
              <div className="card-technical rounded-2xl p-8">
                <h2 className="font-sans font-bold text-2xl text-grafite mb-2">
                  Formulário de Contacto
                </h2>
                <p className="text-gray-600 mb-8">
                  Preencha o formulário abaixo e entraremos em contacto o mais breve possível.
                </p>

                {sent ? (
                  <div className="text-center py-12 animate-fade-up">
                    <div className="w-20 h-20 bg-carmesim/10 rounded-full flex items-center justify-center mx-auto mb-6">
                      <CheckCircle className="w-10 h-10 text-carmesim" />
                    </div>
                    <h3 className="font-sans font-semibold text-xl text-grafite mb-2">
                      Mensagem Enviada!
                    </h3>
                    <p className="text-gray-600">
                      Obrigado pelo seu contacto. Responderemos em breve.
                    </p>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Name */}
                    <div>
                      <label htmlFor="contact-name" className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Nome *
                      </label>
                      <input
                        id="contact-name"
                        type="text"
                        name="name"
                        autoComplete="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="O seu nome completo"
                        className="w-full px-4 py-3 border border-gray-200 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 transition-all"
                        required
                        data-testid="contact-name"
                      />
                    </div>

                    {/* Email */}
                    <div>
                      <label htmlFor="contact-email" className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Email *
                      </label>
                      <input
                        id="contact-email"
                        type="email"
                        inputMode="email"
                        autoComplete="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="seu.email@exemplo.com"
                        className="w-full px-4 py-3 border border-gray-200 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 transition-all"
                        required
                        data-testid="contact-email"
                      />
                    </div>

                    {/* Subject */}
                    <div>
                      <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Assunto
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        {subjects.map((subject) => (
                          <label
                            key={subject.value}
                            className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                              formData.subject === subject.value
                                ? 'bg-grafite text-white'
                                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                            }`}
                          >
                            <input
                              type="radio"
                              name="subject"
                              value={subject.value}
                              checked={formData.subject === subject.value}
                              onChange={handleChange}
                              className="hidden"
                            />
                            <subject.icon className="w-5 h-5" />
                            <span className="text-sm font-medium">{subject.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Message */}
                    <div>
                      <label htmlFor="contact-message" className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Mensagem *
                      </label>
                      <textarea
                        id="contact-message"
                        name="message"
                        value={formData.message}
                        onChange={handleChange}
                        placeholder="Escreva a sua mensagem aqui..."
                        rows={5}
                        className="w-full px-4 py-3 border border-gray-200 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 transition-all resize-none"
                        required
                        data-testid="contact-message"
                      />
                    </div>

                    {/* Submit */}
                    <button
                      type="submit"
                      disabled={sending}
                      className="w-full flex items-center justify-center gap-2 bg-grafite text-white px-6 py-4 rounded-lg font-bold hover:bg-grafite/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="contact-submit"
                    >
                      {sending ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Enviando...
                        </>
                      ) : (
                        <>
                          <Send className="w-5 h-5" />
                          Enviar Mensagem
                        </>
                      )}
                    </button>
                  </form>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ — base de conhecimento (acordeão nativo, zero JS extra) */}
      <section className="py-16 bg-white">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-10">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-4">
              <HelpCircle className="w-4 h-4" />
              Base de Conhecimento
            </span>
            <h2 className="font-sans font-bold text-3xl text-grafite mb-3">
              Perguntas Frequentes
            </h2>
            <p className="text-lg text-gray-600">
              Respostas alinhadas à regulação aplicável (CV-CAR / decretos)
            </p>
          </div>

          <div className="space-y-3">
            {faq.map((item, index) => (
              <details
                key={index}
                className="group card-technical rounded-xl overflow-hidden"
              >
                <summary className="flex items-center justify-between gap-4 p-5 cursor-pointer list-none font-semibold text-grafite">
                  <span>{item.pergunta}</span>
                  <ChevronDown className="w-5 h-5 text-carmesim flex-shrink-0 transition-transform group-open:rotate-180" />
                </summary>
                <div className="px-5 pb-5 text-gray-600 text-sm leading-relaxed">
                  {item.resposta}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};
