// components/mcp/MCPTabs.tsx
// Sistema de tabs para navegación entre módulos MCP

import React from 'react';

export type MCPTabId = 'expedientes' | 'documentacion' | 'explorer';

export interface MCPTab {
  id: MCPTabId;
  label: string;
  icon: React.ReactNode;
  badge?: number;
  description: string;
}

export const MCP_TABS: MCPTab[] = [
  {
    id: 'expedientes',
    label: 'Expedientes',
    description: '10 tools de gestión',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    badge: 10
  },
  {
    id: 'documentacion',
    label: 'Documentación',
    description: '3 tools de normativa',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    badge: 3
  },
  {
    id: 'explorer',
    label: 'Explorador',
    description: 'Pruebas interactivas',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    )
  }
];

interface MCPTabsProps {
  activeTab: MCPTabId;
  onTabChange: (tab: MCPTabId) => void;
  disabled?: boolean;
}

export const MCPTabs: React.FC<MCPTabsProps> = ({
  activeTab,
  onTabChange,
  disabled = false
}) => {
  return (
    <div className="border-b border-gray-200">
      <nav className="flex space-x-1" aria-label="Tabs">
        {MCP_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => !disabled && onTabChange(tab.id)}
              disabled={disabled}
              className={`
                group relative flex items-center gap-2 px-4 py-3 text-sm font-medium
                border-b-2 transition-colors duration-150
                ${isActive
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
                ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              {/* Icon */}
              <span className={isActive ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'}>
                {tab.icon}
              </span>

              {/* Label */}
              <span>{tab.label}</span>

              {/* Badge */}
              {tab.badge !== undefined && (
                <span
                  className={`
                    ml-1 px-2 py-0.5 rounded-full text-xs font-medium
                    ${isActive
                      ? 'bg-primary-100 text-primary-600'
                      : 'bg-gray-100 text-gray-600 group-hover:bg-gray-200'
                    }
                  `}
                >
                  {tab.badge}
                </span>
              )}

              {/* Tooltip con descripción */}
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {tab.description}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};
