import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '@/services/authService';
import { storage } from '@/utils/storage';
import type { AuthContextType } from '@/types/auth';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Cargar token al iniciar
    const savedToken = storage.getToken();
    if (savedToken) {
      setToken(savedToken);
    }
    setLoading(false);
  }, []);

  const login = async (adminToken: string): Promise<boolean> => {
    try {
      const isValid = await authService.validateAdminToken(adminToken);
      if (isValid) {
        storage.setToken(adminToken);
        setToken(adminToken);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error during login:', error);
      return false;
    }
  };

  const logout = () => {
    storage.removeToken();
    setToken(null);
  };

  const value: AuthContextType = {
    isAuthenticated: !!token,
    token,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
