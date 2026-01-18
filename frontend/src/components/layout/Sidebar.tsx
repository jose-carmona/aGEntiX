import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartLine, faClipboardList, faFolderOpen, faRightFromBracket, faFileLines, faPlay, IconDefinition } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '@/hooks/useAuth';

interface NavItem {
  name: string;
  path: string;
  icon: IconDefinition;
}

interface SidebarProps {
  isCollapsed: boolean;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: faChartLine },
  { name: 'Ejecutar Agente', path: '/execute', icon: faPlay },
  { name: 'Visor Expedientes', path: '/expedientes', icon: faFileLines },
  { name: 'Logs', path: '/logs', icon: faClipboardList },
  { name: 'MCP Server Mock', path: '/mcp-server', icon: faFolderOpen },
];

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside
      className={clsx(
        'fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] bg-zinc-800 shadow-md flex flex-col transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <nav className="mt-5 px-2 flex-1">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              title={isCollapsed ? item.name : undefined}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center py-2 text-sm font-medium rounded-md transition-colors duration-200',
                  isCollapsed ? 'px-2 justify-center' : 'px-3',
                  isActive
                    ? 'bg-zinc-700 text-white'
                    : 'text-zinc-300 hover:bg-zinc-700 hover:text-white'
                )
              }
            >
              <FontAwesomeIcon
                icon={item.icon}
                className={clsx('w-5', !isCollapsed && 'mr-3')}
              />
              {!isCollapsed && item.name}
            </NavLink>
          ))}
        </div>
      </nav>
      <div className="px-2 pb-4">
        <button
          onClick={handleLogout}
          title={isCollapsed ? 'Cerrar sesión' : undefined}
          className={clsx(
            'w-full flex items-center py-2 text-sm font-medium rounded-md text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors duration-200',
            isCollapsed ? 'px-2 justify-center' : 'px-3'
          )}
        >
          <FontAwesomeIcon
            icon={faRightFromBracket}
            className={clsx('w-5', !isCollapsed && 'mr-3')}
          />
          {!isCollapsed && 'Cerrar sesión'}
        </button>
      </div>
    </aside>
  );
};
