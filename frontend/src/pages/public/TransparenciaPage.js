import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Users, TrendingUp, PieChart } from 'lucide-react';
import api from '../../utils/api';

export const TransparenciaPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      // Simulated public stats - in production would be from a public endpoint
      setStats({
        totalSocios: 150,
        sociosAtivos: 135,
        taxaAdimplencia: 90,
        receitaAnual: 810000,
        mediaQuota: 500,
      });
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="font-outfit font-bold text-5xl md:text-6xl text-primary mb-6" data-testid="transparency-title">
            Transparência Institucional
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            Conheça os números da ACCTA. Acreditamos na transparência total como pilar da confiança institucional.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card-technical rounded-xl p-8"
          >
            <div className="w-14 h-14 bg-primary rounded-lg flex items-center justify-center mb-4">
              <Users className="w-7 h-7 text-accent" />
            </div>
            <div className="font-mono text-4xl font-bold text-primary mb-2">{stats.totalSocios}</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Total de Sócios</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card-technical rounded-xl p-8"
          >
            <div className="w-14 h-14 bg-accent rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="w-7 h-7 text-primary" />
            </div>
            <div className="font-mono text-4xl font-bold text-accent mb-2">{stats.sociosAtivos}</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Sócios Ativos</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card-technical rounded-xl p-8"
          >
            <div className="w-14 h-14 bg-primary rounded-lg flex items-center justify-center mb-4">
              <PieChart className="w-7 h-7 text-accent" />
            </div>
            <div className="font-mono text-4xl font-bold text-primary mb-2">{stats.taxaAdimplencia}%</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Taxa de Adimplência</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card-technical rounded-xl p-8"
          >
            <div className="w-14 h-14 bg-accent rounded-lg flex items-center justify-center mb-4">
              <DollarSign className="w-7 h-7 text-primary" />
            </div>
            <div className="font-mono text-4xl font-bold text-accent mb-2">{(stats.receitaAnual / 1000).toFixed(0)}K</div>
            <div className="text-sm text-slate-500 uppercase tracking-wider">Receita Anual (CVE)</div>
          </motion.div>
        </div>

        {/* Info Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="card-technical rounded-xl p-8"
          >
            <h2 className="font-outfit font-semibold text-2xl text-primary mb-4">Sistema de Quotas</h2>
            <p className="text-slate-600 mb-4">
              As quotas mensais são descontadas automaticamente em folha de pagamento dos associados, 
              garantindo regularidade e sustentabilidade financeira da associação.
            </p>
            <div className="bg-accent/5 rounded-lg p-4 border border-accent/20">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Quota Mensal:</span>
                <span className="font-mono font-bold text-primary">{stats.mediaQuota} CVE</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="card-technical rounded-xl p-8"
          >
            <h2 className="font-outfit font-semibold text-2xl text-primary mb-4">Destinação dos Recursos</h2>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-accent rounded-full" />
                <span className="text-slate-600">Representação institucional e advocacia</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-accent rounded-full" />
                <span className="text-slate-600">Formação e desenvolvimento profissional</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-accent rounded-full" />
                <span className="text-slate-600">Clube de benefícios para associados</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-accent rounded-full" />
                <span className="text-slate-600">Custos administrativos e operacionais</span>
              </div>
            </div>
          </motion.div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="text-center bg-primary rounded-2xl p-12"
        >
          <h2 className="font-outfit font-semibold text-3xl text-white mb-4">
            Documentos Oficiais
          </h2>
          <p className="text-white/80 mb-6 max-w-2xl mx-auto">
            Acesse nossos estatutos, atas de assembleia e balancetes financeiros completos
          </p>
          <a
            href="/login"
            className="inline-flex items-center gap-2 bg-accent text-primary hover:bg-accent/90 h-12 px-8 rounded-lg font-bold transition-all"
          >
            Acessar Área Reservada
          </a>
        </motion.div>
      </div>
    </div>
  );
};
