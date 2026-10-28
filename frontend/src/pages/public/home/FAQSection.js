import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, HelpCircle } from 'lucide-react';
import {
  Accordion, AccordionItem, AccordionTrigger, AccordionContent,
} from '../../../components/ui/accordion';
import { useI18n } from '../../../i18n';

export const FAQSection = () => {
  const { t, lp, cta } = useI18n();
  const { faq } = cta;
  return (
  <section className="py-16 sm:py-24 bg-gray-50">
    <div className="max-w-3xl mx-auto px-5 sm:px-6">
      <div className="text-center mb-10 sm:mb-12 animate-fade-up">
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-grafite/5 text-grafite rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
          <HelpCircle className="w-3.5 h-3.5" />
          {t('home.faq.badge')}
        </span>
        <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-grafite mb-3 sm:mb-4">
          {t('home.faq.titleStart')}{' '}
          <span className="text-carmesim">{t('home.faq.titleHighlight')}</span>
        </h2>
        <p className="text-sm sm:text-lg text-gray-600">
          {t('home.faq.lead')}
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 px-5 sm:px-8 animate-fade-up">
        <Accordion type="single" collapsible className="w-full">
          {faq.slice(0, 6).map((item, i) => (
            <AccordionItem key={i} value={`faq-${i}`} className="border-gray-100 last:border-0">
              <AccordionTrigger className="text-grafite font-semibold text-sm sm:text-base hover:no-underline py-5 gap-4">
                {item.pergunta}
              </AccordionTrigger>
              <AccordionContent className="text-gray-600 text-sm leading-relaxed">
                {item.resposta}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      <div className="text-center mt-8 animate-fade-up">
        <Link
          to={lp('/profissao')}
          className="inline-flex items-center gap-2 text-carmesim font-semibold hover:text-carmesim-dark transition-colors group text-sm sm:text-base"
        >
          {t('home.faq.link')}
          <ChevronRight className="w-4 sm:w-5 h-4 sm:h-5 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>
    </div>
  </section>
  );
};
