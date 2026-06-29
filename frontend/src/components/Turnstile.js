import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';

// Widget Cloudflare Turnstile (anti-bot) para os formulários públicos.
// A Site Key é PÚBLICA por natureza (vai no HTML) — fica num env opcional com
// fallback para a key do projeto, para o widget funcionar sem rebuild/config.
const SITE_KEY = process.env.REACT_APP_TURNSTILE_SITE_KEY || '0x4AAAAAAADs8kZrozSpCdz7g';
const SCRIPT_ID = 'cf-turnstile-script';
const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';

/**
 * Renderiza o widget Turnstile e devolve o token via `onVerify(token)`.
 * O token é de uso único: chame `ref.current.reset()` após cada submissão
 * (sucesso ou erro) para obter um novo. Em erro/expiração devolve `''`.
 *
 * Renderiza sempre (há SITE_KEY por env ou fallback embutido): a desativação
 * graciosa é do lado do backend (no-op sem `TURNSTILE_SECRET`), pelo que o
 * widget produz sempre um token quando a verificação for ligada.
 */
export const Turnstile = forwardRef(function Turnstile({ onVerify, className = 'my-1' }, ref) {
  const containerRef = useRef(null);
  const widgetIdRef = useRef(null);
  // Guarda o callback numa ref para não re-correr o effect (nem stale closures).
  const onVerifyRef = useRef(onVerify);
  onVerifyRef.current = onVerify;

  useImperativeHandle(
    ref,
    () => ({
      reset() {
        if (window.turnstile && widgetIdRef.current !== null) {
          try {
            window.turnstile.reset(widgetIdRef.current);
          } catch {
            /* widget já removido — ignora */
          }
        }
      },
    }),
    []
  );

  useEffect(() => {
    // Injeta o script da API uma única vez (partilhado por todos os widgets).
    if (!document.getElementById(SCRIPT_ID)) {
      const s = document.createElement('script');
      s.id = SCRIPT_ID;
      s.src = SCRIPT_SRC;
      s.async = true;
      s.defer = true;
      document.head.appendChild(s);
    }

    let cancelled = false;
    const renderWidget = () => {
      if (cancelled || widgetIdRef.current !== null) return;
      if (window.turnstile && containerRef.current) {
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: SITE_KEY,
          callback: (token) => onVerifyRef.current?.(token),
          'error-callback': () => onVerifyRef.current?.(''),
          'expired-callback': () => onVerifyRef.current?.(''),
          'timeout-callback': () => onVerifyRef.current?.(''),
        });
      }
    };

    // Tenta já; se a API ainda não carregou, faz poll curto até estar pronta.
    renderWidget();
    const interval = setInterval(() => {
      if (window.turnstile) {
        renderWidget();
        clearInterval(interval);
      }
    }, 200);

    return () => {
      cancelled = true;
      clearInterval(interval);
      if (window.turnstile && widgetIdRef.current !== null) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch {
          /* ignora */
        }
        widgetIdRef.current = null;
      }
    };
  }, []);

  return <div ref={containerRef} className={className} />;
});
