import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Receipt, Plus, DollarSign, Calendar, CheckCircle2, AlertCircle, Bell } from 'lucide-react';

export const FeeManagement: React.FC = () => {
  const { t } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'invoices' | 'structures' | 'reminders'>('invoices');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showStructureModal, setShowStructureModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);

  // Payment form state
  const [studentId, setStudentId] = useState('');
  const [amount, setAmount] = useState<number>(100000);
  const [paymentMethod, setPaymentMethod] = useState('BANK_TRANSFER');
  const [txnRef, setTxnRef] = useState('');

  // Structure form state
  const [structureName, setStructureName] = useState('');
  const [structureAmount, setStructureAmount] = useState<number>(450000);
  const [dueDate, setDueDate] = useState('2026-03-31');
  const [selectedCatId, setSelectedCatId] = useState('');

  // Assignment form state
  const [assignStructId, setAssignStructId] = useState('');
  const [assignClassId, setAssignClassId] = useState('');

  // Queries
  const { data: summary } = useQuery({
    queryKey: ['fee_summary'],
    queryFn: async () => (await api.get('/fees/reports/summary')).data,
  });

  const { data: invoices = [], isLoading: loadingInvoices } = useQuery({
    queryKey: ['fee_invoices'],
    queryFn: async () => (await api.get('/fees/invoices')).data,
  });

  const { data: structures = [] } = useQuery({
    queryKey: ['fee_structures'],
    queryFn: async () => (await api.get('/fees/structures')).data,
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['fee_categories'],
    queryFn: async () => (await api.get('/fees/categories')).data,
  });

  const { data: classes = [] } = useQuery({
    queryKey: ['academic_classes'],
    queryFn: async () => (await api.get('/academic/classes')).data,
  });

  const { data: years = [] } = useQuery({
    queryKey: ['academic_years'],
    queryFn: async () => (await api.get('/academic/years')).data,
  });

  const { data: reminderRules = [] } = useQuery({
    queryKey: ['fee_reminder_rules'],
    queryFn: async () => (await api.get('/fees/rules')).data,
  });

  // Mutations
  const recordPaymentMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/fees/payments', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fee_invoices'] });
      queryClient.invalidateQueries({ queryKey: ['fee_summary'] });
      setShowPaymentModal(false);
      setStudentId('');
      setTxnRef('');
    },
  });

  const createStructureMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/fees/structures', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fee_structures'] });
      setShowStructureModal(false);
    },
  });

  const assignFeeMutation = useMutation({
    mutationFn: async (payload: any) => api.post('/fees/assignments', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fee_invoices'] });
      queryClient.invalidateQueries({ queryKey: ['fee_summary'] });
      setShowAssignModal(false);
    },
  });

  const handleRecordPayment = (e: React.FormEvent) => {
    e.preventDefault();
    recordPaymentMutation.mutate({
      student_id: studentId,
      payment_date: new Date().toISOString().split('T')[0],
      amount_tzs: amount,
      payment_method: paymentMethod,
      transaction_reference: txnRef,
    });
  };

  const handleCreateStructure = (e: React.FormEvent) => {
    e.preventDefault();
    if (!years[0]?.id || !selectedCatId) return;
    createStructureMutation.mutate({
      academic_year_id: years[0].id,
      fee_category_id: selectedCatId,
      name: structureName,
      amount_tzs: structureAmount,
      due_date: dueDate,
    });
  };

  const handleAssignFee = (e: React.FormEvent) => {
    e.preventDefault();
    assignFeeMutation.mutate({
      fee_structure_id: assignStructId,
      class_group_id: assignClassId,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-navy">
            {t('School Fees & Revenue Management', 'Usimamizi wa Ada na Mapato ya Shule')}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {t('Fee structures, invoicing, verified payment recording and automated SMS reminders.', 'Panga ada, toa ankara, rekodi malipo ya benki na ratibu vikumbusho vya SMS.')}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (categories.length > 0) setSelectedCatId(categories[0].id);
              setShowStructureModal(true);
            }}
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{t('New Fee Structure', 'Muundo Mpya wa Ada')}</span>
          </button>
          <button
            onClick={() => {
              if (structures.length > 0) setAssignStructId(structures[0].id);
              if (classes.length > 0) setAssignClassId(classes[0].id);
              setShowAssignModal(true);
            }}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <Receipt className="w-3.5 h-3.5" />
            <span>{t('Assign Fee to Class', 'Gawia Darasa Ada')}</span>
          </button>
          <button
            onClick={() => setShowPaymentModal(true)}
            className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <DollarSign className="w-3.5 h-3.5" />
            <span>{t('Record Payment', 'Rekodi Malipo')}</span>
          </button>
        </div>
      </div>

      {/* Financial Health Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Total Invoiced', 'Jumla ya Ankara (Invoiced)')}
          </span>
          <div className="text-2xl font-black text-brand-navy mt-1">
            TZS {Number(summary?.total_invoiced_tzs || 0).toLocaleString()}
          </div>
          <span className="text-xs text-slate-500 mt-1 block">
            {summary?.paid_invoices_count || 0} {t('paid in full', 'zimelipwa zote')}
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Total Collected', 'Jumla Iliyokusanywa')}
          </span>
          <div className="text-2xl font-black text-emerald-600 mt-1">
            TZS {Number(summary?.total_collected_tzs || 0).toLocaleString()}
          </div>
          <span className="text-xs text-emerald-600 font-bold mt-1 block">
            {summary?.collection_rate_pct || 0}% {t('collection rate', 'kiwango cha makusanyo')}
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
            {t('Outstanding Balance', 'Baki Inayodaiwa')}
          </span>
          <div className="text-2xl font-black text-rose-600 mt-1">
            TZS {Number(summary?.total_outstanding_tzs || 0).toLocaleString()}
          </div>
          <span className="text-xs text-slate-500 mt-1 block">
            {summary?.pending_invoices_count || 0} {t('invoices overdue / partial', 'ankara zinazodaiwa')}
          </span>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('invoices')}
          className={`py-2.5 px-4 text-xs font-bold border-b-2 transition ${
            activeTab === 'invoices' ? 'border-brand-teal text-brand-navy' : 'border-transparent text-slate-500'
          }`}
        >
          {t('Invoices & Statements', 'Orodha ya Ankara na Baki')}
        </button>
        <button
          onClick={() => setActiveTab('structures')}
          className={`py-2.5 px-4 text-xs font-bold border-b-2 transition ${
            activeTab === 'structures' ? 'border-brand-teal text-brand-navy' : 'border-transparent text-slate-500'
          }`}
        >
          {t('Fee Structures', 'Miundo ya Ada')}
        </button>
        <button
          onClick={() => setActiveTab('reminders')}
          className={`py-2.5 px-4 text-xs font-bold border-b-2 transition ${
            activeTab === 'reminders' ? 'border-brand-teal text-brand-navy' : 'border-transparent text-slate-500'
          }`}
        >
          {t('Automated Reminder Rules', 'Sheria za Vikumbusho')}
        </button>
      </div>

      {/* Tab 1: Invoices */}
      {activeTab === 'invoices' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">{t('Invoice #', 'Namba ya Ankara')}</th>
                  <th className="px-5 py-3">{t('Student', 'Mwanafunzi')}</th>
                  <th className="px-5 py-3">{t('Total (TZS)', 'Jumla')}</th>
                  <th className="px-5 py-3">{t('Balance Due', 'Baki')}</th>
                  <th className="px-5 py-3">{t('Due Date', 'Mwisho')}</th>
                  <th className="px-5 py-3">{t('Status', 'Hali')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invoices.map((inv: any) => (
                  <tr key={inv.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-5 py-3.5 font-bold text-brand-navy text-xs">
                      {inv.invoice_number}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-semibold text-slate-800 text-xs block">
                        {inv.student_name}
                      </span>
                      <span className="text-[10px] text-slate-400 block">
                        {inv.admission_number}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-700 font-medium">
                      {Number(inv.total_amount_tzs).toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5 text-xs font-bold text-rose-600">
                      {Number(inv.balance_due_tzs).toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">
                      {inv.due_date}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        inv.status === 'PAID'
                          ? 'bg-emerald-100 text-emerald-800'
                          : inv.status === 'PARTIALLY_PAID'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}>
                        {inv.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && !loadingInvoices && (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-sm text-slate-400">
                      {t('No fee invoices generated yet.', 'Hakuna ankara zilizotolewa bado.')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Structures */}
      {activeTab === 'structures' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {structures.map((s: any) => (
              <div key={s.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 uppercase">
                  {s.category_name || 'Fee'}
                </span>
                <h4 className="font-bold text-brand-navy text-sm">{s.name}</h4>
                <div className="text-xl font-black text-emerald-600">
                  TZS {Number(s.amount_tzs).toLocaleString()}
                </div>
                <span className="text-xs text-slate-400 block">
                  {t('Due Date', 'Tarehe ya Mwisho')}: {s.due_date}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Reminders */}
      {activeTab === 'reminders' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h3 className="text-sm font-bold text-brand-navy flex items-center gap-2">
            <Bell className="w-4 h-4 text-brand-teal" />
            <span>{t('Automated SMS Fee Reminder Schedule', 'Ratiba ya Vikumbusho vya Ada kwa SMS')}</span>
          </h3>
          <p className="text-xs text-slate-500">
            {t(
              'Configured intervals trigger daily at 09:00 EAT via Celery Beat, notifying guardians of outstanding balances automatically.',
              'Muda uliowekwa huchochea utumaji wa SMS kila siku saa 3:00 Asubuhi kupitia Celery Beat, kuwakumbusha wazazi wenye baki.'
            )}
          </p>

          <div className="divide-y divide-slate-100">
            <div className="py-3 flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-slate-800 block">14 Siku Kabla (Advance Reminder)</span>
                <span className="text-xs text-slate-400">14 days before payment deadline</span>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">Active</span>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-slate-800 block">Siku ya Mwisho (Due Date Reminder)</span>
                <span className="text-xs text-slate-400">On the exact payment due date</span>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">Active</span>
            </div>
            <div className="py-3 flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-slate-800 block">7 Siku Baada ya Tarehe (Overdue Reminder)</span>
                <span className="text-xs text-slate-400">7 days past deadline for unpaid balances</span>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">Active</span>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Record Payment */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Record Student Fee Payment', 'Rekodi Malipo ya Mwanafunzi')}
            </h3>

            <form onSubmit={handleRecordPayment} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Student ID', 'ID ya Mwanafunzi')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="Student UUID"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Amount (TZS)', 'Kiasi Kilicholipwa (TZS)')}
                </label>
                <input
                  type="number"
                  required
                  min={1000}
                  step={500}
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal font-bold text-emerald-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Payment Method', 'Njia ya Malipo')}
                  </label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  >
                    <option value="BANK_TRANSFER">Bank Transfer (CRDB/NMB)</option>
                    <option value="M_PESA">M-Pesa</option>
                    <option value="AIRTEL_MONEY">Airtel Money</option>
                    <option value="TIGO_PESA">Tigo Pesa</option>
                    <option value="HALOPESA">HaloPesa</option>
                    <option value="CASH">Cash</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Reference #', 'Namba ya Muamala')}
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. CRDB-TXN-998"
                    value={txnRef}
                    onChange={(e) => setTxnRef(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowPaymentModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={recordPaymentMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow-sm transition"
                >
                  {recordPaymentMutation.isPending ? t('Saving...', 'Inahifadhi...') : t('Confirm & Issue Receipt', 'Thibitisha na Toa Risiti')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Structure */}
      {showStructureModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('New Fee Structure', 'Muundo Mpya wa Ada')}
            </h3>

            <form onSubmit={handleCreateStructure} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Category', 'Kundi la Ada')}
                </label>
                <select
                  value={selectedCatId}
                  onChange={(e) => setSelectedCatId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                >
                  {categories.map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Structure Name', 'Jina la Ada')}
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Tuition Term 1 2026"
                  value={structureName}
                  onChange={(e) => setStructureName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Amount (TZS)', 'Kiasi (TZS)')}
                  </label>
                  <input
                    type="number"
                    required
                    value={structureAmount}
                    onChange={(e) => setStructureAmount(Number(e.target.value))}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('Due Date', 'Tarehe ya Mwisho')}
                  </label>
                  <input
                    type="date"
                    required
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-teal"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowStructureModal(false)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition"
                >
                  {t('Cancel', 'Ghairi')}
                </button>
                <button
                  type="submit"
                  disabled={createStructureMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-brand-navy hover:bg-slate-800 text-white text-sm font-semibold shadow-sm transition"
                >
                  {createStructureMutation.isPending ? t('Saving...', 'Inahifadhi...') : t('Create Structure', 'Unda Muundo')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Assign Fee */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-brand-navy mb-4">
              {t('Assign Fee Structure to Class', 'Gawia Darasa Zima Ada Hii')}
            </h3>

            <form onSubmit={handleAssignFee} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Fee Structure', 'Muundo wa Ada')}
                </label>
                <select
                  value={assignStructId}
                  onChange={(e) => setAssignStructId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                >
                  {structures.map((s: any) => (
                    <option key={s.id} value={s.id}>
                      {s.name} - TZS {Number(s.amount_tzs).toLocaleString()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('Target Class Group', 'Darasa Linalolengwa')}
                </label>
                <select
                  value={assignClassId}
                  onChange={(e) => setAssignClassId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-brand-teal"
                >
                  {classes.map((cls: any) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name} ({cls.academic_level_name})
                    </option>
                  ))}
                </select>
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
                  disabled={assignFeeMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition"
                >
                  {assignFeeMutation.isPending ? t('Assigning...', 'Inagawia...') : t('Assign and Generate Invoices', 'Gawia na Toa Ankara')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
