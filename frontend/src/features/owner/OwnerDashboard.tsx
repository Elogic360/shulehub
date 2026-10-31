import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Users,
  GraduationCap,
  MessageSquare,
  Receipt,
  Layers,
  Calendar,
  TrendingUp,
  ArrowUpRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const OwnerDashboard: React.FC = () => {
  const { t, user } = useAuth();

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['school_analytics'],
    queryFn: async () => {
      const res = await api.get('/schools/analytics');
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('School Operations Dashboard', 'Dashibodi ya Usimamizi wa Shule')}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {user?.school_name} — {t('Overview of students, communication and finances', 'Muhtasari wa wanafunzi, mawasiliano na ada')}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/owner/communication"
            className="px-3.5 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <MessageSquare className="w-3.5 h-3.5 text-brand-teal" />
            <span>{t('New Announcement', 'Tangazo Jipya')}</span>
          </Link>
          <Link
            to="/owner/fees"
            className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Receipt className="w-3.5 h-3.5" />
            <span>{t('Record Payment', 'Rekodi Malipo ya Ada')}</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Students */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              {t('Active Students', 'Wanafunzi')}
            </span>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <GraduationCap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-brand-navy mt-2">
            {isLoading ? '...' : analytics?.students_count || 0}
          </div>
          <span className="text-xs text-slate-400 mt-1 block">
            {analytics?.classes_count || 0} {t('Class Groups', 'Madarasa')}
          </span>
        </div>

        {/* Guardians */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              {t('Registered Guardians', 'Wazazi / Walezi')}
            </span>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-brand-navy mt-2">
            {isLoading ? '...' : analytics?.guardians_count || 0}
          </div>
          <span className="text-xs text-slate-400 mt-1 block">
            {t('E.164 SMS Verified', 'Namba za Simu Zilizohakikiwa')}
          </span>
        </div>

        {/* SMS Expenditure */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              {t('SMS Dispatched', 'Mawasiliano na SMS')}
            </span>
            <div className="p-2 rounded-lg bg-brand-teal/15 text-brand-teal">
              <MessageSquare className="w-4 h-4 text-brand-navy" />
            </div>
          </div>
          <div className="text-2xl font-black text-brand-navy mt-2">
            {isLoading ? '...' : analytics?.campaigns_count || 0}
          </div>
          <span className="text-xs text-slate-400 mt-1 block">
            TZS {Number(analytics?.total_sms_expenditure_tzs || 0).toLocaleString()} {t('Cost', 'Gharama')}
          </span>
        </div>

        {/* Fee Collection */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              {t('Fee Collection', 'Makusanyo ya Ada')}
            </span>
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <Receipt className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-emerald-600 mt-2">
            TZS {Number(analytics?.total_fees_collected_tzs || 0).toLocaleString()}
          </div>
          <span className="text-xs text-slate-400 mt-1 block">
            Baki: TZS {Number(analytics?.total_fees_outstanding_tzs || 0).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Link
          to="/owner/academic"
          className="bg-white p-5 rounded-xl border border-slate-200 hover:border-brand-teal hover:shadow-md transition group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-lg bg-slate-100 text-brand-navy group-hover:bg-brand-navy group-hover:text-white transition">
              <Layers className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-brand-teal transition" />
          </div>
          <h3 className="text-base font-bold text-brand-navy mt-3">
            {t('Academic Setup', 'Muundo wa Masomo na Madarasa')}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {t('Manage academic years, terms, levels and assign class teachers.', 'Weka miaka ya masomo, mihula na panga walimu wa madarasa.')}
          </p>
        </Link>

        <Link
          to="/owner/students"
          className="bg-white p-5 rounded-xl border border-slate-200 hover:border-brand-teal hover:shadow-md transition group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-lg bg-slate-100 text-brand-navy group-hover:bg-brand-navy group-hover:text-white transition">
              <GraduationCap className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-brand-teal transition" />
          </div>
          <h3 className="text-base font-bold text-brand-navy mt-3">
            {t('Students & Rosters', 'Orodha ya Wanafunzi na Wazazi')}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {t('Register students, import rosters via Excel/CSV, link guardian contacts.', 'Sajili wanafunzi, pakia faili la Excel/CSV, unganisha wazazi.')}
          </p>
        </Link>

        <Link
          to="/owner/fees"
          className="bg-white p-5 rounded-xl border border-slate-200 hover:border-brand-teal hover:shadow-md transition group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-lg bg-slate-100 text-brand-navy group-hover:bg-brand-navy group-hover:text-white transition">
              <Receipt className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-brand-teal transition" />
          </div>
          <h3 className="text-base font-bold text-brand-navy mt-3">
            {t('Fee Structures & Reminders', 'Usimamizi wa Ada na Vikumbusho')}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {t('Define term fees, invoices, record bank payments and schedule SMS reminders.', 'Panga ada za muhula, toa ankara na ratibu vikumbusho vya SMS.')}
          </p>
        </Link>
      </div>
    </div>
  );
};
