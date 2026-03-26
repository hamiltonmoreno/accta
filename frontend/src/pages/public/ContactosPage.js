import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { 
  Mail, 
  Phone, 
  MapPin, 
  Send, 
  MessageSquare,
  Newspaper,
  HandshakeIcon,
  HelpCircle,
  Loader2,
  CheckCircle,
  Plane
} from 'lucide-react';

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
    
    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setSending(false);
    setSent(true);
    toast.success('Mensagem enviada com sucesso!');
    
    // Reset form after delay
    setTimeout(() => {
      setFormData({ name: '', email: '', subject: 'geral', message: '' });
      setSent(false);
    }, 3000);
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
      <section className="relative py-24 bg-grafite overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'linear-gradient(rgba(0,255,156,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,156,0.3) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />
        </div>
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <span className="inline-block px-4 py-2 bg-carmesim/10 border border-accent/30 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Contactos
            </span>
            <h1 className="font-sans font-bold text-5xl lg:text-6xl text-white mb-6" data-testid="contact-title">
              Fale{' '}
              <span className="text-carmesim">Conosco</span>
            </h1>
            <p className="text-xl text-white/80 max-w-3xl mx-auto leading-relaxed">
              Tem dúvidas sobre a associação, a profissão ou deseja propor uma parceria? Utilize os canais oficiais.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Contact Info & Form */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16">
            {/* Contact Information */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="font-sans font-bold text-3xl text-grafite mb-8">
                Informações de Contacto
              </h2>

              <div className="space-y-6 mb-12">
                {/* Address */}
                <div className="flex gap-5">
                  <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center flex-shrink-0">
                    <MapPin className="w-7 h-7 text-carmesim" />
                  </div>
                  <div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-1">Sede</h3>
                    <p className="text-gray-600">
                      Aeroporto Internacional Nelson Mandela<br />
                      Praia - Cabo Verde
                    </p>
                  </div>
                </div>

                {/* Email General */}
                <div className="flex gap-5">
                  <div className="w-14 h-14 bg-carmesim rounded-xl flex items-center justify-center flex-shrink-0">
                    <Mail className="w-7 h-7 text-grafite" />
                  </div>
                  <div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-1">Email Geral</h3>
                    <a href="mailto:secretariado@accta.cv" className="text-carmesim hover:underline">
                      secretariado@accta.cv
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
                    <a href="mailto:comunicacao@accta.cv" className="text-carmesim hover:underline">
                      comunicacao@accta.cv
                    </a>
                  </div>
                </div>

                {/* Phone */}
                <div className="flex gap-5">
                  <div className="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Phone className="w-7 h-7 text-grafite" />
                  </div>
                  <div>
                    <h3 className="font-sans font-semibold text-lg text-grafite mb-1">Telefone</h3>
                    <a href="tel:+238999999" className="text-gray-600 hover:text-carmesim transition-colors">
                      (+238) 999 99 99
                    </a>
                  </div>
                </div>
              </div>

              {/* Map placeholder */}
              <div className="bg-gray-200 rounded-2xl h-64 flex items-center justify-center">
                <div className="text-center">
                  <Plane className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">Mapa da localização</p>
                </div>
              </div>
            </motion.div>

            {/* Contact Form */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="card-technical rounded-2xl p-8">
                <h2 className="font-sans font-bold text-2xl text-grafite mb-2">
                  Formulário de Contacto
                </h2>
                <p className="text-gray-600 mb-8">
                  Preencha o formulário abaixo e entraremos em contacto o mais breve possível.
                </p>

                {sent ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center py-12"
                  >
                    <div className="w-20 h-20 bg-carmesim/10 rounded-full flex items-center justify-center mx-auto mb-6">
                      <CheckCircle className="w-10 h-10 text-carmesim" />
                    </div>
                    <h3 className="font-sans font-semibold text-xl text-grafite mb-2">
                      Mensagem Enviada!
                    </h3>
                    <p className="text-gray-600">
                      Obrigado pelo seu contacto. Responderemos em breve.
                    </p>
                  </motion.div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Name */}
                    <div>
                      <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Nome *
                      </label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="O seu nome completo"
                        className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                        required
                        data-testid="contact-name"
                      />
                    </div>

                    {/* Email */}
                    <div>
                      <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Email *
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="seu.email@exemplo.com"
                        className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
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
                      <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">
                        Mensagem *
                      </label>
                      <textarea
                        name="message"
                        value={formData.message}
                        onChange={handleChange}
                        placeholder="Escreva a sua mensagem aqui..."
                        rows={5}
                        className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none"
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
            </motion.div>
          </div>
        </div>
      </section>

      {/* FAQ Quick Links */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-3xl text-grafite mb-6">
            Perguntas Frequentes
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Antes de nos contactar, verifique se a sua dúvida não está respondida nas nossas páginas informativas.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href="/profissao"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-100 text-grafite rounded-lg hover:bg-gray-200 transition-all font-medium"
            >
              <HelpCircle className="w-5 h-5" />
              Sobre a Profissão
            </a>
            <a
              href="/sobre"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-100 text-grafite rounded-lg hover:bg-gray-200 transition-all font-medium"
            >
              <HelpCircle className="w-5 h-5" />
              Sobre a Associação
            </a>
            <a
              href="/beneficios-publico"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-100 text-grafite rounded-lg hover:bg-gray-200 transition-all font-medium"
            >
              <HelpCircle className="w-5 h-5" />
              Parcerias
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};
