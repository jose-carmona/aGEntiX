import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-blue-800 shadow-sm">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-16">
          <h1 className="text-2xl font-bold text-white">aGEntiX</h1>
          <span className="ml-3 text-sm text-blue-200">
            Dashboard de Administración
          </span>
        </div>
      </div>
    </header>
  );
};
