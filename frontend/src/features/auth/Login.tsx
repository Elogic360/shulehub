import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { School, User, Lock, Phone, Mail, Building, Globe, CheckCircle2, ArrowRight } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, language, setLanguage, t } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login form state
  const [username, setUsername] = useState('admin@shuleconnect.co.tz');
  const [password, setPassword] = useState('SuperAdmin2026!');

  // Register form state
  const [schoolName, setSchoolName] = useState('');
  const [schoolCode, setSchoolCode] = useState('');
  const [schoolType, setSchoolType] = useState('PRIMARY');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');

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

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/auth/register-school', {
        school_name: schoolName,
        school_code: schoolCode,
        school_type: schoolType,
        contact_email: contactEmail,
        contact_phone: contactPhone,
        owner_full_name: ownerName,
        owner_password: ownerPassword,
        region: 'Dar es Salaam',
      });
      login(res.data.access_token, res.data.user);
      window.location.href = '/owner';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Usajili umeshindikana. Tafadhali jaribu tena.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-darkNavy via-brand-navy to-slate-900 flex flex-col justify-center items-center p-4">
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

        {/* Tab switcher */}
        <div className="flex border-b border-slate-200 bg-slate-50">
          <button
            onClick={() => { setIsRegistering(false); setError(null); }}
            className={`flex-1 py-3 text-sm font-semibold border-b-2 transition ${
              !isRegistering
                ? 'border-brand-teal text-brand-navy bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {t('Sign In', 'Ingia Kwenye Akaunti')}
          </button>
          <button
            onClick={() => { setIsRegistering(true); setError(null); }}
            className={`flex-1 py-3 text-sm font-semibold border-b-2 transition ${
              isRegistering
                ? 'border-brand-teal text-brand-navy bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {t('Register School', 'Sajili Shule')}
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          {!isRegistering ? (
            /* Sign In Form */
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
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t('Password', 'Nenosiri')}
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-lg bg-brand-navy hover:bg-slate-800 text-white font-semibold text-sm shadow-md transition flex items-center justify-center gap-2"
              >
                {loading ? t('Signing in...', 'Inaingia...') : t('Sign In', 'Ingia')}
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
          ) : (
            /* School Registration Form */
            <form onSubmit={handleRegister} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('School Name', 'Jina la Shule')}
                </label>
                <input
                  type="text"
                  required
                  value={schoolName}
                  onChange={(e) => setSchoolName(e.target.value)}
                  placeholder="e.g. Feza Primary School"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('School Code', 'Kifupi cha Shule')}
                  </label>
                  <input
                    type="text"
                    required
                    value={schoolCode}
                    onChange={(e) => setSchoolCode(e.target.value.toUpperCase())}
                    placeholder="FEZA01"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal uppercase"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('School Level', 'Ngazi ya Shule')}
                  </label>
                  <select
                    value={schoolType}
                    onChange={(e) => setSchoolType(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white"
                  >
                    <option value="PRIMARY">{t('Primary (Std 1 - 6)', 'Msingi (Std 1 - 6)')}</option>
                    <option value="SECONDARY">{t('Secondary (Form 1 - 4)', 'Sekondari (Form 1 - 4)')}</option>
                    <option value="COMBINED">{t('Combined (Primary + Secondary)', 'Msingi + Sekondari')}</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Official Email', 'Barua Pepe')}
                  </label>
                  <input
                    type="email"
                    required
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    placeholder="info@school.ac.tz"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Mobile Phone', 'Namba ya Simu')}
                  </label>
                  <input
                    type="text"
                    required
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="0712345678"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Owner / Headmaster Full Name', 'Jina Kamili la Mmiliki / Mkuu wa Shule')}
                </label>
                <input
                  type="text"
                  required
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  placeholder="Mwalimu Godfrey Mallya"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Owner Password', 'Nenosiri la Mmiliki')}
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={ownerPassword}
                  onChange={(e) => setOwnerPassword(e.target.value)}
                  placeholder="Angalau herufi 8"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 py-2.5 px-4 rounded-lg bg-brand-navy hover:bg-slate-800 text-white font-semibold text-sm shadow-md transition flex items-center justify-center gap-2"
              >
                {loading ? t('Creating School...', 'Inasajili Shule...') : t('Complete Registration', 'Kamilisha Usajili wa Shule')}
                <CheckCircle2 className="w-4 h-4 text-brand-teal" />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
