import React from 'react';
import { AlertTriangle, ExternalLink, FlaskConical, Loader2, Send, Users } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from '../../../components/ui/card';

const WARNING_LABELS = {
  intersection_reduced: (w) =>
    `Filtros combinados por E — a intersecção reduziu a audiência abaixo do critério "${w.below}".`,
  nominal_not_found: (w) =>
    `Não encontrados na lista nominal (ignorados): ${(w.values || []).join(', ')}.`,
  technical_excluded: (w) =>
    `Contas técnicas excluídas: ${(w.member_ids || []).join(', ')}.`,
  includes_unapproved: (w) =>
    `Inclui contas ainda não aprovadas (${(w.statuses || []).join(', ')}).`,
};

function AudiencePreview({ previewing, audienceReady, audience }) {
  if (!audienceReady) {
    return <span>Defina pelo menos um critério de audiência para ver o alcance.</span>;
  }
  if (previewing || !audience) {
    return (
      <span className="inline-flex items-center gap-1.5">
        <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" /> A calcular…
      </span>
    );
  }
  return (
    <div className="space-y-2 w-full">
      <div>
        Vai para <strong className="text-grafite tabular-nums">{audience.recipients_count}</strong> sócio(s)
        {audience.sample?.length > 0 && (
          <span className="text-[#6B7280]">
            {' '}— {audience.sample.join(', ')}{audience.more > 0 ? ` …mais ${audience.more}` : ''}
          </span>
        )}
      </div>
      {audience.per_type_counts && Object.keys(audience.per_type_counts).length > 1 && (
        <div className="text-xs text-[#6B7280]">
          Por tipo: {Object.entries(audience.per_type_counts).map(([k, n]) => `${k} ${n}`).join(' · ')}
          {' → '}intersecção <strong className="text-grafite">{audience.intersected_count}</strong>
        </div>
      )}
      {(audience.warnings || []).map((w, i) => (
        <p key={i} className="text-xs text-[#B45309] flex items-start gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" aria-hidden="true" />
          <span>{WARNING_LABELS[w.code] ? WARNING_LABELS[w.code](w) : w.code}</span>
        </p>
      ))}
    </div>
  );
}

export function PreviewCard({
  subject, body,
  ctaLabel, ctaUrl, ctaUrlValid,
  channels, segmentReady, countingRecipients,
  inApp, emailCount,
  validationError, canSubmit, pending,
  onSubmitClick,
  // Modo segmentado (spec-comunicados-segmentados)
  audienceMode, audienceReady, audiencePreview, previewing, dryRun,
}) {
  const segmented = audienceMode === 'segmentada';
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

        {/* Modo simulação (dry-run) — aviso neutro */}
        {segmented && dryRun && (
          <div className="rounded-lg border border-[#E5E7EB] bg-[#F5F5F5] p-3 text-sm text-grafite inline-flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />
            Modo simulação — calcula a audiência e regista, mas não envia nada.
          </div>
        )}

        {/* Alcance ao vivo */}
        <div className="rounded-lg border border-[#E5E7EB] p-3">
          <div className="flex items-start gap-2 text-sm text-[#6B7280]">
            <Users className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
            {segmented ? (
              <AudiencePreview
                previewing={previewing}
                audienceReady={audienceReady}
                audience={audiencePreview}
              />
            ) : channels.length === 0 || !segmentReady ? (
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
          {pending ? 'A enviar…' : (segmented && dryRun ? 'Simular envio' : 'Enviar comunicado')}
        </button>
      </CardContent>
    </Card>
  );
}
