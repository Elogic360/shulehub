import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Building,
  ShieldCheck,
  Check,
  Phone,
  Mail,
  Award,
  Clock,
  Link as LinkIcon,
  Copy,
  Plus,
  Share2,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  X,
} from 'lucide-react';

export const PlatformAdminDashboard: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  // Invite Form State
  const [targetSchoolName, setTargetSchoolName] = useState('');
  const [targetContactEmail, setTargetContactEmail] = useState('');
  const [targetContactPhone, setContactPhone] = useState('');
  const [expiresInDays, setExpiresInDays] = useState(14);
  const [notes, setNotes] = useState('');
  const [inviteError, setInviteError] = useState<string | null>(null);

  const { data: schools = [], isLoading: schoolsLoading } = useQuery({
    queryKey: ['admin_schools'],
    queryFn: async () => (await api.get('/schools/all')).data,
  });

  const { data: invitations = [], isLoading: invitationsLoading } = useQuery({
    queryKey: ['school_invitations'],
    queryFn: async () => (await api.get('/auth/school-invitations')).data,
  });

  const verifyMutation = useMutation({
    mutationFn: async (schoolId: string) => api.post(`/schools/${schoolId}/verify`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin_schools'] });
    },
  });

  const createInviteMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/auth/school-invitations', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school_invitations'] });
      setIsInviteModalOpen(false);
      setTargetSchoolName('');
      setTargetContactEmail('');
      setContactPhone('');
      setNotes('');
      setInviteError(null);
    },
    onError: (err: any) => {
      setInviteError(err.response?.data?.detail || 'Imeshindikana kutengeneza kiungo cha usajili.');
    },
  });

  const handleCopyLink = (url: string, token: string) => {
    navigator.clipboard.writeText(url);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  const handleCreateInvite = (e: React.FormEvent) => {
    e.preventDefault();
    createInviteMutation.mutate({
      target_school_name: targetSchoolName || undefined,
      target_contact_email: targetContactEmail || undefined,
      target_contact_phone: targetContactPhone || undefined,
      expires_in_days: Number(expiresInDays),
      notes: notes || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Platform Super Administrator Portal', 'Dashibodi Kuu ya Msimamizi wa Mfumo')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t(
              'Manage all registered schools, private onboarding invitation links, and tenant compliance across Tanzania.',
              'Simamia shule zote zilizosajiliwa, viungo vya mwaliko wa usajili, na uthibitisho wa kisheria nchini kote.'
            )}
          </p>
        </div>

        <button
          onClick={() => setIsInviteModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-brand-teal hover:bg-teal-600 text-brand-darkNavy font-bold text-xs shadow-sm transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>{t('Generate Registration Link', 'Tengeneza Kiungo cha Usajili')}</span>
        </button>
      </div>

      {/* Overview Metric */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Total Registered Schools', 'Shule Zilizosajiliwa')}
          </span>
          <div className="text-2xl font-black text-brand-navy mt-1">
            {schools.length}
          </div>
          <span className="text-xs text-slate-500 mt-0.5 block">
            Primary & Secondary Schools
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Active Invite Links', 'Viungo vya Usajili Vilivyo Hai')}
          </span>
          <div className="text-2xl font-black text-brand-teal mt-1">
            {invitations.filter((i: any) => !i.is_used && !i.is_expired).length}
          </div>
          <span className="text-xs text-slate-500 mt-0.5 block">
            {t('Pending school onboarding', 'Zinasubiri kusajiliwa')}
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Verified Compliance', 'Shule Zilizothibitishwa')}
          </span>
          <div className="text-2xl font-black text-emerald-600 mt-1">
            {schools.filter((s: any) => s.is_verified).length}
          </div>
          <span className="text-xs text-emerald-600 font-semibold mt-0.5 block">
            PDPA 2022 Verified
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Total Students Across Tenants', 'Jumla ya Wanafunzi')}
          </span>
          <div className="text-2xl font-black text-indigo-600 mt-1">
            {schools.reduce((acc: number, curr: any) => acc + (curr.students_count || 0), 0)}
          </div>
          <span className="text-xs text-slate-500 mt-0.5 block">
            National Database Scope
          </span>
        </div>
      </div>

      {/* School Registration Invitations Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-brand-navy flex items-center gap-2">
              <LinkIcon className="w-4 h-4 text-brand-teal" />
              <span>{t('School Onboarding Invitation Links', 'Viungo vya Mwaliko wa Usajili wa Shule')}</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {t(
                'Schools can only register using these authorized links. The public register button is hidden from unauthorized visitors.',
                'Shule zinaweza kusajiliwa kupitia viungo hivi pekee. Sehemu ya kujisajili hadharani imefichwa kwenye ukurasa wa kuingia.'
              )}
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t('Target School / Recipient', 'Mlengwa / Shule')}</th>
                <th className="px-5 py-3">{t('Status', 'Hali')}</th>
                <th className="px-5 py-3">{t('Expires At', 'Mwisho')}</th>
                <th className="px-5 py-3">{t('Shareable Link', 'Kiungo cha Usajili')}</th>
                <th className="px-5 py-3 text-right">{t('Action', 'Hatua')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {invitations.map((inv: any) => {
                const isPending = !inv.is_used && !inv.is_expired;
                return (
                  <tr key={inv.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-5 py-3.5">
                      <span className="font-bold text-xs text-brand-navy block">
                        {inv.target_school_name || t('Open Invitation', 'Mwaliko Wazi')}
                      </span>
                      <span className="text-[11px] text-slate-400 block">
                        {inv.target_contact_email || inv.target_contact_phone || 'Hakuna mawasiliano ya awali'}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      {inv.is_used ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                          <Check className="w-3 h-3 text-emerald-600" />
                          <span>{t('Used', 'Imetumika')}</span>
                        </span>
                      ) : inv.is_expired ? (
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-100 text-rose-800">
                          {t('Expired', 'Imekwisha')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                          <Clock className="w-3 h-3 text-emerald-600" />
                          <span>{t('Active', 'Inasubiri')}</span>
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">
                      {new Date(inv.expires_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-[11px] font-mono text-slate-500 truncate max-w-xs block">
                        {inv.invitation_url}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {isPending && (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleCopyLink(inv.invitation_url, inv.token)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
                          >
                            {copiedToken === inv.token ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                <span className="text-emerald-700">{t('Copied!', 'Imenakiliwa!')}</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5 text-slate-500" />
                                <span>{t('Copy Link', 'Nakili')}</span>
                              </>
                            )}
                          </button>

                          <a
                            href={`https://wa.me/?text=${encodeURIComponent(
                              `Habari, tumia kiungo hiki rasmi kusajili shule yako kwenye ShuleConnect: ${inv.invitation_url}`
                            )}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition"
                          >
                            <Share2 className="w-3.5 h-3.5" />
                            <span>WhatsApp</span>
                          </a>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}

              {invitations.length === 0 && !invitationsLoading && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-xs text-slate-400">
                    {t(
                      'No registration links generated yet. Click "Generate Registration Link" above to onboard a school.',
                      'Bado hakuna viungo vya usajili vilivyotengenezwa. Bonyeza "Tengeneza Kiungo cha Usajili" hapo juu kuikaribisha shule.'
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Schools Roster Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-brand-navy">
            {t('All Registered School Tenants', 'Orodha ya Shule Zote Zilizosajiliwa')}
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t('School Code & Name', 'Kifupi na Jina la Shule')}</th>
                <th className="px-5 py-3">{t('Category', 'Aina')}</th>
                <th className="px-5 py-3">{t('Contact Person', 'Mawasiliano')}</th>
                <th className="px-5 py-3">{t('Students', 'Wanafunzi')}</th>
                <th className="px-5 py-3">{t('Verification', 'Uthibitisho')}</th>
                <th className="px-5 py-3">{t('Action', 'Hatua')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {schools.map((s: any) => (
                <tr key={s.id} className="hover:bg-slate-50/60 transition">
                  <td className="px-5 py-3.5">
                    <span className="font-bold text-xs text-brand-navy block">
                      {s.name}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono block">
                      CODE: {s.code}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs font-semibold text-slate-700">
                    {s.school_type}
                  </td>
                  <td className="px-5 py-3.5 text-xs">
                    <span className="text-slate-800 font-medium block">{s.contact_email}</span>
                    <span className="text-slate-400 font-mono text-[11px] block">{s.contact_phone}</span>
                  </td>
                  <td className="px-5 py-3.5 text-xs font-bold text-brand-navy">
                    {s.students_count || 0}
                  </td>
                  <td className="px-5 py-3.5">
                    {s.is_verified ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                        <Check className="w-3 h-3" />
                        <span>Verified</span>
                      </span>
                    ) : (
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800">
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    {!s.is_verified && (
                      <button
                        onClick={() => verifyMutation.mutate(s.id)}
                        disabled={verifyMutation.isPending}
                        className="px-2.5 py-1 rounded bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition"
                      >
                        {t('Verify School', 'Thibitisha Shule')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {schools.length === 0 && !schoolsLoading && (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-xs text-slate-400">
                    {t('No schools registered yet.', 'Bado hakuna shule zilizosajiliwa.')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generate Invitation Modal */}
      {isInviteModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-100 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 bg-brand-navy text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <LinkIcon className="w-4 h-4 text-brand-teal" />
                <h3 className="text-sm font-bold">
                  {t('Generate School Registration Link', 'Tengeneza Kiungo cha Usajili wa Shule')}
                </h3>
              </div>
              <button
                onClick={() => setIsInviteModalOpen(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateInvite} className="p-6 space-y-4">
              {inviteError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
                  {inviteError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Target School Name (Optional)', 'Jina la Shule Tarajiwa (Sio Lazima)')}
                </label>
                <input
                  type="text"
                  value={targetSchoolName}
                  onChange={(e) => setTargetSchoolName(e.target.value)}
                  placeholder="e.g. St. Jude Academy"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Contact Email', 'Barua Pepe')}
                  </label>
                  <input
                    type="email"
                    value={targetContactEmail}
                    onChange={(e) => setTargetContactEmail(e.target.value)}
                    placeholder="headmaster@school.tz"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Contact Phone', 'Namba ya Simu')}
                  </label>
                  <input
                    type="text"
                    value={targetContactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    placeholder="0754112233"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Link Valid For (Days)', 'Uhai wa Kiungo (Siku)')}
                </label>
                <select
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white"
                >
                  <option value={7}>{t('7 Days (One Week)', 'Siku 7 (Wiki 1)')}</option>
                  <option value={14}>{t('14 Days (Two Weeks)', 'Siku 14 (Wiki 2)')}</option>
                  <option value={30}>{t('30 Days (One Month)', 'Siku 30 (Mwezi 1)')}</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Internal Notes (Optional)', 'Maelezo ya Ndani (Sio Lazima)')}
                </label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Maelezo maalum kuhusu shule hii..."
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsInviteModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={createInviteMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-bold transition flex items-center gap-1.5 shadow"
                >
                  {createInviteMutation.isPending
                    ? t('Generating...', 'Inatengeneza...')
                    : t('Create Shareable Link', 'Tengeneza Kiungo')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
