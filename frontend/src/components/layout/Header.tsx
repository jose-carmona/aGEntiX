import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-blue-800 shadow-sm">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-16">
          <button
            onClick={onToggleSidebar}
            className="p-2 mr-3 text-white hover:bg-blue-700 rounded-md transition-colors duration-200"
            aria-label="Toggle sidebar"
          >
            <FontAwesomeIcon icon={faBars} className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-white">aGEntiX</h1>
          <span className="ml-3 text-sm text-blue-200">
            Dashboard de Administración
          </span>
        </div>
      </div>
    </header>
  );
};
