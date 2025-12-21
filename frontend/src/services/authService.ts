import { api } from './api';
import type { TokenValidationRequest, TokenValidationResponse } from '@/types/auth';

export const authService = {
  validateAdminToken: async (token: string): Promise<boolean> => {
    try {
      const response = await api.post<TokenValidationResponse>(
        '/api/v1/auth/validate-admin-token',
        { token } as TokenValidationRequest
      );
      return response.data.valid;
    } catch (error) {
      console.error('Error validating token:', error);
      return false;
    }
  },
};
