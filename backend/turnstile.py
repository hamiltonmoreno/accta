"""Verificação Cloudflare Turnstile (anti-bot) para formulários públicos.

Complementa as defesas já existentes (rate-limit, lockout, honeypot): bloqueia
o bot antes de chegar a essas camadas. Aplica-se aos formulários sensíveis —
login, registo, recuperação de palavra-passe e contacto.

**Degrada graciosamente** (mesma filosofia do Web Push sem VAPID): sem a env
`TURNSTILE_SECRET` configurada, a verificação é um *no-op* e os formulários
funcionam como hoje. Uma vez configurada a secret no backend, a verificação
liga-se automaticamente — sem necessidade de alterar o frontend. Isto evita
partir o login de todos no momento do deploy (a secret só é definida depois).

Quando ligada, a validação é fail-closed: 403 se o token vier ausente/inválido,
502 se a própria Cloudflare estiver indisponível. Como a site key é pública,
validamos ainda o `hostname` devolvido pela Cloudflare contra o nosso domínio
(`FRONTEND_URL`) — defesa-em-profundidade contra tokens resolvidos noutro
domínio que reutilize a mesma site key.
"""

import os
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, Request

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def turnstile_enabled() -> bool:
    """True só quando a secret está configurada. Lê o env em runtime (não no
    import) para permitir ligar a feature sem reimportar o módulo e simplificar
    os testes."""
    return bool(os.environ.get("TURNSTILE_SECRET"))


def _norm_host(host: str | None) -> str | None:
    """Normaliza um hostname para comparação (minúsculas, sem `www.`)."""
    if not host:
        return None
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def _expected_hostname() -> str | None:
    """Domínio onde o desafio DEVE ter sido resolvido, derivado de `FRONTEND_URL`.
    None se `FRONTEND_URL` não estiver definido — aí não há por onde comparar e a
    validação de hostname é ignorada (o check de `success` mantém-se)."""
    raw = os.environ.get("FRONTEND_URL", "")
    return _norm_host(urlparse(raw).hostname) if raw else None


async def verify_turnstile(token: str, request: Request) -> None:
    """Valida o token Turnstile submetido com o formulário.

    No-op se a feature estiver desligada (sem `TURNSTILE_SECRET`). Quando ligada:
    - 403 se o token vier ausente, a Cloudflare o rejeitar (`success: false`), a
      resposta não for um objeto, ou o `hostname` não bater com `FRONTEND_URL`;
    - 502 se não for possível contactar/parsear a resposta da Cloudflare.
    """
    secret = os.environ.get("TURNSTILE_SECRET")
    if not secret:
        return  # feature desligada — não bloqueia os formulários

    if not token:
        raise HTTPException(status_code=403, detail="Confirme que não é um robô.")

    # IP real do visitante (atrás do Cloudflare + nginx-proxy-manager). Se o
    # header não vier, cai para o client.host; nunca enviamos um valor vazio.
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else None)

    payload = {"secret": secret, "response": token}
    if ip:
        payload["remoteip"] = ip

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(VERIFY_URL, data=payload)
        outcome = resp.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=502, detail="Falha ao validar a verificação anti-bot. Tente novamente.")

    # `isinstance` protege contra JSON válido mas não-objeto (null/lista) numa
    # falha de infra da Cloudflare: nunca deixa passar e devolve 403 em vez de
    # rebentar com 500 ao chamar `.get` num não-dict.
    if not isinstance(outcome, dict) or not outcome.get("success"):
        raise HTTPException(status_code=403, detail="Verificação anti-bot falhou. Tente novamente.")

    # Defesa-em-profundidade: a site key é pública, logo um atacante poderia
    # resolver o desafio noutro domínio com a mesma key e reenviar o token. A
    # Cloudflare devolve o `hostname` onde foi resolvido — exigimo-lo igual ao
    # nosso (FRONTEND_URL), independentemente da allowlist do painel.
    expected = _expected_hostname()
    if expected and _norm_host(outcome.get("hostname")) != expected:
        raise HTTPException(status_code=403, detail="Verificação anti-bot inválida.")
