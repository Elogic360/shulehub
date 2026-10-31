import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Building, ShieldCheck, Check, Phone, Mail, Award, Clock } from 'lucide-react';

export const PlatformAdminDashboard: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const { data: schools = [], isLoading } = useQuery({
    queryKey: ['admin_schools'],
    queryFn: async () => (await api.get('/schools/all')).data,
  });

  const verifyMutation = useMutation({
    mutationFn: async (schoolId: string) => api.post(`/schools/${schoolId}/verify`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin_schools'] });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Platform Super Administrator Portal', 'Dashibodi Kuu ya Msimamizi wa Mfumo')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Manage all registered schools, compliance verification, and tenant quotas across Tanzania.', 'Simamia shule zote zilizosajiliwa, uthibitisho wa kisheria na viwango vya matumizi.')}
          </p>
        </div>
      </div>

      {/* Overview Metric */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
              {schools.length === 0 && !isLoading && (
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
    </div>
  );
};
