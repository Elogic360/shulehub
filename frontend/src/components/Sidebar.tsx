import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Layers,
  Users,
  GraduationCap,
  MessageSquare,
  FileSpreadsheet,
  Receipt,
  Calendar,
  Settings,
  ShieldAlert,
  UserCheck,
  Building,
  Award,
  Smartphone,
  Upload,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { activeRole, t } = useAuth();

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
      isActive
        ? 'bg-brand-navy text-white shadow-sm font-semibold'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
    }`;

  return (
    <aside className="w-64 bg-white border-r border-slate-200/90 flex flex-col min-h-[calc(100vh-4rem)] p-4 shrink-0">
      <nav className="flex-1 space-y-1.5">
        {/* ================= SUPER ADMIN NAVIGATION ================= */}
        {activeRole === 'SUPER_ADMIN' && (
          <>
            <div className="px-3 py-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              {t('Platform Control', 'Usimamizi wa Mfumo')}
            </div>
            <NavLink to="/admin" end className={navItemClass}>
              <LayoutDashboard className="w-4 h-4 text-brand-teal" />
              <span>{t('Platform Overview', 'Dashibodi Kuu')}</span>
            </NavLink>
            <NavLink to="/admin/schools" className={navItemClass}>
              <Building className="w-4 h-4 text-brand-accent" />
              <span>{t('Schools Verification', 'Uthibitisho wa Shule')}</span>
            </NavLink>
          </>
        )}

        {/* ================= SCHOOL OWNER & ADMIN NAVIGATION ================= */}
        {(activeRole === 'SCHOOL_OWNER' || activeRole === 'SCHOOL_ADMIN') && (
          <>
            <div className="px-3 py-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              {t('School Management', 'Usimamizi wa Shule')}
            </div>
            <NavLink to="/owner" end className={navItemClass}>
              <LayoutDashboard className="w-4 h-4 text-brand-teal" />
              <span>{t('Dashboard', 'Dashibodi')}</span>
            </NavLink>
            <NavLink to="/owner/academic" className={navItemClass}>
              <Layers className="w-4 h-4 text-indigo-500" />
              <span>{t('Academic Structure', 'Muundo wa Masomo')}</span>
            </NavLink>
            <NavLink to="/owner/staff" className={navItemClass}>
              <UserCheck className="w-4 h-4 text-emerald-500" />
              <span>{t('Staff & Teachers', 'Walimu na Wafanyakazi')}</span>
            </NavLink>
            <NavLink to="/owner/students" className={navItemClass}>
              <GraduationCap className="w-4 h-4 text-blue-500" />
              <span>{t('Students & Guardians', 'Wanafunzi na Wazazi')}</span>
            </NavLink>

            <div className="pt-3 px-3 py-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              {t('Operations', 'Uendeshaji')}
            </div>
            <NavLink to="/owner/communication" className={navItemClass}>
              <MessageSquare className="w-4 h-4 text-brand-teal" />
              <span>{t('Communication', 'Mawasiliano na SMS')}</span>
            </NavLink>
            <NavLink to="/owner/examinations" className={navItemClass}>
              <FileSpreadsheet className="w-4 h-4 text-amber-500" />
              <span>{t('Examinations', 'Mitihani na Matokeo')}</span>
            </NavLink>
            <NavLink to="/owner/fees" className={navItemClass}>
              <Receipt className="w-4 h-4 text-emerald-600" />
              <span>{t('School Fees', 'Usimamizi wa Ada')}</span>
            </NavLink>
            <NavLink to="/owner/meetings" className={navItemClass}>
              <Calendar className="w-4 h-4 text-violet-500" />
              <span>{t('Meetings', 'Mikutano ya Wazazi')}</span>
            </NavLink>
            <NavLink to="/imports" className={navItemClass}>
              <Upload className="w-4 h-4 text-teal-600" />
              <span>{t('Excel Import Center', 'Kituo cha Excel & CSV')}</span>
            </NavLink>
            <NavLink to="/necta" className={navItemClass}>
              <Award className="w-4 h-4 text-amber-500" />
              <span>{t('NECTA Results', 'Matokeo ya NECTA')}</span>
            </NavLink>
          </>
        )}

        {/* ================= CLASS TEACHER NAVIGATION ================= */}
        {activeRole === 'CLASS_TEACHER' && (
          <>
            <div className="px-3 py-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              {t('Class Workspace', 'Darasani Kwangu')}
            </div>
            <NavLink to="/teacher" end className={navItemClass}>
              <LayoutDashboard className="w-4 h-4 text-brand-teal" />
              <span>{t('Class Dashboard', 'Dashibodi ya Darasa')}</span>
            </NavLink>
            <NavLink to="/teacher/students" className={navItemClass}>
              <GraduationCap className="w-4 h-4 text-blue-500" />
              <span>{t('My Students', 'Wanafunzi Wangu')}</span>
            </NavLink>
            <NavLink to="/teacher/communication" className={navItemClass}>
              <MessageSquare className="w-4 h-4 text-brand-teal" />
              <span>{t('Send Messages', 'Tuma Ujumbe kwa Wazazi')}</span>
            </NavLink>
            <NavLink to="/teacher/examinations" className={navItemClass}>
              <FileSpreadsheet className="w-4 h-4 text-amber-500" />
              <span>{t('Marks & Results', 'Pakia na Tangaza Matokeo')}</span>
            </NavLink>
            <NavLink to="/teacher/fees" className={navItemClass}>
              <Receipt className="w-4 h-4 text-emerald-600" />
              <span>{t('Fee Reminders', 'Kikumbusho cha Ada')}</span>
            </NavLink>
            <NavLink to="/teacher/meetings" className={navItemClass}>
              <Calendar className="w-4 h-4 text-violet-500" />
              <span>{t('Class Meetings', 'Mikutano ya Darasa')}</span>
            </NavLink>
            <NavLink to="/imports" className={navItemClass}>
              <Upload className="w-4 h-4 text-teal-600" />
              <span>{t('Excel Import Center', 'Kituo cha Excel & CSV')}</span>
            </NavLink>
          </>
        )}

        {/* ================= PARENT PORTAL NAVIGATION ================= */}
        {activeRole === 'PARENT' && (
          <>
            <div className="px-3 py-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              {t('Parent Portal', 'Mlango wa Mzazi')}
            </div>
            <NavLink to="/parent" end className={navItemClass}>
              <GraduationCap className="w-4 h-4 text-brand-teal" />
              <span>{t('My Children', 'Watoto Wangu')}</span>
            </NavLink>
          </>
        )}
      </nav>

      {/* Footer Info */}
      <div className="pt-4 mt-auto border-t border-slate-100 text-xs text-slate-400 text-center">
        <span>ShuleConnect Tanzania &copy; 2026</span>
      </div>
    </aside>
  );
};
