import { create } from 'zustand';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('jwt_token'),
  token: localStorage.getItem('jwt_token'),
  login: (token: string) => {
    localStorage.setItem('jwt_token', token);
    set({ isAuthenticated: true, token });
  },
  logout: () => {
    localStorage.removeItem('jwt_token');
    set({ isAuthenticated: false, token: null });
  },
}));
