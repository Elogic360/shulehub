import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  FileSpreadsheet,
  Upload,
  CheckCircle2,
  Send,
  AlertTriangle,
  Award,
  Plus,
} from 'lucide-react';

export const ClassExaminations: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedExamId, setSelectedExamId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');

  const [scoresInput, setScoresInput] = useState<{ [studentId: string]: number }>({});
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importReport, setImportReport] = useState<any | null>(null);
  const [publishSuccessMsg, setPublishSuccessMsg] = useState<string | null>(null);
  const [sendingStudentId, setSendingStudentId] = useState<string | null>(null);
  const [reportSentResult, setReportSentResult] = useState<any | null>(null);
  const [selectedStudentForModal, setSelectedStudentForModal] = useState<any | null>(null);
  const [targetPhoneInput, setTargetPhoneInput] = useState<string>('0683312365');

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

  const { data: exams = [] } = useQuery({
    queryKey: ['examinations'],
    queryFn: async () => {
      const res = await api.get('/examinations');
      if (res.data.length > 0 && !selectedExamId) {
        setSelectedExamId(res.data[0].id);
      }
      return res.data;
    },
  });

  const { data: subjects = [] } = useQuery({
    queryKey: ['subjects'],
    queryFn: async () => {
      const res = await api.get('/examinations/subjects');
      if (res.data.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(res.data[0].id);
      }
      return res.data;
    },
  });

  const { data: resultsSummary, isLoading } = useQuery({
    queryKey: ['class_exam_results', selectedClassId, selectedExamId],
    queryFn: async () => {
      if (!selectedClassId || !selectedExamId) return null;
      return (await api.get(`/examinations/class/${selectedClassId}/summary?examination_id=${selectedExamId}`)).data;
    },
    enabled: !!selectedClassId && !!selectedExamId,
  });

  // Assign Subject to Exam & Submit Marks
  const saveMarksMutation = useMutation({
    mutationFn: async (payload: any) => {
      // 1. Ensure subject is assigned to exam
      const subRes = await api.post('/examinations/subjects/assign', {
        examination_id: selectedExamId,
        subject_id: selectedSubjectId,
        class_group_id: selectedClassId,
      });
      const examSubjectId = subRes.data.id;

      // 2. Submit batch
      const marksPayload = Object.entries(scoresInput).map(([studentId, score]) => ({
        student_id: studentId,
        score: Number(score),
      }));

      return api.post('/examinations/results/batch', {
        examination_subject_id: examSubjectId,
        results: marksPayload,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['class_exam_results'] });
      alert(t('Marks saved successfully!', 'Alama zimehifadhiwa kwa mafanikio!'));
    },
  });

  // Import Results File
  const importResultsMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await api.post(
        `/examinations/results/import-file?examination_id=${selectedExamId}&class_group_id=${selectedClassId}&subject_id=${selectedSubjectId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['class_exam_results'] });
      setImportReport(data);
      if (data.successful_rows > 0 && data.failed_rows === 0) {
        setTimeout(() => setShowImportModal(false), 2000);
      }
    },
  });

  // Publish Results Mutation
  const publishMutation = useMutation({
    mutationFn: async () => {
      return api.post('/examinations/results/publish', {
        examination_id: selectedExamId,
        class_group_id: selectedClassId,
        notify_parents_via_sms: true,
      });
    },
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ['class_exam_results'] });
      setPublishSuccessMsg(`Matokeo yametangazwa na SMS ${res.data.notifications_queued} zimetumwa kwa wazazi!`);
      setTimeout(() => setPublishSuccessMsg(null), 5000);
    },
  });

  // Individual Student Report SMS Mutation
  const sendReportMutation = useMutation({
    mutationFn: async ({ studentId, customPhone }: { studentId: string; customPhone?: string }) => {
      setSendingStudentId(studentId);
      const res = await api.post(`/examinations/students/${studentId}/send-report`, null, {
        params: {
          examination_id: selectedExamId || undefined,
          custom_recipient_phone: customPhone || undefined,
        },
      });
      return res.data;
    },
    onSuccess: (data: any) => {
      setSendingStudentId(null);
      setSelectedStudentForModal(null);
      setReportSentResult(data);
      queryClient.invalidateQueries({ queryKey: ['class_exam_results'] });
      setTimeout(() => setReportSentResult(null), 10000);
    },
    onError: (err: any) => {
      setSendingStudentId(null);
      alert(err.response?.data?.detail || 'Failed to send report SMS');
    },
  });

  const handleScoreChange = (studentId: string, val: string) => {
    setScoresInput((prev) => ({
      ...prev,
      [studentId]: Number(val),
    }));
  };

  const handleImportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    const fd = new FormData();
    fd.append('file', importFile);
    importResultsMutation.mutate(fd);
  };

  return (
    <div className="space-y-6">
      {/* Header with Selectors */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Examination Marks & Results', 'Alama za Mitihani na Matokeo')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Enter marks, import grading sheets and publish verified results to guardians.', 'Ingiza alama, pakia faili la matokeo na tangaza matokeo rasmi kwa wazazi.')}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Class selector */}
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

          {/* Exam selector */}
          <select
            value={selectedExamId}
            onChange={(e) => setSelectedExamId(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
          >
            {exams.map((ex: any) => (
              <option key={ex.id} value={ex.id}>
                {ex.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              setImportReport(null);
              setShowImportModal(true);
            }}
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Upload className="w-3.5 h-3.5 text-brand-teal" />
            <span>{t('Import Marks', 'Pakia Alama')}</span>
          </button>

          <button
            onClick={() => {
              const kelvin = resultsSummary?.students?.find((s: any) => s.admission_number === 'STD3-001') || resultsSummary?.students?.[0];
              if (kelvin) {
                setSelectedStudentForModal(kelvin);
                setTargetPhoneInput('0683312365');
              }
            }}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm transition flex items-center gap-1.5"
            title="Tuma ripoti ya mtihani kwa namba ya majaribio 0683312365"
          >
            <Send className="w-3.5 h-3.5 text-indigo-200" />
            <span>{t('Send Report to 0683312365', 'Tuma Ripoti kwa 0683312365')}</span>
          </button>

          <button
            onClick={() => publishMutation.mutate()}
            disabled={publishMutation.isPending}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md transition flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{publishMutation.isPending ? t('Publishing...', 'Inatangaza...') : t('Publish Results & Notify', 'Tangaza Matokeo na Julisha')}</span>
          </button>
        </div>
      </div>

      {reportSentResult && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 text-xs font-medium space-y-2">
          <div className="flex items-center justify-between font-bold text-sm text-blue-950">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-blue-600" />
              {t('SMS Examination Report Dispatched!', 'Ripoti ya Mtihani Imetumwa kwa SMS!')}
            </span>
            <span className="text-blue-700 font-mono text-xs bg-blue-100 px-2 py-0.5 rounded">
              {reportSentResult.recipient_phone} ({reportSentResult.recipient_name})
            </span>
          </div>
          <div className="p-3 rounded-lg bg-white border border-blue-100 font-mono text-xs text-slate-800 leading-relaxed shadow-sm">
            "{reportSentResult.message_text}"
          </div>
          <div className="flex flex-wrap items-center justify-between text-[11px] text-blue-700 pt-0.5">
            <span>Mwanafunzi: <strong>{reportSentResult.student_name}</strong> ({reportSentResult.admission_number})</span>
            <span>Wastani: <strong>{reportSentResult.average_score}%</strong> (Daraja <strong>{reportSentResult.overall_grade}</strong>)</span>
            <span className="font-mono text-[10px]">SMS Ref: {reportSentResult.provider_message_id}</span>
          </div>
        </div>
      )}

      {publishSuccessMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <span>{publishSuccessMsg}</span>
        </div>
      )}

      {/* Manual Entry Quick Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            {t('Quick Mark Entry for Subject:', 'Ingiza Alama za Somo:')}
          </span>
          <select
            value={selectedSubjectId}
            onChange={(e) => setSelectedSubjectId(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-bold text-brand-navy bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
          >
            {subjects.map((sub: any) => (
              <option key={sub.id} value={sub.id}>
                {sub.name} ({sub.code})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => saveMarksMutation.mutate({})}
          disabled={saveMarksMutation.isPending}
          className="px-4 py-1.5 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition"
        >
          {saveMarksMutation.isPending ? t('Saving...', 'Inahifadhi...') : t('Save Entered Marks', 'Hifadhi Alama')}
        </button>
      </div>

      {/* Examination Performance Matrix Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-brand-navy flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-500" />
            <span>{t('Class Performance Matrix & Ranking', 'Jedwali la Matokeo na Nafasi za Wanafunzi')}</span>
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">{t('Rank', 'Nafasi')}</th>
                <th className="px-4 py-3">{t('Adm #', 'Namba')}</th>
                <th className="px-4 py-3">{t('Student Name', 'Jina la Mwanafunzi')}</th>
                <th className="px-4 py-3 w-32">{t('Input Score', 'Ingiza Alama')}</th>
                <th className="px-4 py-3">{t('Total', 'Jumla')}</th>
                <th className="px-4 py-3">{t('Average', 'Wastani')}</th>
                <th className="px-4 py-3">{t('Grade', 'Daraja')}</th>
                <th className="px-4 py-3 text-right">{t('Action', 'Hatua')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {resultsSummary?.students?.map((st: any) => (
                <tr key={st.student_id} className="hover:bg-slate-50/60 transition">
                  <td className="px-4 py-3 font-black text-xs text-brand-navy">
                    #{st.rank}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {st.admission_number}
                  </td>
                  <td className="px-4 py-3 font-bold text-xs text-slate-800">
                    {st.student_name}
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={0.5}
                      placeholder="0-100"
                      value={scoresInput[st.student_id] !== undefined ? scoresInput[st.student_id] : ''}
                      onChange={(e) => handleScoreChange(st.student_id, e.target.value)}
                      className="w-20 px-2 py-1 text-xs rounded border border-slate-300 font-bold text-brand-navy text-center focus:outline-none focus:ring-1 focus:ring-brand-teal"
                    />
                  </td>
                  <td className="px-4 py-3 text-xs font-semibold text-slate-700">
                    {st.total_score}
                  </td>
                  <td className="px-4 py-3 text-xs font-bold text-brand-navy">
                    {st.average_score}%
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                      st.overall_grade === 'A'
                        ? 'bg-emerald-100 text-emerald-800'
                        : st.overall_grade === 'B'
                        ? 'bg-blue-100 text-blue-800'
                        : st.overall_grade === 'C'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}>
                      Grade {st.overall_grade}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => {
                        setSelectedStudentForModal(st);
                        setTargetPhoneInput(st.admission_number === 'STD3-001' ? '0683312365' : '0683312365');
                      }}
                      className="px-2.5 py-1.5 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-[11px] font-bold shadow-sm transition inline-flex items-center gap-1.5"
                      title={t('Send SMS report card to guardian or test number', 'Tuma ripoti ya mtihani kwa mzazi au namba ya majaribio')}
                    >
                      <Send className="w-3 h-3 text-brand-teal" />
                      <span>{t('Send Report SMS', 'Tuma Ripoti SMS')}</span>
                    </button>
                  </td>
                </tr>
              ))}
              {(!resultsSummary?.students || resultsSummary.students.length === 0) && !isLoading && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-xs text-slate-400">
                    {t('No examination marks recorded yet for this session.', 'Bado hakuna alama zilizorekodiwa.')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Import Marks */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-2">
              {t('Import Examination Marks (CSV / Excel)', 'Pakia Alama za Mtihani (CSV / Excel)')}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Safu wima zinazotakiwa: <code className="text-brand-navy font-bold">admission_number, score</code>
            </p>

            {importReport && (
              <div className="mb-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
                <div className="flex justify-between font-bold text-slate-700">
                  <span>{t('Processed:', 'Zilizopitiwa:')} {importReport.total_rows}</span>
                  <span className="text-emerald-600">{t('Successful:', 'Mafanikio:')} {importReport.successful_rows}</span>
                  <span className="text-rose-600">{t('Errors:', 'Hitilafu:')} {importReport.failed_rows}</span>
                </div>
                {importReport.errors?.length > 0 && (
                  <div className="mt-2 text-rose-700 max-h-32 overflow-y-auto space-y-1 border-t border-slate-200 pt-1">
                    {importReport.errors.map((err: string, i: number) => (
                      <div key={i}>&bull; {err}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleImportSubmit} className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-brand-teal transition bg-slate-50">
                <FileSpreadsheet className="w-8 h-8 text-slate-400 mx-auto mb-2" />
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
                  disabled={!importFile || importResultsMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {importResultsMutation.isPending ? t('Validating...', 'Inahakiki...') : t('Upload & Validate', 'Pakia & Hakiki')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Send Individual Student Report SMS */}
      {selectedStudentForModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-5 h-5 text-brand-teal" />
                <h3 className="text-base font-bold text-brand-navy">
                  {t('Send Exam Report via SMS', 'Tuma Ripoti ya Mtihani kwa SMS')}
                </h3>
              </div>
              <button
                onClick={() => setSelectedStudentForModal(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            {/* Student & Performance Summary */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-sm text-brand-navy">{selectedStudentForModal.student_name}</span>
                <span className="font-mono text-slate-500 font-bold">{selectedStudentForModal.admission_number}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center pt-1 border-t border-slate-200">
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">{t('Rank', 'Nafasi')}</div>
                  <div className="text-sm font-black text-brand-navy">#{selectedStudentForModal.rank}</div>
                </div>
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">{t('Average', 'Wastani')}</div>
                  <div className="text-sm font-black text-brand-navy">{selectedStudentForModal.average_score}%</div>
                </div>
                <div className="bg-white p-2 rounded-lg border border-slate-100">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">{t('Grade', 'Daraja')}</div>
                  <div className="text-sm font-black text-emerald-600">Grade {selectedStudentForModal.overall_grade}</div>
                </div>
              </div>
            </div>

            {/* Recipient Phone with Test Quick-Set */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">
                  {t('Recipient Phone Number (SMS):', 'Nambari ya Simu ya Mzazi (SMS):')}
                </label>
                <button
                  type="button"
                  onClick={() => setTargetPhoneInput('0683312365')}
                  className="text-[11px] font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded transition flex items-center gap-1"
                >
                  <span>👉 {t('Use Test Number: 0683312365', 'Tumia Namba ya Majaribio: 0683312365')}</span>
                </button>
              </div>
              <input
                type="text"
                value={targetPhoneInput}
                onChange={(e) => setTargetPhoneInput(e.target.value)}
                placeholder="e.g. 0683312365 or +255683312365"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 font-mono text-sm text-brand-navy font-bold focus:outline-none focus:ring-2 focus:ring-brand-teal"
              />
              <p className="text-[11px] text-slate-400">
                {t('Defaulted to registered parent or customizable for live SMS evaluation.', 'Namba ya mzazi au namba ya majaribio ya kuangalia ujumbe.')}
              </p>
            </div>

            {/* Message Preview */}
            <div className="p-3 rounded-lg bg-indigo-50/70 border border-indigo-100 text-[11px] space-y-1">
              <span className="font-bold text-indigo-950 uppercase tracking-wider text-[10px] block">
                {t('Simulated SMS Content (with USSD *384*57567#):', 'Muhtasari wa SMS itakayotumwa (na USSD *384*57567#):')}
              </span>
              <p className="font-mono text-slate-700 leading-relaxed text-[11px]">
                Habari Mzazi/Mlezi, Ripoti ya {exams.find((e: any) => e.id === selectedExamId)?.name || 'Mtihani'} kwa {selectedStudentForModal.student_name}: Nafasi: #{selectedStudentForModal.rank}. Wastani: {selectedStudentForModal.average_score}% (Daraja {selectedStudentForModal.overall_grade}). USSD: *384*57567#. St. Jude Premier English Medium Primary School
              </p>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedStudentForModal(null)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                {t('Cancel', 'Ghairi')}
              </button>
              <button
                type="button"
                onClick={() => sendReportMutation.mutate({ studentId: selectedStudentForModal.student_id, customPhone: targetPhoneInput })}
                disabled={sendReportMutation.isPending}
                className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-bold shadow-md transition flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5 text-brand-teal" />
                <span>{sendReportMutation.isPending ? t('Sending SMS...', 'Inatuma SMS...') : t('Send SMS Report Now', 'Tuma Ripoti kwa SMS Sasa')}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
