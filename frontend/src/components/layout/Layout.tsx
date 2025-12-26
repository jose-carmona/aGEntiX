import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Sidebar />
      <main className="ml-64 mt-16 min-h-[calc(100vh-4rem)] p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};
