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
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Confirmar envio</AlertDialogTitle>
          <AlertDialogDescription>
            {segmentReady && !countingRecipients
              ? `Vai enviar este comunicado a ${recipientsTotal} destinatário(s) (${inApp} na app · ${emailCount} por e-mail). Esta ação não pode ser anulada.`
              : 'Vai enviar este comunicado. Esta ação não pode ser anulada.'}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel data-testid="comunicado-confirm-cancel">Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-floresta text-white hover:bg-floresta-dark"
            data-testid="comunicado-confirm-send"
          >
            Enviar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
