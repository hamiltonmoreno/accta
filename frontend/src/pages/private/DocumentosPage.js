import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { documentsAPI, uploadAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { FileText, Download, Search, Upload, X, Plus, Check, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';

export const DocumentosPage = () => {
  const { isAdmin } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.getAll();
      setDocuments(response.data);
    } catch (error) {
      console.error('Erro ao carregar documentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocuments = documents
    .filter((doc) => filter === 'all' || doc.type === filter)
    .filter((doc) => doc.title.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-sans font-bold text-4xl text-grafite mb-2" data-testid="documents-title">
            Secretaria & Documentos
          </h1>
          <p className="text-gray-600">Acesse atas, estatutos, balancetes e outros documentos oficiais</p>
        </div>
        
        {isAdmin && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 bg-grafite text-white px-4 py-2 rounded-lg hover:bg-grafite/90 transition-all font-mono text-sm uppercase tracking-wider"
            data-testid="upload-document-btn"
          >
            <Upload className="w-4 h-4" />
            Novo Documento
          </button>
        )}
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar documentos..."
            className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
            data-testid="search-input"
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          {['all', 'ata', 'estatuto', 'balancete'].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-4 py-2 rounded-lg font-mono text-sm uppercase tracking-wider transition-all ${
                filter === type ? 'bg-grafite text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
              data-testid={`filter-${type}`}
            >
              {type === 'all' ? 'Todos' : type === 'ata' ? 'Atas' : type === 'estatuto' ? 'Estatutos' : 'Balancetes'}
            </button>
          ))}
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="card-technical rounded-xl p-12 text-center" data-testid="no-documents">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-medium mb-1">Nenhum documento encontrado</p>
          <p className="text-sm text-gray-400">
            {isAdmin ? 'Clique em "Novo Documento" para adicionar' : 'Os documentos serão exibidos aqui quando disponíveis'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map((doc, index) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="card-technical rounded-xl p-6 hover:shadow-lg transition-shadow"
              data-testid={`document-${doc.id}`}
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-grafite rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-carmesim" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="inline-block px-3 py-1 bg-carmesim/10 text-carmesim rounded-full text-xs font-mono uppercase tracking-wider mb-2">
                    {doc.type}
                  </span>
                  <h3 className="font-sans font-semibold text-lg text-grafite line-clamp-2">{doc.title}</h3>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs font-mono text-gray-500 mb-4">
                <span>{format(new Date(doc.created_at), 'dd MMM yyyy', { locale: ptBR })}</span>
                <span className="uppercase">{doc.visibility}</span>
              </div>

              {doc.tags && doc.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {doc.tags.slice(0, 3).map((tag, i) => (
                    <span key={i} className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <a
                href={doc.file_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 bg-grafite text-white hover:bg-grafite/90 h-10 px-4 rounded-lg uppercase tracking-wider font-bold text-sm transition-all"
                data-testid={`download-${doc.id}`}
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </motion.div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <AnimatePresence>
        {showUploadModal && (
          <UploadDocumentModal
            onClose={() => setShowUploadModal(false)}
            onSuccess={() => {
              setShowUploadModal(false);
              loadDocuments();
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

const UploadDocumentModal = ({ onClose, onSuccess }) => {
  const fileInputRef = useRef(null);
  const [title, setTitle] = useState('');
  const [type, setType] = useState('ata');
  const [visibility, setVisibility] = useState('socios');
  const [tags, setTags] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['.pdf', '.doc', '.docx'];
      const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
      if (!allowedTypes.includes(ext)) {
        toast.error('Tipo de arquivo não permitido. Use PDF, DOC ou DOCX.');
        return;
      }
      // Validate size (10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        toast.error('Arquivo muito grande. Máximo 10MB.');
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title || !file) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }

    setUploading(true);
    setUploadProgress(20);

    try {
      // 1. Upload the file
      const uploadResponse = await uploadAPI.uploadFile('documents', file);
      setUploadProgress(60);
      
      // 2. Create the document entry
      const documentData = {
        title,
        file_url: uploadResponse.data.file_url,
        type,
        visibility,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      };
      
      await documentsAPI.create(documentData);
      setUploadProgress(100);
      
      toast.success('Documento enviado com sucesso!');
      onSuccess();
    } catch (error) {
      console.error('Erro ao enviar documento:', error);
      toast.error(error.response?.data?.detail || 'Erro ao enviar documento');
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg" data-testid="upload-modal">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="font-sans font-bold text-2xl text-grafite">Novo Documento</h2>
              <p className="text-sm text-gray-500">Faça upload de um documento para a secretaria</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              data-testid="close-modal"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Title */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-500 mb-2">
                Título *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ex: Ata da Assembleia Geral - Março 2025"
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                required
                data-testid="document-title-input"
              />
            </div>

            {/* Type & Visibility */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-gray-500 mb-2">
                  Tipo
                </label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  data-testid="document-type-select"
                >
                  <option value="ata">Ata</option>
                  <option value="estatuto">Estatuto</option>
                  <option value="balancete">Balancete</option>
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-gray-500 mb-2">
                  Visibilidade
                </label>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  data-testid="document-visibility-select"
                >
                  <option value="publico">Público</option>
                  <option value="socios">Sócios</option>
                  <option value="direcao">Direção</option>
                </select>
              </div>
            </div>

            {/* Tags */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-500 mb-2">
                Tags (separadas por vírgula)
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="Ex: assembleia, 2025, decisões"
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                data-testid="document-tags-input"
              />
            </div>

            {/* File Upload */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-500 mb-2">
                Arquivo *
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileSelect}
                className="hidden"
                data-testid="document-file-input"
              />
              
              {file ? (
                <div className="flex items-center justify-between p-4 bg-carmesim/5 border border-carmesim/20 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-carmesim rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-grafite" />
                    </div>
                    <div>
                      <div className="font-sans font-semibold text-grafite text-sm">{file.name}</div>
                      <div className="font-mono text-xs text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full p-8 border-2 border-dashed border-gray-200 rounded-lg hover:border-primary hover:bg-gray-50 transition-all group"
                  data-testid="select-file-btn"
                >
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 bg-gray-100 group-hover:bg-grafite/10 rounded-lg flex items-center justify-center mb-3 transition-colors">
                      <Plus className="w-6 h-6 text-gray-400 group-hover:text-grafite transition-colors" />
                    </div>
                    <span className="font-sans font-semibold text-gray-600 mb-1">
                      Clique para selecionar
                    </span>
                    <span className="text-xs text-gray-400">PDF, DOC ou DOCX (máx. 10MB)</span>
                  </div>
                </button>
              )}
            </div>

            {/* Progress Bar */}
            {uploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Enviando...</span>
                  <span className="font-mono text-carmesim">{uploadProgress}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadProgress}%` }}
                    className="h-full bg-carmesim rounded-full"
                  />
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-3 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors font-mono uppercase tracking-wider"
                disabled={uploading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={uploading || !file || !title}
                className="flex-1 flex items-center justify-center gap-2 bg-grafite text-white px-4 py-3 rounded-lg hover:bg-grafite/90 transition-colors font-mono uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="submit-document-btn"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Enviar
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </motion.div>
    </>
  );
};
