import React from 'react';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../../components/ui/alert-dialog';

export function ConfirmDialog({
  open, onOpenChange, onConfirm,
  segmentReady, countingRecipients,
  recipientsTotal, inApp, emailCount,
  dryRun = false,
}) {
  const reachText = segmentReady && !countingRecipients
    ? (dryRun
      ? `Vai simular o envio a ${recipientsTotal} destinatário(s). Nada será enviado — apenas calcula a audiência e regista.`
      : `Vai enviar este comunicado a ${recipientsTotal} destinatário(s) (${inApp} na app · ${emailCount} por e-mail). Esta ação não pode ser anulada.`)
    : (dryRun
      ? 'Vai simular o envio. Nada será enviado.'
      : 'Vai enviar este comunicado. Esta ação não pode ser anulada.');
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{dryRun ? 'Confirmar simulação' : 'Confirmar envio'}</AlertDialogTitle>
          <AlertDialogDescription>{reachText}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid="comunicado-confirm-cancel">Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-floresta text-white hover:bg-floresta-dark"
            data-testid="comunicado-confirm-send"
          >
            {dryRun ? 'Simular' : 'Enviar'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
