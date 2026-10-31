import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Calendar, Plus, Users, CheckCircle2, XCircle, Clock } from 'lucide-react';

export const ClassMeetings: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [meetingDate, setMeetingDate] = useState('2026-03-20');
  const [startTime, setStartTime] = useState('09:00:00');
  const [endTime, setEndTime] = useState('11:30:00');
  const [venue, setVenue] = useState('Ukumbi Mkuu wa Shule');

  // Queries
  const { data: meetings = [], isLoading } = useQuery({
    queryKey: ['school_meetings'],
    queryFn: async () => (await api.get('/meetings')).data,
  });

  const { data: classes = [] } = useQuery({
    queryKey: ['teacher_classes'],
    queryFn: async () => (await api.get('/academic/classes')).data,
  });

  // Create Meeting Mutation
  const createMeetingMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/meetings', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school_meetings'] });
      setShowCreateModal(false);
      setTitle('');
      setDescription('');
    },
  });

  const handleCreateMeeting = (e: React.FormEvent) => {
    e.preventDefault();
    createMeetingMutation.mutate({
      title,
      description,
      meeting_date: meetingDate,
      start_time: startTime,
      end_time: endTime,
      venue,
      class_group_ids: classes.map((c: any) => c.id),
      send_sms_invitation: true,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('Parent-Teacher Meetings & Conferences', 'Mikutano ya Wazazi na Walimu')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Schedule meetings, distribute SMS invitations and track real-time parent RSVPs.', 'Ratibu mikutano, tuma mialiko kwa SMS na fuatilia majibu ya wazazi.')}
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4 text-brand-teal" />
          <span>{t('Schedule Meeting', 'Panga Mkutano Mpya')}</span>
        </button>
      </div>

      {/* Meetings List Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {meetings.map((m: any) => (
          <div key={m.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-bold text-brand-teal uppercase tracking-wider block">
                  {m.venue}
                </span>
                <h3 className="text-base font-bold text-brand-navy mt-0.5">
                  {m.title}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-xs font-bold text-slate-800 block">{m.meeting_date}</span>
                <span className="text-[11px] text-slate-400 block">{m.start_time} - {m.end_time}</span>
              </div>
            </div>

            {m.description && (
              <p className="text-xs text-slate-500 line-clamp-2">
                {m.description}
              </p>
            )}

            {/* Attendance Tally */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold">
              <div className="flex items-center gap-1.5 text-emerald-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>{m.confirmed_count} {t('Confirmed', 'Wanahudhuria')}</span>
              </div>
              <div className="flex items-center gap-1.5 text-rose-700">
                <XCircle className="w-4 h-4 text-rose-600" />
                <span>{m.declined_count} {t('Declined', 'Hawaji')}</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-500">
                <Clock className="w-4 h-4" />
                <span>{m.invitations_count} {t('Invited', 'Mialiko')}</span>
              </div>
            </div>
          </div>
        ))}
        {meetings.length === 0 && !isLoading && (
          <div className="col-span-2 bg-white p-8 rounded-xl border border-slate-200 text-center text-xs text-slate-400">
            {t('No meetings scheduled yet.', 'Bado hakuna mikutano iliyopangwa.')}
          </div>
        )}
      </div>

      {/* Modal: Create Meeting */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Schedule Parent-Teacher Meeting', 'Panga Mkutano wa Wazazi')}
            </h3>

            <form onSubmit={handleCreateMeeting} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Meeting Title', 'Kichwa cha Mkutano')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mkutano wa Maendeleo ya Kitaaluma"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Description / Agenda', 'Ajenda au Maelezo')}
                </label>
                <textarea
                  rows={2}
                  placeholder="Ajenda: Matokeo ya mitihani, michango na maendeleo..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                ></textarea>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Meeting Date', 'Tarehe')}
                  </label>
                  <input
                    type="date"
                    required
                    value={meetingDate}
                    onChange={(e) => setMeetingDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Start Time', 'Muda')}
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="09:00:00"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Venue', 'Ukumbi / Eneo')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ukumbi Mkuu wa Shule"
                  value={venue}
                  onChange={(e) => setVenue(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={createMeetingMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {createMeetingMutation.isPending ? t('Scheduling...', 'Inapanga...') : t('Schedule & Send SMS', 'Panga na Tuma SMS')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
