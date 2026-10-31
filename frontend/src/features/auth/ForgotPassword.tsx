import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { Mail, ArrowLeft, ArrowRight, ShieldCheck, CheckCircle2, Globe, Loader2 } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export const ForgotPassword: React.FC = () => {
  const { language, setLanguage, t } = useAuth();
  const [identifier, setIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [message, setMessage] = useState('');
  const [devToken, setDevToken] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) return;

    setLoading(true);
    try {
      const res = await api.post('/auth/forgot-password', { identifier });
      setMessage(res.data.message);
      if (res.data.dev_reset_token) {
        setDevToken(res.data.dev_reset_token);
      }
      setSubmitted(true);
    } catch (err: any) {
      // Security: even on error, provide a reassuring generic message
      setMessage(
        t(
          'If an account exists with that identifier, instructions have been sent.',
          'Ikiwa akaunti inalingana na taarifa hiyo ipo, maelekezo yametumwa.'
        )
      );
      setSubmitted(true);
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
            {t('Password Recovery Portal', 'Mfumo wa Kurejesha Nenosiri')}
          </p>
        </div>

        <div className="p-6">
          {!submitted ? (
            <>
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900 mb-1">
                  {t('Forgot Your Password?', 'Umesahau Nenosiri Lako?')}
                </h2>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {t(
                    'Enter your registered email address or mobile phone number (+255). We will dispatch instructions to securely reset your credentials.',
                    'Weka barua pepe au namba yako ya simu iliyosajiliwa (+255). Tutakutumia maelekezo ya kuweka nenosiri jipya kwa usalama.'
                  )}
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    {t('Email or Mobile Number', 'Barua Pepe au Namba ya Simu')}
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      placeholder="0712345678 / user@shuleconnect.co.tz"
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent"
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
                  {t('Send Reset Instructions', 'Tuma Maelekezo ya Kurejesha')}
                </Button>
              </form>
            </>
          ) : (
            <div className="text-center py-4 space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                <CheckCircle2 className="w-6 h-6" />
              </div>

              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {t('Instructions Dispatched', 'Maelekezo Yametumwa')}
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {message}
                </p>
              </div>

              {/* Developer / Demo convenience link when running locally */}
              {devToken && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-left text-xs text-amber-900">
                  <span className="font-bold block mb-1">Local Testing Mode:</span>
                  <p className="mb-2">Click below to proceed directly with your token:</p>
                  <Link
                    to={`/reset-password?token=${devToken}`}
                    className="text-brand-blue font-bold hover:underline inline-flex items-center gap-1"
                  >
                    Set New Password <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              )}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <Link
              to="/login"
              className="text-slate-600 hover:text-brand-navy font-semibold flex items-center gap-1.5 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              {t('Back to Sign In', 'Rudi Kuingia')}
            </Link>

            <span className="text-[11px] font-medium text-emerald-600 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              {t('Secure System', 'Salama')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};