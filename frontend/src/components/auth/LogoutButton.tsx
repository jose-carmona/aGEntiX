import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';

export const LogoutButton: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={handleLogout}
      className="ml-auto"
    >
      Cerrar Sesión
    </Button>
  );
};
