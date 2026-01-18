/**
 * Authentication context provider.
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  oauth_provider?: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    // Initialize from sessionStorage if available
    if (typeof window !== 'undefined') {
      const savedUser = sessionStorage.getItem('user');
      if (savedUser) {
        try {
          return JSON.parse(savedUser);
        } catch {
          return null;
        }
      }
    }
    return null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load user on mount
    loadUser();
    
    // Set up periodic token refresh (every 50 minutes)
    const refreshInterval = setInterval(() => {
      if (apiClient.isAuthenticated()) {
        loadUser();
      }
    }, 50 * 60 * 1000); // 50 minutes
    
    return () => clearInterval(refreshInterval);
  }, []);

  const loadUser = async () => {
    if (apiClient.isAuthenticated()) {
      try {
        const userData = await apiClient.getCurrentUser();
        setUser(userData);
        // Save to sessionStorage
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('user', JSON.stringify(userData));
        }
      } catch (error: any) {
        console.error('Failed to load user:', error);
        // Only logout if it's a 401 (unauthorized), not on network errors
        if (error?.response?.status === 401) {
          apiClient.logout();
          setUser(null);
          if (typeof window !== 'undefined') {
            sessionStorage.removeItem('user');
          }
        }
      }
    }
    setLoading(false);
  };

  const login = async (email: string, password: string) => {
    await apiClient.login(email, password);
    await loadUser();
  };

  const register = async (email: string, password: string, fullName?: string) => {
    await apiClient.register(email, password, fullName);
    // Auto-login after registration
    await login(email, password);
  };

  const logout = async () => {
    await apiClient.logoutUser();
    setUser(null);
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('user');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
