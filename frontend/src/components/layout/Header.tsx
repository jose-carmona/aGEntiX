import React from 'react';
import { LogoutButton } from '@/components/auth/LogoutButton';

export const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-primary-800">aGEntiX</h1>
            <span className="ml-3 text-sm text-gray-500">
              Dashboard de Administración
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <LogoutButton />
          </div>
        </div>
      </div>
    </header>
  );
};
