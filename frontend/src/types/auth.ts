export interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  login: (token: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

export interface TokenValidationRequest {
  token: string;
}

export interface TokenValidationResponse {
  valid: boolean;
  message: string;
}
