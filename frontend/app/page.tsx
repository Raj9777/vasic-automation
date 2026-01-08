"use client";
import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [activeTab, setActiveTab] = useState('single');
  const [url, setUrl] = useState('');
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const handleScrape = async () => {
    if (!url) return;
    setLoading(true);
    setStatus('Scanning website... this may take 10-20 seconds...');
    setLeads([]);

    try {
      const response = await axios.post('https://vasic-backend.onrender.com/scrape', { url });
      setLeads(response.data.leads);
      if (response.data.leads.length > 0) {
        setStatus(`Success! Found ${response.data.leads.length} verified leads.`);
      } else {
        setStatus('No emails found on this page.');
      }
    } catch (error) {
      setStatus('Error: Could not scan this site.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-8 font-sans">
      <h1 className="text-5xl font-extrabold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
        Vasic Automation
      </h1>
      <p className="mb-8 text-gray-400 text-lg">AI-Powered Decision Maker Verification</p>

      {/* TABS */}
      <div className="flex space-x-4 mb-8 bg-gray-800 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('single')}
          className={`px-6 py-2 rounded-md font-bold transition ${
            activeTab === 'single' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'
          }`}
        >
          Single Scan (Free)
        </button>
        <button
          onClick={() => setActiveTab('bulk')}
          className={`px-6 py-2 rounded-md font-bold transition flex items-center ${
            activeTab === 'bulk' ? 'bg-purple-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'
          }`}
        >
          Bulk Scan <span className="ml-2 text-xs bg-yellow-500 text-black px-1.5 rounded uppercase">Pro</span>
        </button>
      </div>

      {/* SINGLE SCAN VIEW */}
      {activeTab === 'single' && (
        <div className="w-full max-w-2xl bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
          <label className="block text-sm font-bold mb-3 text-gray-300">Target Website URL</label>
          <div className="flex space-x-2 mb-6">
            <input
              type="text"
              className="flex-1 p-4 rounded-xl bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-lg"
              placeholder="https://example-agency.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button
              onClick={handleScrape}
              disabled={loading}
              className={`px-8 rounded-xl font-bold text-lg transition ${
                loading ? 'bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 shadow-blue-500/50 shadow-lg'
              }`}
            >
              {loading ? 'Scanning...' : 'Scan'}
            </button>
          </div>

          {status && <p className="mb-4 text-center text-sm text-yellow-400 animate-pulse">{status}</p>}

          {leads.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
              <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 font-bold text-xs text-gray-400 uppercase tracking-wider">
                Results
              </div>
              {leads.map((lead, index) => (
                <div key={index} className="p-4 border-b border-gray-800 last:border-0 flex justify-between items-center hover:bg-gray-800/50 transition">
                  <div className="flex flex-col">
                    <span className="font-mono text-white text-base">{lead.email}</span>
                    <span className="text-xs text-gray-500 mt-0.5">{lead.source}</span>
                  </div>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-bold shadow-sm ${
                    lead.confidence.includes('HIGH') ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 
                    lead.confidence.includes('Team') ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  }`}>
                    {lead.confidence}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* BULK SCAN VIEW (LOCKED) */}
      {activeTab === 'bulk' && (
        <div className="w-full max-w-2xl bg-gray-800 p-12 rounded-2xl shadow-2xl border border-purple-500/30 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
            PREMIUM
          </div>
          <h2 className="text-3xl font-bold mb-4">Unlock Bulk Power ⚡</h2>
          <p className="text-gray-400 mb-8 max-w-md mx-auto">
            Upload a CSV of 500+ websites and verify thousands of leads in minutes. 
            Export directly to HubSpot or Salesforce.
          </p>
          
          <div className="bg-gray-900/50 p-6 rounded-xl mb-8 border border-gray-700 text-left opacity-50 blur-sm select-none">
             <div className="h-4 bg-gray-700 rounded w-3/4 mb-3"></div>
             <div className="h-4 bg-gray-700 rounded w-1/2 mb-3"></div>
             <div className="h-4 bg-gray-700 rounded w-full"></div>
          </div>

          <button className="bg-gradient-to-r from-purple-600 to-pink-600 px-8 py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-purple-500/20 transition transform hover:-translate-y-1">
            Get Pro Access ($29/mo)
          </button>
          
          <p className="mt-4 text-xs text-gray-500">
            Limited spots for Beta. <a href="mailto:founder@vasic.io" className="text-blue-400 hover:underline">Contact Sales</a>
          </p>
        </div>
      )}
    </div>
  );
}
