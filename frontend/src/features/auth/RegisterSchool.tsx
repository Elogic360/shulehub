import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import {
  Building,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Mail,
  Lock,
  Phone,
  User,
  Globe,
  Loader2,
  Eye,
  EyeOff,
  Home,
} from 'lucide-react';

export const RegisterSchool: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login, language, setLanguage, t } = useAuth();

  const token = searchParams.get('token') || '';

  const [validating, setValidating] = useState(true);
  const [isValidToken, setIsValidToken] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Form states
  const [schoolName, setSchoolName] = useState('');
  const [schoolCode, setSchoolCode] = useState('');
  const [schoolType, setSchoolType] = useState('PRIMARY');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setValidating(false);
        setIsValidToken(false);
        setValidationError(
          t(
            'Missing invitation token. School registration requires an authorized invitation link.',
            'Huna kiungo cha mwaliko. Usajili wa shule unahitaji kiungo rasmi cha mwaliko kutoka kwa Msimamizi Mkuu.'
          )
        );
        return;
      }

      try {
        const res = await api.get(`/auth/school-invitations/validate?token=${encodeURIComponent(token)}`);
        setIsValidToken(true);
        if (res.data.target_school_name) setSchoolName(res.data.target_school_name);
        if (res.data.target_contact_email) setContactEmail(res.data.target_contact_email);
        if (res.data.target_contact_phone) setContactPhone(res.data.target_contact_phone);
      } catch (err: any) {
        setIsValidToken(false);
        setValidationError(
          err.response?.data?.detail ||
            t(
              'Invalid, expired, or already used registration link.',
              'Kiungo hiki cha usajili si sahihi, kimekwisha muda wake, au kimeshatumika tayari.'
            )
        );
      } finally {
        setValidating(false);
      }
    };

    validateToken();
  }, [token, t]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);

    try {
      const res = await api.post('/auth/register-school', {
        school_name: schoolName,
        school_code: schoolCode.toUpperCase(),
        school_type: schoolType,
        contact_email: contactEmail,
        contact_phone: contactPhone,
        owner_full_name: ownerName,
        owner_password: ownerPassword,
        region: 'Dar es Salaam',
        invitation_token: token,
      });

      login(res.data.access_token, res.data.user);
      navigate('/owner');
    } catch (err: any) {
      setFormError(
        err.response?.data?.detail ||
          t('Registration failed. Please review your details.', 'Usajili umeshindikana. Tafadhali hakiki taarifa zako.')
      );
    } finally {
      setSubmitting(false);
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

      <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden my-8">
        {/* Header Banner */}
        <div className="bg-brand-navy p-6 text-center border-b border-slate-800">
          <div className="w-12 h-12 mx-auto rounded-xl bg-brand-teal/20 border border-brand-teal/40 flex items-center justify-center text-brand-teal font-black text-2xl mb-3">
            S
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Shule<span className="text-brand-teal">Hub</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {t('Official School Registration Portal', 'Mfumo Rasmi wa Usajili wa Shule')}
          </p>
        </div>

        {validating ? (
          <div className="p-12 text-center space-y-4">
            <Loader2 className="w-8 h-8 text-brand-teal animate-spin mx-auto" />
            <p className="text-xs text-slate-500 font-medium">
              {t('Verifying registration invitation...', 'Inahakiki kiungo cha mwaliko wa usajili...')}
            </p>
          </div>
        ) : !isValidToken ? (
          /* Invalid or Missing Token State */
          <div className="p-8 text-center space-y-5">
            <div className="w-14 h-14 mx-auto rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
              <AlertTriangle className="w-7 h-7" />
            </div>

            <div>
              <h2 className="text-base font-bold text-slate-800">
                {t('Unauthorized Registration Access', 'Ufikiaji wa Usajili Hauna Idhini')}
              </h2>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed max-w-md mx-auto">
                {validationError}
              </p>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-left text-xs text-slate-600 space-y-2">
              <span className="font-bold text-slate-800 block">
                {t('How to register a school:', 'Jinsi ya kusajili shule:')}
              </span>
              <p>
                {t(
                  '1. School onboarding on ShuleHub is private and invite-only.',
                  '1. Usajili wa shule unafanyika kwa mwaliko maalum pekee.'
                )}
              </p>
              <p>
                {t(
                  '2. Contact ShuleHub Super Administrators to obtain an official onboarding link.',
                  '2. Wasiliana na Uongozi Mkuu wa ShuleHub kupata kiungo rasmi cha usajili.'
                )}
              </p>
            </div>

            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-lg bg-brand-navy hover:bg-slate-800 text-white font-semibold text-xs shadow-md transition"
            >
              <ArrowRight className="w-4 h-4 text-brand-teal" />
              {t('Return to Sign In', 'Rudi Kuingia Kwenye Akaunti')}
            </Link>
          </div>
        ) : (
          /* Valid Token: Authorized School Registration Form */
          <div className="p-6">
            <div className="mb-5 p-3 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold text-emerald-900 block">
                  {t('Verified Invitation Link', 'Mwaliko Uliothibitishwa')}
                </span>
                <span className="text-[11px] text-emerald-700 block mt-0.5">
                  {t(
                    'You are authorized to register a new school tenant on ShuleHub.',
                    'Umeidhinishwa kusajili shule mpya kwenye mfumo wa ShuleHub.'
                  )}
                </span>
              </div>
            </div>

            {formError && (
              <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('School Name', 'Jina la Shule')}
                </label>
                <div className="relative">
                  <Building className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={schoolName}
                    onChange={(e) => setSchoolName(e.target.value)}
                    placeholder="e.g. Feza Primary School"
                    className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
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
                    {t('Official Email', 'Barua Pepe ya Shule')}
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="email"
                      required
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      placeholder="info@school.ac.tz"
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Mobile Phone', 'Namba ya Simu')}
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
                      placeholder="0712345678"
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <span className="text-xs font-bold text-brand-navy block mb-3 uppercase tracking-wider">
                  {t('Administrator & Owner Account', 'Akaunti ya Mmiliki / Mkuu wa Shule')}
                </span>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      {t('Owner Full Name', 'Jina Kamili la Mmiliki / Mkuu')}
                    </label>
                    <div className="relative">
                      <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                      <input
                        type="text"
                        required
                        value={ownerName}
                        onChange={(e) => setOwnerName(e.target.value)}
                        placeholder="Mwalimu Godfrey Mallya"
                        className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      {t('Owner Password', 'Nenosiri la Mmiliki')}
                    </label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        required
                        minLength={8}
                        value={ownerPassword}
                        onChange={(e) => setOwnerPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full pl-9 pr-10 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
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
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-4 py-2.5 px-4 rounded-lg bg-brand-navy hover:bg-slate-800 text-white font-semibold text-sm shadow-md transition flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 text-brand-teal animate-spin" />
                    <span>{t('Registering School...', 'Inasajili Shule...')}</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-brand-teal" />
                    <span>{t('Complete School Registration', 'Kamilisha Usajili wa Shule')}</span>
                  </>
                )}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};