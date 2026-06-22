# Contrato — Rota & ponto de entrada no rodapé

> Esta feature não expõe APIs de backend. Os "contratos" são de **UI/rota** (frontend).

## Contrato de rota

| Propriedade | Valor |
|-------------|-------|
| Path | `/plataforma` |
| Layout | `<PublicLayout>` (cabeçalho + rodapé partilhados) |
| Componente | `PlataformaPage` (named export) de `pages/public/PlataformaPage.js` |
| Carregamento | **lazy** (`React.lazy` + `Suspense`, como as outras páginas públicas) |
| Acesso | público (sem auth, sem RBAC) |
| Métodos | navegação client-side (GET da SPA) |

**Registo esperado em `frontend/src/App.js`:**

```jsx
// junto aos restantes imports lazy (~L13–32)
const PlataformaPage = lazy(() =>
  import('./pages/public/PlataformaPage').then((m) => ({ default: m.PlataformaPage }))
);

// no bloco de rotas públicas de AppRoutes() (~L117–133)
<Route path="/plataforma" element={<PublicLayout><PlataformaPage /></PublicLayout>} />
```

### Critérios de aceitação da rota
- `GET /plataforma` (navegação) renderiza `PlataformaPage` dentro do `PublicLayout`.
- A rota não exige autenticação e não chama endpoints protegidos.
- Acesso direto por URL e via SPA funcionam (sem 404 do router).

## Contrato do link discreto no rodapé

| Propriedade | Valor |
|-------------|-------|
| Ficheiro | `frontend/src/layouts/PublicLayout.js` (rodapé ~L132–172) |
| Local | barra inferior (junto a copyright / "Política de Privacidade", ~L167–170) |
| Componente | `<Link to="/plataforma">` (react-router) |
| Label (PT-PT) | "A plataforma" |
| Estilo (discreto) | classes de baixa proeminência, ex. `text-white/50 hover:text-white transition-colors text-xs sm:text-sm` |

### Critérios de aceitação do link
- O link aparece no rodapé de **todas** as páginas públicas (rodapé partilhado).
- É visualmente **discreto** — não compete com "Links Rápidos"/"Área Reservada".
- Clicar navega para `/plataforma` sem recarregar a página (SPA).
