import React from 'react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';

/**
 * Recorte quadrado no cliente antes do upload (spec-foto-de-perfil §4.2, D2),
 * versão SEM dependências (fallback aprovado pelo dono): recorte CENTRAL por
 * canvas — corta o maior quadrado central da imagem e redimensiona para
 * ~512×512 JPEG (mantém o ficheiro pequeno, dentro dos 2 MB de `avatars`). Sem
 * ajuste manual (pan/zoom): a pré-visualização circular usa `object-cover`,
 * logo é WYSIWYG do que fica guardado. O caller embrulha o Blob num File `.jpg`
 * (a validação do backend exige extensão).
 */
async function getCenterCroppedBlob(imageSrc, size = 512) {
  const image = await new Promise((resolve, reject) => {
    const img = new Image();
    img.addEventListener('load', () => resolve(img));
    img.addEventListener('error', reject);
    img.src = imageSrc;
  });
  const side = Math.min(image.naturalWidth, image.naturalHeight);
  const sx = (image.naturalWidth - side) / 2;
  const sy = (image.naturalHeight - side) / 2;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(image, sx, sy, side, side, 0, 0, size, size);
  return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.9));
}

export function AvatarCropDialog({ open, imageSrc, onCancel, onConfirm, pending }) {
  const handleConfirm = async () => {
    if (!imageSrc) return;
    try {
      const blob = await getCenterCroppedBlob(imageSrc);
      if (blob) onConfirm(blob);
      else toast.error('Não foi possível processar a imagem.');
    } catch {
      toast.error('Erro ao processar a imagem. Tente novamente.');
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onCancel(); }}>
      <DialogContent className="max-w-sm" data-testid="avatar-crop-dialog">
        <DialogHeader>
          <DialogTitle>Confirmar foto de perfil</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-[#6B7280]">
          A foto será recortada num quadrado central. Para outro enquadramento,
          recorte a imagem antes de a carregar.
        </p>
        <div className="flex justify-center py-2">
          <div className="w-40 h-40 rounded-full overflow-hidden border-4 border-white shadow-md bg-[#F5F5F5]">
            {imageSrc && <img src={imageSrc} alt="Pré-visualização da foto" className="w-full h-full object-cover" />}
          </div>
        </div>
        <DialogFooter className="gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={pending}
            className="px-4 py-2 text-sm font-semibold rounded-lg border border-[#D1D5DB] text-grafite hover:bg-[#F5F5F5] transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={pending}
            className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
            data-testid="avatar-crop-confirm"
          >
            {pending ? 'A guardar...' : 'Guardar foto'}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default AvatarCropDialog;
