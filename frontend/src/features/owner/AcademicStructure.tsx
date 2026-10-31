import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Layers, Plus, Check, UserCheck, Shield } from 'lucide-react';

export const AcademicStructure: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [showClassModal, setShowClassModal] = useState(false);
  const [className, setClassName] = useState('');
  const [stream, setStream] = useState('A');
  const [selectedLevelId, setSelectedLevelId] = useState('');
  const [selectedYearId, setSelectedYearId] = useState('');
  const [capacity, setCapacity] = useState(50);

  // Queries
  const { data: levels = [] } = useQuery({
    queryKey: ['academic_levels'],
    queryFn: async () => (await api.get('/academic/levels')).data,
  });

  const { data: years = [] } = useQuery({
    queryKey: ['academic_years'],
    queryFn: async () => (await api.get('/academic/years')).data,
  });

  const { data: classes = [], isLoading } = useQuery({
    queryKey: ['academic_classes'],
    queryFn: async () => (await api.get('/academic/classes')).data,
  });

  // Create Class Mutation
  const createClassMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/academic/classes', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic_classes'] });
      setShowClassModal(false);
      setClassName('');
    },
  });

  const handleCreateClass = (e: React.FormEvent) => {
    e.preventDefault();
    createClassMutation.mutate({
      academic_level_id: selectedLevelId || levels[0]?.id,
      academic_year_id: selectedYearId || years[0]?.id,
      name: className,
      stream,
      capacity,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Academic Structure & Classes', 'Muundo wa Masomo na Madarasa')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Configure academic levels, class streams and class teacher assignments.', 'Weka madarasa, mikondo (streams) na panga walimu wa madarasa.')}
          </p>
        </div>

        <button
          onClick={() => {
            if (levels.length > 0) setSelectedLevelId(levels[0].id);
            if (years.length > 0) setSelectedYearId(years[0].id);
            setShowClassModal(true);
          }}
          className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center gap-2 self-start"
        >
          <Plus className="w-4 h-4 text-brand-teal" />
          <span>{t('Add Class Group', 'Ongeza Darasa')}</span>
        </button>
      </div>

      {/* Academic Levels Pill Overview */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          {t('Configured Academic Levels', 'Ngazi za Masomo Zilizosanidiwa')}
        </h2>
        <div className="flex flex-wrap gap-2">
          {levels.map((lvl: any) => (
            <div
              key={lvl.id}
              className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-700 flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-brand-teal"></span>
              <span className="font-semibold text-brand-navy">{lvl.name}</span>
              <span className="text-[10px] text-slate-400 uppercase">({lvl.school_type})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Class Groups Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-brand-navy">
            {t('Active Class Groups & Streams', 'Orodha ya Madarasa na Mikondo')}
          </h2>
          <span className="text-xs text-slate-500 font-medium">
            {classes.length} {t('Classes', 'Madarasa')}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t('Class Name', 'Jina la Darasa')}</th>
                <th className="px-5 py-3">{t('Level', 'Ngazi')}</th>
                <th className="px-5 py-3">{t('Stream', 'Mkondo')}</th>
                <th className="px-5 py-3">{t('Capacity', 'Uwezo')}</th>
                <th className="px-5 py-3">{t('Class Teacher', 'Mwalimu wa Darasa')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {classes.map((cls: any) => (
                <tr key={cls.id} className="hover:bg-slate-50/60 transition">
                  <td className="px-5 py-3.5 font-bold text-brand-navy">
                    {cls.name}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-600 font-medium">
                    {cls.academic_level_name || 'Level'}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="inline-block px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                      {cls.stream || 'Default'}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-500">
                    {cls.capacity} {t('Students', 'Wanafunzi')}
                  </td>
                  <td className="px-5 py-3.5">
                    {cls.teacher ? (
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">
                          {cls.teacher.full_name.charAt(0)}
                        </div>
                        <div>
                          <span className="text-xs font-bold text-slate-800 block">
                            {cls.teacher.full_name}
                          </span>
                          <span className="text-[10px] text-slate-400 block">
                            {cls.teacher.phone_number}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-amber-600 font-medium italic">
                        {t('Not Assigned', 'Hajapangwa')}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {classes.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-sm text-slate-400">
                    {t('No class groups created yet.', 'Bado hakuna madarasa yaliyoundwa.')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Create Class */}
      {showClassModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Create Class Group & Stream', 'Unda Darasa na Mkondo')}
            </h3>

            <form onSubmit={handleCreateClass} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Academic Level', 'Ngazi ya Masomo')}
                </label>
                <select
                  value={selectedLevelId}
                  onChange={(e) => setSelectedLevelId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                >
                  {levels.map((lvl: any) => (
                    <option key={lvl.id} value={lvl.id}>
                      {lvl.name} ({lvl.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Class Name', 'Jina la Darasa')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Standard 1A / Form 2 East"
                  value={className}
                  onChange={(e) => setClassName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Stream', 'Mkondo (Stream)')}
                  </label>
                  <input
                    type="text"
                    placeholder="A / B / Blue"
                    value={stream}
                    onChange={(e) => setStream(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Capacity', 'Idadi ya Wanafunzi')}
                  </label>
                  <input
                    type="number"
                    min={10}
                    max={120}
                    value={capacity}
                    onChange={(e) => setCapacity(Number(e.target.value))}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowClassModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={createClassMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {createClassMutation.isPending ? t('Saving...', 'Inahifadhi...') : t('Create Class', 'Unda Darasa')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
