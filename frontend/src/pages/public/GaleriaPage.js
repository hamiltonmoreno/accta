import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { galleryAPI, mediaUrl } from '../../utils/api';
import { useBodyScrollLock } from '../../hooks/useBodyScrollLock';
import { Camera, X, ChevronLeft, ChevronRight, Images, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { PageBanner } from '../../components/PageBanner';

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
        aria-label="Fechar"
        className="absolute top-4 right-4 z-50 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors outline-none focus-visible:ring-2 focus-visible:ring-white/70"
        data-testid="lightbox-close"
      >
        <X className="w-6 h-6 text-white" aria-hidden="true" />
      </button>

      {/* Counter */}
      <div className="absolute top-4 left-4 z-50 px-3 py-1.5 bg-white/10 rounded-full text-white text-sm font-mono">
        {currentIndex + 1} / {photos.length}
      </div>

      {/* Prev */}
      {currentIndex > 0 && (
        <button
          onClick={(e) => { e.stopPropagation(); onPrev(); }}
          aria-label="Foto anterior"
          className="absolute left-3 sm:left-6 top-1/2 -translate-y-1/2 z-50 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          data-testid="lightbox-prev"
        >
          <ChevronLeft className="w-5 h-5 sm:w-6 sm:h-6 text-white" aria-hidden="true" />
        </button>
      )}

      {/* Next */}
      {currentIndex < photos.length - 1 && (
        <button
          onClick={(e) => { e.stopPropagation(); onNext(); }}
          aria-label="Próxima foto"
          className="absolute right-3 sm:right-6 top-1/2 -translate-y-1/2 z-50 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          data-testid="lightbox-next"
        >
          <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6 text-white" aria-hidden="true" />
        </button>
      )}

      {/* Image */}
      <div className="max-w-5xl max-h-[85vh] mx-4" onClick={(e) => e.stopPropagation()}>
        <img key={photo.id}
          src={photo.url}
          alt={photo.caption || ''}
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
        src={mediaUrl(album.cover_url)}
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
        src={mediaUrl(album.cover_url)}
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
            alt={photo.caption || ''}
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
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [lightboxIndex, setLightboxIndex] = useState(-1);

  const { data: albums = [], isLoading: loadingAlbums } = useQuery({
    queryKey: ['publicAlbums'],
    queryFn: async () => (await galleryAPI.getPublicAlbums()).data,
  });

  const { data: photos = [] } = useQuery({
    queryKey: ['publicPhotos', selectedAlbum?.id],
    queryFn: async () => (await galleryAPI.getPublicPhotos(selectedAlbum.id)).data,
    enabled: !!selectedAlbum,
  });

  const openAlbum = (album) => setSelectedAlbum(album);
  const closeAlbum = () => setSelectedAlbum(null);

  return (
    <div>
      {/* Hero Banner */}
      <PageBanner
        pageKey="galeria"
        badge="Galeria"
        icon={Camera}
        title="Galeria de Fotos"
        subtitle="Imagens dos aeroportos, torre de controlo, equipa e paisagens de Cabo Verde"
      />

      {/* Content */}
      <section className="max-w-7xl mx-auto px-5 sm:px-6 py-10 sm:py-16">
        {loadingAlbums && !selectedAlbum ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-4 sm:gap-6" data-testid="albums-loading">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[4/3] rounded-xl" />
            ))}
          </div>
        ) : selectedAlbum ? (
          <AlbumView
            album={selectedAlbum}
            photos={photos}
            onBack={closeAlbum}
            onOpenLightbox={(index) => setLightboxIndex(index)}
          />
        ) : albums.length === 0 ? (
          <EmptyState
            icon={Images}
            title="Nenhum álbum disponível"
            description="Os álbuns de fotos serão publicados em breve."
            testId="no-albums"
          />
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
              className="inline-flex items-center justify-center gap-2 bg-floresta text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-floresta-dark transition-colors"
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
