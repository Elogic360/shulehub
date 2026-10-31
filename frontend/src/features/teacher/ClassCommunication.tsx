import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Send,
  MessageSquare,
  Users,
  User,
  Calculator,
  Eye,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
} from 'lucide-react';

export const ClassCommunication: React.FC = () => {
  const { t, user } = useAuth();
  const queryClient = useQueryClient();

  // Targeting mode: CLASS_BULK | SELECTED_GUARDIANS | INDIVIDUAL
  const [targetingMode, setTargetingMode] = useState<'CLASS_BULK' | 'SELECTED_GUARDIANS' | 'INDIVIDUAL'>('CLASS_BULK');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedGuardianIds, setSelectedGuardianIds] = useState<string[]>([]);
  const [title, setTitle] = useState('');
  const [messageContent, setMessageContent] = useState('');

  // Preview & estimation state
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [dispatchSuccess, setDispatchSuccess] = useState<string | null>(null);

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

  const { data: students = [] } = useQuery({
    queryKey: ['students_for_selection', selectedClassId],
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

  const { data: templates = [] } = useQuery({
    queryKey: ['message_templates'],
    queryFn: async () => (await api.get('/communication/templates/all')).data,
  });

  // Calculate live characters & segments estimate
  const charLength = messageContent.length;
  const estimatedSegments = charLength <= 160 ? 1 : Math.ceil(charLength / 153);

  // Preview Mutation
  const previewMutation = useMutation({
    mutationFn: async (payload: any) => (await api.post('/communication/preview', payload)).data,
    onSuccess: (data) => {
      setPreviewData(data);
      setIsPreviewing(true);
    },
  });

  // Dispatch Mutation
  const dispatchMutation = useMutation({
    mutationFn: async (payload: any) => (await api.post('/communication', payload)).data,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['class_campaigns'] });
      setDispatchSuccess(`Ujumbe umetumwa kwa wazazi ${data.recipient_count}!`);
      setTitle('');
      setMessageContent('');
      setPreviewData(null);
      setIsPreviewing(false);
      setTimeout(() => setDispatchSuccess(null), 4000);
    },
  });

  const handlePreview = () => {
    previewMutation.mutate({
      title,
      message_content: messageContent,
      targeting_mode: targetingMode,
      class_group_id: selectedClassId,
      guardian_ids: targetingMode !== 'CLASS_BULK' ? selectedGuardianIds : undefined,
    });
  };

  const handleDispatch = (e: React.FormEvent) => {
    e.preventDefault();
    dispatchMutation.mutate({
      title,
      message_content: messageContent,
      targeting_mode: targetingMode,
      class_group_id: selectedClassId,
      guardian_ids: targetingMode !== 'CLASS_BULK' ? selectedGuardianIds : undefined,
    });
  };

  const insertVariable = (varName: string) => {
    setMessageContent((prev) => `${prev} {{${varName}}}`);
  };

  const toggleGuardianSelection = (guardianId: string) => {
    if (targetingMode === 'INDIVIDUAL') {
      setSelectedGuardianIds([guardianId]);
    } else {
      setSelectedGuardianIds((prev) =>
        prev.includes(guardianId) ? prev.filter((id) => id !== guardianId) : [...prev, guardianId]
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Class Communication Center', 'Kituo cha Mawasiliano ya Darasa')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Dispatch targeted SMS announcements directly to guardians with delivery tracking.', 'Tuma matangazo na ujumbe mfupi wa SMS moja kwa moja kwa wazazi.')}
          </p>
        </div>

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
      </div>

      {dispatchSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <span>{dispatchSuccess}</span>
        </div>
      )}

      {/* Main Composer & Targeting Modes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Composer Left Column (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
            {/* 1. Targeting Mode Switcher */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                {t('Targeting Mode', 'Hali ya Utumaji')}
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => { setTargetingMode('CLASS_BULK'); setSelectedGuardianIds([]); }}
                  className={`p-3 rounded-lg border text-xs font-bold transition flex flex-col items-center gap-1.5 ${
                    targetingMode === 'CLASS_BULK'
                      ? 'border-brand-teal bg-brand-navy text-white shadow-sm'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <Users className="w-4 h-4 text-brand-teal" />
                  <span>{t('Class Bulk (All)', 'Darasa Zima (Wote)')}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setTargetingMode('SELECTED_GUARDIANS')}
                  className={`p-3 rounded-lg border text-xs font-bold transition flex flex-col items-center gap-1.5 ${
                    targetingMode === 'SELECTED_GUARDIANS'
                      ? 'border-brand-teal bg-brand-navy text-white shadow-sm'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{t('Selected Parents', 'Wazazi Walioteuliwa')}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setTargetingMode('INDIVIDUAL')}
                  className={`p-3 rounded-lg border text-xs font-bold transition flex flex-col items-center gap-1.5 ${
                    targetingMode === 'INDIVIDUAL'
                      ? 'border-brand-teal bg-brand-navy text-white shadow-sm'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <User className="w-4 h-4 text-brand-accent" />
                  <span>{t('Individual Parent', 'Mzazi Mmoja')}</span>
                </button>
              </div>
            </div>

            {/* If Selected or Individual, show guardian picker */}
            {targetingMode !== 'CLASS_BULK' && (
              <div className="border border-slate-200 rounded-lg p-3 bg-slate-50 max-h-48 overflow-y-auto space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  {targetingMode === 'INDIVIDUAL'
                    ? t('Select One Guardian:', 'Chagua Mzazi Mmoja:')
                    : t('Check Guardians to Receive Message:', 'Chagua Wazazi Watakaopokea:')}
                </span>
                {students.map((st: any) => {
                  const g = st.guardians?.[0];
                  if (!g) return null;
                  const isChecked = selectedGuardianIds.includes(g.id);
                  return (
                    <label
                      key={st.id}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer text-xs transition ${
                        isChecked ? 'bg-brand-navy/10 font-bold text-brand-navy' : 'hover:bg-slate-100 text-slate-700'
                      }`}
                    >
                      <input
                        type={targetingMode === 'INDIVIDUAL' ? 'radio' : 'checkbox'}
                        checked={isChecked}
                        onChange={() => toggleGuardianSelection(g.id)}
                        className="text-brand-teal focus:ring-brand-teal"
                      />
                      <span>{g.full_name} ({st.first_name} {st.last_name} &bull; {g.primary_phone})</span>
                    </label>
                  );
                })}
              </div>
            )}

            {/* Campaign Title */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {t('Announcement Title', 'Kichwa cha Tangazo')}
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Kikao cha Wazazi cha Muhula wa Kwanza"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
              />
            </div>

            {/* Message Body & Variable Chips */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  {t('Message Content (SMS Text)', 'Yaliyomo Katika Ujumbe (SMS)')}
                </label>
                <span className="text-[11px] text-slate-400 font-medium">
                  {charLength} herufi &bull; {estimatedSegments} {t('segment(s)', 'SMS')}
                </span>
              </div>

              {/* Dynamic Variable Chips */}
              <div className="flex flex-wrap gap-1.5 mb-2">
                {[
                  { name: 'parent_name', label: 'Jina la Mzazi' },
                  { name: 'student_name', label: 'Jina la Mwanafunzi' },
                  { name: 'class_name', label: 'Darasa' },
                  { name: 'school_name', label: 'Jina la Shule' },
                ].map((v) => (
                  <button
                    key={v.name}
                    type="button"
                    onClick={() => insertVariable(v.name)}
                    className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300/80 transition"
                  >
                    + {`{{${v.name}}}`}
                  </button>
                ))}
              </div>

              <textarea
                required
                rows={4}
                value={messageContent}
                onChange={(e) => setMessageContent(e.target.value)}
                placeholder="Habari {{parent_name}}, tunapenda kuwajulisha kuwa..."
                className="w-full p-3 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal leading-relaxed"
              ></textarea>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={handlePreview}
                disabled={!messageContent || previewMutation.isPending}
                className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition flex items-center gap-1.5"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>{previewMutation.isPending ? t('Checking...', 'Inahakiki...') : t('Preview & Cost', 'Hakiki & Makadirio')}</span>
              </button>

              <button
                type="button"
                onClick={handleDispatch}
                disabled={!title || !messageContent || dispatchMutation.isPending}
                className="px-5 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-bold shadow-md transition flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5 text-brand-teal" />
                <span>{dispatchMutation.isPending ? t('Dispatching...', 'Inatuma...') : t('Send Campaign', 'Tuma Sasa')}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Preview & Estimation Right Column (1 col) */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Calculator className="w-3.5 h-3.5 text-brand-teal" />
              <span>{t('Dispatch Estimation', 'Makadirio ya Utumaji')}</span>
            </h3>

            {previewData ? (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-1">
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>{t('Eligible Recipients:', 'Idadi ya Wazazi:')}</span>
                    <span className="font-bold text-brand-navy">{previewData.unique_recipients_count}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>{t('Total SMS Segments:', 'Jumla ya SMS:')}</span>
                    <span className="font-bold text-brand-navy">{previewData.total_segments}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-600 pt-1 border-t border-slate-200">
                    <span>{t('Estimated Cost:', 'Gharama ya Jumla:')}</span>
                    <span className="font-bold text-emerald-600">TZS {previewData.estimated_total_cost_tzs.toLocaleString()}</span>
                  </div>
                </div>

                {previewData.preview_sample?.[0] && (
                  <div>
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                      {t('Simulated Handset SMS Preview:', 'Muonekano wa SMS kwa Mzazi:')}
                    </span>
                    <div className="p-3 rounded-xl bg-slate-900 text-slate-100 text-xs font-mono border border-slate-800 leading-relaxed">
                      {previewData.preview_sample[0].rendered_text}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-400">
                {t('Click "Preview & Cost" to inspect recipient rendering and SMS cost before sending.', 'Bofya "Hakiki & Makadirio" kutazama muonekano kabla ya kutuma.')}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Campaign Delivery Reports Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-brand-navy">
            {t('Recent Class Campaigns & Delivery Logs', 'Kumbukumbu za Ujumbe Uliotumwa')}
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">{t('Title & Message', 'Kichwa na Ujumbe')}</th>
                <th className="px-5 py-3">{t('Targeting', 'Walengwa')}</th>
                <th className="px-5 py-3">{t('Recipients', 'Wapokeaji')}</th>
                <th className="px-5 py-3">{t('Cost (TZS)', 'Gharama')}</th>
                <th className="px-5 py-3">{t('Status', 'Hali')}</th>
                <th className="px-5 py-3">{t('Date', 'Tarehe')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {campaigns.map((camp: any) => (
                <tr key={camp.id} className="hover:bg-slate-50/60 transition">
                  <td className="px-5 py-3.5 max-w-xs">
                    <span className="font-bold text-xs text-brand-navy block">
                      {camp.title}
                    </span>
                    <span className="text-[11px] text-slate-400 truncate block">
                      {camp.message_content}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-600 font-medium">
                    {camp.targeting_mode.replace('_', ' ')}
                  </td>
                  <td className="px-5 py-3.5 text-xs font-bold text-brand-navy">
                    {camp.delivered_count} / {camp.recipient_count}
                  </td>
                  <td className="px-5 py-3.5 text-xs font-semibold text-slate-700">
                    {Number(camp.total_cost_tzs).toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                      {camp.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-400">
                    {new Date(camp.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {campaigns.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-sm text-slate-400">
                    {t('No communication campaigns dispatched yet.', 'Bado hakuna jumbe zilizotumwa.')}
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
