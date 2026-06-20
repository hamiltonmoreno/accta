import React from 'react';
import { Bell, Mail } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from '../../../components/ui/card';
import { Input } from '../../../components/ui/input';
import { Textarea } from '../../../components/ui/textarea';
import { Label } from '../../../components/ui/label';
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from '../../../components/ui/select';
import { Checkbox } from '../../../components/ui/checkbox';
import { MemberSelector } from './MemberSelector';
import { AudienceBuilder } from './AudienceBuilder';
import { SEGMENT_KIND_LABELS } from './tokens';

export function ComposerCard({
  subject, setSubject,
  body, setBody,
  tipo, setTipo,
  channels, toggleChannel,
  segKind, setSegKind,
  segValue, setSegValue,
  userIds, toggleUser,
  ctaLabel, setCtaLabel,
  ctaUrl, setCtaUrl,
  ctaUrlValid,
  valueOptions,
  // Modo segmentado (spec-comunicados-segmentados)
  audienceMode, setAudienceMode,
  af, setAf, cargoOptions, categoriaOptions,
  dryRun, setDryRun, showDryRun,
  restricted = false,
}) {
  const segmented = restricted || audienceMode === 'segmentada';
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-grafite">Novo comunicado</CardTitle>
        <CardDescription>Preencha os campos e reveja antes de disparar.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Assunto */}
        <div className="space-y-1.5">
          <Label htmlFor="comunicado-subject">Assunto</Label>
          <Input
            id="comunicado-subject"
            value={subject}
            maxLength={200}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Ex.: Convocatória da Assembleia Geral Ordinária"
            data-testid="comunicado-subject"
          />
        </div>

        {/* Corpo */}
        <div className="space-y-1.5">
          <Label htmlFor="comunicado-body">Corpo da mensagem</Label>
          <Textarea
            id="comunicado-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={6}
            placeholder="Escreva o conteúdo do comunicado…"
            data-testid="comunicado-body"
          />
          <p className="text-xs text-[#6B7280]">Mínimo 10 caracteres. As quebras de parágrafo são preservadas.</p>
        </div>

        {/* Tipo */}
        <div className="space-y-1.5">
          <Label htmlFor="comunicado-tipo">Tipo</Label>
          <Select value={tipo} onValueChange={setTipo}>
            <SelectTrigger id="comunicado-tipo" data-testid="comunicado-tipo">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="informativo">Informativo</SelectItem>
              <SelectItem value="oficial">Oficial</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-[#6B7280]">
            {tipo === 'oficial'
              ? 'Oficial: chega a todos os destinatários, ignorando as preferências de opt-out.'
              : 'Informativo: respeita o opt-out de e-mails de cada sócio.'}
          </p>
        </div>

        {/* Canais */}
        <div className="space-y-2">
          <Label>Canais</Label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={channels.includes('in_app')}
                onCheckedChange={() => toggleChannel('in_app')}
                data-testid="comunicado-channel-in_app"
              />
              <span className="inline-flex items-center gap-1.5 text-sm text-grafite">
                <Bell className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />
                Notificação na app
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={channels.includes('email')}
                onCheckedChange={() => toggleChannel('email')}
                data-testid="comunicado-channel-email"
              />
              <span className="inline-flex items-center gap-1.5 text-sm text-grafite">
                <Mail className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />
                E-mail
              </span>
            </label>
          </div>
          {channels.length === 0 && (
            <p className="text-xs text-[#B91C1C]">Selecione pelo menos um canal.</p>
          )}
        </div>

        {/* Destinatários — modo simples (segment) ou segmentado (audience_filter) */}
        <div className="space-y-2">
          <Label htmlFor="comunicado-audience-mode">Destinatários</Label>
          {restricted ? (
            <p className="text-xs text-[#6B7280]">
              Pode dirigir-se apenas a órgãos sociais (Direcção, Mesa da AG, Conselho Fiscal).
            </p>
          ) : (
            <Select value={audienceMode} onValueChange={setAudienceMode}>
              <SelectTrigger id="comunicado-audience-mode" data-testid="comunicado-audience-mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="simples">Audiência simples</SelectItem>
                <SelectItem value="segmentada">Audiência segmentada</SelectItem>
              </SelectContent>
            </Select>
          )}

          {!segmented && (
            <div className="space-y-1.5 pt-1">
              <Select
                value={segKind}
                onValueChange={(v) => { setSegKind(v); setSegValue(''); }}
              >
                <SelectTrigger id="comunicado-segment" data-testid="comunicado-segment">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(SEGMENT_KIND_LABELS).map(([k, label]) => (
                    <SelectItem key={k} value={k}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {(segKind === 'role' || segKind === 'member_category' || segKind === 'orgao') && (
                <div className="pt-1">
                  <Select value={segValue} onValueChange={setSegValue}>
                    <SelectTrigger data-testid="comunicado-segment-value">
                      <SelectValue placeholder="Escolha um valor…" />
                    </SelectTrigger>
                    <SelectContent>
                      {valueOptions.map((o) => (
                        <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {segKind === 'manual' && (
                <div className="pt-1">
                  <MemberSelector selectedIds={userIds} onToggle={toggleUser} />
                </div>
              )}
            </div>
          )}

          {segmented && (
            <div className="pt-1">
              <AudienceBuilder
                af={af} setAf={setAf}
                cargoOptions={cargoOptions} categoriaOptions={categoriaOptions}
                restricted={restricted}
              />
            </div>
          )}

          {segmented && showDryRun && (
            <label className="flex items-center gap-2 cursor-pointer pt-1">
              <Checkbox checked={dryRun} onCheckedChange={() => setDryRun(!dryRun)} data-testid="comunicado-dry-run" />
              <span className="text-sm text-grafite">Simulação (dry-run) — não envia, apenas calcula e regista</span>
            </label>
          )}
        </div>

        {/* CTA opcional */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="comunicado-cta-label">Botão (texto) — opcional</Label>
            <Input
              id="comunicado-cta-label"
              value={ctaLabel}
              onChange={(e) => setCtaLabel(e.target.value)}
              placeholder="Ex.: Ver convocatória"
              data-testid="comunicado-cta-label"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="comunicado-cta-url">Botão (URL) — opcional</Label>
            <Input
              id="comunicado-cta-url"
              value={ctaUrl}
              onChange={(e) => setCtaUrl(e.target.value)}
              placeholder="https://…"
              aria-invalid={!ctaUrlValid}
              data-testid="comunicado-cta-url"
            />
            {!ctaUrlValid && (
              <p className="text-xs text-[#B91C1C]">Deve começar por http:// ou https://.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
