import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Globe, School as SchoolIcon, User, Shield } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, language, setLanguage, t, activeRole } = useAuth();

  return (
    <header className="h-16 bg-brand-navy border-b border-slate-800 text-white flex items-center justify-between px-6 sticky top-0 z-40 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-brand-teal/20 border border-brand-teal/40 flex items-center justify-center text-brand-teal font-black text-xl">
          S
        </div>
        <div>
          <span className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
            Shule<span className="text-brand-teal">Hub</span>
          </span>
          {user?.school_name && (
            <span className="text-xs text-slate-400 block -mt-1 font-medium truncate max-w-[200px] md:max-w-xs">
              {user.school_name}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Language Switcher */}
        <button
          onClick={() => setLanguage(language === 'sw' ? 'en' : 'sw')}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-800/80 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition"
          title="Switch Language / Badili Lugha"
        >
          <Globe className="w-3.5 h-3.5 text-brand-teal" />
          <span>{language === 'sw' ? 'SW' : 'EN'}</span>
        </button>

        {/* User Info & Role Badge */}
        <div className="flex items-center gap-3 pl-2 border-l border-slate-700/60">
          <div className="hidden sm:block text-right">
            <span className="block text-sm font-medium text-slate-100 leading-tight">
              {user?.full_name}
            </span>
            <span className="inline-block px-1.5 py-0.5 mt-0.5 rounded text-[10px] font-bold bg-brand-teal/15 text-brand-teal uppercase tracking-wide">
              {activeRole.replace('_', ' ')}
            </span>
          </div>

          <button
            onClick={logout}
            className="p-2 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-300 hover:text-rose-400 transition"
            title={t('Logout', 'Ondoka')}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
