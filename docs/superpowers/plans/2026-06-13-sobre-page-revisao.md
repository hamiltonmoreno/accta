# Revisão da página "Sobre / Quem Somos" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar a página pública `/sobre` factualmente correta, em PT-PT, com melhor layout/UI-UX, e com a secção "Corpos Sociais" preenchida dinamicamente (nome + foto dos dirigentes eleitos) a partir de um endpoint público novo, degradando para "Vago" quando o cargo não tem titular.

**Architecture:** Backend FastAPI expõe `GET /api/governance/corpos-sociais` (público) que lê os titulares de cargo estatutário da BD (DAO Mongo-compatível) e devolve a estrutura completa dos 3 órgãos. Frontend (`SobrePage.js`) consome via TanStack Query, reescreve a copy com tom factual e aplica o relatório UI/UX.

**Tech Stack:** FastAPI + asyncpg DAO + Pydantic (backend); React 19 + TanStack Query + Tailwind + Lucide (frontend). Ramo `feature/sobre-page-revisao`.

**Spec:** `docs/superpowers/specs/2026-06-13-sobre-page-revisao-design.md`

---

## File Structure

- `backend/models.py` — modelos de resposta `CorpoSocial*` (Modify).
- `backend/routes/governance.py` — endpoint público + mapa de exibição de órgãos (Modify).
- `backend/tests/test_governance_corpos_sociais.py` — testes do endpoint (Create).
- `frontend/src/lib/queryClient.js` — queryKey `governance.corposSociais` (Modify).
- `frontend/src/utils/api.js` — `governanceAPI.getCorposSociais` (Modify).
- `frontend/src/pages/public/SobrePage.js` — redesign + copy + fetch (Modify).
- `frontend/src/index.css` ou `App.css` — guard `prefers-reduced-motion` (Verify/Modify).

---

## Task 1: Modelos de resposta dos Corpos Sociais (backend)

**Files:**
- Modify: `backend/models.py` (acrescentar no fim, antes de qualquer `__all__` se existir; senão no fim)

- [ ] **Step 1: Adicionar os modelos Pydantic**

No topo de `models.py` confirma que existem `from typing import List, Optional` e `from pydantic import BaseModel` (já existem — são usados em todo o ficheiro). Acrescenta no fim do ficheiro:

```python
# ===== Corpos Sociais (página pública /sobre) =====
# Resposta do endpoint público GET /api/governance/corpos-sociais.
# Expõe APENAS nome + foto dos titulares ativos — nunca email/id/role.

class CorpoSocialTitular(BaseModel):
    name: str
    photo_url: Optional[str] = None


class CorpoSocialCargo(BaseModel):
    key: str
    label: str
    ordem: int
    seats: int
    titulares: List[CorpoSocialTitular] = []


class CorpoSocialOrgao(BaseModel):
    id: str
    nome: str
    tipo: str
    cargos: List[CorpoSocialCargo] = []


class CorposSociaisResponse(BaseModel):
    orgaos: List[CorpoSocialOrgao] = []
```

- [ ] **Step 2: Verificar que importa**

Run: `cd backend && python -c "import models; print(models.CorposSociaisResponse.model_fields.keys())"`
Expected: `dict_keys(['orgaos'])`

- [ ] **Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat(sobre): modelos Pydantic de resposta dos corpos sociais"
```

---

## Task 2: Endpoint público dos Corpos Sociais (backend, TDD)

**Files:**
- Test: `backend/tests/test_governance_corpos_sociais.py` (Create)
- Modify: `backend/routes/governance.py`

- [ ] **Step 1: Escrever o teste a falhar**

Cria `backend/tests/test_governance_corpos_sociais.py`:

```python
"""Endpoint público GET /api/governance/corpos-sociais (spec-sobre §3)."""

from unittest.mock import MagicMock

import pytest

from routes import governance  # importa p/ o patch de db do conftest aterrar


class _Cursor:
    """Cursor mínimo compatível com o DAO: find(...).to_list(n)."""

    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, n):
        return self._docs[:n]


def _wire_holders(mock_db, holders_by_cargo):
    """Configura users.find p/ devolver titulares por cargo.

    Pedir a fixture `mock_db` garante que o conftest já fez o patch de
    `routes.governance.db` -> mock_db (senão `governance.db` seria o DAO real).
    """

    def _find(filtro, projection=None):
        cargo = filtro.get("cargo")
        return _Cursor(list(holders_by_cargo.get(cargo, [])))

    mock_db.users.find = MagicMock(side_effect=_find)


