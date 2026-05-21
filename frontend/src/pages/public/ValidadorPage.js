import React, { useState } from 'react';
import { QrCode, Search } from 'lucide-react';
import { validatorAPI } from '../../utils/api';
import { PageBanner } from '../../components/PageBanner';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  WALLET_VALIDATION_CONFIG,
  USER_STATUS_CONFIG, USER_STATUS_FALLBACK, getStatusConfig,
} from '../../lib/statusConfig';

const VALID = WALLET_VALIDATION_CONFIG.valida;
const INVALID = WALLET_VALIDATION_CONFIG.invalida;

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
    <>
      <PageBanner
        pageKey="validador"
        badge="Validação"
        icon={QrCode}
        title="Validador de Carteira"
        subtitle="Insira o código QR para validar a carteira de sócio ACCTA"
      />
      <div className="py-16 min-h-[70vh]">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Form */}
        <div className="card-technical rounded-2xl p-8 mb-8 animate-fade-up">
          <form onSubmit={handleValidate} className="space-y-6">
            <div>
              <label htmlFor="qr-hash" className="block text-xs uppercase tracking-widest text-gray-500 mb-2">
                Código QR
              </label>
              <input
                id="qr-hash"
                type="text"
                value={qrHash}
                onChange={(e) => setQrHash(e.target.value)}
                placeholder="Cole o código QR aqui"
                className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 transition-all"
                data-testid="qr-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !qrHash.trim()}
              className="w-full bg-grafite text-white hover:bg-grafite/90 h-12 px-6 rounded-lg font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
        </div>

        {/* Result */}
        {error && (
          <div className="card-technical rounded-2xl p-8 border-2 border-[#B91C1C] animate-fade-up"
            data-testid="validation-error">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-[#FEF2F2] rounded-full flex items-center justify-center">
                <INVALID.icon className="w-6 h-6 text-[#B91C1C]" aria-hidden="true" />
              </div>
              <div>
                <h3 className="font-sans font-semibold text-xl text-[#B91C1C]">{INVALID.label}</h3>
                <p className="text-gray-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="card-technical rounded-2xl p-8 border-2 border-[#15803D] animate-fade-up"
            data-testid="validation-success">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-[#F0FDF4] rounded-full flex items-center justify-center">
                <VALID.icon className="w-6 h-6 text-[#15803D]" aria-hidden="true" />
              </div>
              <div>
                <h3 className="font-sans font-semibold text-xl text-[#15803D]">{VALID.label}</h3>
                <p className="text-gray-600">Esta carteira é autêntica</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="border-t border-gray-200 pt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1">
                      Nome
                    </label>
                    <p className="font-sans font-semibold text-grafite" data-testid="validated-name">{result.name}</p>
                  </div>
                  <div>
                    <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1">
                      Nº Sócio
                    </label>
                    <p className="font-semibold text-grafite" data-testid="validated-member-id">{result.member_id || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1">
                      Status
                    </label>
                    {(() => {
                      const sc = getStatusConfig(USER_STATUS_CONFIG, result.status, USER_STATUS_FALLBACK);
                      const ScIcon = sc.icon;
                      return (
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs uppercase tracking-wide ${sc.className}`}
                          data-testid="validated-status"
                        >
                          <ScIcon className="w-3 h-3" aria-hidden="true" />
                          {result.status}
                        </span>
                      );
                    })()}
                  </div>
                  {result.admission_date && (
                    <div>
                      <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1">
                        Admissão
                      </label>
                      <p className="text-grafite">
                        {format(new Date(result.admission_date), 'dd/MM/yyyy', { locale: ptBR })}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    </>
  );
};
