# Contrato — `GET /api/auth/registration-options` (alteração aditiva)

**Estado**: público (sem autenticação), sem rate-limit dedicado. **Alimenta o formulário público de inscrição** (`CriarContaPage`).

## Antes

```json
{ "cargos": ["Sócio", "Vogal", "Tesoureiro", "Secretário", "Vice-Presidente", "Presidente", "Direcção", "Conselho Fiscal"] }
```

## Depois (aditivo — não-quebra)

```json
{
  "cargos": ["Sócio", "Vogal", "Tesoureiro", "Secretário", "Vice-Presidente", "Presidente", "Direcção", "Conselho Fiscal"],
  "departamentos": [
    "Formação e Certificação",
    "Segurança Operacional (Safety)",
    "Assuntos Profissionais e Laborais",
    "Assuntos Técnicos e Operacionais",
    "Relações Institucionais e Internacionais",
    "Comunicação e Imagem",
    "Assuntos Jurídicos",
    "Tesouraria e Finanças",
    "Eventos, Cultura e Ação Social"
  ]
}
```

## Regras

- `departamentos` == `models.DEPARTAMENTOS` (fonte única backend). Ordem estável.
- **Compatibilidade**: clientes que só lêem `cargos` continuam a funcionar (campo novo ignorado). O frontend mantém um `DEPARTAMENTOS_FALLBACK` local caso o pedido falhe (à imagem de `CARGOS_FALLBACK`).
- Nenhuma alteração ao corpo de `POST /api/auth/register`: `department` continua opcional, string livre (max 80). O valor submetido é o item escolhido ou o texto de «Outro».

## `POST /api/auth/register` — invariantes preservadas (não muda)

- Rate-limit `3/hour`, verificação Turnstile e honeypot `website` **intactos** (FR-017).
- `role` forçado a `socio`; `status` = `pendente_aprovacao`.
- `department` guardado tal como recebido (ou `""`).

## Teste decisivo (backend)

`GET /api/auth/registration-options` → 200 com `departamentos` presente, não-vazio, == `models.DEPARTAMENTOS`.
