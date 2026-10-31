import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { Lock, Mail, Globe, ArrowRight, ShieldCheck, Eye, EyeOff, Home } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, language, setLanguage, t } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // Login form state
  const [username, setUsername] = useState('admin@shuleconnect.co.tz');
  const [password, setPassword] = useState('SuperAdmin2026!');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/auth/login', { username, password });
      login(res.data.access_token, res.data.user);
      
      // Route based on role
      const roles: string[] = res.data.user.roles || [];
      if (res.data.user.is_superadmin) {
        window.location.href = '/admin';
      } else if (roles.includes('SCHOOL_OWNER') || roles.includes('SCHOOL_ADMIN')) {
        window.location.href = '/owner';
      } else if (roles.includes('CLASS_TEACHER')) {
        window.location.href = '/teacher';
      } else if (roles.includes('PARENT')) {
        window.location.href = '/parent';
      } else {
        window.location.href = '/';
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Imeshindikana kuingia. Tafadhali hakiki taarifa zako.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-darkNavy via-brand-navy to-slate-900 flex flex-col justify-center items-center p-4">
      <div className="absolute top-4 left-4">
        <Link
          to="/"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
        >
          <Home className="w-3.5 h-3.5 text-brand-teal" />
          <span>{t('Back to Website', 'Rudi Tovutini')}</span>
        </Link>
      </div>
      <div className="absolute top-4 right-4">
        <button
          onClick={() => setLanguage(language === 'sw' ? 'en' : 'sw')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
        >
          <Globe className="w-3.5 h-3.5 text-brand-teal" />
          <span>{language === 'sw' ? 'English' : 'Kiswahili'}</span>
        </button>
      </div>

      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden">
        {/* Header Banner */}
        <div className="bg-brand-navy p-6 text-center border-b border-slate-800">
          <div className="w-12 h-12 mx-auto rounded-xl bg-brand-teal/20 border border-brand-teal/40 flex items-center justify-center text-brand-teal font-black text-2xl mb-3">
            S
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Shule<span className="text-brand-teal">Connect</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {t(
              'Education Communication & Parent Engagement SaaS',
              'Mfumo wa Mawasiliano ya Shule na Wazazi Tanzania'
            )}
          </p>
        </div>

        {/* Section title */}
        <div className="px-6 pt-5 pb-2 border-b border-slate-100 flex items-center justify-between">
          <span className="text-sm font-bold text-slate-800">
            {t('Sign In to Account', 'Ingia Kwenye Akaunti')}
          </span>
          <span className="text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200">
            <ShieldCheck className="w-3 h-3" />
            {t('Secure Portal', 'Mlango Salama')}
          </span>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          {/* Sign In Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                {t('Email or Mobile Number (+255)', 'Barua Pepe au Simu (07xx / +255)')}
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="0712345678 / admin@shuleconnect.co.tz"
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  {t('Password', 'Nenosiri')}
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-semibold text-brand-teal hover:text-teal-700 transition"
                >
                  {t('Forgot password?', 'Umesahau nenosiri?')}
                </Link>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-lg bg-brand-navy hover:bg-slate-800 text-white font-semibold text-sm shadow-md transition flex items-center justify-center gap-2"
            >
              {loading ? t('Signing in...', 'Inaingia...') : t('Sign In', 'Ingia Kwenye Akaunti')}
              <ArrowRight className="w-4 h-4 text-brand-teal" />
            </button>

            {/* Demo Quick Logins */}
            <div className="mt-6 pt-4 border-t border-slate-100">
              <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                {t('Demo Superadmin Access', 'Ufikiaji wa Haraka wa Jaribio')}
              </span>
              <button
                type="button"
                onClick={() => {
                  setUsername('admin@shuleconnect.co.tz');
                  setPassword('SuperAdmin2026!');
                }}
                className="w-full py-1.5 px-3 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition text-left flex items-center justify-between"
              >
                <span>SuperAdmin (admin@shuleconnect.co.tz)</span>
                <span className="text-[10px] text-brand-teal font-bold uppercase">Autofill</span>
              </button>
            </div>
          </form>

          {/* Secure Onboarding Note */}
          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {t(
                'Want to onboard your school? Registration is strictly authorized via an official invitation link generated by ShuleConnect Super Administrators.',
                'Unahitaji kusajili shule yako? Usajili unafanyika rasmi kupitia kiungo salama cha mwaliko kinachotolewa na Wasimamizi Wakuu wa ShuleConnect.'
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
