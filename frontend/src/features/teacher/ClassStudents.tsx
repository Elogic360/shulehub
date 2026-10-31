import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { GraduationCap, Plus, Upload, Search, Phone, UserCheck, AlertTriangle } from 'lucide-react';

export const ClassStudents: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);

  // Single student form state
  const [admNo, setAdmNo] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [gender, setGender] = useState('MALE');
  const [parentName, setParentName] = useState('');
  const [parentPhone, setParentPhone] = useState('');
  const [relationship, setRelationship] = useState('PARENT');

  // Import file state
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importErrors, setImportErrors] = useState<string[]>([]);
  const [importSuccessMsg, setImportSuccessMsg] = useState<string | null>(null);

  // Queries
  const { data: classes = [] } = useQuery({
    queryKey: ['teacher_classes'],
    queryFn: async () => {
      const res = await api.get('/academic/classes');
      if (res.data.length > 0 && !selectedClassId) {
        setSelectedClassId(res.data[0].id);
      }
      return res.data;
    },
  });

  const { data: years = [] } = useQuery({
    queryKey: ['academic_years'],
    queryFn: async () => (await api.get('/academic/years')).data,
  });

  const { data: students = [], isLoading } = useQuery({
    queryKey: ['students', selectedClassId, searchTerm],
    queryFn: async () => {
      if (!selectedClassId) return [];
      const params = new URLSearchParams();
      params.append('class_group_id', selectedClassId);
      if (searchTerm) params.append('search', searchTerm);
      return (await api.get(`/students?${params.toString()}`)).data;
    },
    enabled: !!selectedClassId,
  });

  // Create Student Mutation
  const createStudentMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/students', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setShowAddModal(false);
      setAdmNo('');
      setFirstName('');
      setLastName('');
      setParentName('');
      setParentPhone('');
    },
  });

  // Import Mutation
  const importMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post(
        `/students/import?class_group_id=${selectedClassId}&academic_year_id=${years[0]?.id}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['students'] });
      setImportSuccessMsg(`Wanafunzi ${data.imported_count} wameingizwa kwa mafanikio!`);
      setImportErrors(data.errors || []);
      if (!data.errors || data.errors.length === 0) {
        setTimeout(() => setShowImportModal(false), 1500);
      }
    },
    onError: (err: any) => {
      setImportErrors([err.response?.data?.detail || 'Hitilafu wakati wa kupakia faili']);
    },
  });

  const handleCreateStudent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !years[0]?.id) return;
    createStudentMutation.mutate({
      admission_number: admNo,
      first_name: firstName,
      last_name: lastName,
      gender,
      class_group_id: selectedClassId,
      academic_year_id: years[0].id,
      guardian: parentName && parentPhone ? {
        full_name: parentName,
        primary_phone: parentPhone,
        preferred_language: 'sw',
        relationship_type: relationship,
      } : undefined,
    });
  };

  const handleImportFile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    setImportErrors([]);
    setImportSuccessMsg(null);
    const formData = new FormData();
    formData.append('file', importFile);
    importMutation.mutate(formData);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Class Student Roster', 'Orodha ya Wanafunzi wa Darasa')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Manage enrolled students, link parents and upload roster spreadsheets.', 'Sajili wanafunzi, unganisha wazazi na pakia majina kupitia Excel/CSV.')}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {classes.length > 1 && (
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              className="px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
            >
              {classes.map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => {
              setImportErrors([]);
              setImportSuccessMsg(null);
              setShowImportModal(true);
            }}
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Upload className="w-3.5 h-3.5 text-brand-teal" />
            <span>{t('Import CSV / Excel', 'Pakia Excel / CSV')}</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5 text-brand-teal" />
            <span>{t('Add Student', 'Sajili Mwanafunzi')}</span>
          </button>
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-400 ml-2" />
        <input
          type="text"
          placeholder={t('Search by name or admission number...', 'Tafuta kwa jina au namba ya usajili...')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full text-sm outline-none text-slate-700 placeholder-slate-400"
        />
      </div>

      {/* Students Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t('Adm #', 'Namba')}</th>
                <th className="px-5 py-3">{t('Full Name', 'Jina Kamili')}</th>
                <th className="px-5 py-3">{t('Gender', 'Jinsia')}</th>
                <th className="px-5 py-3">{t('Class', 'Darasa')}</th>
                <th className="px-5 py-3">{t('Guardian Contact (E.164)', 'Mzazi na Mawasiliano')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {students.map((st: any) => (
                <tr key={st.id} className="hover:bg-slate-50/60 transition">
                  <td className="px-5 py-3.5 font-bold text-xs text-brand-navy">
                    {st.admission_number}
                  </td>
                  <td className="px-5 py-3.5 text-xs font-bold text-slate-800">
                    {st.first_name} {st.middle_name ? `${st.middle_name} ` : ''}{st.last_name}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-500">
                    {st.gender}
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-600 font-medium">
                    {st.class_name || 'Standard 1'}
                  </td>
                  <td className="px-5 py-3.5 text-xs">
                    {st.guardians?.[0] ? (
                      <div className="flex items-center gap-2">
                        <Phone className="w-3.5 h-3.5 text-emerald-600" />
                        <div>
                          <span className="font-semibold text-slate-800 block">
                            {st.guardians[0].full_name} ({st.guardians[0].relationship})
                          </span>
                          <span className="text-[11px] font-mono text-slate-500">
                            {st.guardians[0].primary_phone}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-amber-600 italic">
                        {t('No guardian linked', 'Hana mlezi aliyeunganishwa')}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {students.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-sm text-slate-400">
                    {t('No students found in this class.', 'Hakuna wanafunzi waliopatikana.')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Add Single Student */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Register New Student', 'Sajili Mwanafunzi Mpya')}
            </h3>

            <form onSubmit={handleCreateStudent} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Admission Number', 'Namba ya Usajili')}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. STD/2026/045"
                    value={admNo}
                    onChange={(e) => setAdmNo(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal uppercase"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Gender', 'Jinsia')}
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  >
                    <option value="MALE">{t('Male', 'Mvulana')}</option>
                    <option value="FEMALE">{t('Female', 'Msichana')}</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('First Name', 'Jina la Kwanza')}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Baraka"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Last Name', 'Jina la Ukoo')}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Juma"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              {/* Guardian Info Section */}
              <div className="pt-3 border-t border-slate-200">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
                  {t('Guardian Information', 'Taarifa za Mzazi / Mlezi')}
                </span>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      {t('Guardian Full Name', 'Jina Kamili la Mzazi')}
                    </label>
                    <input
                      type="text"
                      placeholder="Mariam Juma"
                      value={parentName}
                      onChange={(e) => setParentName(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        {t('Phone Number (07xx)', 'Namba ya Simu')}
                      </label>
                      <input
                        type="text"
                        placeholder="0712345678"
                        value={parentPhone}
                        onChange={(e) => setParentPhone(e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        {t('Relationship', 'Uhusiano')}
                      </label>
                      <select
                        value={relationship}
                        onChange={(e) => setRelationship(e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                      >
                        <option value="MOTHER">Mama (Mother)</option>
                        <option value="FATHER">Baba (Father)</option>
                        <option value="GUARDIAN">Mlezi (Guardian)</option>
                        <option value="UNCLE">Mjomba (Uncle)</option>
                        <option value="AUNT">Shangazi (Aunt)</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={createStudentMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {createStudentMutation.isPending ? t('Saving...', 'Inahifadhi...') : t('Save Student', 'Hifadhi Mwanafunzi')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Bulk Import */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-2">
              {t('Bulk Import Students (CSV / Excel)', 'Pakia Wanafunzi kwa Wingi')}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Faili linapaswa kuwa na safu wima: <code className="text-brand-navy font-bold">admission_number, first_name, last_name, gender, parent_name, parent_phone</code>
            </p>

            {importSuccessMsg && (
              <div className="mb-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
                {importSuccessMsg}
              </div>
            )}

            {importErrors.length > 0 && (
              <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs max-h-40 overflow-y-auto space-y-1">
                <div className="font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Hitilafu Zilizogunduliwa ({importErrors.length}):</span>
                </div>
                {importErrors.map((err, i) => (
                  <div key={i} className="pl-4">&bull; {err}</div>
                ))}
              </div>
            )}

            <form onSubmit={handleImportFile} className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-brand-teal transition bg-slate-50">
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <input
                  type="file"
                  required
                  accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-navy file:text-white hover:file:bg-slate-800"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={!importFile || importMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {importMutation.isPending ? t('Validating & Importing...', 'Inahakiki na Kupakia...') : t('Upload & Process', 'Pakia na Ingiza')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
