import React, { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { Lock, Eye, EyeOff, ArrowRight, ShieldCheck, CheckCircle2, AlertTriangle, Globe } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { language, setLanguage, t } = useAuth();

  const tokenParam = searchParams.get('token') || '';
  const [token, setToken] = useState(tokenParam);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token.trim()) {
      setError(t('Reset token is required.', 'Kiungo cha kurejesha nenosiri kinahitajika.'));
      return;
    }

    if (newPassword.length < 8) {
      setError(t('Password must be at least 8 characters long.', 'Nenosiri lazima liwe na angalau herufi 8.'));
      return;
    }

    if (newPassword !== confirmPassword) {
      setError(t('Passwords do not match.', 'Manenosiri hayafanani.'));
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/reset-password', {
        token: token.trim(),
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          t(
            'Failed to reset password. The link may have expired or is invalid.',
            'Imeshindikana kurejesha nenosiri. Huenda kiungo kimekwisha au si sahihi.'
          )
      );
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
            {t('Set New Secure Password', 'Weka Nenosiri Jipya Salama')}
          </p>
        </div>

        <div className="p-6">
          {!success ? (
            <>
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900 mb-1">
                  {t('Reset Your Password', 'Weka Nenosiri Jipya')}
                </h2>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {t(
                    'Choose a strong password with at least 8 characters to safeguard your school data.',
                    'Chagua nenosiri thabiti lenye angalau herufi 8 kulinda taarifa za shule yako.'
                  )}
                </p>
              </div>

              {error && (
                <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                {!tokenParam && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                      {t('Reset Token', 'Kodi ya Kurejesha')}
                    </label>
                    <input
                      type="text"
                      required
                      value={token}
                      onChange={(e) => setToken(e.target.value)}
                      placeholder="Paste your reset token here"
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    {t('New Password', 'Nenosiri Jipya')}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      minLength={8}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-9 pr-10 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    {t('Confirm New Password', 'Thibitisha Nenosiri Jipya')}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      minLength={8}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-9 pr-10 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full justify-center"
                  disabled={loading}
                  isLoading={loading}
                  rightIcon={<ArrowRight className="w-4 h-4 text-brand-teal" />}
                >
                  {t('Update Password', 'Badilisha Nenosiri')}
                </Button>
              </form>
            </>
          ) : (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 mx-auto rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                <CheckCircle2 className="w-8 h-8" />
              </div>

              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {t('Password Successfully Reset', 'Nenosiri Limewekwa Upya')}
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {t(
                    'Your password has been successfully updated. You can now securely sign in to your ShuleConnect account.',
                    'Nenosiri lako limebadilishwa kwa ufanisi. Sasa unaweza kuingia kwenye akaunti yako ya ShuleConnect.'
                  )}
                </p>
              </div>

              <Link to="/login" className="block pt-2">
                <Button variant="primary" size="lg" className="w-full justify-center" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  {t('Sign In Now', 'Ingia Kwenye Akaunti Sasa')}
                </Button>
              </Link>
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <Link
              to="/login"
              className="text-slate-600 hover:text-brand-navy font-semibold transition"
            >
              {t('Back to Sign In', 'Rudi Kuingia')}
            </Link>

            <span className="text-[11px] font-medium text-emerald-600 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              {t('Argon2id Encrypted', 'Imelindwa na Argon2id')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};