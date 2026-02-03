import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { QrCode, CheckCircle, XCircle, Search } from 'lucide-react';
import { validatorAPI } from '../../utils/api';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const ValidadorPage = () => {
  const [qrHash, setQrHash] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleValidate = async (e) => {
    e.preventDefault();
    if (!qrHash.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await validatorAPI.validate(qrHash.trim());
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Carteira não encontrada');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-16 min-h-[70vh]">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="w-20 h-20 bg-primary rounded-2xl flex items-center justify-center mx-auto mb-6">
            <QrCode className="w-10 h-10 text-accent" />
          </div>
          <h1 className="font-outfit font-bold text-4xl md:text-5xl text-primary mb-4" data-testid="validator-title">
            Validador de Carteira
          </h1>
          <p className="text-lg text-slate-600">
            Insira o código QR para validar a carteira de sócio ACCTA
          </p>
        </motion.div>

        {/* Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-technical rounded-2xl p-8 mb-8"
        >
          <form onSubmit={handleValidate} className="space-y-6">
            <div>
              <label htmlFor="qr-hash" className="block font-mono text-xs uppercase tracking-widest text-slate-500 mb-2">
                Código QR
              </label>
              <input
                id="qr-hash"
                type="text"
                value={qrHash}
                onChange={(e) => setQrHash(e.target.value)}
                placeholder="Cole o código QR aqui"
                className="w-full px-4 py-3 border border-slate-200 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                data-testid="qr-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !qrHash.trim()}
              className="w-full bg-primary text-white hover:bg-primary/90 h-12 px-6 rounded-lg uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="validate-button"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Validar Carteira
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* Result */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card-technical rounded-2xl p-8 border-2 border-alert"
            data-testid="validation-error"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-alert/10 rounded-full flex items-center justify-center">
                <XCircle className="w-6 h-6 text-alert" />
              </div>
              <div>
                <h3 className="font-outfit font-semibold text-xl text-alert">Carteira Inválida</h3>
                <p className="text-slate-600">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card-technical rounded-2xl p-8 border-2 border-accent"
            data-testid="validation-success"
          >
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-accent" />
              </div>
              <div>
                <h3 className="font-outfit font-semibold text-xl text-primary">Carteira Válida</h3>
                <p className="text-slate-600">Esta carteira é autêntica</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="border-t border-slate-200 pt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-mono text-xs uppercase tracking-widest text-slate-500 mb-1">
                      Nome
                    </label>
                    <p className="font-manrope font-semibold text-primary" data-testid="validated-name">{result.name}</p>
                  </div>
                  <div>
                    <label className="block font-mono text-xs uppercase tracking-widest text-slate-500 mb-1">
                      Nº Sócio
                    </label>
                    <p className="font-mono font-semibold text-primary" data-testid="validated-member-id">{result.member_id || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block font-mono text-xs uppercase tracking-widest text-slate-500 mb-1">
                      Status
                    </label>
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wide ${
                        result.status === 'ativo'
                          ? 'bg-accent/10 text-accent'
                          : 'bg-alert/10 text-alert'
                      }`}
                      data-testid="validated-status"
                    >
                      {result.status}
                    </span>
                  </div>
                  {result.admission_date && (
                    <div>
                      <label className="block font-mono text-xs uppercase tracking-widest text-slate-500 mb-1">
                        Admissão
                      </label>
                      <p className="font-mono text-primary">
                        {format(new Date(result.admission_date), 'dd/MM/yyyy', { locale: ptBR })}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};