@pytest.mark.asyncio
async def test_estrutura_completa_mesmo_sem_titulares(mock_db):
    _wire_holders(mock_db, {})
    res = await governance.get_corpos_sociais()
    data = res.model_dump()

    ids = [o["id"] for o in data["orgaos"]]
    assert ids == ["assembleia_geral", "direcao", "conselho_fiscal"]
    # AG mostra-se como "Mesa da Assembleia Geral"
    assert data["orgaos"][0]["nome"] == "Mesa da Assembleia Geral"
    # todos os cargos presentes, todos "Vago" (titulares == [])
    for orgao in data["orgaos"]:
        assert orgao["cargos"], f"órgão {orgao['id']} sem cargos"
        for cargo in orgao["cargos"]:
            assert cargo["titulares"] == []


@pytest.mark.asyncio
async def test_titular_ativo_aparece_sem_campos_sensiveis(mock_db):
    _wire_holders(mock_db, {
        "dir_presidente": [
            {"name": "Ana Silva", "photo_url": "/uploads/avatars/ana.jpg"}
        ]
    })
    res = await governance.get_corpos_sociais()
    data = res.model_dump()

    direcao = next(o for o in data["orgaos"] if o["id"] == "direcao")
    pres = next(c for c in direcao["cargos"] if c["key"] == "dir_presidente")
    assert pres["titulares"] == [
        {"name": "Ana Silva", "photo_url": "/uploads/avatars/ana.jpg"}
    ]
    # nenhum campo sensível na serialização
    assert set(pres["titulares"][0].keys()) == {"name", "photo_url"}


@pytest.mark.asyncio
async def test_filtro_so_membros_ativos_estatutarios(mock_db):
    """O endpoint filtra por cargo+status+membro; o teste confirma o filtro."""
    capturado = {}

    def _find(filtro, projection=None):
        capturado.update(filtro)
        return _Cursor([])

    mock_db.users.find = MagicMock(side_effect=_find)
    await governance.get_corpos_sociais()

    assert capturado.get("status") == "ativo"
    assert "$or" in capturado  # _MEMBER_FILTER (account_type member/ausente)
    assert capturado["$or"] == [
        {"account_type": "member"},
        {"account_type": {"$exists": False}},
    ]


@pytest.mark.asyncio
async def test_cargos_ordenados_por_ordem(mock_db):
    _wire_holders(mock_db, {})
    res = await governance.get_corpos_sociais()
    data = res.model_dump()
    for orgao in data["orgaos"]:
        ordens = [c["ordem"] for c in orgao["cargos"]]
        assert ordens == sorted(ordens)
```

- [ ] **Step 2: Correr o teste e confirmar que falha**

Run: `cd backend && pytest tests/test_governance_corpos_sociais.py -v`
Expected: FAIL — `AttributeError: module 'routes.governance' has no attribute 'get_corpos_sociais'`

- [ ] **Step 3: Implementar o endpoint**

Em `backend/routes/governance.py`, substituir o conteúdo por (mantendo o endpoint `structure` existente):

```python
"""Rotas de governança estatutária (spec-governanca-estatutaria.md).

Fase 0: endpoint de estrutura. As fases seguintes (assembleias, eleições,
disciplina) vivem em módulos dedicados (`routes/assembleias.py`, etc.).
Corpos sociais públicos: spec-sobre §3.
"""

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import db
from governance import (
    ASSEMBLEIA_GERAL,
    CARGOS_CATALOG,
    CONSELHO_FISCAL,
    DIRECAO,
    ORGAOS,
    governance_structure,
)
from models import CorposSociaisResponse, User

router = APIRouter(prefix="/governance", tags=["governance"])

# Ordem e rótulos de exibição pública dos órgãos sociais (a Mesa da AG
# apresenta-se como "Mesa da Assembleia Geral").
_PUBLIC_ORGAO_ORDER = [ASSEMBLEIA_GERAL, DIRECAO, CONSELHO_FISCAL]
_ORGAO_DISPLAY = {
    ASSEMBLEIA_GERAL: "Mesa da Assembleia Geral",
    DIRECAO: "Direcção",
    CONSELHO_FISCAL: "Conselho Fiscal",
}
# Sócios reais: account_type "member" ou ausente (retro-compat). Igual ao
# filtro usado em routes/admin.py (_MEMBER_FILTER).
_MEMBER_FILTER = {"$or": [{"account_type": "member"}, {"account_type": {"$exists": False}}]}


