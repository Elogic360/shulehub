import React, { useState, useEffect } from 'react';
import { 
  Upload, FileSpreadsheet, Download, CheckCircle, AlertTriangle, 
  XCircle, RotateCcw, Clock, ArrowRight, ShieldCheck, FileText, Check 
} from 'lucide-react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface ImportBatch {
  id: string;
  workflow_type: string;
  status: string;
  total_rows: number;
  new_records: number;
  updated_records: number;
  rejected_records: number;
  created_at: string;
  committed_at?: string;
  reverted_at?: string;
}

interface StagedRow {
  row_number: number;
  status: string;
  action_type: string;
  data: Record<string, any>;
  error_summary?: string;
}

interface ValidationError {
  row_number: number;
  column_name: string;
  error_code: string;
  error_message: string;
  raw_value?: string;
}

export const ImportCenter: React.FC = () => {
  const { language, t } = useAuth();
  const [workflow, setWorkflow] = useState<'STUDENT_REGISTRATION' | 'EXAM_RESULTS' | 'FEE_STRUCTURES' | 'FEE_BALANCES'>('STUDENT_REGISTRATION');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<any>(null);
  const [previewRows, setPreviewRows] = useState<StagedRow[]>([]);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [activeTab, setActiveTab] = useState<'upload' | 'preview' | 'errors' | 'history'>('upload');
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, [workflow]);

  const fetchHistory = async () => {
    try {
      const res = await api.get(`/imports/history/list?workflow_type=${workflow}`);
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to load history', err);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const res = await api.get(`/imports/templates?workflow_type=${workflow}`);
      const tpl = res.data[workflow];
      const blob = new Blob([tpl.sample_csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${workflow.toLowerCase()}_template.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      alert('Failed to download template');
    }
  };

  const handleLoadDemoFile = () => {
    let demoCsv = '';
    let filename = '';
    if (workflow === 'STUDENT_REGISTRATION') {
      demoCsv = `reg_no,full_name,gender,date_of_birth,guardian_name,guardian_phone,guardian_relationship
STD3-001,Kelvin Rashidi,M,2017-03-14,Amina Bakari,0683312365,MOTHER
STD3-002,Neema Charles Mtweve,F,2017-07-22,Charles Mtweve,0713998877,FATHER
STD3-003,Baraka Daniel Msangi,M,2017-11-05,Daniel Msangi,0755112233,FATHER
STD3-004,Faraja Zawadi Komba,F,2017-05-18,Zawadi Komba,0768445566,MOTHER
STD3-005,Brian Joseph Mdemu,M,2017-01-30,Joseph Mdemu,0784112244,FATHER`;
      filename = 'sample_students_std3.csv';
    } else if (workflow === 'EXAM_RESULTS') {
      demoCsv = `admission_number,student_name,MATH,KISW,ENG,SCI,SST
STD3-001,Kelvin Rashidi,88,94,82,90,85
STD3-002,Neema Charles Mtweve,92,89,95,91,88
STD3-003,Baraka Daniel Msangi,76,82,78,74,79
STD3-004,Faraja Zawadi Komba,85,90,87,83,86`;
      filename = 'sample_exam_marks_std3.csv';
    } else if (workflow === 'FEE_BALANCES') {
      demoCsv = `admission_number,student_name,total_fees,total_paid,balance,as_of_date
STD3-001,Kelvin Rashidi,450000,450000,0,2026-10-31
STD3-002,Neema Charles Mtweve,450000,250000,200000,2026-10-31
STD3-003,Baraka Daniel Msangi,450000,150000,300000,2026-10-31`;
      filename = 'sample_fee_balances_std3.csv';
    } else {
      demoCsv = `fee_category,fee_description,amount,due_date
TUITION,Standard 3 Term 1 Tuition,450000,2026-03-31
TRANSPORT,Kinondoni Bus Service,150000,2026-03-31
MEALS,Hot Lunch Plan,120000,2026-03-31`;
      filename = 'sample_fee_structures_std3.csv';
    }

    const demoBlob = new Blob([demoCsv], { type: 'text/csv;charset=utf-8;' });
    const demoFile = new File([demoBlob], filename, { type: 'text/csv' });
    setFile(demoFile);
    setMessage(
      language === 'sw'
        ? `Faili la majaribio '${filename}' limepakiwa tayari. Bofya 'Pakia na Uhakiki' kuendelea.`
        : `Sample demo file '${filename}' loaded. Click 'Upload & Validate' to inspect.`
    );
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setMessage(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workflow_type', workflow);

    try {
      const res = await api.post('/imports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setBatchId(res.data.batch_id);
      setBatchStatus(res.data);
      await loadPreviewAndErrors(res.data.batch_id);
      setActiveTab('preview');
      fetchHistory();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const loadPreviewAndErrors = async (id: string) => {
    try {
      const [prevRes, errRes, statRes] = await Promise.all([
        api.get(`/imports/${id}/preview`),
        api.get(`/imports/${id}/errors`),
        api.get(`/imports/${id}`),
      ]);
      setPreviewRows(prevRes.data.rows);
      setErrors(errRes.data.errors);
      setBatchStatus(statRes.data);
    } catch (err) {
      console.error('Failed to load preview details', err);
    }
  };

  const handleCommit = async () => {
    if (!batchId) return;
    setLoading(true);
    try {
      await api.post(`/imports/${batchId}/approve`);
      await api.post(`/imports/${batchId}/commit`);
      setMessage(language === 'sw' ? 'Mchakato umekamilika na data zimehifadhiwa kikamilifu!' : 'Import successfully committed into database!');
      await loadPreviewAndErrors(batchId);
      fetchHistory();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Commit failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = async (id: string) => {
    if (!confirm(language === 'sw' ? 'Una uhakika unataka kurudisha nyuma mabadiliko haya?' : 'Are you sure you want to revert this import?')) return;
    setLoading(true);
    try {
      await api.post(`/imports/${id}/revert`);
      setMessage(language === 'sw' ? 'Mabadiliko yamerudishwa nyuma kikamilifu!' : 'Import reverted successfully!');
      if (batchId === id) {
        await loadPreviewAndErrors(id);
      }
      fetchHistory();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Reversion failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <FileSpreadsheet className="w-7 h-7 text-teal-600" />
            {language === 'sw' ? 'Kituo cha Kupakia Excel na CSV' : 'Unified Excel Import Center'}
          </h1>
          <p className="text-slate-600 text-sm">
            {language === 'sw' 
              ? 'Pakia wanafunzi, matokeo, miundo ya ada na masalio kwa usalama na uhakiki kamili.' 
              : 'Safely upload student rosters, exam marks, fee schedules, and balances with preview & rollback.'}
          </p>
        </div>
        <button
          onClick={handleDownloadTemplate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm"
        >
          <Download className="w-4 h-4 text-teal-600" />
          {language === 'sw' ? 'Pakua Kiolezo (Template)' : 'Download Template'}
        </button>
      </div>

      {/* Workflow Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { id: 'STUDENT_REGISTRATION', label: language === 'sw' ? 'Usajili wa Wanafunzi' : 'Student Enrollment', desc: 'Roster & Guardians' },
          { id: 'EXAM_RESULTS', label: language === 'sw' ? 'Matokeo ya Mitihani' : 'Exam Results', desc: 'Multi-Subject Scores' },
          { id: 'FEE_STRUCTURES', label: language === 'sw' ? 'Miundo ya Ada' : 'Fee Structures', desc: 'Tuition & Plans' },
          { id: 'FEE_BALANCES', label: language === 'sw' ? 'Masalio ya Ada' : 'Fee Balances', desc: 'Snapshot Balances' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => {
              setWorkflow(t.id as any);
              setBatchId(null);
              setBatchStatus(null);
              setActiveTab('upload');
            }}
            className={`p-4 text-left rounded-xl border transition ${
              workflow === t.id
                ? 'border-teal-500 bg-teal-50/50 shadow-sm'
                : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            <div className={`font-semibold text-sm ${workflow === t.id ? 'text-teal-900' : 'text-slate-800'}`}>
              {t.label}
            </div>
            <div className="text-xs text-slate-500 mt-1">{t.desc}</div>
          </button>
        ))}
      </div>

      {/* Main Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6">
          {[
            { id: 'upload', label: language === 'sw' ? 'Pakia Faili' : 'Upload File', icon: Upload },
            { id: 'preview', label: language === 'sw' ? 'Hakiki Data (Preview)' : 'Preview Staging', icon: FileText, count: previewRows.length },
            { id: 'errors', label: language === 'sw' ? 'Ripoti ya Hitilafu' : 'Validation Errors', icon: AlertTriangle, count: errors.length, error: errors.length > 0 },
            { id: 'history', label: language === 'sw' ? 'Historia ya Upakiaji' : 'Import History', icon: Clock },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-4 px-4 text-sm font-medium border-b-2 transition ${
                  activeTab === tab.id
                    ? 'border-teal-600 text-teal-700 bg-white'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                <Icon className={`w-4 h-4 ${tab.error ? 'text-rose-500' : ''}`} />
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${tab.error ? 'bg-rose-100 text-rose-700' : 'bg-slate-200 text-slate-700'}`}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {message && (
            <div className="mb-6 p-4 rounded-lg bg-teal-50 border border-teal-200 text-teal-900 text-sm flex items-center justify-between">
              <span>{message}</span>
              <button onClick={() => setMessage(null)} className="text-teal-700 font-bold">×</button>
            </div>
          )}

          {/* TAB 1: UPLOAD */}
          {activeTab === 'upload' && (
            <div className="max-w-2xl mx-auto py-8">
              <form onSubmit={handleUpload} className="space-y-6">
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-teal-500 transition bg-slate-50/50">
                  <FileSpreadsheet className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-sm font-medium text-slate-700 mb-1">
                    {language === 'sw' ? 'Chagua faili la Excel (.xlsx) au CSV' : 'Select an Excel (.xlsx) or CSV file'}
                  </p>
                  <p className="text-xs text-slate-500 mb-4">
                    {language === 'sw' ? 'Upeo wa ukubwa wa faili: 15MB. Fomula zote zitalindwa.' : 'Maximum file size: 15MB. Formula injection protected.'}
                  </p>
                  <input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
                  />

                  <div className="mt-4 pt-3 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <span className="text-xs text-slate-500 font-medium">
                      {language === 'sw' ? 'Au tumia faili la majaribio:' : 'Or use demo test data:'}
                    </span>
                    <button
                      type="button"
                      onClick={handleLoadDemoFile}
                      className="px-3 py-1.5 rounded-lg bg-teal-50 border border-teal-200 text-teal-800 text-xs font-bold hover:bg-teal-100 transition shadow-xs flex items-center gap-1.5"
                    >
                      <FileSpreadsheet className="w-3.5 h-3.5 text-teal-600" />
                      <span>{language === 'sw' ? 'Pakia Faili la Majaribio (Kelvin & 0683312365)' : 'Load Demo Sample (Kelvin & 0683312365)'}</span>
                    </button>
                  </div>
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    type="submit"
                    disabled={!file || loading}
                    className="px-6 py-2.5 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 transition disabled:opacity-50 flex items-center gap-2 shadow-sm"
                  >
                    {loading ? (
                      <span>{language === 'sw' ? 'Inachakata...' : 'Processing...'}</span>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        {language === 'sw' ? 'Pakia na Uhakiki' : 'Upload & Validate'}
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 2: PREVIEW */}
          {activeTab === 'preview' && (
            <div className="space-y-6">
              {batchStatus && (
                <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="text-xs text-slate-500">{language === 'sw' ? 'Jumla ya Mistari' : 'Total Rows'}</div>
                    <div className="text-xl font-bold text-slate-800">{batchStatus.total_rows}</div>
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                    <div className="text-xs text-emerald-700">{language === 'sw' ? 'Rekodi Mpya' : 'New Records'}</div>
                    <div className="text-xl font-bold text-emerald-800">{batchStatus.new_records}</div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="text-xs text-blue-700">{language === 'sw' ? 'Zitakazohuishwa' : 'Updates'}</div>
                    <div className="text-xl font-bold text-blue-800">{batchStatus.updated_records || 0}</div>
                  </div>
                  <div className="p-3 bg-rose-50 rounded-lg border border-rose-200">
                    <div className="text-xs text-rose-700">{language === 'sw' ? 'Zenye Makosa' : 'Errors/Rejected'}</div>
                    <div className="text-xl font-bold text-rose-800">{batchStatus.rejected_records}</div>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <div className="text-xs text-amber-700">{language === 'sw' ? 'Rudufu' : 'Duplicates'}</div>
                    <div className="text-xl font-bold text-amber-800">{batchStatus.duplicate_records || 0}</div>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <div className="text-xs text-purple-700">{language === 'sw' ? 'Hali' : 'Status'}</div>
                    <div className="text-sm font-bold text-purple-800">{batchStatus.status}</div>
                  </div>
                </div>
              )}

              {/* Action Toolbar */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-sm text-slate-600 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  {language === 'sw' ? 'Hakiki data zilizopo kwenye staging kabla ya kuhifadhi rasmi.' : 'Verify staged rows before committing permanently.'}
                </div>
                {batchStatus?.status === 'PREVIEW_READY' && (
                  <button
                    onClick={handleCommit}
                    disabled={loading}
                    className="px-5 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 transition flex items-center gap-2 shadow-sm"
                  >
                    <Check className="w-4 h-4" />
                    {language === 'sw' ? 'Thibitisha na Hifadhi (Commit)' : 'Approve & Commit'}
                  </button>
                )}
              </div>

              {/* Staged Table */}
              <div className="border border-slate-200 rounded-lg overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-100 text-slate-700 text-xs uppercase font-semibold">
                    <tr>
                      <th className="py-3 px-4">#</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Hali' : 'Status'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Kitendo' : 'Action'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Data za Mstari' : 'Row Details'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Hitilafu' : 'Errors'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {previewRows.map((row) => (
                      <tr key={row.row_number} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-4 font-mono text-xs">{row.row_number}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            row.status === 'VALID' || row.status === 'COMMITTED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-rose-100 text-rose-800'
                          }`}>
                            {row.status === 'VALID' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                            {row.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-semibold text-xs text-slate-700">{row.action_type}</td>
                        <td className="py-3 px-4 font-mono text-xs text-slate-800 max-w-md truncate">
                          {JSON.stringify(row.data)}
                        </td>
                        <td className="py-3 px-4 text-xs text-rose-600">{row.error_summary || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: ERRORS */}
          {activeTab === 'errors' && (
            <div className="space-y-4">
              {errors.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                  <p className="font-medium">{language === 'sw' ? 'Hakuna hitilafu yoyote iliyogunduliwa!' : 'No validation errors found!'}</p>
                </div>
              ) : (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-rose-50 text-rose-900 text-xs uppercase font-semibold">
                      <tr>
                        <th className="py-3 px-4">Mstari (Row)</th>
                        <th className="py-3 px-4">Safu (Column)</th>
                        <th className="py-3 px-4">Nambari ya Kosa</th>
                        <th className="py-3 px-4">Maelezo</th>
                        <th className="py-3 px-4">Thamani Iliyopo</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {errors.map((err, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-3 px-4 font-mono font-bold text-slate-800">{err.row_number}</td>
                          <td className="py-3 px-4 font-mono text-slate-700">{err.column_name}</td>
                          <td className="py-3 px-4 text-xs font-semibold text-rose-700">{err.error_code}</td>
                          <td className="py-3 px-4 text-slate-800">{err.error_message}</td>
                          <td className="py-3 px-4 font-mono text-xs text-slate-500">{err.raw_value || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: HISTORY */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-100 text-slate-700 text-xs uppercase font-semibold">
                    <tr>
                      <th className="py-3 px-4">{language === 'sw' ? 'Tarehe' : 'Date'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Aina ya Mchakato' : 'Workflow'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Hali' : 'Status'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Mistari' : 'Rows'}</th>
                      <th className="py-3 px-4">{language === 'sw' ? 'Mpya / Zilizohuishwa' : 'New / Updated'}</th>
                      <th className="py-3 px-4 text-right">{language === 'sw' ? 'Kitendo' : 'Actions'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {history.map((h) => (
                      <tr key={h.id} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-4 text-xs text-slate-600">{new Date(h.created_at).toLocaleString()}</td>
                        <td className="py-3 px-4 font-semibold text-xs text-slate-800">{h.workflow_type}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            h.status === 'COMMITTED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : h.status === 'REVERTED'
                              ? 'bg-slate-100 text-slate-600'
                              : 'bg-amber-100 text-amber-800'
                          }`}>
                            {h.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-xs">{h.total_rows}</td>
                        <td className="py-3 px-4 text-xs text-slate-600">{h.new_records} / {h.updated_records}</td>
                        <td className="py-3 px-4 text-right">
                          {h.status === 'COMMITTED' && (
                            <button
                              onClick={() => handleRevert(h.id)}
                              className="inline-flex items-center gap-1 px-3 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded text-xs font-semibold transition"
                            >
                              <RotateCcw className="w-3.5 h-3.5" />
                              {language === 'sw' ? 'Rudisha Nyuma (Revert)' : 'Revert'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
