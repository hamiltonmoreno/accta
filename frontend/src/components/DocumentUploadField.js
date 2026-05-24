import React, { useRef, useState } from 'react';
import { Upload, FileCheck, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { prestacaoContasAPI } from '../utils/api';

/**
 * Campo de upload de documento para os diálogos de prestação de contas.
 * Faz upload + cria o registo `documents` no backend e devolve o document_id
 * via onChange. `kind` define visibilidade/título (política server-side).
 */
export function DocumentUploadField({ kind, value, onChange, required = false, label = 'Documento (PDF)' }) {
  const inputRef = useRef(null);
  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);

  const handlePick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { data } = await prestacaoContasAPI.uploadDocumento(file, { kind });
      setFileName(file.name);
      onChange?.(data.document_id, data);
      toast.success('Documento carregado.');
    } catch (err) {
      onChange?.('', null);
      setFileName('');
      toast.error(err.response?.data?.detail || 'Falha ao carregar o documento.');
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <div>
      <label className="block text-xs font-medium text-[#6B7280] mb-1">
        {label}{required ? ' *' : ''}
      </label>
      <input ref={inputRef} type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={handlePick} data-testid={`doc-upload-${kind}`} />
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-[#D1D5DB] rounded-md text-grafite hover:bg-[#F5F5F5] focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 disabled:opacity-60"
        >
          {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {uploading ? 'A carregar…' : (value ? 'Substituir ficheiro' : 'Escolher ficheiro')}
        </button>
        {value && !uploading && (
          <span className="inline-flex items-center gap-1 text-xs text-[#6B7280]">
            <FileCheck className="h-4 w-4 text-grafite" /> {fileName || 'Documento carregado'}
          </span>
        )}
      </div>
    </div>
  );
}

export default DocumentUploadField;