@router.get("/structure")
async def get_governance_structure(current_user: User = Depends(get_current_user)):
    """Estrutura completa de governança: órgãos sociais, catálogo de cargos
    (key + label + órgão + vagas + role/privilégios default), categorias de
    membro, privilégios, roles, duração de mandato e slots eleitorais.

    Fonte única para o frontend (substitui o hard-code e os aliases
    deprecated /users/meta/cargos e /users/meta/privileges)."""
    return governance_structure()


@router.get("/corpos-sociais", response_model=CorposSociaisResponse)
async def get_corpos_sociais():
    """Titulares atuais dos órgãos sociais para a página pública /sobre.

    Público (sem autenticação). Devolve a estrutura estatutária completa dos
    3 órgãos a partir do catálogo, com `titulares: []` (→ "Vago" no frontend)
    quando o cargo não tem titular ativo. Expõe APENAS nome + foto."""
    orgaos_out = []
    for orgao_id in _PUBLIC_ORGAO_ORDER:
        cargos = sorted(
            (c for c in CARGOS_CATALOG if c["orgao"] == orgao_id),
            key=lambda c: c["ordem"],
        )
        cargos_out = []
        for cargo in cargos:
            holders = await db.users.find(
                {"cargo": cargo["key"], "status": "ativo", **_MEMBER_FILTER},
                {"_id": 0, "name": 1, "photo_url": 1},
            ).to_list(cargo["seats"] or 100)
            titulares = [
                {"name": h.get("name") or "—", "photo_url": h.get("photo_url")}
                for h in holders
            ]
            cargos_out.append(
                {
                    "key": cargo["key"],
                    "label": cargo["label"],
                    "ordem": cargo["ordem"],
                    "seats": cargo["seats"],
                    "titulares": titulares,
                }
            )
        orgaos_out.append(
            {
                "id": orgao_id,
                "nome": _ORGAO_DISPLAY[orgao_id],
                "tipo": ORGAOS[orgao_id]["tipo"],
                "cargos": cargos_out,
            }
        )
    return {"orgaos": orgaos_out}
```

- [ ] **Step 4: Correr o teste e confirmar que passa**

Run: `cd backend && pytest tests/test_governance_corpos_sociais.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Lint**

Run: `cd backend && ruff check routes/governance.py models.py && ruff format routes/governance.py models.py`
Expected: sem erros (format pode reescrever espaços)

- [ ] **Step 6: Commit**

```bash
git add backend/routes/governance.py backend/tests/test_governance_corpos_sociais.py
git commit -m "feat(sobre): endpoint público GET /governance/corpos-sociais"
```

---

## Task 3: queryKey + grupo de API no frontend

**Files:**
- Modify: `frontend/src/lib/queryClient.js:81-83`
- Modify: `frontend/src/utils/api.js:146-148`

- [ ] **Step 1: Acrescentar a queryKey**

Em `frontend/src/lib/queryClient.js`, no objeto `governance`, mudar de:

```javascript
  governance: {
    structure: () => ['governance', 'structure'],
  },
```

para:

```javascript
  governance: {
    structure: () => ['governance', 'structure'],
    corposSociais: () => ['governance', 'corpos-sociais'],
  },
```

- [ ] **Step 2: Acrescentar o método de API**

Em `frontend/src/utils/api.js`, mudar o grupo `governanceAPI` de:

```javascript
export const governanceAPI = {
  structure: () => api.get('/governance/structure'),
};
```

para:

```javascript
export const governanceAPI = {
  structure: () => api.get('/governance/structure'),
  // Público (sem auth) — titulares dos órgãos sociais p/ a página /sobre.
  getCorposSociais: () => api.get('/governance/corpos-sociais'),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/queryClient.js frontend/src/utils/api.js
git commit -m "feat(sobre): queryKey e API client dos corpos sociais"
```

---

## Task 4: Redesenhar `SobrePage.js` (copy factual + UI/UX + fetch dinâmico)

**Files:**
- Modify: `frontend/src/pages/public/SobrePage.js` (substituição integral)

Aplica veracidade (F1–F5), UI/UX (U1–U9) e copy factual. Substitui **todo** o ficheiro por:

- [ ] **Step 1: Substituir o ficheiro**

```jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageBanner } from '../../components/PageBanner';
import { Skeleton } from '../../components/ui/skeleton';
import { ASSOCIACAO_NOME_COMPLETO, fir, camadas } from '../../content/cta';
import { governanceAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import {
  Shield,
  Eye,
  Users,
  Star,
  Target,
  Award,
  Globe,
  UserCircle,
  Building,
  Scale,
  ArrowRight,
} from 'lucide-react';

// Iniciais p/ placeholder de avatar (titular sem foto).
const initials = (name) =>
  (name || '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase() || '—';

// Cartão de um titular (foto + nome) ou estado "Vago".
const TitularCard = ({ titular, cargoLabel, accent }) => {
  const vago = !titular;
  const ring = accent ? 'bg-carmesim/5' : 'bg-gray-50';
  return (
    <div className={`flex items-center gap-3 p-3 ${ring} rounded-lg`}>
      {vago ? (
        <span
          aria-hidden="true"
          className="flex w-10 h-10 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-500"
        >
          <UserCircle className="w-7 h-7" />
        </span>
      ) : titular.photo_url ? (
        <img
          src={titular.photo_url}
          alt={`Foto de ${titular.name} — ${cargoLabel}`}
          loading="lazy"
          className="w-10 h-10 shrink-0 rounded-full object-cover"
        />
      ) : (
        <span
          aria-hidden="true"
          className={`flex w-10 h-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
            accent ? 'bg-carmesim/10 text-carmesim' : 'bg-grafite/10 text-grafite'
          }`}
        >
          {initials(titular.name)}
        </span>
      )}
      <div className="min-w-0">
        <div className="font-semibold text-grafite truncate">{cargoLabel}</div>
        <div className="text-sm text-gray-600 truncate">
          {vago ? <span className="text-gray-500">Vago</span> : titular.name}
        </div>
      </div>
    </div>
  );
};

// Bloco de um órgão social (lista os seus cargos; vários titulares por cargo).
const OrgaoCard = ({ orgao, icon: Icon, accent }) => (
  <div
    className={`card-technical rounded-2xl p-8 animate-fade-up ${
      accent ? 'border-2 border-carmesim' : ''
    }`}
  >
    <div
      className={`w-16 h-16 ${
        accent ? 'bg-carmesim' : 'bg-grafite'
      } rounded-xl flex items-center justify-center mb-6`}
    >
      <Icon className="w-8 h-8 text-white" aria-hidden="true" />
    </div>
    <h3 className="font-sans font-bold text-2xl text-grafite mb-6">{orgao.nome}</h3>
    <div className="space-y-3">
      {orgao.cargos.map((cargo) => {
        if (!cargo.titulares.length) {
          return (
            <TitularCard
              key={cargo.key}
              titular={null}
              cargoLabel={cargo.label}
              accent={accent}
            />
          );
        }
        return cargo.titulares.map((t, i) => (
          <TitularCard
            key={`${cargo.key}-${i}`}
            titular={t}
            cargoLabel={cargo.label}
            accent={accent}
          />
        ));
      })}
    </div>
  </div>
);

const ORGAO_ICONS = {
  assembleia_geral: Building,
  direcao: Users,
  conselho_fiscal: Scale,
};

export const SobrePage = () => {
  const asa = camadas.find((c) => c.sigla === 'ASA');

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.governance.corposSociais(),
    queryFn: () => governanceAPI.getCorposSociais().then((r) => r.data),
    staleTime: 5 * 60 * 1000, // dado quase estático
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <PageBanner
        pageKey="sobre"
        badge="A Associação"
        title="Quem Somos"
        subtitle="A associação profissional dos controladores de tráfego aéreo de Cabo Verde"
      />

      {/* Introdução */}
      <section className="py-12 sm:py-20 lg:py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fade-up">
              <h2 className="font-sans font-bold text-4xl text-grafite mb-8">
                Unidos pela <span className="text-carmesim">Segurança Aérea</span>
              </h2>
              <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
                <p>
                  A{' '}
                  <strong className="text-grafite">{ASSOCIACAO_NOME_COMPLETO}</strong>{' '}
                  é a associação de representação profissional dos controladores
                  de tráfego aéreo no arquipélago. Reúne os profissionais que
                  asseguram a gestão de um dos espaços aéreos mais estratégicos
                  do Atlântico, atuando na valorização da carreira, na promoção
                  da excelência técnica e na cooperação com as autoridades
                  nacionais e os parceiros do setor.
                </p>
                <p>
                  Mais do que uma estrutura associativa, somos um{' '}
                  <span className="text-grafite font-semibold">
                    parceiro técnico
                  </span>{' '}
                  no desenvolvimento da aviação civil nacional.
                </p>
              </div>
            </div>

            <div className="relative animate-fade-up">
              <div className="bg-gradient-to-br from-grafite to-grafite/80 rounded-2xl p-8 text-white">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 bg-carmesim rounded-xl flex items-center justify-center">
                    <Globe className="w-8 h-8 text-white" aria-hidden="true" />
                  </div>
                  <div>
                    <div className="font-sans font-bold text-2xl">{fir.nome}</div>
                    <div className="text-white/70">{fir.baseLegal}</div>
                  </div>
                </div>
                <p className="text-white/80 leading-relaxed">
                  Os nossos profissionais atuam na {fir.nome}, uma das maiores
                  regiões de informação de voo do Atlântico, coordenando voos
                  entre a Europa, a África e as Américas. A prestação dos
                  serviços de tráfego aéreo é operada pela{' '}
                  {asa ? asa.nome : 'ASA'}.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Missão, Visão, Valores */}
      <section className="py-12 sm:py-20 lg:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-carmesim/10 text-carmesim rounded-full text-sm uppercase tracking-wider mb-6">
              Os Nossos Pilares
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite">
              Missão, Visão e Valores
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            <div className="card-technical rounded-2xl p-8 border-l-4 border-carmesim animate-fade-up">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-carmesim rounded-xl flex items-center justify-center">
                  <Target className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">
                  A Nossa Missão
                </h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                Representar e valorizar os controladores de tráfego aéreo,
                promovendo a <strong>segurança operacional</strong>, o{' '}
                <strong>desenvolvimento contínuo</strong> da profissão e o{' '}
                <strong>bem-estar</strong> dos associados.
              </p>
            </div>

            <div className="card-technical rounded-2xl p-8 border-l-4 border-grafite animate-fade-up">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 bg-grafite rounded-xl flex items-center justify-center">
                  <Eye className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="font-sans font-bold text-2xl text-grafite">
                  A Nossa Visão
                </h3>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                Ser uma associação de referência na representação da classe e na
                contribuição técnica para a{' '}
                <strong>segurança da navegação aérea no Atlântico</strong>.
              </p>
            </div>
          </div>

          {/* Valores — neutral-led, Carmesim só no valor-chave "Segurança" (U3) */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: Shield,
                title: 'Segurança',
                desc: 'O nosso compromisso inegociável.',
                color: 'bg-carmesim/10 text-carmesim',
              },
              {
                icon: Award,
                title: 'Excelência',
                desc: 'Rigor técnico em cada comunicação.',
                color: 'bg-grafite/10 text-grafite',
              },
              {
                icon: Users,
                title: 'União',
                desc: 'A força do coletivo acima do individual.',
                color: 'bg-grafite/10 text-grafite',
              },
              {
                icon: Star,
                title: 'Transparência',
                desc: 'Gestão clara e responsável.',
                color: 'bg-grafite/10 text-grafite',
              },
            ].map((value, index) => (
              <div
                key={index}
                className="card-technical rounded-xl p-6 text-center hover:shadow-lg transition-shadow animate-fade-up"
              >
                <div
                  className={`w-16 h-16 ${value.color} rounded-full flex items-center justify-center mx-auto mb-4`}
                >
                  <value.icon className="w-8 h-8" aria-hidden="true" />
                </div>
                <h4 className="font-sans font-bold text-xl text-grafite mb-2">
                  {value.title}
                </h4>
                <p className="text-gray-600">{value.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Corpos Sociais — dinâmico */}
      <section className="py-12 sm:py-20 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-grafite/5 text-grafite rounded-full text-sm uppercase tracking-wider mb-6">
              Gestão Atual
            </span>
            <h2 className="font-sans font-bold text-4xl text-grafite mb-4">
              Corpos Sociais
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Os órgãos sociais que dirigem e fiscalizam a associação
            </p>
          </div>

          {isLoading && (
            <div className="grid md:grid-cols-3 gap-8">
              {[0, 1, 2].map((i) => (
                <div key={i} className="card-technical rounded-2xl p-8">
                  <Skeleton className="w-16 h-16 rounded-xl mb-6" />
                  <Skeleton className="h-7 w-2/3 mb-6" />
                  <div className="space-y-3">
                    <Skeleton className="h-16 w-full rounded-lg" />
                    <Skeleton className="h-16 w-full rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && (
            <p className="text-center text-gray-600">
              Informação dos corpos sociais indisponível de momento.
            </p>
          )}

          {!isLoading && !isError && data && (
            <div className="grid md:grid-cols-3 gap-8">
              {data.orgaos.map((orgao) => (
                <OrgaoCard
                  key={orgao.id}
                  orgao={orgao}
                  icon={ORGAO_ICONS[orgao.id] || Building}
                  accent={orgao.id === 'direcao'}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="py-12 sm:py-20 lg:py-24 bg-grafite">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-sans font-bold text-4xl text-white mb-6">
            Quer saber mais sobre a nossa atuação?
          </h2>
          <p className="text-xl text-white/80 mb-10">
            Consulte os documentos de governança e os relatórios de gestão
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/transparencia"
              className="inline-flex items-center gap-2 bg-floresta text-white px-8 py-4 rounded-lg font-bold text-lg hover:bg-floresta-dark transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 ring-offset-2 ring-offset-grafite"
            >
              Ver Transparência
              <ArrowRight className="w-5 h-5" aria-hidden="true" />
            </Link>
            <Link
              to="/contactos"
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white border border-white/20 px-8 py-4 rounded-lg font-bold text-lg hover:bg-white/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 ring-offset-2 ring-offset-grafite"
            >
              Fale Connosco
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
```

