import { useState } from 'react';

export default function Home() {
  const [domain, setDomain] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('fast'); // 'fast' or 'deep'

  const BACKEND_URL = "https://vasic-backend.onrender.com"; // Your Live Backend

  const handleSearch = async () => {
    if (!domain) return;
    setLoading(true);
    setError('');
    setResults(null);

    // Choose endpoint based on tab
    const endpoint = activeTab === 'deep' ? '/deep-search' : '/scan-website';

    try {
      const res = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain }),
      });

      const data = await res.json();

      if (data.status === 'success') {
        setResults(data);
      } else {
        setError(data.message || 'Scan failed.');
      }
    } catch (err) {
      setError('Network error. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans">
      <div className="max-w-2xl mx-auto bg-white p-6 rounded-xl shadow-lg">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Vasic Automation 🚀</h1>
        <p className="text-gray-500 mb-6">Find decision maker emails instantly.</p>

        {/* --- TABS --- */}
        <div className="flex space-x-4 mb-6 border-b">
          <button 
            onClick={() => setActiveTab('fast')}
            className={`pb-2 px-4 ${activeTab === 'fast' ? 'border-b-2 border-blue-600 text-blue-600 font-bold' : 'text-gray-500'}`}
          >
            ⚡ Fast Scan (Free)
          </button>
          <button 
            onClick={() => setActiveTab('deep')}
            className={`pb-2 px-4 ${activeTab === 'deep' ? 'border-b-2 border-purple-600 text-purple-600 font-bold' : 'text-gray-500'}`}
          >
            🔍 Deep Search (Pro)
          </button>
        </div>

        {/* --- INPUT --- */}
        <div className="flex gap-2 mb-6">
          <input
            type="text"
            placeholder="e.g. tesla.com"
            className="flex-1 border p-3 rounded-lg focus:outline-none focus:ring-2 ring-blue-500"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className={`px-6 py-3 rounded-lg text-white font-bold transition ${
              activeTab === 'deep' ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'
            } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Scanning...' : 'Find Emails'}
          </button>
        </div>

        {/* --- ERROR MESSAGE --- */}
        {error && (
          <div className="p-4 mb-6 bg-red-50 text-red-600 rounded-lg border border-red-200">
            ❌ {error}
          </div>
        )}

        {/* --- RESULTS DISPLAY --- */}
        {results && (
          <div className="space-y-6 animate-fade-in">
            {/* 1. EMAILS FOUND */}
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <h3 className="text-green-800 font-bold mb-2 flex items-center">
                ✅ Found {results.emails.length} Emails
              </h3>
              {results.emails.length > 0 ? (
                <ul className="space-y-2">
                  {results.emails.map((email, i) => (
                    <li key={i} className="flex justify-between items-center bg-white p-2 rounded border border-green-100">
                      <span className="font-mono text-gray-700">{email}</span>
                      <button 
                        onClick={() => navigator.clipboard.writeText(email)}
                        className="text-xs text-blue-500 hover:underline"
                      >
                        Copy
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 italic">No direct emails found on this pass.</p>
              )}
            </div>

            {/* 2. VERIFIED SOURCES (Only for Deep Search) */}
            {results.related_links && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 className="text-gray-700 font-bold mb-2 text-sm uppercase tracking-wide">
                  Verified Sources (Google)
                </h3>
                <ul className="space-y-2 text-sm">
                  {results.related_links.map((link, i) => (
                    <li key={i}>
                      <a href={link.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline truncate block">
                        🔗 {link.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}