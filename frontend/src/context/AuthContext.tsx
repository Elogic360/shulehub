import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, Language } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  language: Language;
  login: (token: string, user: User) => void;
  logout: () => void;
  setLanguage: (lang: Language) => void;
  t: (en: string, sw: string) => string;
  activeRole: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('shuleconnect_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('shuleconnect_token');
  });

  const [language, setLangState] = useState<Language>(() => {
    return (localStorage.getItem('shuleconnect_lang') as Language) || 'en';
  });

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('shuleconnect_token', newToken);
    localStorage.setItem('shuleconnect_user', JSON.stringify(newUser));
    if (newUser.school_id) {
      localStorage.setItem('shuleconnect_school_id', newUser.school_id);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('shuleconnect_token');
    localStorage.removeItem('shuleconnect_user');
    localStorage.removeItem('shuleconnect_school_id');
    window.location.href = '/login';
  };

  const setLanguage = (lang: Language) => {
    setLangState(lang);
    localStorage.setItem('shuleconnect_lang', lang);
  };

  const t = (en: string, sw: string) => {
    return language === 'sw' ? sw : en;
  };

  const activeRole = user?.is_superadmin
    ? 'SUPER_ADMIN'
    : (user?.roles?.[0] || 'GUEST');

  return (
    <AuthContext.Provider value={{ user, token, language, login, logout, setLanguage, t, activeRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
