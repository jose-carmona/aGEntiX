import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);

  const toggleSidebar = () => {
    setIsSidebarCollapsed(prev => !prev);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onToggleSidebar={toggleSidebar} />
      <Sidebar isCollapsed={isSidebarCollapsed} />
      <main
        className={`mt-16 min-h-[calc(100vh-4rem)] p-6 overflow-auto transition-all duration-300 ${
          isSidebarCollapsed ? 'ml-16' : 'ml-64'
        }`}
      >
        <Outlet />
      </main>
    </div>
  );
};
