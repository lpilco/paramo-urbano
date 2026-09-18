/**
 * @fileoverview Accessible Alert Banner component.
 * @module components/common/AlertBanner
 */

import React from 'react';

export interface AlertBannerProps {
  type: 'danger' | 'warning' | 'success';
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type,
  title,
  message,
  actionText,
  onAction,
}) => {
  const iconMap = {
    danger: '⚠️',
    warning: '⚡',
    success: '✓',
  };

  return (
    <aside
      className={`alert-banner alert-banner-${type}`}
      role="alert"
      aria-live="polite"
    >
      <span style={{ fontSize: '1.25rem', lineHeight: 1 }} aria-hidden="true">
        {iconMap[type]}
      </span>
      <div style={{ flex: 1 }}>
        {title && (
          <h4
            style={{
              fontSize: '0.95rem',
              fontWeight: 700,
              marginBottom: '0.2rem',
              color: 'inherit',
            }}
          >
            {title}
          </h4>
        )}
        <p style={{ fontSize: '0.85rem', color: 'inherit', margin: 0 }}>
          {message}
        </p>
      </div>
      {actionText && onAction && (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onAction}
          style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
        >
          {actionText}
        </button>
      )}
    </aside>
  );
};
