import React, { useState } from 'react';
import { Smartphone, RotateCcw, Send, CheckCircle, ShieldCheck, PhoneCall } from 'lucide-react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export const UssdSimulator: React.FC = () => {
  const { language, t } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('+255754123456');
  const [serviceCode, setServiceCode] = useState('*384*55#');
  const [userInput, setUserInput] = useState('');
  const [screenText, setScreenText] = useState('Karibu ShuleConnect USSD Simulator.\nBonyeza [Piga] kuanza.');
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [sessionId, setSessionId] = useState(`USSD_SIM_${Date.now()}`);
  const [inputHistory, setInputHistory] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const startSession = async () => {
    setLoading(true);
    const newSessionId = `USSD_SIM_${Date.now()}`;
    setSessionId(newSessionId);
    setInputHistory([]);
    setUserInput('');

    try {
      const formData = new FormData();
      formData.append('sessionId', newSessionId);
      formData.append('serviceCode', serviceCode);
      formData.append('phoneNumber', phoneNumber);
      formData.append('text', '');

      const res = await api.post('/ussd', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setScreenText(res.data);
      setIsSessionActive(!res.data.startsWith('END'));
    } catch (err: any) {
      setScreenText(`Hitilafu: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sendStep = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!userInput.trim() || !isSessionActive) return;

    setLoading(true);
    const updatedHistory = [...inputHistory, userInput.trim()];
    setInputHistory(updatedHistory);
    const combinedText = updatedHistory.join('*');

    try {
      const formData = new FormData();
      formData.append('sessionId', sessionId);
      formData.append('serviceCode', serviceCode);
      formData.append('phoneNumber', phoneNumber);
      formData.append('text', combinedText);

      const res = await api.post('/ussd', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setScreenText(res.data);
      setIsSessionActive(!res.data.startsWith('END'));
      setUserInput('');
    } catch (err: any) {
      setScreenText(`Hitilafu: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Smartphone className="w-7 h-7 text-teal-600" />
          {language === 'sw' ? 'Kifanisi cha USSD (Interactive USSD Simulator)' : 'Interactive USSD Simulator'}
        </h1>
        <p className="text-slate-600 text-sm">
          {language === 'sw'
            ? 'Jaribu muundo wa menyu za USSD, uhakiki wa namba 6 za siri (OTP), na ufikiaji wa taarifa za wazazi moja kwa moja.'
            : 'Test USSD menu paths, multi-school routing, and 6-digit OTP verification live against the state engine.'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
        {/* Settings Panel */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="font-semibold text-slate-800 text-base flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-teal-600" />
            {language === 'sw' ? 'Vigezo vya Mwigaji' : 'Simulation Parameters'}
          </h2>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {language === 'sw' ? 'Namba ya Simu ya Mzazi (E.164)' : 'Parent Phone Number (E.164)'}
            </label>
            <input
              type="text"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {language === 'sw' ? 'Nambari ya Huduma (Service Code)' : 'Service Code'}
            </label>
            <input
              type="text"
              value={serviceCode}
              onChange={(e) => setServiceCode(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono"
            />
          </div>

          <button
            onClick={startSession}
            disabled={loading}
            className="w-full py-2.5 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 transition flex items-center justify-center gap-2 shadow-sm"
          >
            <PhoneCall className="w-4 h-4" />
            {language === 'sw' ? 'Piga Nambari (*Piga*)' : 'Dial / Start USSD'}
          </button>
        </div>

        {/* Phone Mockup Screen */}
        <div className="md:col-span-2 flex justify-center">
          <div className="w-full max-w-sm bg-slate-900 p-6 rounded-[2.5rem] shadow-2xl border-4 border-slate-800">
            {/* Phone Speaker & Notch */}
            <div className="w-24 h-4 bg-slate-800 rounded-full mx-auto mb-6"></div>

            {/* USSD Display Box */}
            <div className="bg-slate-800 rounded-2xl p-5 border border-slate-700 min-h-[220px] flex flex-col justify-between">
              <div className="text-emerald-400 font-mono text-sm whitespace-pre-wrap leading-relaxed">
                {screenText}
              </div>

              {isSessionActive && (
                <form onSubmit={sendStep} className="mt-4 pt-3 border-t border-slate-700 flex gap-2">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Chaguo (1, 2, n.k)..."
                    autoFocus
                    className="flex-1 bg-slate-900 border border-slate-600 rounded px-3 py-1.5 text-white font-mono text-sm focus:outline-none focus:border-teal-500"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-3 py-1.5 bg-teal-500 text-slate-900 font-bold rounded text-xs hover:bg-teal-400"
                  >
                    Send
                  </button>
                </form>
              )}
            </div>

            {/* Keypad Buttons */}
            <div className="grid grid-cols-3 gap-3 mt-6">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((k) => (
                <button
                  key={k}
                  onClick={() => setUserInput((prev) => prev + k)}
                  className="py-3 bg-slate-800 hover:bg-slate-700 text-white font-mono font-bold rounded-xl border border-slate-700 text-base active:bg-teal-600 transition"
                >
                  {k}
                </button>
              ))}
            </div>

            {/* End session control */}
            <div className="mt-6 flex justify-between items-center text-xs text-slate-500 px-2">
              <span>Hali: {isSessionActive ? 'Kipindi Kinaendelea' : 'Kipindi Kimefungwa'}</span>
              <button
                onClick={startSession}
                className="text-teal-400 hover:underline flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                {language === 'sw' ? 'Anza Upya' : 'Restart'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
