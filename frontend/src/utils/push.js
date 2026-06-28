// Web Push — subscrição/cancelamento no browser e sincronização com o backend.
// O Service Worker (public/sw.js) trata os eventos `push`/`notificationclick`.
import { pushAPI } from './api';

// Suporte real a Web Push (Android/Chrome, desktop; iOS 16.4+ só dentro do PWA).
export const isPushSupported = () =>
  typeof window !== 'undefined' &&
  'serviceWorker' in navigator &&
  'PushManager' in window &&
  'Notification' in window;

const isIos = () =>
  /iphone|ipad|ipod/i.test(navigator.userAgent || '') ||
  // iPadOS recente reporta-se como Mac com touch
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

const isStandalone = () =>
  window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true;

// iPhone fora do PWA: o push não funciona até "Adicionar à Tela de Início".
export const getIosNeedsInstall = () => isIos() && !isStandalone();

export const getPermission = () => (isPushSupported() ? Notification.permission : 'unsupported');

// VAPID public key (base64url) → Uint8Array para applicationServerKey.
const urlBase64ToUint8Array = (base64String) => {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = window.atob(base64);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) output[i] = raw.charCodeAt(i);
  return output;
};

const getRegistration = async () => {
  // index.js regista /sw.js em produção; garante que está pronto.
  if (!navigator.serviceWorker) return null;
  return navigator.serviceWorker.ready;
};

// Devolve a subscrição ativa deste browser, ou null.
export const getExistingSubscription = async () => {
  if (!isPushSupported()) return null;
  const reg = await getRegistration();
  if (!reg) return null;
  return reg.pushManager.getSubscription();
};

// Pede permissão (se preciso), subscreve e regista no backend. Lança em falha
// para o componente mostrar o toast adequado.
export const subscribeToPush = async () => {
  if (!isPushSupported()) throw new Error('Este dispositivo não suporta notificações push.');

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    throw new Error('Permissão de notificações negada.');
  }

  const reg = await getRegistration();
  if (!reg) throw new Error('Service worker indisponível.');

  const { data } = await pushAPI.getVapidKey();
  const applicationServerKey = urlBase64ToUint8Array(data.publicKey);

  let subscription = await reg.pushManager.getSubscription();
  if (!subscription) {
    subscription = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey,
    });
  }

  await pushAPI.subscribe(subscription.toJSON());
  return subscription;
};

// Cancela a subscrição local e remove-a no backend.
export const unsubscribeFromPush = async () => {
  const subscription = await getExistingSubscription();
  if (!subscription) return;
  const payload = subscription.toJSON();
  try {
    await subscription.unsubscribe();
  } finally {
    await pushAPI.unsubscribe(payload).catch(() => {});
  }
};
