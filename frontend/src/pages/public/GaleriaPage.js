import React, { useEffect, useState, useCallback } from 'react';
import { galleryAPI } from '../../utils/api';
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock';
import { Camera, X, ChevronLeft, ChevronRight, Images, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { unsplashSrcSet } from '../../utils/unsplash';

const Lightbox = ({ photos, currentIndex, onClose, onPrev, onNext }) => {
  useBodyScrollLock(true);
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
    <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center animate-fade-up"
      onClick={onClose}
      data-testid="lightbox">
      {/* Close */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-50 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
        data-testid="lightbox-close"
      >
        <X className="w-6 h-6 text-white" />
      </button>

      {/* Counter */}
      <div className="absolute top-4 left-4 z-50 px-3 py-1.5 bg-white/10 rounded-full text-white text-sm font-mono">
        {currentIndex + 1} / {photos.length}
      </div>

      {/* Prev */}
      {currentIndex > 0 && (
        <button
          onClick={(e) => { e.stopPropagation(); onPrev(); }}
          className="absolute left-3 sm:left-6 top-1/2 -translate-y-1/2 z-50 p-2 sm:p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
          data-testid="lightbox-prev"
        >
          <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
        </button>
      )}

      {/* Next */}
      {currentIndex < photos.length - 1 && (
        <button
          onClick={(e) => { e.stopPropagation(); onNext(); }}
          className="absolute right-3 sm:right-6 top-1/2 -translate-y-1/2 z-50 p-2 sm:p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
          data-testid="lightbox-next"
        >
          <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
        </button>
      )}

      {/* Image */}
      <div className="max-w-5xl max-h-[85vh] mx-4" onClick={(e) => e.stopPropagation()}>
        <img key={photo.id}
          src={photo.url}
          alt={photo.caption}
          className="max-w-full max-h-[80vh] object-contain rounded-lg animate-fade-up" />
        {photo.caption && (
          <p className="text-white/80 text-center mt-4 text-sm sm:text-base">{photo.caption}</p>
        )}
      </div>
    </div>
  );
};

const AlbumCard = ({ album, onClick }) => (
  <button onClick={onClick}
    className="group text-left w-full animate-fade-up"
    data-testid={`album-${album.id}`}>
    <div className="relative overflow-hidden rounded-xl aspect-[4/3]">
      <img
        src={album.cover_url}
        alt={album.title}
        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        loading="lazy"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-5">
        <h3 className="font-bold text-lg sm:text-xl text-white mb-1 transition-colors">
          {album.title}
        </h3>
        <div className="flex items-center gap-1.5 text-white/70 text-xs sm:text-sm">
          <Camera className="w-3.5 h-3.5" />
          <span>{album.photo_count} foto{album.photo_count !== 1 ? 's' : ''}</span>
        </div>
      </div>
    </div>
  </button>
);

const AlbumView = ({ album, photos, onBack, onOpenLightbox }) => (
  <div>
    {/* Album Header */}
    <div className="relative h-48 sm:h-64 md:h-80 overflow-hidden rounded-xl mb-6 sm:mb-8">
      <img
        src={album.cover_url}
        alt={album.title}
        className="w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-grafite via-grafite/60 to-grafite/20" />
      <div className="absolute bottom-0 left-0 right-0 p-5 sm:p-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-white/70 hover:text-white text-sm mb-3 transition-colors"
          data-testid="album-back"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar a galeria
        </button>
        <h2 className="font-bold text-2xl sm:text-3xl md:text-4xl text-white mb-1">
          {album.title}
        </h2>
        <p className="text-white/70 text-sm sm:text-base max-w-xl">
          {album.description}
        </p>
      </div>
    </div>

    {/* Photo Grid */}
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-3">
      {photos.map((photo, index) => (
        <button key={photo.id}
          onClick={() => onOpenLightbox(index)}
          className="group relative aspect-square overflow-hidden rounded-lg animate-fade-up"
          data-testid={`photo-${photo.id}`}>
          <img
            src={photo.url}
            alt={photo.caption}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-end">
            {photo.caption && (
              <p className="text-white text-xs p-2 opacity-0 group-hover:opacity-100 transition-opacity line-clamp-2">
                {photo.caption}
              </p>
            )}
          </div>
        </button>
      ))}
    </div>
  </div>
);

export const GaleriaPage = () => {
  const [albums, setAlbums] = useState([]);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lightboxIndex, setLightboxIndex] = useState(-1);

  const loadAlbums = useCallback(async () => {
    try {
      const res = await galleryAPI.getPublicAlbums();
      setAlbums(res.data);
    } catch (err) {
      console.error('Erro ao carregar albuns:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAlbums(); }, [loadAlbums]);

  const openAlbum = async (album) => {
    setSelectedAlbum(album);
    setLoading(true);
    try {
      const res = await galleryAPI.getPublicPhotos(album.id);
      setPhotos(res.data);
    } catch (err) {
      console.error('Erro ao carregar fotos:', err);
    } finally {
      setLoading(false);
    }
  };

  const closeAlbum = () => {
    setSelectedAlbum(null);
    setPhotos([]);
  };

  return (
    <div>
      {/* Hero Banner */}
      <section className="relative h-64 sm:h-80 md:h-96 flex items-center overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=1280&auto=format&fit=crop"
          srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&auto=format&fit=crop')}
          sizes="100vw"
          alt="Galeria ACCTA"
          decoding="async"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/80 to-grafite/40" />
        <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6 w-full">
          <div className="animate-fade-up">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 border border-white/20 rounded-full mb-4">
              <Camera className="w-3.5 h-3.5 text-white" />
              <span className="text-white text-xs uppercase tracking-wider font-semibold">Galeria</span>
            </div>
            <h1 className="font-bold text-3xl sm:text-4xl md:text-5xl text-white mb-3" data-testid="gallery-title">
              Galeria de Fotos
            </h1>
            <p className="text-white/70 text-sm sm:text-lg max-w-xl">
              Imagens dos aeroportos, torre de controlo, equipa e paisagens de Cabo Verde
            </p>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="max-w-7xl mx-auto px-5 sm:px-6 py-10 sm:py-16">
        {loading && !selectedAlbum ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
          </div>
        ) : selectedAlbum ? (
          <AlbumView
            album={selectedAlbum}
            photos={photos}
            onBack={closeAlbum}
            onOpenLightbox={(index) => setLightboxIndex(index)}
          />
        ) : albums.length === 0 ? (
          <div className="text-center py-16" data-testid="no-albums">
            <Images className="w-16 h-16 text-gray-200 mx-auto mb-4" />
            <h3 className="text-xl text-gray-400 font-semibold">Nenhum álbum disponível</h3>
            <p className="text-gray-400 text-sm mt-2">Os álbuns de fotos serão publicados em breve.</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-4 sm:gap-6">
            {albums.map((album) => (
              <AlbumCard
                key={album.id}
                album={album}
                onClick={() => openAlbum(album)}
              />
            ))}
          </div>
        )}
      </section>

      {/* CTA */}
      <section className="bg-grafite py-12 sm:py-16">
        <div className="max-w-4xl mx-auto px-5 sm:px-6 text-center">
          <h2 className="font-bold text-2xl sm:text-3xl text-white mb-3">
            Conheça a nossa <span className="text-white">história</span>
          </h2>
          <p className="text-white/60 text-sm sm:text-base mb-6">
            Descubra mais sobre a associação e a profissão de controlador de tráfego aéreo
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            <Link
              to="/sobre"
              className="inline-flex items-center justify-center gap-2 bg-carmesim text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-carmesim-dark transition-colors"
            >
              Sobre a ACCTA
            </Link>
            <Link
              to="/profissao"
              className="inline-flex items-center justify-center gap-2 bg-white/10 text-white border border-white/20 px-6 py-3 rounded-lg font-bold text-sm hover:bg-white/20 transition-colors"
            >
              A Profissão
            </Link>
          </div>
        </div>
      </section>

      {/* Lightbox */}
      {lightboxIndex >= 0 && (
          <Lightbox
            photos={photos}
            currentIndex={lightboxIndex}
            onClose={() => setLightboxIndex(-1)}
            onPrev={() => setLightboxIndex(Math.max(0, lightboxIndex - 1))}
            onNext={() => setLightboxIndex(Math.min(photos.length - 1, lightboxIndex + 1))}
          />
        )}
      </div>
  );
};
