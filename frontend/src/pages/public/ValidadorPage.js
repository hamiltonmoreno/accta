import React, { useState } from 'react';
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
        <div className="text-center mb-12 animate-fade-up">
          <div className="w-20 h-20 bg-grafite rounded-2xl flex items-center justify-center mx-auto mb-6">
            <QrCode className="w-10 h-10 text-white" />
          </div>
          <h1 className="font-sans font-bold text-4xl md:text-5xl text-grafite mb-4" data-testid="validator-title">
            Validador de Carteira
          </h1>
          <p className="text-lg text-gray-600">
            Insira o código QR para validar a carteira de sócio ACCTA
          </p>
        </div>

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
          <div className="card-technical rounded-2xl p-8 border-2 border-alert animate-fade-up"
            data-testid="validation-error">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-alert/10 rounded-full flex items-center justify-center">
                <XCircle className="w-6 h-6 text-alert" />
              </div>
              <div>
                <h3 className="font-sans font-semibold text-xl text-[#B91C1C]">Carteira Inválida</h3>
                <p className="text-gray-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="card-technical rounded-2xl p-8 border-2 border-carmesim animate-fade-up"
            data-testid="validation-success">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-carmesim/10 rounded-full flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-carmesim" />
              </div>
              <div>
                <h3 className="font-sans font-semibold text-xl text-grafite">Carteira Válida</h3>
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
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs uppercase tracking-wide ${
                        result.status === 'ativo'
                          ? 'bg-carmesim/10 text-carmesim'
                          : 'bg-alert/10 text-[#B91C1C]'
                      }`}
                      data-testid="validated-status"
                    >
                      {result.status}
                    </span>
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
  );
};
