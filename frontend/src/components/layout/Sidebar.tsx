import React from 'react';
import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';

interface NavItem {
  name: string;
  path: string;
  icon: string;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: '📊' },
  { name: 'Logs', path: '/logs', icon: '📋' },
  { name: 'Pruebas de Agentes', path: '/test-panel', icon: '🧪' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white shadow-md border-r border-gray-200">
      <nav className="mt-5 px-2">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200',
                  isActive
                    ? 'bg-primary-100 text-primary-900'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                )
              }
            >
              <span className="mr-3 text-xl">{item.icon}</span>
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>
    </aside>
  );
};
