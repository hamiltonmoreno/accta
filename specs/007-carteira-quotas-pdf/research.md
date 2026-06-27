# Research — Exportar carteira de quotas em PDF

Fase 0. Decisões técnicas. A feature reutiliza infra existente; quase nada é novo.

---

## D1 — Geração do PDF (reutilizar o gerador *branded* existente)

**Decision**: Reutilizar `fpdf` (fpdf2, já dependência) e os helpers de
`backend/routes/finances.py`: `_new_relatorio_pdf()` (página A4, auto page-break) e
`_fmt()` (formatação CVE), com o **mesmo cabeçalho de marca** dos PDF atuais —
retângulo Carmesim `(199,32,47)`, título branco "ACCTA - Cabo Verde", texto Grafite
`(58,58,58)`, linha "Gerado em … UTC". Adicionar um renderer `_render_carteira(pdf,
member, items, total)` análogo a `_render_dre()`.

**Rationale**: Consistência visual com o DRE/Relatório e Contas, zero deps novas,
caminho mais curto. `StreamingResponse(io.BytesIO(...), media_type="application/pdf",
headers={"Content-Disposition": "attachment; filename=…"})` já é o padrão (linha ~1132).

**Alternatives considered**: WeasyPrint/HTML→PDF — rejeitado (dep nova, runtime mais
pesado). reportlab — já há `fpdf` em uso; não misturar.

---

## D2 — RBAC: self-service, só o próprio (sem privilégio, sem audit)

**Decision**: Endpoint `GET /api/finances/me/quotas/pdf` com `Depends(get_current_user)`,
construindo o PDF a partir da **mesma query** de `/me/quotas` (filtro fixo
`user_id == current_user.id`, `type=receita`, `category ∈ {quotas, joias}`). Sem
verificação de privilégio (qualquer autenticado vê só os seus). **Sem audit log** —
é leitura dos próprios dados, não escrita de admin.

**Rationale**: Espelha exatamente a postura de `/me/quotas` (já em prod, RBAC-safe).
Princípio III: audit é para escritas de admin; um export self-service de dados próprios
não o exige (nem `/me/quotas` o faz). FR-005/FR-006 garantidos pelo `get_current_user`
+ filtro por `user_id` (não há parâmetro de "outro sócio" — impossível por construção).

**Alternatives considered**: aceitar `user_id` na query (admin exportar a de terceiros)
— **fora de âmbito** e violaria a privacidade (spec restringe ao próprio). Auditar o
export — desnecessário (Simplicity); pode ser follow-up se o dono quiser rasto.

---

## D3 — Codificação de texto (acentos PT)

**Decision**: Manter os **rótulos** do PDF em ASCII (como os PDF atuais: "Descricao",
"Gerado em…"). Os **dados** do sócio (nome, descrição/período) são renderizados como
estão; PT cabe em **latin-1** (á é í ó ú ã õ ç à â ê…), que as core fonts do fpdf
suportam. Sanitizar defensivamente apenas caracteres **fora** de latin-1 (raros) para
não rebentar a geração.

**Rationale**: As core fonts (Helvetica) do fpdf codificam em latin-1; PT está todo em
latin-1, por isso nomes como "José"/"Sócio" funcionam sem fonte TTF embebida. Evita
empacotar um .ttf Unicode (dep/peso) e mantém a convenção dos PDF existentes.

**Alternatives considered**: Embeber DejaVuSans (Unicode) — rejeitado por agora
(ficheiro de fonte + setup; só seria preciso para caracteres fora de latin-1, que não
ocorrem em nomes PT). Transliterar tudo para ASCII — rejeitado (mutilaria o nome do
próprio sócio no seu comprovativo).

---

## D4 — Download no frontend (reutilizar o idioma de blob existente)

**Decision**: Novo método `financesAPI.myQuotasPdf()` em `utils/api.js` (GET,
`responseType: 'blob'`, `withCredentials` herdado do cliente axios). Na `CarteiraPage`,
botão "Exportar PDF" que faz `URL.createObjectURL(new Blob([res.data], {type:'application/pdf'}))`
+ `<a download>` — **exatamente** o idioma já usado em `DRETab.js`/`CashFlowTab.js` e na
própria `CarteiraPage` (download do QR PNG, ~linha 159).

**Rationale**: Padrão estabelecido, lida com o cookie httpOnly (axios `withCredentials`)
em dev (proxy mesma-origem) e prod (cross-origin `SameSite=None`). Sem reinventar.

**Alternatives considered**: `<a href>` direto para o endpoint — funcionaria
(cookie cross-origin SameSite=None) mas o padrão da app é blob via axios; manter
consistência e tratamento de erro uniforme (toast).

---

## D5 — Conteúdo e layout do PDF

**Decision**: Estrutura do documento:
1. **Cabeçalho de marca** ACCTA (Carmesim/branco) + subtítulo "Carteira de Quotas".
2. **Identificação**: nome do sócio, n.º de sócio, data de emissão (UTC).
3. **Tabela** de lançamentos (mais recente→antigo, como `/me/quotas`): Data,
   Período/Descrição, Categoria (Quota/Joia), Valor (CVE). Subtotais por ano quando
   ajudar a leitura.
4. **Total pago** em destaque.
5. **Rodapé**: nota "Comprovativo pessoal de uso interno — sem valor fiscal." (FR-004).
6. **Carteira vazia** (FR-007): linha "Sem lançamentos registados." + Total 0.

Filename: `Carteira_Quotas_ACCTA_<member_id|socio>.pdf`.

**Rationale**: Cobre FR-002/003/004/007; espelha a vista da Carteira (FR-008:
mesmos itens e total que `/me/quotas`).

**Alternatives considered**: Seletor de ano/período — fora do MVP (Assumption do spec);
o PDF cobre toda a carteira.

---

## Resumo de impacto

- **Backend**: `routes/finances.py` — 1 endpoint (`GET /me/quotas/pdf`) + `_render_carteira()`.
- **Frontend**: `CarteiraPage.js` (botão) + `utils/api.js` (método).
- **Deps**: zero novas. **Schema/dados**: sem alterações (leitura).
- **Release**: toca `backend/` → **Via B** no corte para prod (não agora).
- **Sem decisões pendentes do dono.**
