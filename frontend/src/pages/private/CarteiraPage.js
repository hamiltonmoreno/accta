import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import QRCode from 'react-qr-code';
import { CreditCard, Download, Shield, Wifi, WifiOff, Smartphone, Share2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';

const OfflineBanner = ({ isOnline }) => {
  if (isOnline) return null;
  return (
    <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-center gap-3 animate-fade-up"
      data-testid="offline-banner">
      <WifiOff className="w-5 h-5 text-orange-600 flex-shrink-0" />
      <div>
        <p className="text-sm font-semibold text-orange-800">Modo Offline</p>
        <p className="text-xs text-orange-600">A exibir dados guardados localmente. QR Code disponivel.</p>
      </div>
    </div>
  );
};

const InstallPrompt = ({ deferredPrompt, onInstall }) => {
  if (!deferredPrompt) return null;
  return (
    <div className="card-technical rounded-xl p-5 border-2 border-dashed border-carmesim/30 bg-carmesim/5 animate-fade-up"
      data-testid="install-prompt">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-carmesim/10 rounded-xl flex items-center justify-center">
          <Smartphone className="w-6 h-6 text-carmesim" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-grafite text-sm">Instalar Carteira Digital</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Adicione ao ecra inicial para acesso rapido, mesmo sem internet
          </p>
        </div>
        <button
          onClick={onInstall}
          className="bg-carmesim text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-carmesim-dark transition-colors"
          data-testid="install-pwa-btn"
        >
          Instalar
        </button>
      </div>
    </div>
  );
};

export const CarteiraPage = () => {
  const { user } = useAuth();
  const [flipped, setFlipped] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [cachedUser, setCachedUser] = useState(null);

  const isActive = user?.status === 'ativo';
  const displayUser = user || cachedUser;

  // Cache user data for offline use
  useEffect(() => {
    if (user) {
      localStorage.setItem('accta_wallet_cache', JSON.stringify({
        name: user.name,
        member_id: user.member_id,
        status: user.status,
        qr_code_hash: user.qr_code_hash,
        admission_date: user.admission_date,
        role: user.role,
        license_number: user.license_number,
      }));

      // Also send to service worker
      if (navigator.serviceWorker?.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'CACHE_WALLET_DATA',
          payload: user,
        });
      }
    }
  }, [user]);

  // Load cached data when offline
  useEffect(() => {
    if (!user) {
      const cached = localStorage.getItem('accta_wallet_cache');
      if (cached) {
        try {
          setCachedUser(JSON.parse(cached));
        } catch (e) { /* ignore */ }
      }
    }
  }, [user]);

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // PWA install prompt
  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      toast.success('App instalada com sucesso!');
    }
    setDeferredPrompt(null);
  };

  const handleDownloadQR = useCallback(() => {
    const svgElement = document.getElementById('wallet-qr-svg');
    if (!svgElement) return;

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = 300;
      canvas.height = 350;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw QR code centered
      ctx.drawImage(img, 50, 20, 200, 200);

      // Add text
      ctx.fillStyle = '#3A3A3A';
      ctx.font = 'bold 16px Open Sans, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('ACCTA - Cabo Verde', 150, 250);
      ctx.font = '14px Open Sans, sans-serif';
      ctx.fillText(displayUser?.name || '', 150, 275);
      ctx.font = '12px JetBrains Mono, monospace';
      ctx.fillStyle = '#666';
      ctx.fillText(`Socio: ${displayUser?.member_id || 'N/A'}`, 150, 300);
      ctx.fillText(`Status: ${displayUser?.status || 'N/A'}`, 150, 320);

      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `carteira-accta-${displayUser?.member_id || 'socio'}.png`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('QR Code guardado com sucesso!');
      });
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  }, [displayUser]);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Carteira Digital ACCTA',
          text: `${displayUser?.name} - Socio ACCTA Cabo Verde`,
          url: window.location.href,
        });
      } catch (err) {
        // User cancelled share
      }
    } else {
      navigator.clipboard?.writeText(window.location.href);
      toast.success('Link copiado!');
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="font-sans font-bold text-4xl text-grafite mb-2" data-testid="wallet-title">
          Carteira Digital
        </h1>
        <div className="flex items-center justify-center gap-2 text-gray-500">
          {isOnline ? (
            <Wifi className="w-4 h-4 text-green-500" />
          ) : (
            <WifiOff className="w-4 h-4 text-orange-500" />
          )}
          <p className="text-sm">
            Sua identificacao digital de socio ACCTA
          </p>
        </div>
      </div>

      <OfflineBanner isOnline={isOnline} />
      <InstallPrompt deferredPrompt={deferredPrompt} onInstall={handleInstall} />

      {/* Digital Wallet Card */}
      <div className="relative animate-fade-up"
        style={{ perspective: '1000px' }}>
        <div
          className={`relative w-full cursor-pointer`}
          style={{ transformStyle: 'preserve-3d', transition: 'transform 0.7s', transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
          onClick={() => setFlipped(!flipped)}
          data-testid="wallet-card"
        >
          {/* Front */}
          <div
            className="relative w-full rounded-xl overflow-hidden shadow-2xl"
            style={{ backfaceVisibility: 'hidden', aspectRatio: '1.586' }}
          >
            <div
              className={`absolute inset-0 ${
                isActive
                  ? 'bg-gradient-to-br from-grafite via-grafite to-grafite-dark'
                  : 'bg-gradient-to-br from-slate-400 to-slate-600 grayscale'
              }`}
            >
              {/* Holographic overlay for active */}
              {isActive && (
                <div className="absolute inset-0 opacity-10 bg-gradient-to-tr from-carmesim via-transparent to-transparent" />
              )}

              {/* Content */}
              <div className="relative h-full p-8 flex flex-col justify-between text-white">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-sans font-bold text-2xl mb-1">ACCTA</div>
                    <div className="font-mono text-xs uppercase tracking-widest opacity-80">Cabo Verde</div>
                  </div>
                  <CreditCard className="w-8 h-8 opacity-80" />
                </div>

                {/* Member Info */}
                <div>
                  <div className="font-mono text-xs uppercase tracking-widest opacity-80 mb-2">Socio</div>
                  <div className="font-sans font-bold text-3xl mb-4">{displayUser?.name}</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="font-mono text-xs uppercase tracking-widest opacity-80 mb-1">N Socio</div>
                      <div className="font-mono font-bold text-lg">{displayUser?.member_id || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="font-mono text-xs uppercase tracking-widest opacity-80 mb-1">Status</div>
                      <div
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wide ${
                          isActive ? 'bg-carmesim text-white' : 'bg-white/20 text-white'
                        }`}
                        data-testid="wallet-status"
                      >
                        {displayUser?.status}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Back */}
          <div
            className="absolute top-0 left-0 w-full rounded-xl overflow-hidden shadow-2xl bg-white"
            style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', aspectRatio: '1.586' }}
          >
            <div className="h-full p-8 flex flex-col items-center justify-center">
              <div className="text-center mb-4">
                <div className="font-sans font-bold text-xl text-grafite mb-1">Codigo de Validacao</div>
                <div className="font-mono text-xs text-gray-500">Apresente este QR Code para validacao</div>
              </div>

              {displayUser?.qr_code_hash && (
                <div className="p-4 bg-white rounded-xl shadow-inner border border-gray-200" data-testid="qr-code">
                  <QRCode id="wallet-qr-svg" value={displayUser.qr_code_hash} size={160} />
                </div>
              )}

              <div className="mt-4 text-center">
                <div className="font-mono text-xs text-gray-400 uppercase tracking-widest">ACCTA - Cabo Verde</div>
                {displayUser?.admission_date && (
                  <div className="font-mono text-xs text-gray-400 mt-1">
                    Socio desde {format(new Date(displayUser.admission_date), 'MMMM yyyy', { locale: ptBR })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="text-center animate-fade-up">
        <p className="text-sm text-gray-500">
          Clique no cartao para ver o QR Code
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-center">
        <button
          onClick={handleDownloadQR}
          className="flex items-center gap-2 px-5 py-2.5 bg-grafite text-white rounded-lg text-sm font-semibold hover:bg-grafite/90 transition-colors"
          data-testid="download-qr-btn"
        >
          <Download className="w-4 h-4" />
          Guardar QR Code
        </button>
        <button
          onClick={handleShare}
          className="flex items-center gap-2 px-5 py-2.5 border border-gray-200 text-grafite rounded-lg text-sm font-semibold hover:bg-gray-50 transition-colors"
          data-testid="share-wallet-btn"
        >
          <Share2 className="w-4 h-4" />
          Partilhar
        </button>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-technical rounded-xl p-5 animate-fade-up">
          <div className="w-10 h-10 bg-grafite rounded-lg flex items-center justify-center mb-3">
            <Shield className="w-5 h-5 text-carmesim" />
          </div>
          <h3 className="font-sans font-semibold text-grafite mb-1">Validacao Segura</h3>
          <p className="text-sm text-gray-600">
            QR Code criptografado e unico
          </p>
        </div>

        <div className="card-technical rounded-xl p-5 animate-fade-up">
          <div className="w-10 h-10 bg-grafite rounded-lg flex items-center justify-center mb-3">
            <WifiOff className="w-5 h-5 text-carmesim" />
          </div>
          <h3 className="font-sans font-semibold text-grafite mb-1">Acesso Offline</h3>
          <p className="text-sm text-gray-600">
            Funciona sem ligacao a internet
          </p>
        </div>

        <div className="card-technical rounded-xl p-5 animate-fade-up">
          <div className="w-10 h-10 bg-grafite rounded-lg flex items-center justify-center mb-3">
            <Smartphone className="w-5 h-5 text-carmesim" />
          </div>
          <h3 className="font-sans font-semibold text-grafite mb-1">Instalar App</h3>
          <p className="text-sm text-gray-600">
            Adicione ao ecra inicial
          </p>
        </div>
      </div>
    </div>
  );
};
