import React from 'react';
import { ExternalLink, Loader2, Send, Users } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from '../../../components/ui/card';

export function PreviewCard({
  subject, body,
  ctaLabel, ctaUrl, ctaUrlValid,
  channels, segmentReady, countingRecipients,
  inApp, emailCount,
  validationError, canSubmit, pending,
  onSubmitClick,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-grafite">Pré-visualização</CardTitle>
        <CardDescription>Como o sócio verá o comunicado.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border border-[#E5E7EB] bg-[#F5F5F5] p-4">
          <h3 className="font-semibold text-grafite break-words">
            {subject || 'Assunto do comunicado'}
          </h3>
          <div className="mt-2 space-y-2 text-sm text-grafite">
            {(body || 'O corpo da mensagem aparecerá aqui.')
              .split('\n')
              .map((para, i) => (
                <p key={i} className="break-words whitespace-pre-wrap">{para || ' '}</p>
              ))}
          </div>
          {ctaLabel && ctaUrl && ctaUrlValid && (
            // Mock visual do botão do EMAIL (pré-visualização), não um botão
            // da página: o Carmesim sólido é intencional — replica o CTA tal
            // como aparece no email enviado, fora da taxonomia de cor de ação
            // das páginas (ver lib/buttonStyles.js / spec-botoes-cor-acao).
            <a
              href={ctaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-[#A51B27] transition-colors focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
            >
              {ctaLabel}
              <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
            </a>
          )}
        </div>

        {/* Contagem ao vivo */}
        <div className="rounded-lg border border-[#E5E7EB] p-3">
          <div className="flex items-center gap-2 text-sm text-[#6B7280]">
            <Users className="w-4 h-4" aria-hidden="true" />
            {channels.length === 0 || !segmentReady ? (
              <span>Selecione canais e destinatários para ver o alcance.</span>
            ) : countingRecipients ? (
              <span className="inline-flex items-center gap-1.5">
                <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                A calcular…
              </span>
            ) : (
              <span>
                Vai para <strong className="text-grafite tabular-nums">{inApp}</strong> na app
                {' · '}
                <strong className="text-grafite tabular-nums">{emailCount}</strong> por e-mail
              </span>
            )}
          </div>
        </div>

        {validationError && (
          <p className="text-xs text-[#B91C1C]" data-testid="comunicado-validation">{validationError}</p>
        )}

        {/* O ÚNICO botão primário (ação positiva, Floresta) da vista */}
        <button
          type="button"
          onClick={onSubmitClick}
          disabled={!canSubmit}
          className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-floresta text-white font-semibold hover:bg-floresta-dark transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
          data-testid="comunicado-submit"
        >
          {pending ? (
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="w-4 h-4" aria-hidden="true" />
          )}
          {pending ? 'A disparar…' : 'Disparar comunicado'}
        </button>
      </CardContent>
    </Card>
  );
}
