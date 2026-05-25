import { useState } from 'react';
import { X } from 'lucide-react';

export default function LoginModal({ close, setUserName }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    if (!email) return;

    setMessage('');
    setIsError(false);

    // Strict Domain Validation
    if (!email.toLowerCase().endsWith('@thapar.edu')) {
      setIsError(true);
      setMessage('Not in Organization. Only @thapar.edu emails are allowed.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/auth/send-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Check your Thapar email inbox for your login link!');
      } else {
        setIsError(true);
        setMessage(data.detail || 'Something went wrong. Try again.');
      }
    } catch (error) {
      setIsError(true);
      setMessage('Cannot connect to the server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-[#212121] w-full max-w-[400px] rounded-2xl p-8 relative border border-white/10">
        <button onClick={close} className="absolute top-4 right-4 text-gray-500 hover:text-white">
          <X size={20} />
        </button>

        <h2 className="text-2xl font-bold text-center mb-2">Thapar Workspace Login</h2>
        <p className="text-sm text-gray-400 text-center mb-8">
          Sign in using your institutional email address.
        </p>

        {/* Dynamic Alert Banner */}
        {message && (
          <div className={`text-sm text-center mb-4 p-3 rounded-xl border transition-all duration-300 ${isError
            ? 'bg-red-500/10 text-red-400 border-red-500/20 animate-pulse'
            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
            }`}>
            {message}
          </div>
        )}

        <form onSubmit={handleEmailLogin} className="space-y-3">
          <input
            type="email"
            placeholder="rollnumber@thapar.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            className="w-full bg-[#303030] border border-white/10 p-3 rounded-xl outline-none focus:ring-1 ring-white/30 disabled:opacity-50 text-white"
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-black font-bold py-3 rounded-xl hover:bg-gray-200 transition disabled:opacity-50"
          >
            {loading ? 'Sending Link...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}
