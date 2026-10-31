import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  GraduationCap,
  MessageSquare,
  FileSpreadsheet,
  Receipt,
  Calendar,
  Users,
  Send,
  PlusCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const TeacherDashboard: React.FC = () => {
  const { t, user } = useAuth();
  const [selectedClassId, setSelectedClassId] = useState<string>('');

  const { data: classes = [], isLoading: loadingClasses } = useQuery({
    queryKey: ['teacher_assigned_classes'],
    queryFn: async () => {
      const res = await api.get('/academic/classes');
      if (res.data.length > 0 && !selectedClassId) {
        setSelectedClassId(res.data[0].id);
      }
      return res.data;
    },
  });

  const activeClass = classes.find((c: any) => c.id === selectedClassId) || classes[0];

  const { data: students = [] } = useQuery({
    queryKey: ['class_students', selectedClassId],
    queryFn: async () => {
      if (!selectedClassId) return [];
      return (await api.get(`/students?class_group_id=${selectedClassId}`)).data;
    },
    enabled: !!selectedClassId,
  });

  const { data: campaigns = [] } = useQuery({
    queryKey: ['class_campaigns', selectedClassId],
    queryFn: async () => {
      if (!selectedClassId) return [];
      return (await api.get(`/communication?class_group_id=${selectedClassId}`)).data;
    },
    enabled: !!selectedClassId,
  });

  return (
    <div className="space-y-6">
      {/* Top Banner with Class Selector */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-brand-teal uppercase tracking-wider block">
            {t('Class Teacher Workspace', 'Darasani Kwangu')}
          </span>
          <h1 className="text-xl font-bold text-brand-navy mt-0.5">
            {user?.full_name} &mdash; {activeClass?.name || t('Assigned Class', 'Darasa Lililopangwa')}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {user?.school_name} &bull; Stream: {activeClass?.stream || 'A'}
          </p>
        </div>

        {classes.length > 1 && (
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-600">
              {t('Switch Class:', 'Badili Darasa:')}
            </label>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
            >
              {classes.map((cls: any) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Class Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              {t('Enrolled Students', 'Wanafunzi Darasani')}
            </span>
            <div className="text-2xl font-black text-brand-navy mt-1">
              {students.length}
            </div>
            <span className="text-xs text-slate-500">
              Uwezo wa darasa: {activeClass?.capacity || 50}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-blue-50 text-blue-600">
            <GraduationCap className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              {t('Parent Messages Sent', 'Ujumbe Uliotumwa')}
            </span>
            <div className="text-2xl font-black text-brand-navy mt-1">
              {campaigns.length}
            </div>
            <span className="text-xs text-emerald-600 font-semibold">
              Bulk, Selected & Individual
            </span>
          </div>
          <div className="p-3 rounded-xl bg-brand-teal/15 text-brand-teal">
            <MessageSquare className="w-6 h-6 text-brand-navy" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              {t('Quick Actions', 'Hatua za Haraka')}
            </span>
            <div className="flex gap-2 mt-2">
              <Link
                to="/teacher/communication"
                className="px-3 py-1.5 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-bold shadow-sm transition flex items-center gap-1"
              >
                <Send className="w-3 h-3 text-brand-teal" />
                <span>{t('Send SMS', 'Tuma SMS')}</span>
              </Link>
              <Link
                to="/teacher/examinations"
                className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold shadow-sm transition flex items-center gap-1"
              >
                <FileSpreadsheet className="w-3 h-3" />
                <span>{t('Marks', 'Matokeo')}</span>
              </Link>
            </div>
          </div>
          <div className="p-3 rounded-xl bg-slate-100 text-slate-600">
            <Users className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Class Students Overview Preview */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-brand-navy">
              {t('My Students Roster', 'Orodha ya Wanafunzi wa Darasa')}
            </h2>
            <span className="text-xs text-slate-400">
              {students.length} {t('registered students', 'wanafunzi waliosajiliwa')}
            </span>
          </div>

          <Link
            to="/teacher/students"
            className="text-xs font-bold text-brand-teal hover:underline flex items-center gap-1"
          >
            <span>{t('View All & Add', 'Tazama Wote & Ongeza')}</span>
            <PlusCircle className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t('Adm #', 'Namba ya Usajili')}</th>
                <th className="px-5 py-3">{t('Student Name', 'Jina la Mwanafunzi')}</th>
                <th className="px-5 py-3">{t('Gender', 'Jinsia')}</th>
                <th className="px-5 py-3">{t('Primary Guardian & Contact', 'Mzazi / Mlezi na Simu')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {students.slice(0, 5).map((st: any) => (
                <tr key={st.id} className="hover:bg-slate-50/60 transition">
                  <td className="px-5 py-3.5 font-bold text-xs text-brand-navy">
                    {st.admission_number}
                  </td>
                  <td className="px-5 py-3.5 text-xs font-semibold text-slate-800">
                    {st.first_name} {st.last_name}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-500">
                    {st.gender}
                  </td>
                  <td className="px-5 py-3.5 text-xs">
                    {st.guardians?.[0] ? (
                      <div>
                        <span className="font-semibold text-slate-800 block">
                          {st.guardians[0].full_name} ({st.guardians[0].relationship})
                        </span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          {st.guardians[0].primary_phone}
                        </span>
                      </div>
                    ) : (
                      <span className="text-rose-500 italic">Hana mlezi</span>
                    )}
                  </td>
                </tr>
              ))}
              {students.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-5 py-8 text-center text-xs text-slate-400">
                    {t('No students in this class yet. Click "Add Student" to enroll.', 'Hakuna wanafunzi kwenye darasa hili bado.')}
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
