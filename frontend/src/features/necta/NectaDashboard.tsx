import React, { useState, useEffect } from 'react';
import { 
  Award, CheckCircle, XCircle, Search, RefreshCw, Send, 
  ExternalLink, FileText, Check, AlertCircle 
} from 'lucide-react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export const NectaDashboard: React.FC = () => {
  const { language, t } = useAuth();
  const [exams, setExams] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeExamId, setActiveExamId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchExams();
  }, []);

  useEffect(() => {
    if (activeExamId) {
      fetchMatches(activeExamId);
    }
  }, [activeExamId]);

  const fetchExams = async () => {
    try {
      const res = await api.get('/necta/examinations');
      setExams(res.data);
      if (res.data.length > 0 && !activeExamId) {
        setActiveExamId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load NECTA exams', err);
    }
  };

  const fetchMatches = async (examId: string) => {
    try {
      const res = await api.get(`/necta/matches?examination_id=${examId}`);
      setMatches(res.data);
    } catch (err) {
      console.error('Failed to load matches', err);
    }
  };

  const handleAutoMatch = async () => {
    if (!activeExamId) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('examination_id', activeExamId);
      const res = await api.post('/necta/auto-match', formData);
      setMessage(
        language === 'sw'
          ? `Ulinganishaji umekamilika! Wanafunzi ${res.data.exact_matches} wamethibitishwa papo hapo.`
          : `Auto-match completed! ${res.data.exact_matches} candidates matched automatically.`
      );
      fetchMatches(activeExamId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Auto-match failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReviewDecision = async (matchId: string, decision: 'MATCHED' | 'REJECTED') => {
    try {
      const formData = new FormData();
      formData.append('decision', decision);
      await api.post(`/necta/matches/${matchId}/review`, formData);
      if (activeExamId) fetchMatches(activeExamId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Review failed');
    }
  };

  const handleNotifyGuardian = async (matchId: string) => {
    try {
      const res = await api.post(`/necta/matches/${matchId}/notify`);
      alert(language === 'sw' ? 'Ujumbe wa siri umetumwa kwa mzazi!' : 'Confidential notification dispatched to guardian!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Notification failed');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Award className="w-7 h-7 text-teal-600" />
            {language === 'sw' ? 'Matokeo ya Kitaifa (NECTA) na Ulinganishaji' : 'NECTA National Results & Candidate Matching'}
          </h1>
          <p className="text-slate-600 text-sm">
            {language === 'sw'
              ? 'Upatikanaji wa matokeo ya FTNA na CSEE, uhakiki wa namba za watahiniwa na taarifa salama za wazazi.'
              : 'Official FTNA and CSEE assessment provenance, student candidate matching, and confidential parent notifications.'}
          </p>
        </div>
        <button
          onClick={handleAutoMatch}
          disabled={loading || !activeExamId}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {language === 'sw' ? 'Endesha Ulinganishaji (Auto-Match)' : 'Run Auto-Match'}
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-teal-50 border border-teal-200 text-teal-900 text-sm flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-teal-700 font-bold">×</button>
        </div>
      )}

      {/* Examination Selector */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        {exams.map((ex) => (
          <button
            key={ex.id}
            onClick={() => setActiveExamId(ex.id)}
            className={`px-4 py-3 rounded-xl border text-left whitespace-nowrap transition ${
              activeExamId === ex.id
                ? 'border-teal-500 bg-teal-50/50 shadow-sm'
                : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            <div className="font-semibold text-sm text-slate-800">{ex.exam_type} {ex.exam_year}</div>
            <div className="text-xs text-slate-500">{ex.center_number} — {ex.center_name}</div>
          </button>
        ))}
      </div>

      {/* Matching Matrix Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-700">
            {language === 'sw' ? 'Orodha ya Watahiniwa na Ulinganisho wa Wanafunzi' : 'Candidate Matching Verification Matrix'}
          </span>
          <span className="text-xs text-slate-500 font-mono">
            {matches.length} {language === 'sw' ? 'Watahiniwa' : 'Candidates'}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase font-semibold">
              <tr>
                <th className="py-3 px-4">Namba ya Mtahiniwa</th>
                <th className="py-3 px-4">Jina NECTA</th>
                <th className="py-3 px-4">Daraja / Points</th>
                <th className="py-3 px-4">Mwanafunzi Shuleni</th>
                <th className="py-3 px-4">Uwezekano (Confidence)</th>
                <th className="py-3 px-4">Hali (Status)</th>
                <th className="py-3 px-4 text-right">Vitendo (Actions)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {matches.map((m) => (
                <tr key={m.match_id} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">{m.candidate.index_number}</td>
                  <td className="py-3 px-4 font-medium text-slate-800">{m.candidate.candidate_name}</td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      Div {m.candidate.division || '—'} ({m.candidate.points || 0} pts)
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900">{m.student.full_name}</div>
                    <div className="text-xs text-slate-500 font-mono">{m.student.admission_number}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      m.match_confidence >= 0.95
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {(m.match_confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                      m.status === 'MATCHED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : m.status === 'REJECTED'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    {m.status === 'PENDING_REVIEW' && (
                      <>
                        <button
                          onClick={() => handleReviewDecision(m.match_id, 'MATCHED')}
                          className="px-2.5 py-1 bg-emerald-600 text-white rounded text-xs font-semibold hover:bg-emerald-700"
                        >
                          {language === 'sw' ? 'Kubali' : 'Approve'}
                        </button>
                        <button
                          onClick={() => handleReviewDecision(m.match_id, 'REJECTED')}
                          className="px-2.5 py-1 bg-rose-100 text-rose-700 rounded text-xs font-semibold hover:bg-rose-200"
                        >
                          {language === 'sw' ? 'Kataa' : 'Reject'}
                        </button>
                      </>
                    )}
                    {m.status === 'MATCHED' && (
                      <button
                        onClick={() => handleNotifyGuardian(m.match_id)}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-teal-50 text-teal-700 border border-teal-200 rounded text-xs font-semibold hover:bg-teal-100"
                      >
                        <Send className="w-3.5 h-3.5" />
                        {language === 'sw' ? 'Taarifu Mzazi' : 'Notify Parent'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
