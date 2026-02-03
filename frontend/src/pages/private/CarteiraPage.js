import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { QRCodeSVG } from 'react-qr-code';
import { CreditCard, Download, Shield } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const CarteiraPage = () => {
  const { user } = useAuth();
  const [flipped, setFlipped] = useState(false);

  const isActive = user?.status === 'ativo';

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="font-outfit font-bold text-4xl text-primary mb-4" data-testid="wallet-title">
          Carteira Digital
        </h1>
        <p className="text-slate-600">
          Sua identificação digital de sócio ACCTA. Use o QR Code para validação e benefícios.
        </p>
      </div>

      {/* Digital Wallet Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
        style={{ perspective: '1000px' }}
      >
        <div
          className={`relative w-full transition-transform duration-700 cursor-pointer ${
            flipped ? '[transform:rotateY(180deg)]' : ''
          }`}
          style={{ transformStyle: 'preserve-3d' }}
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
                  ? 'bg-gradient-to-br from-primary via-primary to-[#0A3A5A]'
                  : 'bg-gradient-to-br from-slate-400 to-slate-600 grayscale'
              }`}
            >
              {/* Holographic overlay for active */}
              {isActive && (
                <div className="absolute inset-0 opacity-20 bg-gradient-to-tr from-accent via-transparent to-transparent" />
              )}

              {/* Content */}
              <div className="relative h-full p-8 flex flex-col justify-between text-white">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-outfit font-bold text-2xl mb-1">ACCTA</div>
                    <div className="font-mono text-xs uppercase tracking-widest opacity-80">Cabo Verde</div>
                  </div>
                  <CreditCard className="w-8 h-8 opacity-80" />
                </div>

                {/* Member Info */}
                <div>
                  <div className="font-mono text-xs uppercase tracking-widest opacity-80 mb-2">Sócio</div>
                  <div className="font-outfit font-bold text-3xl mb-4">{user?.name}</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="font-mono text-xs uppercase tracking-widest opacity-80 mb-1">Nº Sócio</div>
                      <div className="font-mono font-bold text-lg">{user?.member_id || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="font-mono text-xs uppercase tracking-widest opacity-80 mb-1">Status</div>
                      <div
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wide ${
                          isActive ? 'bg-accent text-primary' : 'bg-white/20 text-white'
                        }`}
                        data-testid="wallet-status"
                      >
                        {user?.status}
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
              <div className="text-center mb-6">
                <div className="font-outfit font-bold text-2xl text-primary mb-2">Código de Validação</div>
                <div className="font-mono text-sm text-slate-500">Apresente este QR Code para validação</div>
              </div>

              {user?.qr_code_hash && (
                <div className="p-6 bg-white rounded-xl shadow-inner border border-slate-200" data-testid="qr-code">
                  <QRCodeSVG value={user.qr_code_hash} size={200} />
                </div>
              )}

              <div className="mt-6 text-center">
                <div className="font-mono text-xs text-slate-400 uppercase tracking-widest">ACCTA - Cabo Verde</div>
                {user?.admission_date && (
                  <div className="font-mono text-xs text-slate-400 mt-1">
                    Sócio desde {format(new Date(user.admission_date), 'MMMM yyyy', { locale: ptBR })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Instructions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-center"
      >
        <p className="text-sm text-slate-500 mb-4">
          Clique no cartão para ver o QR Code
        </p>
      </motion.div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-accent" />
          </div>
          <h3 className="font-outfit font-semibold text-xl text-primary mb-2">Validação Segura</h3>
          <p className="text-slate-600">
            Seu QR Code é criptografado e único, garantindo autenticação segura
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card-technical rounded-xl p-6"
        >
          <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
            <Download className="w-6 h-6 text-accent" />
          </div>
          <h3 className="font-outfit font-semibold text-xl text-primary mb-2">Acesso Offline</h3>
          <p className="text-slate-600">
            Capture uma imagem do QR Code para usar sem conexão à internet
          </p>
        </motion.div>
      </div>
    </div>
  );
};
