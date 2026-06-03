"""Regras puras de co-aprovação / dupla assinatura (Art. 54; spec-controlos §4.1).

Sem acesso à base de dados — fonte única da regra estatutária, partilhada pela
rota `routes/atos.py` e pelos testes. A classificação de órgão/cargo deriva
SEMPRE da key canónica do cargo via `permissions` (que delega em `governance`),
nunca de campos denormalizados.

Resumo da regra:
- Acto **vinculativo**: ≥2 assinaturas de membros da Direcção, uma delas o Presidente.
- Acto de **pagamento** (vincula + sai dinheiro): o mesmo + a assinatura do Tesoureiro.
- O Presidente conta também como 1 dos membros da Direcção.
- Qualquer decisão "rejeitado" fecha o acto como rejeitado.
"""

from __future__ import annotations

from permissions import is_direcao, is_presidente, is_tesoureiro

# Requisitos por tipo de acto (default estatutário, §12.3). `min_direcao` conta
# assinaturas APROVADAS de membros da Direcção (o Presidente inclui-se).
_REQUISITOS = {
    "vinculativo": {"min_direcao": 2, "exige_presidente": True, "exige_tesoureiro": False},
    "pagamento": {"min_direcao": 2, "exige_presidente": True, "exige_tesoureiro": True},
}


def requisitos_for_tipo(tipo: str) -> dict:
    """Snapshot dos requisitos para o tipo de acto. Devolve uma cópia nova
    (o chamador congela-a no documento, não partilha o dict do módulo)."""
    return dict(_REQUISITOS.get(tipo, _REQUISITOS["vinculativo"]))


def _cargo_doc(assinatura: dict) -> dict:
    """Adapta uma assinatura ao mínimo que os helpers de `permissions` esperam."""
    return {"cargo": assinatura.get("cargo")}


def evaluate_status(assinaturas: list[dict], requisitos: dict) -> str:
    """Apura o estado de um acto a partir das assinaturas e dos requisitos.

    Devolve "rejeitado" | "aprovado" | "pendente". Não muta entradas.
    """
    if any(a.get("decisao") == "rejeitado" for a in assinaturas):
        return "rejeitado"

    aprovados = [a for a in assinaturas if a.get("decisao") == "aprovado"]
    n_direcao = sum(1 for a in aprovados if is_direcao(_cargo_doc(a)))
    if n_direcao < requisitos.get("min_direcao", 0):
        return "pendente"
    if requisitos.get("exige_presidente") and not any(is_presidente(_cargo_doc(a)) for a in aprovados):
        return "pendente"
    if requisitos.get("exige_tesoureiro") and not any(is_tesoureiro(_cargo_doc(a)) for a in aprovados):
        return "pendente"
    return "aprovado"
