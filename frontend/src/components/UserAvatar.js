import React from 'react';
import { Avatar, AvatarImage, AvatarFallback } from './ui/avatar';
import { mediaUrl } from '../utils/api';
import { cn } from '../lib/utils';

/**
 * Avatar do utilizador — FONTE ÚNICA de exibição (spec-foto-de-perfil §4.1).
 * Foto quando existe; iniciais carmesim como fallback — exatamente o aspeto
 * anterior — quando NÃO há foto, em erro/404 ou enquanto carrega (o
 * AvatarFallback do Radix trata os três casos). Substitui todas as caixas de
 * iniciais hand-rolled do portal.
 *
 * Props: `name`, `photoUrl`, `size` (xs|sm|md|lg|xl), `className` (sobrepõe o
 * tamanho quando um local precisa de dimensão específica/responsiva) e
 * `fallbackClassName` (sobrepõe a COR do fallback — por defeito carmesim; alguns
 * locais usavam neutro/âmbar e preservam-no). `cn` usa twMerge → a última classe
 * em conflito ganha.
 */
const SIZES = {
  xs: { box: 'h-8 w-8', text: 'text-xs' },
  sm: { box: 'h-9 w-9', text: 'text-sm' },
  md: { box: 'h-10 w-10', text: 'text-base' },
  lg: { box: 'h-16 w-16', text: 'text-2xl' },
  xl: { box: 'h-24 w-24', text: 'text-4xl' },
};

export function UserAvatar({ name, photoUrl, size = 'md', className, fallbackClassName }) {
  const sz = SIZES[size] || SIZES.md;
  const initial = name?.charAt(0)?.toUpperCase() || '?';
  return (
    <Avatar className={cn(sz.box, 'flex-shrink-0', className)}>
      {photoUrl ? <AvatarImage src={mediaUrl(photoUrl)} alt={name || 'Avatar'} /> : null}
      <AvatarFallback className={cn('bg-carmesim text-white font-bold', sz.text, fallbackClassName)}>
        {initial}
      </AvatarFallback>
    </Avatar>
  );
}

export default UserAvatar;
