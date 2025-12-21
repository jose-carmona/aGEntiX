import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export const Login: React.FC = () => {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const success = await login(token);

      if (success) {
        navigate('/dashboard');
      } else {
        setError('Token de administración inválido');
      }
    } catch (err) {
      setError('Error al validar el token. Intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <Card>
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">aGEntiX</h1>
            <p className="mt-2 text-gray-600">Dashboard de Administración</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Token de Administración"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Introduce el token"
              required
              error={error}
            />

            <Button
              type="submit"
              disabled={loading || !token.trim()}
              className="w-full"
            >
              {loading ? 'Validando...' : 'Acceder al Dashboard'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              Sistema de Gestión de Agentes IA para GEX
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
