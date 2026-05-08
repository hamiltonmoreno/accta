import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { galleryAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock';
import { toast } from 'sonner';
import {
  Camera, Upload, CheckCircle, XCircle, Trash2,
  Images, X, ChevronLeft, ChevronRight, Clock, Eye,
  EyeOff, FolderPlus, Pencil
} from 'lucide-react';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../components/ui/alert-dialog';

// ===== LIGHTBOX =====
const Lightbox = ({ photos, currentIndex, onClose, onPrev, onNext }) => {
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft') onPrev();
      if (e.key === 'ArrowRight') onNext();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose, onPrev, onNext]);
  const photo = photos[currentIndex];
  if (!photo) return null;
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center" onClick={onClose} data-testid="lightbox">
      <button onClick={onClose} className="absolute top-4 right-4 z-50 p-2 bg-white/10 hover:bg-white/20 rounded-full" aria-label="Fechar" data-testid="lightbox-close">
        <X className="w-6 h-6 text-white" aria-hidden="true" />
      </button>
      <div className="absolute top-4 left-4 z-50 px-3 py-1.5 bg-white/10 rounded-full text-white text-sm font-mono">{currentIndex + 1}/{photos.length}</div>
      {currentIndex > 0 && (
        <button onClick={(e) => { e.stopPropagation(); onPrev(); }} className="absolute left-4 top-1/2 -translate-y-1/2 z-50 p-3 bg-white/10 hover:bg-white/20 rounded-full" aria-label="Foto anterior" data-testid="lightbox-prev">
          <ChevronLeft className="w-6 h-6 text-white" aria-hidden="true" />
        </button>
      )}
      {currentIndex < photos.length - 1 && (
        <button onClick={(e) => { e.stopPropagation(); onNext(); }} className="absolute right-4 top-1/2 -translate-y-1/2 z-50 p-3 bg-white/10 hover:bg-white/20 rounded-full" aria-label="Próxima foto" data-testid="lightbox-next">
          <ChevronRight className="w-6 h-6 text-white" aria-hidden="true" />
        </button>
      )}
      <div className="max-w-5xl max-h-[85vh] mx-4" onClick={(e) => e.stopPropagation()}>
        <motion.img key={photo.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          src={photo.url} alt={photo.caption} className="max-w-full max-h-[80vh] object-contain rounded-lg" />
        {photo.caption && <p className="text-white/80 text-center mt-4 text-sm">{photo.caption}</p>}
      </div>
    </motion.div>
  );
};

