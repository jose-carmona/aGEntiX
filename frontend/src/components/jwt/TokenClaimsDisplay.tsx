// components/jwt/TokenClaimsDisplay.tsx
// Visualización de claims del token JWT

import React from 'react';

interface TokenClaimsDisplayProps {
  claims: Record<string, unknown>;
  layout?: 'grid' | 'compact' | 'full';
}

export const TokenClaimsDisplay: React.FC<TokenClaimsDisplayProps> = ({
  claims,
  layout = 'grid'
}) => {
  // Layout compacto: solo claims principales en una línea
  if (layout === 'compact') {
    return (
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
        <span><strong>exp_id:</strong> {String(claims.exp_id || '-')}</span>
        <span><strong>sub:</strong> {String(claims.sub || '-')}</span>
        <span>
          <strong>permisos:</strong>{' '}
          {Array.isArray(claims.permisos) ? claims.permisos.length : 0}
        </span>
      </div>
    );
  }

  // Layout full: JSON completo
  if (layout === 'full') {
    return (
      <div className="pt-4 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Claims del Token:</h3>
        <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto font-mono max-h-48">
          {JSON.stringify(claims, null, 2)}
        </pre>
      </div>
    );
  }

  // Layout grid (default): claims principales en grid
  return (
    <div className="pt-4 border-t border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-2">Claims del Token:</h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-500">iss:</span>{' '}
          <span className="text-gray-900">{String(claims.iss || '-')}</span>
        </div>
        <div>
          <span className="text-gray-500">sub:</span>{' '}
          <span className="text-gray-900">{String(claims.sub || '-')}</span>
        </div>
        <div>
          <span className="text-gray-500">exp_id:</span>{' '}
          <span className="text-gray-900">{String(claims.exp_id || '-')}</span>
        </div>
        <div>
          <span className="text-gray-500">tarea_id:</span>{' '}
          <span className="text-gray-900">{String(claims.tarea_id || '-')}</span>
        </div>
        <div className="col-span-2">
          <span className="text-gray-500">permisos:</span>{' '}
          <span className="text-xs text-gray-900">
            {Array.isArray(claims.permisos) ? claims.permisos.join(', ') : '-'}
          </span>
        </div>
      </div>
    </div>
  );
};
