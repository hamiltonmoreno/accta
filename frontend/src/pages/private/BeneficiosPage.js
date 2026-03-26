import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { benefitsAPI } from '../../utils/api';
import { Gift, MapPin, Percent } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export const BeneficiosPage = () => {
  const { user, isAtivo } = useAuth();
  const [benefits, setBenefits] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBenefits();
  }, []);

  const loadBenefits = async () => {
    try {
      const response = await benefitsAPI.getAll();
      setBenefits(response.data);
    } catch (error) {
      console.error('Erro ao carregar benefícios:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-sans font-bold text-4xl text-grafite mb-2" data-testid="benefits-title">
          Clube de Benefícios
        </h1>
        <p className="text-gray-600">Descontos exclusivos para sócios ACCTA em parceiros selecionados</p>
      </div>

      {/* Status Alert */}
      {!isAtivo && (
        <div className="card-technical rounded-xl p-6 border-2 border-alert" data-testid="benefits-restricted">
          <div className="flex items-start gap-4">
            <Gift className="w-6 h-6 text-alert flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-sans font-semibold text-lg text-alert mb-2">Benefícios Restritos</h3>
              <p className="text-gray-600">
                Apenas sócios com status ativo têm acesso ao clube de benefícios. Por favor, regularize sua situação.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Card */}
      {isAtivo && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-technical rounded-xl p-6 bg-carmesim/5 border-accent/20"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center flex-shrink-0">
              <Gift className="w-6 h-6 text-grafite" />
            </div>
            <div>
              <h3 className="font-sans font-semibold text-lg text-grafite mb-2">Como Usar</h3>
              <p className="text-gray-600 mb-3">
                Apresente sua carteira digital nos estabelecimentos parceiros para validar seu status de sócio e aproveitar os descontos.
              </p>
              <p className="text-sm text-gray-500">
                Todos os descontos são válidos mediante apresentação do QR Code da carteira digital.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Benefits Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : benefits.length === 0 ? (
        <div className="card-technical rounded-xl p-12 text-center" data-testid="no-benefits">
          <p className="text-gray-500">Nenhum benefício disponível no momento</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {benefits.map((benefit, index) => (
            <motion.div
              key={benefit.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card-technical rounded-xl overflow-hidden hover:shadow-xl transition-shadow"
              data-testid={`benefit-${benefit.id}`}
            >
              {benefit.logo_url && (
                <div className="h-48 bg-gray-100 flex items-center justify-center p-6">
                  <img src={benefit.logo_url} alt={benefit.name} className="max-h-full max-w-full object-contain" />
                </div>
              )}
              
              <div className="p-6">
                <h3 className="font-sans font-semibold text-2xl text-grafite mb-3">{benefit.name}</h3>
                <p className="text-gray-600 mb-4 line-clamp-3">{benefit.description}</p>
                
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-2">
                    <Percent className="w-5 h-5 text-carmesim" />
                    <span className="font-mono font-bold text-2xl text-carmesim">{benefit.discount_percent}%</span>
                  </div>
                  <div className="text-xs font-mono text-gray-500 uppercase">
                    {benefit.validation_count} usos
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};