- [ ] **Step 2: Confirmar que o componente `Skeleton` existe**

Run: `ls frontend/src/components/ui/skeleton.jsx frontend/src/components/ui/skeleton.js 2>/dev/null`
Expected: existe um deles. Se o import falhar no build, ajustar o caminho de `Skeleton`.

- [ ] **Step 3: Lint do frontend**

Run: `cd frontend && npx eslint src/pages/public/SobrePage.js --ext .js,.jsx --max-warnings=60`
Expected: sem erros (warnings ≤ limite)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/public/SobrePage.js
git commit -m "feat(sobre): redesign factual + corpos sociais dinâmicos (UI/UX)"
```

---

## Task 5: Garantir `prefers-reduced-motion` (U4)

**Files:**
- Verify/Modify: `frontend/src/index.css` (e/ou `frontend/src/App.css`)

- [ ] **Step 1: Verificar se já existe guard**

Run: `cd frontend && grep -rn "prefers-reduced-motion" src/`
Expected: idealmente já existe um bloco que desliga animações. Se aparecer, **não** alterar (Task concluída).

- [ ] **Step 2: Se NÃO existir, localizar a definição de `animate-fade-up`**

Run: `cd frontend && grep -rn "animate-fade-up\|fade-up\|@keyframes" src/index.css src/App.css`
Expected: encontrar onde a animação é definida.

- [ ] **Step 3: Se faltar, acrescentar o guard ao fim de `src/index.css`**

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 4: Commit (apenas se houve alteração)**

```bash
git add frontend/src/index.css
git commit -m "a11y(sobre): respeitar prefers-reduced-motion nas animações"
```

---

## Task 6: Verificação final (suíte + build)

- [ ] **Step 1: Testes backend relevantes**

Run: `cd backend && pytest tests/test_governance_corpos_sociais.py -v`
Expected: PASS

- [ ] **Step 2: Build do frontend**

Run: `cd frontend && yarn build`
Expected: build OK (sem erros de import/compilação)

- [ ] **Step 3: Revisão visual manual (checklist UI/UX §4 da spec)**

Verificar em 375/768/1024/1440px: sem scroll horizontal; "Vago" legível; avatares redondos; focus visível nos CTA; contraste ok. (Frontend já corre localmente — backend :8001, frontend :3000, login dev `dev@accta.cv`; a `/sobre` é pública.)

- [ ] **Step 4: Commit final / nada a fazer se já tudo commitado**

```bash
git status
```

---

## Notas de execução
- **Não** correr a suíte completa de backend à espera de verde — `test_smoke.py` e ficheiros `import requests` falham por ambiente (sem Postgres/servidor); isso é esperado. Corre só `test_governance_corpos_sociais.py`.
- Sem alterações destrutivas de schema, sem emails, sem CORS/JWT. Integração final: PR `feature/sobre-page-revisao → develop`.
