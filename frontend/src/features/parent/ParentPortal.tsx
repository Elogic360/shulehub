import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  GraduationCap,
  Award,
  Receipt,
  Calendar,
  Bell,
  CheckCircle2,
  XCircle,
  Phone,
  ShieldCheck,
} from 'lucide-react';

export const ParentPortal: React.FC = () => {
  const { t, user } = useAuth();
  const queryClient = useQueryClient();

  const { data: portal, isLoading } = useQuery({
    queryKey: ['parent_portal_summary'],
    queryFn: async () => (await api.get('/parents/portal/summary')).data,
  });

  const rsvpMutation = useMutation({
    mutationFn: async ({ invitationId, status }: { invitationId: string; status: string }) => {
      return api.post('/meetings/respond', {
        invitation_id: invitationId,
        response_status: status,
        channel: 'PORTAL',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parent_portal_summary'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-brand-navy to-slate-900 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-brand-teal uppercase tracking-wider block">
            {t('Parent & Guardian Portal', 'Mlango wa Mzazi na Mlezi')}
          </span>
          <h1 className="text-2xl font-black mt-1">
            {t('Welcome,', 'Karibu,')} {portal?.guardian_name || user?.full_name}
          </h1>
          <p className="text-xs text-slate-300 mt-1 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-brand-teal" />
            <span>Simu: {portal?.phone_number || user?.phone_number} &bull; Personal Data Protected (PDPA 2022)</span>
          </p>
        </div>

        <div className="px-4 py-2 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 text-right">
          <span className="text-[11px] text-slate-300 block">{t('USSD Access Code', 'Namba ya USSD')}</span>
          <span className="text-base font-black text-brand-teal tracking-wider">*384*55#</span>
        </div>
      </div>

      {/* Children Section */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold text-brand-navy uppercase tracking-wider">
          {t('My Enrolled Children', 'Watoto Wangu Shuleni')}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {portal?.children?.map((child: any) => (
            <div key={child.student_id} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-bold text-brand-teal uppercase tracking-wider block">
                    {child.school_name} &bull; {child.class_name}
                  </span>
                  <h3 className="text-lg font-bold text-brand-navy mt-0.5">
                    {child.full_name}
                  </h3>
                  <span className="text-xs text-slate-400 font-mono">
                    Namba: {child.admission_number}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600">
                  <GraduationCap className="w-5 h-5" />
                </div>
              </div>

              {/* Fee Outstanding Summary */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                    {t('Fee Balance Due', 'Baki ya Ada')}
                  </span>
                  <span className="text-base font-black text-rose-600">
                    TZS {Number(child.outstanding_fee_tzs).toLocaleString()}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">{t('Fee Payer Status', 'Hali ya Mlipaji')}</span>
                  <span className="text-xs font-bold text-emerald-600">Active Guardian</span>
                </div>
              </div>

              {/* Exam Results Table */}
              <div>
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-amber-500" />
                  <span>{t('Published Academic Results', 'Matokeo Rasmi ya Mitihani')}</span>
                </span>

                {child.exam_results?.length > 0 ? (
                  <div className="border border-slate-100 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-[10px] text-slate-400 uppercase font-bold">
                        <tr>
                          <th className="px-3 py-2">{t('Subject', 'Somo')}</th>
                          <th className="px-3 py-2">{t('Score', 'Alama')}</th>
                          <th className="px-3 py-2">{t('Grade', 'Daraja')}</th>
                          <th className="px-3 py-2">{t('Remarks', 'Maoni')}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {child.exam_results.map((res: any, idx: number) => (
                          <tr key={idx}>
                            <td className="px-3 py-2 font-medium text-slate-800">{res.subject}</td>
                            <td className="px-3 py-2 font-bold text-brand-navy">{res.score}%</td>
                            <td className="px-3 py-2">
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                {res.grade}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-slate-500 text-[11px]">{res.remarks}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <span className="text-xs text-slate-400 italic block py-2">
                    {t('No published results yet for this term.', 'Bado hakuna matokeo yaliyotangazwa kwa muhula huu.')}
                  </span>
                )}
              </div>
            </div>
          ))}

          {(!portal?.children || portal.children.length === 0) && !isLoading && (
            <div className="col-span-2 bg-white p-8 rounded-2xl border border-slate-200 text-center text-xs text-slate-400">
              {t('No student profile is currently linked to your telephone number.', 'Hakuna mwanafunzi aliyeunganishwa na namba yako ya simu bado.')}
            </div>
          )}
        </div>
      </div>

      {/* Announcements & Meeting Invitations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Announcements */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Bell className="w-3.5 h-3.5 text-brand-teal" />
            <span>{t('School Announcements', 'Matangazo ya Shule')}</span>
          </h2>

          <div className="divide-y divide-slate-100">
            {portal?.announcements?.map((a: any) => (
              <div key={a.id} className="py-3 space-y-1">
                <span className="text-xs font-bold text-brand-navy block">{a.title}</span>
                <p className="text-xs text-slate-600 leading-relaxed">{a.content}</p>
                <span className="text-[10px] text-slate-400 block">{a.published_at?.split('T')[0]}</span>
              </div>
            ))}
            {(!portal?.announcements || portal.announcements.length === 0) && (
              <span className="text-xs text-slate-400 py-3 block text-center">Hakuna matangazo mapya</span>
            )}
          </div>
        </div>

        {/* Meeting Invitations & Interactive RSVP */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-violet-500" />
            <span>{t('Parent-Teacher Meetings & RSVPs', 'Mialiko ya Mikutano ya Wazazi')}</span>
          </h2>

          <div className="space-y-3">
            {portal?.meetings?.map((m: any) => (
              <div key={m.invitation_id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-xs font-bold text-brand-navy">{m.title}</h4>
                    <span className="text-[11px] text-slate-500 block">
                      {m.meeting_date} &bull; Saa {m.start_time} &bull; {m.venue}
                    </span>
                  </div>

                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    m.response_status === 'CONFIRMED'
                      ? 'bg-emerald-100 text-emerald-800'
                      : m.response_status === 'DECLINED'
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-slate-200 text-slate-700'
                  }`}>
                    {m.response_status}
                  </span>
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => rsvpMutation.mutate({ invitationId: m.invitation_id, status: 'CONFIRMED' })}
                    disabled={rsvpMutation.isPending}
                    className="flex-1 py-1 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center justify-center gap-1"
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{t('I will attend', 'Nitahudhuria')}</span>
                  </button>
                  <button
                    onClick={() => rsvpMutation.mutate({ invitationId: m.invitation_id, status: 'DECLINED' })}
                    disabled={rsvpMutation.isPending}
                    className="flex-1 py-1 px-3 rounded-lg bg-slate-200 hover:bg-rose-100 hover:text-rose-700 text-slate-700 text-xs font-bold transition flex items-center justify-center gap-1"
                  >
                    <XCircle className="w-3 h-3" />
                    <span>{t('Decline', 'Sitahudhuria')}</span>
                  </button>
                </div>
              </div>
            ))}
            {(!portal?.meetings || portal.meetings.length === 0) && (
              <span className="text-xs text-slate-400 py-3 block text-center">Hakuna mialiko ya mikutano kwa sasa</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
