import { storage } from '@/utils/storage';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir token a todas las peticiones
api.interceptors.request.use(
  (config) => {
    const token = storage.getToken();
    if (token && config.url !== '/api/v1/auth/validate-admin-token') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido o expirado
      storage.removeToken();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
