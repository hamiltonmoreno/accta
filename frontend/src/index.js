import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Service Worker (PWA da carteira) — SÓ em produção.
// Em dev o bundle é sempre /static/js/bundle.js (sem content-hash), e o sw.js
// serve JS/CSS cache-first → a app fica presa numa build antiga em cache. Por
// isso, em dev não registamos e ainda desregistamos qualquer SW já instalado
// (limpa máquinas que abriram a app antes desta correção).
if ('serviceWorker' in navigator) {
  if (process.env.NODE_ENV === 'production') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // SW registration failed silently
      });
    });
  } else {
    navigator.serviceWorker
      .getRegistrations()
      .then((regs) => regs.forEach((r) => r.unregister()))
      .catch(() => {});
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
