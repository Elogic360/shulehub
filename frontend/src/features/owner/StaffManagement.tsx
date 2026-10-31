import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { UserCheck, Plus, CheckCircle, Shield, Phone, Mail } from 'lucide-react';

export const StaffManagement: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [showAddStaffModal, setShowAddStaffModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);

  // Form states
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [roleName, setRoleName] = useState('CLASS_TEACHER');

  // Assign modal state
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');

  // Queries
  const { data: classes = [] } = useQuery({
    queryKey: ['academic_classes'],
    queryFn: async () => (await api.get('/academic/classes')).data,
  });

  const { data: years = [] } = useQuery({
    queryKey: ['academic_years'],
    queryFn: async () => (await api.get('/academic/years')).data,
  });

  // Add Staff Mutation
  const addStaffMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/auth/register-staff', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic_classes'] });
      setShowAddStaffModal(false);
      setFullName('');
      setEmail('');
      setPhone('');
      setPassword('');
    },
  });

  // Assign Teacher Mutation
  const assignTeacherMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/academic/classes/assign-teacher', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic_classes'] });
      setShowAssignModal(false);
    },
  });

  const handleRegisterStaff = (e: React.FormEvent) => {
    e.preventDefault();
    addStaffMutation.mutate({
      full_name: fullName,
      email: email || undefined,
      phone_number: phone,
      password,
      role_name: roleName,
    });
  };

  const handleAssignTeacher = (e: React.FormEvent) => {
    e.preventDefault();
    if (!years[0]?.id) return;
    assignTeacherMutation.mutate({
      class_group_id: selectedClassId,
      teacher_user_id: selectedTeacherId,
      academic_year_id: years[0].id,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Staff & Teacher Management', 'Usimamizi wa Walimu na Wafanyakazi')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Register class teachers and assign operational administrative rights.', 'Sajili walimu na panga madarasa wanayosimamia rasmi.')}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddStaffModal(true)}
            className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4 text-brand-teal" />
            <span>{t('Register Teacher', 'Sajili Mwalimu')}</span>
          </button>
          <button
            onClick={() => {
              if (classes.length > 0) setSelectedClassId(classes[0].id);
              setShowAssignModal(true);
            }}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <UserCheck className="w-4 h-4" />
            <span>{t('Assign Class', 'Panga Darasa')}</span>
          </button>
        </div>
      </div>

      {/* Class Allocation Grid */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-brand-navy">
            {t('Class Teacher Assignments', 'Orodha ya Walimu Waliopangwa Madarasani')}
          </h2>
        </div>

        <div className="divide-y divide-slate-100">
          {classes.map((cls: any) => (
            <div key={cls.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 transition">
              <div>
                <span className="font-bold text-brand-navy text-sm block">
                  {cls.name}
                </span>
                <span className="text-xs text-slate-500 block">
                  {cls.academic_level_name} &bull; Stream: {cls.stream || 'A'}
                </span>
              </div>

              <div>
                {cls.teacher ? (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 font-bold text-xs flex items-center justify-center">
                      {cls.teacher.full_name.charAt(0)}
                    </div>
                    <div>
                      <span className="text-xs font-bold text-slate-800 block">
                        {cls.teacher.full_name}
                      </span>
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Phone className="w-3 h-3 text-slate-400" />
                        {cls.teacher.phone_number}
                      </span>
                    </div>
                  </div>
                ) : (
                  <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-200 inline-block">
                    {t('Needs Class Teacher Assignment', 'Linahitaji Kupangiwa Mwalimu')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal: Register Staff */}
      {showAddStaffModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Register New Staff Member', 'Sajili Mwalimu / Mfanyakazi')}
            </h3>

            <form onSubmit={handleRegisterStaff} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Full Name', 'Jina Kamili')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="Mwl. John Mwita"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Mobile Phone (+255)', 'Namba ya Simu')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="0712345678"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Email Address (Optional)', 'Barua Pepe')}
                </label>
                <input
                  type="email"
                  placeholder="teacher@school.ac.tz"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Role', 'Wadhifa')}
                  </label>
                  <select
                    value={roleName}
                    onChange={(e) => setRoleName(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  >
                    <option value="CLASS_TEACHER">{t('Class Teacher', 'Mwalimu wa Darasa')}</option>
                    <option value="SCHOOL_ADMIN">{t('School Administrator', 'Mtawala wa Shule')}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Initial Password', 'Nenosiri')}
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddStaffModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={addStaffMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {addStaffMutation.isPending ? t('Saving...', 'Inasajili...') : t('Register', 'Sajili')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Assign Class Teacher */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Assign Class Teacher', 'Panga Mwalimu wa Darasa')}
            </h3>

            <form onSubmit={handleAssignTeacher} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Select Class', 'Chagua Darasa')}
                </label>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                >
                  {classes.map((cls: any) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name} ({cls.academic_level_name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Teacher User ID', 'ID au Namba ya Mwalimu')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ingiza User ID ya Mwalimu"
                  value={selectedTeacherId}
                  onChange={(e) => setSelectedTeacherId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={assignTeacherMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow-sm transition"
                >
                  {assignTeacherMutation.isPending ? t('Saving...', 'Inahifadhi...') : t('Assign', 'Panga Mwalimu')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
