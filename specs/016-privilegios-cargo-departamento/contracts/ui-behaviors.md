# Contrato — Comportamentos de UI (Spec 016)

Estes são contratos de interface para o utilizador (não há endpoints novos). Verificáveis no navegador (Princípio VII).

## C1 — Rótulos de privilégio (US1) · `EditUserModal`

- **Dado** a grelha de privilégios, **então** cada uma das 12 permissões mostra um rótulo PT não-vazio.
- **Fallback**: um privilégio sem entrada em `PRIVILEGE_LABELS` mostra a sua chave técnica (via `privilegeLabel()`), nunca vazio.
- Chaves→rótulos novos: `emit_cf_parecer`→«Emitir Parecer (Conselho Fiscal)», `send_comunicados`→«Enviar Comunicados», `comunicar_intra_orgao`→«Comunicar entre Órgãos».

## C2 — Seletor de função no convite (US3) · `InviteModal`

- O `<select>` de função lista **4** opções (Administrador, Sócio, Financeiro, Moderador), derivadas de `ROLES` + `ROLE_LABELS`.
- Rótulo do campo = «Função no Sistema» (consistente com `EditUserModal`).
- Default selecionado = «Sócio».

## C3 — Dropdown de departamento (US2) · `CriarContaPage`, `InviteModal`, `EditUserModal`

- O campo «Departamento» é um `<select>` com os 9 departamentos + opção final **«Outro»**; **opcional** (estado inicial «Selecionar…» permitido).
- Escolher «Outro» revela um `<input>` de texto livre; o valor submetido/guardado é: item da lista escolhido, ou o texto de «Outro».
- **Público**: opções via `registrationAPI.options().departamentos` (fallback local se falhar). **Admin**: via constante `DEPARTAMENTOS` de `tokens.js`.
- **Preservação de legado (`EditUserModal`)**: se `department` guardado ∉ lista e ≠ vazio, abre com «Outro» selecionado e o valor no campo de texto (sem perda).

## C4 — Botão «Aplicar predefinições do cargo» (US4) · `EditUserModal`

- **Visível** apenas se `account_type !== 'technical'` **e** o `cargo` do sócio existe no catálogo de `GET /api/governance/structure`.
- **Ao clicar**: preenche `role` = `role_default` do cargo e `privileges` = `privileges_default` do cargo (cópia). Não grava — o admin ajusta e depois «Guardar».
- **Nunca** altera função/privilégios automaticamente sem o clique.
- **Estilo**: botão **secundário** neutro (`border-[#D1D5DB]`), nunca Carmesim-positivo nem Floresta (o primário positivo da vista é «Guardar»).
- **Edge**: cargo com `privileges_default` vazio → o clique esvazia os privilégios explicitamente (reversível antes de guardar).
