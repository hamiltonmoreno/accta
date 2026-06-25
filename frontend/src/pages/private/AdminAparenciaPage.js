import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Paintbrush } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { AdminMarcaPage } from './AdminMarcaPage';
import { AdminBannersPage } from './AdminBannersPage';

/**
 * Aparência do Site (spec-padronizacao-banners + spec-gestao-logo-marca) —
 * consolida a gestão do logótipo e dos banners numa só página com tabs.
 * Reutiliza os geridores existentes em modo `embedded` (sem header próprio).
 * O tab inicial pode vir por ?tab=logo|banners (redirects de /admin/marca e
 * /admin/banners apontam para cá).
 */
export const AdminAparenciaPage = () => {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') === 'banners' ? 'banners' : 'logo';

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
          <Paintbrush className="w-5 h-5 text-carmesim" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-grafite">Aparência do Site</h1>
          <p className="text-sm text-[#6B7280]">Gerir o logótipo da marca, o favicon, o ícone da app/partilha e os banners das páginas públicas.</p>
        </div>
      </div>

      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
        <TabsList>
          <TabsTrigger value="logo" data-testid="tab-logo">Logótipo</TabsTrigger>
          <TabsTrigger value="banners" data-testid="tab-banners">Banners</TabsTrigger>
        </TabsList>
        <TabsContent value="logo" className="mt-6">
          <AdminMarcaPage embedded />
        </TabsContent>
        <TabsContent value="banners" className="mt-6">
          <AdminBannersPage embedded />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminAparenciaPage;
