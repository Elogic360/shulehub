import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const routeNameMap: Record<string, { en: string; sw: string }> = {
  admin: { en: 'Platform Administration', sw: 'Utawala wa Mfumo' },
  schools: { en: 'School Verification', sw: 'Uthibitisho wa Shule' },
  owner: { en: 'School Workspace', sw: 'Usimamizi wa Shule' },
  academic: { en: 'Academic Structure', sw: 'Muundo wa Masomo' },
  staff: { en: 'Staff & Teachers', sw: 'Walimu na Wafanyakazi' },
  students: { en: 'Students & Guardians', sw: 'Wanafunzi na Wazazi' },
  communication: { en: 'Communication & SMS', sw: 'Mawasiliano na SMS' },
  examinations: { en: 'Examinations & Reports', sw: 'Mitihani na Matokeo' },
  fees: { en: 'Fee Ledger & Invoices', sw: 'Usimamizi wa Ada' },
  meetings: { en: 'Meetings & Events', sw: 'Mikutano ya Wazazi' },
  teacher: { en: 'Teacher Workspace', sw: 'Eneo la Mwalimu' },
  parent: { en: 'Parent Portal', sw: 'Mlango wa Mzazi' },
  imports: { en: 'Excel Import Center', sw: 'Kituo cha Excel' },
  necta: { en: 'NECTA Integration', sw: 'Matokeo ya NECTA' },
  'ussd-simulator': { en: 'USSD Simulator', sw: 'Kifanisi cha USSD' },
};

export const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const { language } = useAuth();

  const pathnames = location.pathname.split('/').filter((x) => x);
  if (pathnames.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="mb-5 flex items-center gap-1.5 text-xs text-slate-500 font-medium">
      <Link
        to="/dashboard"
        className="flex items-center gap-1 text-slate-400 hover:text-brand-navy transition"
      >
        <Home className="w-3.5 h-3.5" />
        <span className="sr-only">Home</span>
      </Link>

      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const entry = routeNameMap[value];
        const label = entry ? (language === 'sw' ? entry.sw : entry.en) : value.replace('-', ' ');

        return (
          <React.Fragment key={to}>
            <ChevronRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />
            {isLast ? (
              <span className="text-slate-800 font-semibold truncate max-w-xs capitalize" aria-current="page">
                {label}
              </span>
            ) : (
              <Link to={to} className="hover:text-brand-navy transition capitalize">
                {label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};