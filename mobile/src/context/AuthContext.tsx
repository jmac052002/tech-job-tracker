import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/authService';
import { tokenStorage } from '../services/tokenStorage';
import { User } from '../types';

// Why context for auth?
// Multiple screens need to know if the user is logged in (nav guards, header, etc.)
// Context makes this available everywhere without passing props down the tree.

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // true until we check stored token

  // On app start — check if a token is already saved
  // If yes, fetch user profile to restore session
  useEffect(() => {
    async function restoreSession() {
      try {
        const token = await tokenStorage.get();
        if (token) {
          const me = await authService.getMe();
          setUser(me);
        }
      } catch {
        // Token expired or invalid — clear it
        await tokenStorage.remove();
      } finally {
        setIsLoading(false);
      }
    }
    restoreSession();
  }, []);

  async function login(email: string, password: string) {
    await authService.login(email, password);
    const me = await authService.getMe();
    setUser(me);
  }

  async function register(email: string, password: string) {
    const result = await authService.register(email, password);
    setUser(result.user);
  }

  async function logout() {
    await authService.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook — cleaner than importing useContext + AuthContext in every component
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
