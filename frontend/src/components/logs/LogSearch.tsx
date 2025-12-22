import { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface LogSearchProps {
  searchText: string | undefined;
  onSearchChange: (text: string | undefined) => void;
}

export function LogSearch({ searchText, onSearchChange }: LogSearchProps) {
  const [localSearch, setLocalSearch] = useState(searchText || '');

  // Actualizar búsqueda local cuando cambia externamente
  useEffect(() => {
    setLocalSearch(searchText || '');
  }, [searchText]);

  // Debounce: actualizar después de que el usuario deje de escribir
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(localSearch || undefined);
    }, 300);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localSearch]);

  const handleClear = () => {
    setLocalSearch('');
    onSearchChange(undefined);
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>

        <input
          type="text"
          value={localSearch}
          onChange={(e) => setLocalSearch(e.target.value)}
          placeholder="Buscar en logs (mensaje, contexto, errores)..."
          className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />

        {localSearch && (
          <button
            onClick={handleClear}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            aria-label="Limpiar búsqueda"
          >
            <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {localSearch && (
        <p className="mt-2 text-sm text-gray-500">
          Buscando: <span className="font-medium text-gray-700">{localSearch}</span>
        </p>
      )}
    </div>
  );
}
