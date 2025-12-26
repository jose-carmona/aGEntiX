import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartLine, faClipboardList, faFlaskVial, faRightFromBracket, IconDefinition } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '@/hooks/useAuth';

interface NavItem {
  name: string;
  path: string;
  icon: IconDefinition;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: faChartLine },
  { name: 'Logs', path: '/logs', icon: faClipboardList },
  { name: 'Pruebas de Agentes', path: '/test-panel', icon: faFlaskVial },
];

export const Sidebar: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="fixed top-16 left-0 z-40 w-64 h-[calc(100vh-4rem)] bg-zinc-800 shadow-md flex flex-col">
      <nav className="mt-5 px-2 flex-1">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200',
                  isActive
                    ? 'bg-zinc-700 text-white'
                    : 'text-zinc-300 hover:bg-zinc-700 hover:text-white'
                )
              }
            >
              <FontAwesomeIcon icon={item.icon} className="mr-3 w-5" />
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>
      <div className="px-2 pb-4">
        <button
          onClick={handleLogout}
          className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-md text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors duration-200"
        >
          <FontAwesomeIcon icon={faRightFromBracket} className="mr-3 w-5" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
};