// ===== UPLOAD MODAL =====
const UploadModal = ({ albums, onClose, onUploaded }) => {
  const [albumId, setAlbumId] = useState(albums[0]?.id || '');
  const [caption, setCaption] = useState('');
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!albumId || files.length === 0) { toast.error('Selecione um album e pelo menos uma foto'); return; }
    setUploading(true);
    let uploaded = 0;
    for (const file of files) {
      try {
        await galleryAPI.uploadPhoto(albumId, file, caption);
        uploaded++;
        setProgress(Math.round((uploaded / files.length) * 100));
      } catch (err) {
        toast.error(`Erro ao enviar ${file.name}: ${err.response?.data?.detail || 'Erro'}`);
      }
    }
    toast.success(`${uploaded} foto${uploaded > 1 ? 's' : ''} enviada${uploaded > 1 ? 's' : ''}!`);
    setUploading(false);
    onUploaded();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="rounded-xl shadow-2xl w-full max-w-md" style={{ backgroundColor: 'var(--surface-card)' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5" style={{ borderBottom: '1px solid var(--surface-border)' }}>
          <h2 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>Submeter Fotos</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-100" aria-label="Fechar" data-testid="close-upload-modal"><X className="w-5 h-5 text-gray-400" aria-hidden="true" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style={{ color: 'var(--text-muted)' }}>Album *</label>
            <select value={albumId} onChange={(e) => setAlbumId(e.target.value)} data-testid="upload-album-select"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none">
              {albums.map(a => <option key={a.id} value={a.id}>{a.title}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style={{ color: 'var(--text-muted)' }}>Legenda</label>
            <input type="text" value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="Descricao da foto..."
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="upload-caption-input" />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style={{ color: 'var(--text-muted)' }}>Fotos * (JPG, PNG, WEBP)</label>
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-carmesim/50 transition-colors"
              data-testid="upload-file-input">
              <Upload className="w-8 h-8 text-gray-300 mb-2" />
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {files.length > 0 ? `${files.length} foto${files.length > 1 ? 's' : ''} selecionada${files.length > 1 ? 's' : ''}` : 'Clique para selecionar'}
              </span>
              <input type="file" accept="image/jpeg,image/png,image/webp" multiple className="hidden"
                onChange={(e) => setFiles(Array.from(e.target.files))} />
            </label>
          </div>

          {uploading && (
            <div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-carmesim h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-center mt-1" style={{ color: 'var(--text-muted)' }}>{progress}%</p>
            </div>
          )}

          <button type="submit" disabled={uploading || files.length === 0} className="w-full btn-primary py-3 text-sm font-semibold" data-testid="upload-submit-btn">
            {uploading ? 'A enviar...' : `Submeter ${files.length > 0 ? files.length : ''} Foto${files.length > 1 ? 's' : ''}`}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

// ===== ALBUM MODAL =====
const AlbumModal = ({ album, onClose, onSaved }) => {
  const isEdit = !!album;
  const [form, setForm] = useState({
    title: album?.title || '', description: album?.description || '',
    visibility: album?.visibility || 'public', order: album?.order || 0,
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error('Titulo e obrigatorio'); return; }
    setSaving(true);
    try {
      if (isEdit) {
        await galleryAPI.updateAlbum(album.id, form);
        toast.success('Album atualizado');
      } else {
        await galleryAPI.createAlbum(form);
        toast.success('Album criado');
      }
      onSaved();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro');
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="rounded-xl shadow-2xl w-full max-w-md" style={{ backgroundColor: 'var(--surface-card)' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5" style={{ borderBottom: '1px solid var(--surface-border)' }}>
          <h2 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{isEdit ? 'Editar Album' : 'Novo Album'}</h2>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-100" aria-label="Fechar" data-testid="close-album-modal"><X className="w-5 h-5 text-gray-400" aria-hidden="true" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style={{ color: 'var(--text-muted)' }}>Titulo *</label>
            <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Ex: Aeroportos de Cabo Verde"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="album-title-input" />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style={{ color: 'var(--text-muted)' }}>Descricao</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Descricao do album..." rows={2}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none resize-none"
              data-testid="album-desc-input" />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider mb-1.5 block" style={{ color: 'var(--text-muted)' }}>Visibilidade</label>
            <div className="flex gap-2">
              {[{ val: 'public', label: 'Publico', icon: Eye }, { val: 'private', label: 'Socios', icon: EyeOff }].map(opt => (
                <button key={opt.val} type="button" onClick={() => setForm({ ...form, visibility: opt.val })}
                  data-testid={`visibility-${opt.val}`}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                    form.visibility === opt.val ? 'bg-carmesim text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                  }`}>
                  <opt.icon className="w-4 h-4" /> {opt.label}
                </button>
              ))}
            </div>
          </div>
          <button type="submit" disabled={saving} className="w-full btn-primary py-3 text-sm font-semibold" data-testid="save-album-btn">
            {saving ? 'A guardar...' : isEdit ? 'Atualizar Album' : 'Criar Album'}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

// ===== PENDING PHOTOS PANEL =====
const PendingPanel = ({ onAction }) => {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await galleryAPI.getPending();
      setPending(res.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (photoId) => {
    try { await galleryAPI.approvePhoto(photoId); toast.success('Foto aprovada!'); load(); onAction(); } catch { toast.error('Erro'); }
  };
  const handleReject = async (photoId) => {
    try { await galleryAPI.rejectPhoto(photoId); toast.success('Foto rejeitada'); load(); onAction(); } catch { toast.error('Erro'); }
  };

  if (!loading && pending.length === 0) return null;

  return (
    <div className="card-technical overflow-hidden" data-testid="pending-photos-panel">
      <div className="flex items-center gap-3 p-4" style={{ borderBottom: '1px solid var(--surface-border)' }}>
        <div className="w-9 h-9 bg-orange-500 rounded-lg flex items-center justify-center">
          <Clock className="w-4 h-4 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Fotos Pendentes</h3>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{pending.length} foto{pending.length !== 1 ? 's' : ''} a aguardar aprovacao</p>
        </div>
      </div>
      {loading ? (
        <div className="p-6 text-center"><div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin inline-block" /></div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 p-4">
          {pending.map(photo => (
            <div key={photo.id} className="relative group rounded-lg overflow-hidden" data-testid={`pending-photo-${photo.id}`}>
              <img src={photo.url} alt={photo.caption} className="w-full aspect-square object-cover" />
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                <p className="text-white text-xs text-center px-2 truncate w-full">{photo.uploaded_by_name}</p>
                <p className="text-white/70 text-xs truncate w-full text-center">{photo.album_title}</p>
                <div className="flex gap-2 mt-1">
                  <button onClick={() => handleApprove(photo.id)} className="p-2 bg-green-600 rounded-full text-white hover:bg-green-700" aria-label="Aprovar foto" data-testid={`approve-photo-${photo.id}`}>
                    <CheckCircle className="w-4 h-4" aria-hidden="true" />
                  </button>
                  <button onClick={() => handleReject(photo.id)} className="p-2 bg-carmesim rounded-full text-white hover:bg-carmesim-dark" aria-label="Rejeitar foto" data-testid={`reject-photo-${photo.id}`}>
                    <XCircle className="w-4 h-4" aria-hidden="true" />
                  </button>
                </div>
              </div>
              {photo.caption && <p className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs px-2 py-1 truncate">{photo.caption}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ===== MAIN PAGE =====
export const GaleriaAdminPage = () => {
  const { isAdmin } = useAuth();
  const [albums, setAlbums] = useState([]);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lightboxIndex, setLightboxIndex] = useState(-1);
  const [showUpload, setShowUpload] = useState(false);
  const [showAlbumModal, setShowAlbumModal] = useState(false);
  const [editingAlbum, setEditingAlbum] = useState(null);
  const [confirmDeleteAlbum, setConfirmDeleteAlbum] = useState(null);
  const [confirmDeletePhoto, setConfirmDeletePhoto] = useState(null);

  const loadAlbums = useCallback(async () => {
    try {
      const res = await galleryAPI.getAlbums();
      setAlbums(res.data);
    } catch { toast.error('Erro ao carregar albuns'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadAlbums(); }, [loadAlbums]);

  const openAlbum = async (album) => {
    setSelectedAlbum(album);
    setLoading(true);
    try {
      const res = await galleryAPI.getPhotos(album.id);
      setPhotos(res.data);
    } catch { toast.error('Erro ao carregar fotos'); }
    finally { setLoading(false); }
  };

  const handleDeleteAlbum = async (albumId) => {
    try { await galleryAPI.deleteAlbum(albumId); toast.success('Album removido'); loadAlbums(); setSelectedAlbum(null); } catch { toast.error('Erro'); }
  };

  const handleDeletePhoto = async (photoId) => {
    try { await galleryAPI.deletePhoto(photoId); toast.success('Foto removida'); openAlbum(selectedAlbum); } catch { toast.error('Erro'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="page-title" data-testid="gallery-admin-title">Galeria de Fotos</h1>
          <p className="page-subtitle">Visualize, submeta e {isAdmin ? 'gira ' : ''}fotos da comunidade ACCTA</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowUpload(true)} className="btn-primary flex items-center gap-2 text-sm" data-testid="upload-photos-btn">
            <Upload className="w-4 h-4" /> Submeter Fotos
          </button>
          {isAdmin && (
            <button onClick={() => { setEditingAlbum(null); setShowAlbumModal(true); }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold btn-outline" data-testid="create-album-btn">
              <FolderPlus className="w-4 h-4" /> Novo Album
            </button>
          )}
        </div>
      </div>

      {/* Pending Photos (Admin) */}
      {isAdmin && <PendingPanel onAction={() => { loadAlbums(); if (selectedAlbum) openAlbum(selectedAlbum); }} />}

      {/* Selected Album View */}
      {selectedAlbum ? (
        <div>
          <button onClick={() => { setSelectedAlbum(null); setPhotos([]); }}
            className="flex items-center gap-2 text-sm mb-4" style={{ color: 'var(--text-muted)' }} data-testid="back-to-albums">
            <ChevronLeft className="w-4 h-4" /> Voltar aos albuns
          </button>

          <div className="card-technical p-5 sm:p-6 mb-6">
            <div className="flex items-start justify-between flex-wrap gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="font-bold text-xl" style={{ color: 'var(--text-primary)' }}>{selectedAlbum.title}</h2>
                  {selectedAlbum.visibility === 'private' && (
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs uppercase tracking-wider rounded-full font-semibold">Privado</span>
                  )}
                </div>
                {selectedAlbum.description && <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{selectedAlbum.description}</p>}
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{photos.length} foto{photos.length !== 1 ? 's' : ''}</p>
              </div>
              {isAdmin && (
                <div className="flex gap-2">
                  <button onClick={() => { setEditingAlbum(selectedAlbum); setShowAlbumModal(true); }}
                    className="p-2 rounded-lg hover:bg-gray-100" style={{ color: 'var(--text-muted)' }} aria-label="Editar álbum" data-testid="edit-album-btn">
                    <Pencil className="w-4 h-4" aria-hidden="true" />
                  </button>
                  <button onClick={() => setConfirmDeleteAlbum(selectedAlbum.id)}
                    className="p-2 rounded-lg text-gray-400 hover:text-carmesim hover:bg-carmesim/10" aria-label="Apagar álbum" data-testid="delete-album-btn">
                    <Trash2 className="w-4 h-4" aria-hidden="true" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12"><div className="w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin inline-block" /></div>
          ) : photos.length === 0 ? (
            <div className="card-technical p-12 text-center" data-testid="no-photos">
              <Camera className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
              <p style={{ color: 'var(--text-secondary)' }}>Nenhuma foto neste album</p>
              <button onClick={() => setShowUpload(true)} className="text-carmesim text-sm font-semibold mt-2 hover:underline">Submeter a primeira foto</button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-3">
              {photos.map((photo, index) => (
                <motion.div key={photo.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: index * 0.03 }}
                  className="group relative aspect-square overflow-hidden rounded-lg" data-testid={`gallery-photo-${photo.id}`}>
                  <button onClick={() => setLightboxIndex(index)} className="w-full h-full">
                    <img src={photo.url} alt={photo.caption} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" loading="lazy" />
                  </button>
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors pointer-events-none" />
                  {(isAdmin || photo.uploaded_by === undefined) && (
                    <button onClick={() => setConfirmDeletePhoto(photo.id)}
                      className="absolute top-2 right-2 p-1.5 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 text-white hover:bg-carmesim transition-all"
                      aria-label="Apagar foto"
                      data-testid={`delete-photo-${photo.id}`}>
                      <Trash2 className="w-3 h-3" aria-hidden="true" />
                    </button>
                  )}
                  {photo.caption && (
                    <p className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent text-white text-xs px-3 py-2 opacity-0 group-hover:opacity-100 transition-opacity">{photo.caption}</p>
                  )}
                  {photo.uploaded_by_name && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 bg-black/50 rounded-full text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                      {photo.uploaded_by_name}
                    </span>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Albums Grid */
        loading ? (
          <div className="text-center py-12"><div className="w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin inline-block" /></div>
        ) : albums.length === 0 ? (
          <div className="card-technical p-12 text-center" data-testid="no-albums-private">
            <Images className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
            <p className="font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>Nenhum album criado</p>
            {isAdmin && <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Crie o primeiro album para comecar a receber fotos</p>}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {albums.map((album, i) => (
              <motion.div key={album.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className="card-technical overflow-hidden group cursor-pointer" onClick={() => openAlbum(album)}
                data-testid={`album-card-${album.id}`}>
                <div className="relative aspect-[16/10] overflow-hidden">
                  {album.cover_url ? (
                    <img src={album.cover_url} alt={album.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center" style={{ backgroundColor: 'var(--surface-card-hover)' }}>
                      <Images className="w-12 h-12" style={{ color: 'var(--text-muted)' }} />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <div className="absolute top-3 right-3 flex items-center gap-1.5">
                    {album.visibility === 'private' && (
                      <span className="px-2 py-0.5 bg-black/50 rounded-full text-white text-xs uppercase tracking-wider font-semibold flex items-center gap-1">
                        <EyeOff className="w-3 h-3" /> Privado
                      </span>
                    )}
                  </div>
                  <div className="absolute bottom-3 left-3 right-3">
                    <h3 className="font-bold text-white text-lg group-hover:text-carmesim transition-colors">{album.title}</h3>
                    <div className="flex items-center gap-1.5 text-white/70 text-xs mt-0.5">
                      <Camera className="w-3.5 h-3.5" />
                      <span>{album.photo_count} foto{album.photo_count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                </div>
                {album.description && (
                  <div className="px-4 py-3">
                    <p className="text-xs line-clamp-2" style={{ color: 'var(--text-secondary)' }}>{album.description}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )
      )}

      {/* Modals */}
      {showUpload && albums.length > 0 && <UploadModal albums={albums} onClose={() => setShowUpload(false)} onUploaded={() => { loadAlbums(); if (selectedAlbum) openAlbum(selectedAlbum); }} />}
      {showAlbumModal && <AlbumModal album={editingAlbum} onClose={() => { setShowAlbumModal(false); setEditingAlbum(null); }} onSaved={loadAlbums} />}

      {/* Lightbox */}
      <AnimatePresence>
        {lightboxIndex >= 0 && (
          <Lightbox photos={photos} currentIndex={lightboxIndex} onClose={() => setLightboxIndex(-1)}
            onPrev={() => setLightboxIndex(Math.max(0, lightboxIndex - 1))}
            onNext={() => setLightboxIndex(Math.min(photos.length - 1, lightboxIndex + 1))} />
        )}
      </AnimatePresence>

      <AlertDialog open={!!confirmDeleteAlbum} onOpenChange={(open) => !open && setConfirmDeleteAlbum(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover álbum</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza? O álbum e todas as suas fotos serão removidos permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => { handleDeleteAlbum(confirmDeleteAlbum); setConfirmDeleteAlbum(null); }}
            >
              Remover álbum
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!confirmDeletePhoto} onOpenChange={(open) => !open && setConfirmDeletePhoto(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover foto</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja remover esta foto? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => { handleDeletePhoto(confirmDeletePhoto); setConfirmDeletePhoto(null); }}
            >
              Remover foto
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
