import React from 'react';
import { cn } from '../lib/utils';

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  action,
  className,
  testId,
}) => {
  return (
    <div
      className={cn(
        'card-technical rounded-xl p-8 sm:p-12 text-center',
        className,
      )}
      role="status"
      aria-live="polite"
      data-testid={testId}
    >
      {Icon && (
        <div className="flex justify-center mb-4">
          <Icon className="w-12 h-12 sm:w-16 sm:h-16 text-gray-300" aria-hidden="true" />
        </div>
      )}
      {title && (
        <p className="text-grafite font-semibold mb-1">{title}</p>
      )}
      {description && (
        <p className="text-sm text-gray-500 max-w-md mx-auto">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
};

export default EmptyState;
